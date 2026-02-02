# apps/immunization/models.py
from django.db import models
from django.utils import timezone
from datetime import date, timedelta
from apps.users.models import CustomUser, Facility
from apps.delivery.models import Baby


class VaccineType(models.Model):
    """
    Master list of vaccines in Kenya EPI schedule
    """
    
    name = models.CharField(
        max_length=100,
        unique=True,
        help_text="Vaccine name (e.g., BCG, OPV 1, Pentavalent 1)"
    )
    description = models.TextField(
        blank=True,
        help_text="What this vaccine protects against"
    )
    recommended_age_weeks = models.IntegerField(
        help_text="Recommended age in weeks when vaccine should be given"
    )
    is_active = models.BooleanField(
        default=True,
        help_text="Is this vaccine currently in use?"
    )
    
    # Additional Info
    route = models.CharField(
        max_length=50,
        blank=True,
        help_text="Route of administration (oral, IM, SC, ID)"
    )
    site = models.CharField(
        max_length=50,
        blank=True,
        help_text="Site of administration (right thigh, left thigh, etc.)"
    )
    dosage = models.CharField(
        max_length=50,
        blank=True,
        help_text="Dosage (e.g., 0.5ml, 2 drops)"
    )
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'vaccine_types'
        ordering = ['recommended_age_weeks', 'name']
        verbose_name = 'Vaccine Type'
        verbose_name_plural = 'Vaccine Types'
    
    def __str__(self):
        return f"{self.name} (Week {self.recommended_age_weeks})"
    
    @property
    def age_display(self):
        """Human-readable age"""
        weeks = self.recommended_age_weeks
        if weeks == 0:
            return "At Birth"
        elif weeks < 4:
            return f"{weeks} weeks"
        elif weeks < 52:
            months = weeks // 4
            return f"{months} months"
        else:
            years = weeks // 52
            return f"{years} year{'s' if years > 1 else ''}"


class ImmunizationSchedule(models.Model):
    """
    Auto-generated immunization schedule for each baby
    Created when baby is registered
    """
    
    # Links
    baby = models.ForeignKey(
        Baby,
        on_delete=models.CASCADE,
        related_name='immunization_schedules',
        help_text="Baby this vaccine is scheduled for"
    )
    vaccine = models.ForeignKey(
        VaccineType,
        on_delete=models.PROTECT,
        related_name='schedules',
        help_text="Type of vaccine"
    )
    
    # Scheduling
    scheduled_date = models.DateField(
        help_text="Date when vaccine is scheduled (AUTO-CALCULATED)"
    )
    
    # Administration
    administered = models.BooleanField(
        default=False,
        help_text="Has vaccine been given?"
    )
    administration_date = models.DateField(
        null=True,
        blank=True,
        help_text="Date when vaccine was actually given"
    )
    missed = models.BooleanField(
        default=False,
        help_text="Was vaccine missed? (more than 4 weeks overdue)"
    )
    
    # Vaccine Details
    batch_number = models.CharField(
        max_length=50,
        blank=True,
        help_text="Vaccine batch/lot number"
    )
    expiry_date = models.DateField(
        null=True,
        blank=True,
        help_text="Vaccine expiry date"
    )
    
    # Staff & Facility
    administered_by = models.ForeignKey(
        CustomUser,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='administered_vaccines',
        help_text="Healthcare worker who administered vaccine"
    )
    facility = models.ForeignKey(
        Facility,
        on_delete=models.PROTECT,
        related_name='immunizations',
        help_text="Facility where vaccine was/will be given"
    )
    
    # Adverse Events
    adverse_event = models.BooleanField(
        default=False,
        help_text="Did baby experience any adverse event?"
    )
    adverse_event_details = models.TextField(
        blank=True,
        help_text="Details of adverse event (fever, rash, swelling, etc.)"
    )
    
    # Notes
    notes = models.TextField(
        blank=True,
        help_text="Additional notes"
    )
    
    # Metadata
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'immunization_schedules'
        ordering = ['baby', 'scheduled_date']
        verbose_name = 'Immunization Schedule'
        verbose_name_plural = 'Immunization Schedules'
        unique_together = ['baby', 'vaccine']
        indexes = [
            models.Index(fields=['facility', 'scheduled_date']),
            models.Index(fields=['scheduled_date', 'administered']),
            models.Index(fields=['baby', 'administered']),
        ]
    
    def save(self, *args, **kwargs):
        """
        Auto-mark as missed if vaccine is more than 4 weeks overdue
        """
        if not self.administered and not self.missed and self.scheduled_date:
            # Check if vaccine is more than 4 weeks (28 days) overdue
            if self.scheduled_date < date.today() - timedelta(weeks=4):
                self.missed = True
        
        super().save(*args, **kwargs)
    
    def __str__(self):
        status = "✓ Given" if self.administered else ("✗ Missed" if self.missed else "Scheduled")
        return f"{self.baby.display_name} - {self.vaccine.name} ({status})"
    
    @property
    def status(self):
        """Get vaccination status"""
        if not self.scheduled_date:
            return "Not Scheduled"
        
        if self.administered:
            return "Administered"
        elif self.missed:
            return "Missed"
        elif self.scheduled_date < date.today():
            return "Overdue"
        elif self.scheduled_date == date.today():
            return "Due Today"
        else:
            return "Upcoming"
    
    @property
    def is_overdue(self):
        """Check if vaccine is overdue"""
        if not self.scheduled_date:
            return False
        return not self.administered and not self.missed and self.scheduled_date < date.today()
    
    @property
    def days_until_due(self):
        """Calculate days until vaccine is due"""
        if self.administered or self.missed or not self.scheduled_date:
            return 0
        return (self.scheduled_date - date.today()).days
    
    @property
    def is_due_soon(self):
        """Check if vaccine is due within 3 days (for SMS reminders)"""
        if self.administered or self.missed or not self.scheduled_date:
            return False
        days = self.days_until_due
        return 0 <= days <= 3
    
    @property
    def baby_age_at_schedule(self):
        """Baby's age in weeks when vaccine is scheduled"""
        if not self.scheduled_date:
            return None
        days = (self.scheduled_date - self.baby.delivery.delivery_date).days
        return days // 7


