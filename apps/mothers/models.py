# apps/mothers/models.py
from django.db import models
from django.core.validators import RegexValidator
from django.utils import timezone
from datetime import timedelta, date
from apps.users.models import CustomUser, Facility


class Mother(models.Model):
    """
    Registered mothers in the maternal health system
    Core patient information for tracking maternal health
    """
    
    # Personal Information
    first_name = models.CharField(
        max_length=100,
        help_text="Mother's first name"
    )
    last_name = models.CharField(
        max_length=100,
        help_text="Mother's last name"
    )
    date_of_birth = models.DateField(
        help_text="Mother's date of birth (for age calculation)"
    )
    
    # Identification
    national_id = models.CharField(
        max_length=20,
        unique=True,
        blank=True,
        null=True,
        help_text="National ID number (if available)"
    )
    
    # Contact Information
    phone_regex = RegexValidator(
        regex=r'^\+?254?\d{9,12}$',
        message="Phone format: '+254712345678'"
    )
    phone_number = models.CharField(
        validators=[phone_regex],
        max_length=15,
        help_text="Primary phone number for SMS reminders (REQUIRED)"
    )
    alternate_phone = models.CharField(
        max_length=15,
        blank=True,
        help_text="Alternative contact number"
    )
    
    # Location Information
    county = models.CharField(
        max_length=100,
        help_text="County of residence"
    )
    sub_county = models.CharField(
        max_length=100,
        help_text="Sub-county of residence"
    )
    ward = models.CharField(
        max_length=100,
        help_text="Ward of residence"
    )
    village = models.CharField(
        max_length=100,
        blank=True,
        help_text="Village/Estate (optional)"
    )
    
    # Facility Assignment
    facility = models.ForeignKey(
        Facility,
        on_delete=models.PROTECT,
        related_name='mothers',
        help_text="Health facility where mother is registered"
    )
    registered_by = models.ForeignKey(
        CustomUser,
        on_delete=models.SET_NULL,
        null=True,
        related_name='registered_mothers',
        help_text="Nurse/CHV who registered this mother"
    )
    registration_date = models.DateField(
        auto_now_add=True,
        help_text="Date when mother was registered in the system"
    )
    
    # Emergency Contact
    next_of_kin_name = models.CharField(
        max_length=200,
        blank=True,
        help_text="Next of kin full name"
    )
    next_of_kin_phone = models.CharField(
        max_length=15,
        blank=True,
        help_text="Next of kin phone number"
    )
    next_of_kin_relationship = models.CharField(
        max_length=50,
        blank=True,
        help_text="Relationship to mother (e.g., Husband, Sister, Mother)"
    )
    
    # Status
    is_active = models.BooleanField(
        default=True,
        help_text="Is this mother's record active in the system?"
    )
    
    # Metadata
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'mothers'
        ordering = ['-registration_date']
        verbose_name = 'Mother'
        verbose_name_plural = 'Mothers'
        indexes = [
            models.Index(fields=['facility', 'is_active']),
            models.Index(fields=['phone_number']),
            models.Index(fields=['county', 'sub_county']),
        ]
    
    def __str__(self):
        return f"{self.first_name} {self.last_name} - {self.phone_number}"
    
    @property
    def full_name(self):
        """Returns mother's full name"""
        return f"{self.first_name} {self.last_name}"
    
    @property
    def age(self):
        """Calculate mother's current age in years"""
        today = date.today()
        age = today.year - self.date_of_birth.year
        # Adjust if birthday hasn't occurred this year
        if (today.month, today.day) < (self.date_of_birth.month, self.date_of_birth.day):
            age -= 1
        return age
    
    @property
    def active_pregnancy(self):
        """Get mother's current active pregnancy (if any)"""
        return self.pregnancies.filter(status='ACTIVE').first()
    
    @property
    def has_active_pregnancy(self):
        """Check if mother has an active pregnancy"""
        return self.pregnancies.filter(status='ACTIVE').exists()
    
    @property
    def total_pregnancies(self):
        """Count total number of pregnancies"""
        return self.pregnancies.count()
    
    def get_location_display(self):
        """Returns formatted location string"""
        location_parts = [self.village, self.ward, self.sub_county, self.county]
        return ", ".join([part for part in location_parts if part])


