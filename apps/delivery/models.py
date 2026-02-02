# apps/delivery/models.py
from django.db import models
from django.utils import timezone
from datetime import date, timedelta
from apps.users.models import CustomUser, Facility
from apps.mothers.models import Mother, Pregnancy
from decimal import Decimal



class Delivery(models.Model):
    """
    Delivery records - Birth event details
    Records when and how baby was born
    """
    
    DELIVERY_TYPES = [
        ('SVD', 'Spontaneous Vaginal Delivery (Normal)'),
        ('ASSISTED', 'Assisted Vaginal Delivery (Vacuum/Forceps)'),
        ('CSECTION', 'Caesarean Section'),
        ('BREECH', 'Breech Delivery'),
    ]
    
    DELIVERY_OUTCOMES = [
        ('LIVE', 'Live Birth'),
        ('STILLBIRTH', 'Stillbirth'),
        ('NEONATAL_DEATH', 'Neonatal Death (within 24 hours)'),
    ]
    
    # Link to Pregnancy
    pregnancy = models.OneToOneField(
        Pregnancy,
        on_delete=models.CASCADE,
        related_name='delivery',
        help_text="Pregnancy that ended in this delivery"
    )
    
    # Delivery Date & Time
    delivery_date = models.DateField(
        help_text="Date of delivery"
    )
    delivery_time = models.TimeField(
        help_text="Time of delivery (24-hour format)"
    )
    
    # Delivery Details
    delivery_type = models.CharField(
        max_length=20,
        choices=DELIVERY_TYPES,
        help_text="Type/mode of delivery"
    )
    delivery_outcome = models.CharField(
        max_length=20,
        choices=DELIVERY_OUTCOMES,
        help_text="Outcome of delivery"
    )
    number_of_babies = models.IntegerField(
        default=1,
        help_text="Number of babies born (1=singleton, 2=twins, 3=triplets)"
    )
    
    # Mother's Condition
    mother_condition = models.CharField(
        max_length=100,
        blank=True,
        help_text="Mother's condition after delivery (stable, critical, etc.)"
    )
    complications = models.TextField(
        blank=True,
        help_text="Any complications during delivery (hemorrhage, pre-eclampsia, etc.)"
    )
    blood_loss_ml = models.IntegerField(
        null=True,
        blank=True,
        help_text="Estimated blood loss in milliliters"
    )
    
    # Placenta Details
    placenta_complete = models.BooleanField(
        default=True,
        help_text="Was placenta delivered completely?"
    )
    placenta_weight_grams = models.IntegerField(
        null=True,
        blank=True,
        help_text="Weight of placenta in grams"
    )
    
    # Staff & Facility
    facility = models.ForeignKey(
        Facility,
        on_delete=models.PROTECT,
        related_name='deliveries',
        help_text="Facility where delivery occurred"
    )
    attended_by = models.ForeignKey(
        CustomUser,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='attended_deliveries',
        help_text="Healthcare provider who attended delivery"
    )
    
    # Clinical Notes
    notes = models.TextField(
        blank=True,
        help_text="Additional clinical notes"
    )
    
    # Metadata
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'deliveries'
        ordering = ['-delivery_date', '-delivery_time']
        verbose_name = 'Delivery'
        verbose_name_plural = 'Deliveries'
        indexes = [
            models.Index(fields=['facility', 'delivery_date']),
            models.Index(fields=['delivery_outcome']),
        ]
    
    def save(self, *args, **kwargs):
        """
        Auto-update pregnancy status when delivery is recorded
        """
        super().save(*args, **kwargs)
        
        # Update pregnancy status based on delivery outcome
        if self.delivery_outcome == 'LIVE':
            self.pregnancy.status = 'DELIVERED'
        elif self.delivery_outcome == 'STILLBIRTH':
            self.pregnancy.status = 'STILLBIRTH'
        
        self.pregnancy.save()
    
    def __str__(self):
        return f"Delivery - {self.pregnancy.mother.full_name} on {self.delivery_date} ({self.get_delivery_outcome_display()})"
    
    @property
    def mother(self):
        """Quick access to mother"""
        return self.pregnancy.mother
    
    @property
    def gestational_age_at_delivery(self):
        """Calculate gestational age at delivery in weeks"""
        if self.pregnancy.lmp:
            days = (self.delivery_date - self.pregnancy.lmp).days
            return days // 7
        return None
    
    @property
    def is_preterm(self):
        """Check if delivery was preterm (<37 weeks)"""
        ga = self.gestational_age_at_delivery
        return ga < 37 if ga else None
    
    @property
    def is_term(self):
        """Check if delivery was at term (37-42 weeks)"""
        ga = self.gestational_age_at_delivery
        return 37 <= ga <= 42 if ga else None
    
    @property
    def is_postterm(self):
        """Check if delivery was postterm (>42 weeks)"""
        ga = self.gestational_age_at_delivery
        return ga > 42 if ga else None