# ============================================================================
# UTILITY FUNCTIONS
# ============================================================================

def get_upcoming_immunizations(facility=None, days=7):
    """
    Get immunizations scheduled in the next X days
    Used for dashboard displays
    """
    today = date.today()
    end_date = today + timedelta(days=days)
    
    queryset = ImmunizationSchedule.objects.filter(
        scheduled_date__range=[today, end_date],
        administered=False,
        missed=False
    ).select_related('baby__mother', 'vaccine', 'facility')
    
    if facility:
        queryset = queryset.filter(facility=facility)
    
    return queryset.order_by('scheduled_date')


def get_missed_immunizations(facility=None):
    """
    Get all missed immunizations that need follow-up
    """
    queryset = ImmunizationSchedule.objects.filter(
        missed=True
    ).select_related('baby__mother', 'vaccine', 'facility')
    
    if facility:
        queryset = queryset.filter(facility=facility)
    
    return queryset.order_by('scheduled_date')


def get_overdue_immunizations(facility=None):
    """
    Get vaccines that are overdue but not yet marked as missed
    """
    today = date.today()
    
    queryset = ImmunizationSchedule.objects.filter(
        scheduled_date__lt=today,
        administered=False,
        missed=False
    ).select_related('baby__mother', 'vaccine', 'facility')
    
    if facility:
        queryset = queryset.filter(facility=facility)
    
    return queryset.order_by('scheduled_date')


def mark_overdue_vaccines_as_missed(weeks_overdue=4):
    """
    Automatically mark vaccines as missed if they're overdue by X weeks
    Should be run daily via cron job
    """
    cutoff_date = date.today() - timedelta(weeks=weeks_overdue)
    
    overdue_vaccines = ImmunizationSchedule.objects.filter(
        scheduled_date__lt=cutoff_date,
        administered=False,
        missed=False
    )
    
    count = overdue_vaccines.update(missed=True)
    
    return count  # Number of vaccines marked as missed