class Pregnancy(models.Model):
    """
    Pregnancy records with automatic EDD calculation and risk assessment
    Tracks individual pregnancies for mothers
    """
    
    RISK_LEVELS = [
        ('LOW', 'Low Risk'),
        ('MEDIUM', 'Medium Risk'),
        ('HIGH', 'High Risk'),
    ]
    
    STATUS_CHOICES = [
        ('ACTIVE', 'Active'),
        ('DELIVERED', 'Delivered'),
        ('MISCARRIAGE', 'Miscarriage'),
        ('STILLBIRTH', 'Stillbirth'),
        ('TRANSFERRED', 'Transferred to Another Facility'),
    ]
    
    # Basic Information
    mother = models.ForeignKey(
        Mother,
        on_delete=models.CASCADE,
        related_name='pregnancies',
        help_text="Mother for this pregnancy"
    )
    pregnancy_number = models.IntegerField(
        help_text="Gravida - Total number of pregnancies including current (1, 2, 3, etc.)"
    )
    
    # Pregnancy Dates (AUTO-CALCULATED)
    lmp = models.DateField(
        verbose_name="Last Menstrual Period",
        help_text="First day of last menstrual period (used to calculate EDD)"
    )
    edd = models.DateField(
        verbose_name="Estimated Due Date",
        editable=False,
        help_text="AUTO-CALCULATED: LMP + 280 days (40 weeks)"
    )
    gestational_age_weeks = models.IntegerField(
        editable=False,
        default=0,
        help_text="AUTO-CALCULATED: Current weeks of pregnancy"
    )
    
    # Risk Assessment
    risk_level = models.CharField(
        max_length=20,
        choices=RISK_LEVELS,
        default='LOW',
        help_text="Risk level based on maternal factors"
    )
    risk_factors = models.TextField(
        blank=True,
        help_text="Details: High BP, diabetes, previous C-section, age >35, etc."
    )
    
    # Status
    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default='ACTIVE',
        help_text="Current status of this pregnancy"
    )
    
    # Facility & Registration
    facility = models.ForeignKey(
        Facility,
        on_delete=models.PROTECT,
        related_name='pregnancies',
        help_text="Facility where pregnancy is being managed"
    )
    registered_by = models.ForeignKey(
        CustomUser,
        on_delete=models.SET_NULL,
        null=True,
        related_name='registered_pregnancies',
        help_text="Nurse/CHV who registered this pregnancy"
    )
    registration_date = models.DateField(
        auto_now_add=True,
        help_text="Date when pregnancy was registered"
    )
    
    # Obstetric History
    parity = models.IntegerField(
        default=0,
        help_text="Number of previous deliveries (P0, P1, P2, etc.)"
    )
    previous_csection = models.BooleanField(
        default=False,
        help_text="Has mother had a C-section before?"
    )
    previous_complications = models.TextField(
        blank=True,
        help_text="Details of any previous pregnancy/delivery complications"
    )
    
    # Additional Notes
    notes = models.TextField(
        blank=True,
        help_text="Additional clinical notes"
    )
    
    # Metadata
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'pregnancies'
        ordering = ['-registration_date']
        verbose_name = 'Pregnancy'
        verbose_name_plural = 'Pregnancies'
        unique_together = ['mother', 'pregnancy_number']
        indexes = [
            models.Index(fields=['facility', 'status']),
            models.Index(fields=['edd']),
            models.Index(fields=['risk_level', 'status']),
        ]
    
    def save(self, *args, **kwargs):
        """
        AUTO-CALCULATE EDD and gestational age before saving
        This is the MAGIC that makes the system smart!
        """
        if self.lmp:
            # Calculate EDD = LMP + 280 days (40 weeks)
            self.edd = self.lmp + timedelta(days=280)
            
            # Calculate current gestational age in weeks
            today = date.today()
            days_pregnant = (today - self.lmp).days
            self.gestational_age_weeks = max(0, days_pregnant // 7)  # Ensure non-negative
        
        super().save(*args, **kwargs)
    
    def __str__(self):
        return f"{self.mother.full_name} - G{self.pregnancy_number}P{self.parity} (EDD: {self.edd})"
    
    @property
    def gravida_para_display(self):
        """Returns G/P notation (e.g., G2P1)"""
        return f"G{self.pregnancy_number}P{self.parity}"
    
    @property
    def weeks_remaining(self):
        """Calculate weeks until EDD"""
        if self.status != 'ACTIVE':
            return 0
        today = date.today()
        days_remaining = (self.edd - today).days
        return max(0, days_remaining // 7)
    
    @property
    def days_remaining(self):
        """Calculate days until EDD"""
        if self.status != 'ACTIVE':
            return 0
        today = date.today()
        return max(0, (self.edd - today).days)
    
    @property
    def is_overdue(self):
        """Check if pregnancy is past EDD"""
        return date.today() > self.edd and self.status == 'ACTIVE'
    
    @property
    def trimester(self):
        """Get current trimester (1, 2, or 3)"""
        if self.gestational_age_weeks <= 12:
            return 1
        elif self.gestational_age_weeks <= 26:
            return 2
        else:
            return 3
    
    @property
    def is_high_risk(self):
        """Check if pregnancy is flagged as high risk"""
        return self.risk_level == 'HIGH'
    
    def get_gestational_age_display(self):
        """Returns formatted gestational age (e.g., '24 weeks')"""
        return f"{self.gestational_age_weeks} weeks"
    
    def get_time_to_delivery_display(self):
        """Returns human-readable time until delivery"""
        if self.status != 'ACTIVE':
            return f"Status: {self.get_status_display()}"
        
        if self.is_overdue:
            days_overdue = (date.today() - self.edd).days
            return f"Overdue by {days_overdue} days"
        
        weeks = self.weeks_remaining
        days = self.days_remaining % 7
        
        if weeks == 0:
            return f"{days} days remaining"
        elif days == 0:
            return f"{weeks} weeks remaining"
        else:
            return f"{weeks} weeks, {days} days remaining"