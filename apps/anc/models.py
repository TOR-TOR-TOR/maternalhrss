# apps/anc/models.py
from django.db import models
from django.utils import timezone
from datetime import date, timedelta
from apps.users.models import CustomUser, Facility
from apps.mothers.models import Pregnancy


class ANCVisit(models.Model):
    """
    Antenatal Care (ANC) visit records
    Tracks each of the 4 required ANC visits during pregnancy
    Auto-generated when pregnancy is registered
    """
    
    # Basic Information
    pregnancy = models.ForeignKey(
        Pregnancy,
        on_delete=models.CASCADE,
        related_name='anc_visits',
        help_text="Pregnancy this visit belongs to"
    )
    visit_number = models.IntegerField(
        help_text="Contact number (1-8, following Kenya MoH 2022 Guidelines)"
    )
    
    # Visit Scheduling
    scheduled_date = models.DateField(
        help_text="Date when visit is scheduled (AUTO-GENERATED)"
    )
    actual_visit_date = models.DateField(
        null=True,
        blank=True,
        help_text="Date when mother actually attended"
    )
    
    # Attendance Status
    attended = models.BooleanField(
        default=False,
        help_text="Did mother attend this visit?"
    )
    missed = models.BooleanField(
        default=False,
        help_text="Visit was missed (marked after 7+ days late)"
    )
    
    # Clinical Measurements
    weight_kg = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        null=True,
        blank=True,
        help_text="Mother's weight in kilograms"
    )
    blood_pressure = models.CharField(
        max_length=20,
        blank=True,
        help_text="Blood pressure reading (e.g., 120/80)"
    )
    hemoglobin = models.DecimalField(
        max_digits=4,
        decimal_places=1,
        null=True,
        blank=True,
        help_text="Hemoglobin level (g/dL)"
    )
    fundal_height = models.IntegerField(
        null=True,
        blank=True,
        help_text="Fundal height in centimeters"
    )
    fetal_heartbeat = models.BooleanField(
        default=True,
        help_text="Fetal heartbeat detected?"
    )
    
    # Danger Signs
    has_danger_signs = models.BooleanField(
        default=False,
        help_text="Does mother show any danger signs?"
    )
    danger_signs_notes = models.TextField(
        blank=True,
        help_text="Details of danger signs (bleeding, severe headache, blurred vision, etc.)"
    )
    
    # Interventions & Supplements
    iron_given = models.BooleanField(
        default=False,
        help_text="Iron supplement given?"
    )
    folic_acid_given = models.BooleanField(
        default=False,
        help_text="Folic acid supplement given?"
    )
    deworming_done = models.BooleanField(
        default=False,
        help_text="Deworming medication given?"
    )
    tetanus_vaccine_given = models.BooleanField(
        default=False,
        help_text="Tetanus vaccine (TT) given?"
    )
    
    # Clinical Notes
    clinical_notes = models.TextField(
        blank=True,
        help_text="Nurse's clinical observations and notes"
    )
    next_visit_date = models.DateField(
        null=True,
        blank=True,
        help_text="Recommended date for next visit"
    )
    
    # Facility & Staff
    facility = models.ForeignKey(
        Facility,
        on_delete=models.PROTECT,
        related_name='anc_visits',
        help_text="Facility where visit occurred"
    )
    recorded_by = models.ForeignKey(
        CustomUser,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='recorded_anc_visits',
        help_text="Nurse/CHV who recorded this visit"
    )
    
    # Metadata
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'anc_visits'
        ordering = ['pregnancy', 'visit_number']
        verbose_name = 'ANC Visit'
        verbose_name_plural = 'ANC Visits'
        unique_together = ['pregnancy', 'visit_number']
        indexes = [
            models.Index(fields=['facility', 'scheduled_date']),
            models.Index(fields=['scheduled_date', 'attended']),
            models.Index(fields=['pregnancy', 'attended']),
            models.Index(fields=['has_danger_signs']),
        ]
    
    def __str__(self):
        status = "✓ Attended" if self.attended else ("✗ Missed" if self.missed else "Scheduled")
        return f"ANC {self.visit_number} - {self.pregnancy.mother.full_name} ({status})"
    
    def save(self, *args, **kwargs):
        """
        Auto-mark as missed if visit date has passed and not attended
        """
        if not self.attended and not self.missed:
            # Check if visit is more than 7 days overdue
            if self.scheduled_date < date.today() - timedelta(days=7):
                self.missed = True
        
        super().save(*args, **kwargs)
    
    @property
    def status(self):
        """Get visit status as string"""
        if self.attended:
            return "Attended"
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
        """Check if visit is overdue"""
        return not self.attended and not self.missed and self.scheduled_date < date.today()
    
    @property
    def days_until_visit(self):
        """Calculate days until scheduled visit"""
        if self.attended or self.missed:
            return 0
        return (self.scheduled_date - date.today()).days
    
    @property
    def is_due_soon(self):
        """Check if visit is due within 3 days (for SMS reminders)"""
        if self.attended or self.missed:
            return False
        days = self.days_until_visit
        return 0 <= days <= 3
    
    def get_clinical_summary(self):
        """Get summary of clinical measurements"""
        summary = []
        if self.weight_kg:
            summary.append(f"Weight: {self.weight_kg}kg")
        if self.blood_pressure:
            summary.append(f"BP: {self.blood_pressure}")
        if self.hemoglobin:
            summary.append(f"Hb: {self.hemoglobin}g/dL")
        if self.fundal_height:
            summary.append(f"FH: {self.fundal_height}cm")
        
        return ", ".join(summary) if summary else "No measurements recorded"
    
    def get_supplements_given(self):
        """Get list of supplements/interventions given"""
        supplements = []
        if self.iron_given:
            supplements.append("Iron")
        if self.folic_acid_given:
            supplements.append("Folic Acid")
        if self.deworming_done:
            supplements.append("Deworming")
        if self.tetanus_vaccine_given:
            supplements.append("TT Vaccine")
        
        return ", ".join(supplements) if supplements else "None"