class Baby(models.Model):
    """
    Baby registration after delivery
    Triggers auto-generation of immunization schedule
    """
    
    GENDER_CHOICES = [
        ('M', 'Male'),
        ('F', 'Female'),
    ]
    
    # Links
    delivery = models.ForeignKey(
        Delivery,
        on_delete=models.CASCADE,
        related_name='babies',
        help_text="Delivery event when baby was born"
    )
    mother = models.ForeignKey(
        Mother,
        on_delete=models.CASCADE,
        related_name='babies',
        help_text="Mother of this baby"
    )
    
    # Baby Details
    first_name = models.CharField(
        max_length=100,
        blank=True,
        help_text="Baby's first name (can be added later)"
    )
    middle_name = models.CharField(
        max_length=100,
        blank=True,
        help_text="Baby's middle name (optional)"
    )
    last_name = models.CharField(
        max_length=100,
        blank=True,
        help_text="Baby's last name (usually same as mother)"
    )
    gender = models.CharField(
        max_length=1,
        choices=GENDER_CHOICES,
        help_text="Baby's gender"
    )
    
    # Birth Measurements
    birth_weight_grams = models.IntegerField(
        help_text="Birth weight in grams (e.g., 3200 for 3.2kg)"
    )
    birth_length_cm = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        null=True,
        blank=True,
        help_text="Birth length in centimeters"
    )
    head_circumference_cm = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        null=True,
        blank=True,
        help_text="Head circumference in centimeters"
    )
    
    # APGAR Scores (Assessment of newborn health)
    apgar_score_1min = models.IntegerField(
        null=True,
        blank=True,
        help_text="APGAR score at 1 minute (0-10)"
    )
    apgar_score_5min = models.IntegerField(
        null=True,
        blank=True,
        help_text="APGAR score at 5 minutes (0-10)"
    )
    
    # Multiple Births
    birth_order = models.IntegerField(
        default=1,
        help_text="Birth order for multiple births (1st, 2nd, 3rd)"
    )
    
    # Health Condition at Birth
    health_condition = models.CharField(
        max_length=100,
        blank=True,
        help_text="Baby's health condition at birth (healthy, needs monitoring, etc.)"
    )
    complications = models.TextField(
        blank=True,
        help_text="Any birth complications or health issues"
    )
    required_resuscitation = models.BooleanField(
        default=False,
        help_text="Did baby require resuscitation?"
    )
    
    # Birth Registration
    birth_notification_number = models.CharField(
        max_length=50,
        blank=True,
        help_text="Birth notification number (if registered)"
    )
    
    # Facility & Staff
    facility = models.ForeignKey(
        Facility,
        on_delete=models.PROTECT,
        related_name='babies',
        help_text="Facility where baby was born"
    )
    registered_by = models.ForeignKey(
        CustomUser,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='registered_babies',
        help_text="Staff who registered the baby"
    )
    
    # Metadata
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'babies'
        ordering = ['-delivery__delivery_date', 'birth_order']
        verbose_name = 'Baby'
        verbose_name_plural = 'Babies'
        indexes = [
            models.Index(fields=['mother', 'delivery']),
            models.Index(fields=['facility']),
        ]
    
    def __str__(self):
        name = self.full_name or f"Baby {self.get_gender_display()}"
        return f"{name} - Born {self.delivery.delivery_date}"
    
    @property
    def full_name(self):
        """Get baby's full name"""
        names = [self.first_name, self.middle_name, self.last_name]
        return " ".join([n for n in names if n])
    
    @property
    def display_name(self):
        """Get display name (first name or 'Baby Boy/Girl')"""
        if self.first_name:
            return self.first_name
        return f"Baby {self.get_gender_display()}"
    
    @property
    def age_in_days(self):
        """Calculate baby's age in days"""
        today = date.today()
        return (today - self.delivery.delivery_date).days
    
    @property
    def age_in_weeks(self):
        """Calculate baby's age in weeks"""
        return self.age_in_days // 7
    
    @property
    def age_in_months(self):
        """Calculate baby's age in months (approximate)"""
        return self.age_in_days // 30
    
    @property
    def birth_weight_kg(self):
        """Convert birth weight to kilograms"""
        if self.birth_weight_grams is None:
            return None
        return self.birth_weight_grams / 1000
    
    @property
    def is_low_birth_weight(self):
        """Check if baby had low birth weight (<2500g)"""
        return self.birth_weight_grams < 2500
    
    @property
    def is_very_low_birth_weight(self):
        """Check if baby had very low birth weight (<1500g)"""
        return self.birth_weight_grams < 1500
    
    @property
    def weight_category(self):
        """Categorize birth weight"""
        if self.birth_weight_grams is None:
            return None
        elif self.birth_weight_grams < 1500:
            return "Very Low Birth Weight"
        elif self.birth_weight_grams < 2500:
            return "Low Birth Weight"
        elif self.birth_weight_grams <= 4000:
            return "Normal Birth Weight"
        else:
            return "Macrosomia (Large)"
    
    def get_age_display(self):
        """Get human-readable age"""
        days = self.age_in_days
        
        if days == 0:
            return "Born today"
        elif days == 1:
            return "1 day old"
        elif days < 7:
            return f"{days} days old"
        elif days < 30:
            weeks = days // 7
            return f"{weeks} week{'s' if weeks > 1 else ''} old"
        else:
            months = days // 30
            return f"{months} month{'s' if months > 1 else ''} old"


