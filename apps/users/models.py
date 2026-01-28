# apps/users/models.py
from django.db import models
from django.core.validators import RegexValidator
from django.contrib.auth.models import AbstractUser


class Facility(models.Model):
    """
    Health facilities following Kenya's 6-level health system
    Based on Kenya Health Policy 2014-2030
    """
    
    FACILITY_LEVELS = [
        ('LEVEL_1', 'Level 1 - Community Health Services'),
        ('LEVEL_2', 'Level 2 - Dispensaries and Clinics'),
        ('LEVEL_3', 'Level 3 - Health Centres and Maternity Homes'),
        ('LEVEL_4', 'Level 4 - Primary Hospitals (Sub-County)'),
        ('LEVEL_5', 'Level 5 - Secondary Hospitals (County Referral)'),
        ('LEVEL_6', 'Level 6 - Tertiary Hospitals (National Referral)'),
    ]
    
    # Basic Information
    name = models.CharField(
        max_length=200,
        help_text="Official facility name"
    )
    facility_level = models.CharField(
        max_length=20,
        choices=FACILITY_LEVELS,
        help_text="Kenya health system level (1-6)"
    )
    mfl_code = models.CharField(
        max_length=20,
        blank=True,
        help_text="Master Facility List Code (if available)"
    )
    
    # Location Information
    county = models.CharField(max_length=100)
    sub_county = models.CharField(max_length=100)
    ward = models.CharField(max_length=100, blank=True)
    village = models.CharField(max_length=100, blank=True)
    
    # Contact Information
    phone_regex = RegexValidator(
        regex=r'^\+?254?\d{9,12}$',
        message="Phone format: '+254712345678'"
    )
    phone_number = models.CharField(
        validators=[phone_regex],
        max_length=15
    )
    alternate_phone = models.CharField(
        max_length=15,
        blank=True
    )
    email = models.EmailField(blank=True)
    
    # Operational Status
    is_active = models.BooleanField(
        default=True,
        help_text="Is facility currently operational?"
    )
    is_24_hours = models.BooleanField(
        default=False,
        help_text="Does facility operate 24/7?"
    )
    has_maternity_services = models.BooleanField(
        default=True,
        help_text="Does facility provide maternal health services?"
    )
    
    # Metadata
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'facilities'
        ordering = ['county', 'facility_level', 'name']
        verbose_name = 'Facility'
        verbose_name_plural = 'Facilities'
        indexes = [
            models.Index(fields=['county', 'sub_county']),
            models.Index(fields=['facility_level']),
        ]
    
    def __str__(self):
        return f"{self.name} ({self.get_facility_level_display()}) - {self.county}"
    
    def get_level_number(self):
        """Returns just the level number (1-6)"""
        return self.facility_level.split('_')[1]
```

---

class CustomUser(AbstractUser):
    """
    Extended user model for maternal health system
    Supports role-based access: Nurses/CHVs, Facility Managers, MOH Administrators
    """
    
    ROLE_CHOICES = [
        ('NURSE', 'Nurse/CHV'),
        ('MANAGER', 'Facility Manager'),
        ('MOH', 'MOH Administrator'),
    ]
    
    # Role & Access
    role = models.CharField(
        max_length=20,
        choices=ROLE_CHOICES,
        help_text="User's role in the system"
    )
    
    # Contact Information
    phone_regex = RegexValidator(
        regex=r'^\+?254?\d{9,12}$',
        message="Phone format: '+254712345678'"
    )
    phone_number = models.CharField(
        validators=[phone_regex],
        max_length=15,
        unique=True,
        help_text="User's mobile number (must be unique)"
    )
    
    # Facility Assignment
    facility = models.ForeignKey(
        Facility,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='staff',
        help_text="Health facility where user works (optional for MOH admins)"
    )
    
    # Additional Fields
    is_active_user = models.BooleanField(
        default=True,
        help_text="Can this user access the system?"
    )
    
    # Metadata
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'users'
        ordering = ['-date_joined']
        verbose_name = 'User'
        verbose_name_plural = 'Users'
        indexes = [
            models.Index(fields=['role']),
            models.Index(fields=['facility']),
        ]
    
    def __str__(self):
        return f"{self.get_full_name()} ({self.get_role_display()})"
    
    def get_facility_name(self):
        """Returns facility name or 'No Facility' for MOH admins"""
        return self.facility.name if self.facility else "No Facility (MOH)"
    
    def can_manage_facility(self):
        """Check if user has facility management permissions"""
        return self.role in ['MANAGER', 'MOH']
    
    def can_view_all_facilities(self):
        """Check if user can view all facilities (MOH only)"""
        return self.role == 'MOH'