# ============================================================================
# SIGNAL TO AUTO-GENERATE ANC VISITS WHEN PREGNANCY IS CREATED
# ============================================================================

from django.db.models.signals import post_save
from django.dispatch import receiver

@receiver(post_save, sender=Pregnancy)
def auto_generate_anc_visits(sender, instance, created, **kwargs):
    """
    Automatically generate 8 ANC contact schedules when a new pregnancy is registered
    Following Kenya Ministry of Health Guidelines 2022
    
    Kenya 8-Contact ANC Model:
    - Contact 1: Week 8-12 (1st Trimester) - we use week 10
    - Contact 2: Week 20 (2nd Trimester)
    - Contact 3: Week 26 (2nd Trimester)
    - Contact 4: Week 30 (3rd Trimester)
    - Contact 5: Week 34 (3rd Trimester)
    - Contact 6: Week 36 (3rd Trimester)
    - Contact 7: Week 38 (3rd Trimester)
    - Contact 8: Week 40 (3rd Trimester)
    
    Distribution: 1 visit in T1, 2 visits in T2, 5 visits in T3
    """
    
    if created and instance.lmp:
        # Define ANC visit schedule based on Kenya MoH 2022 Guidelines
        # (week number, visit number, trimester)
        anc_schedule = [
            (10, 1, 1),   # Contact 1: Week 10 (1st Trimester)
            (20, 2, 2),   # Contact 2: Week 20 (2nd Trimester)
            (26, 3, 2),   # Contact 3: Week 26 (2nd Trimester)
            (30, 4, 3),   # Contact 4: Week 30 (3rd Trimester)
            (34, 5, 3),   # Contact 5: Week 34 (3rd Trimester)
            (36, 6, 3),   # Contact 6: Week 36 (3rd Trimester)
            (38, 7, 3),   # Contact 7: Week 38 (3rd Trimester)
            (40, 8, 3),   # Contact 8: Week 40 (3rd Trimester - at EDD)
        ]
        
        # Create each ANC contact
        for weeks, visit_num, trimester in anc_schedule:
            # Calculate scheduled date: LMP + number of weeks
            scheduled_date = instance.lmp + timedelta(weeks=weeks)
            
            # Only create if doesn't already exist
            ANCVisit.objects.get_or_create(
                pregnancy=instance,
                visit_number=visit_num,
                defaults={
                    'scheduled_date': scheduled_date,
                    'facility': instance.facility,
                }
            )
        
        print(f"✓ Auto-generated 8 ANC contacts for {instance.mother.full_name} (Kenya MoH 2022 Guidelines)")


# ============================================================================
# UTILITY FUNCTIONS
# ============================================================================

def get_upcoming_anc_visits(facility=None, days=7):
    """
    Get ANC visits scheduled in the next X days
    Used for dashboard displays
    """
    today = date.today()
    end_date = today + timedelta(days=days)
    
    queryset = ANCVisit.objects.filter(
        scheduled_date__range=[today, end_date],
        attended=False,
        missed=False,
        pregnancy__status='ACTIVE'
    ).select_related('pregnancy__mother', 'facility')
    
    if facility:
        queryset = queryset.filter(facility=facility)
    
    return queryset.order_by('scheduled_date')


def get_missed_anc_visits(facility=None):
    """
    Get all missed ANC visits that need follow-up
    """
    queryset = ANCVisit.objects.filter(
        missed=True,
        pregnancy__status='ACTIVE'
    ).select_related('pregnancy__mother', 'facility')
    
    if facility:
        queryset = queryset.filter(facility=facility)
    
    return queryset.order_by('scheduled_date')


def get_overdue_anc_visits(facility=None):
    """
    Get visits that are overdue but not yet marked as missed
    (Scheduled date passed, not attended, not marked missed)
    """
    today = date.today()
    
    queryset = ANCVisit.objects.filter(
        scheduled_date__lt=today,
        attended=False,
        missed=False,
        pregnancy__status='ACTIVE'
    ).select_related('pregnancy__mother', 'facility')
    
    if facility:
        queryset = queryset.filter(facility=facility)
    
    return queryset.order_by('scheduled_date')


def mark_overdue_visits_as_missed(days_overdue=7):
    """
    Automatically mark visits as missed if they're overdue by X days
    Should be run daily via cron job
    """
    cutoff_date = date.today() - timedelta(days=days_overdue)
    
    overdue_visits = ANCVisit.objects.filter(
        scheduled_date__lt=cutoff_date,
        attended=False,
        missed=False,
        pregnancy__status='ACTIVE'
    )
    
    count = overdue_visits.update(missed=True)
    
    return count  # Number of visits marked as missed