# ============================================================================
# SIGNAL TO AUTO-GENERATE IMMUNIZATION SCHEDULE WHEN BABY IS REGISTERED
# ============================================================================

from django.db.models.signals import post_save
from django.dispatch import receiver

@receiver(post_save, sender=Baby)
def auto_generate_immunization_schedule(sender, instance, created, **kwargs):
    """
    Automatically generate immunization schedule when baby is registered
    Following Kenya Expanded Programme on Immunization (EPI) 2023
    
    Kenya EPI Schedule:
    - At Birth: BCG, OPV 0
    - 6 weeks: OPV 1, Pentavalent 1, PCV 1, Rota 1
    - 10 weeks: OPV 2, Pentavalent 2, PCV 2, Rota 2
    - 14 weeks: OPV 3, Pentavalent 3, PCV 3
    - 9 months: Measles-Rubella 1, Vitamin A
    - 18 months: Measles-Rubella 2
    """
    
    # Import here to avoid circular dependency
    from apps.immunization.models import VaccineType, ImmunizationSchedule
    
    if created:
        birth_date = instance.delivery.delivery_date
        
        # Kenya EPI Schedule (vaccine name, age in weeks)
        kenya_epi_schedule = [
            # At Birth (0 weeks)
            ('BCG', 0),
            ('OPV 0', 0),
            
            # 6 Weeks
            ('OPV 1', 6),
            ('Pentavalent 1', 6),
            ('PCV 1', 6),
            ('Rota 1', 6),
            
            # 10 Weeks
            ('OPV 2', 10),
            ('Pentavalent 2', 10),
            ('PCV 2', 10),
            ('Rota 2', 10),
            
            # 14 Weeks
            ('OPV 3', 14),
            ('Pentavalent 3', 14),
            ('PCV 3', 14),
            
            # 9 Months (36 weeks)
            ('Measles-Rubella 1', 36),
            ('Vitamin A (6 months)', 36),
            
            # 18 Months (72 weeks)
            ('Measles-Rubella 2', 72),
        ]
        
        created_count = 0
        
        for vaccine_name, age_weeks in kenya_epi_schedule:
            # Get or create vaccine type
            vaccine, _ = VaccineType.objects.get_or_create(
                name=vaccine_name,
                defaults={
                    'recommended_age_weeks': age_weeks,
                    'description': f'Part of Kenya EPI schedule at {age_weeks} weeks'
                }
            )
            
            # Calculate scheduled date
            scheduled_date = birth_date + timedelta(weeks=age_weeks)
            
            # Create immunization schedule entry
            schedule, created = ImmunizationSchedule.objects.get_or_create(
                baby=instance,
                vaccine=vaccine,
                defaults={
                    'scheduled_date': scheduled_date,
                    'facility': instance.facility,
                }
            )
            
            if created:
                created_count += 1
        
        print(f"✓ Auto-generated {created_count} vaccine doses for {instance.display_name} (Kenya EPI 2023)")