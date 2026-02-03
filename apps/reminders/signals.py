# apps/reminders/signals.py
"""
Signal handlers for automatic reminder creation
(Optional - for future automatic trigger implementation)

Currently, reminders are created by the daily cron job.
These signals can be used for real-time reminder creation when:
- ANC visit is scheduled
- Baby is registered (vaccination schedule created)
- Danger signs are flagged
"""

from django.db.models.signals import post_save
from django.dispatch import receiver
from apps.anc.models import ANCVisit
from apps.delivery.models import Baby
from .models import SystemLog, create_anc_reminder


# Example: Automatically log when danger signs are flagged
@receiver(post_save, sender=ANCVisit)
def log_danger_signs(sender, instance, created, **kwargs):
    """
    Automatically log when danger signs are flagged in ANC visit
    """
    if not created and instance.has_danger_signs:
        # Check if this is a new danger sign (not already logged)
        # This prevents duplicate logs on every save
        if instance.tracker.has_changed('has_danger_signs'):
            # Log the danger sign
            SystemLog.log_danger_sign(
                anc_visit=instance,
                user=instance.recorded_by
            )
            
            # TODO: Optionally create immediate danger sign reminder
            # (This would require SMS gateway to be set up)
            # from .models import ReminderTemplate
            # template = ReminderTemplate.get_active_template('DANGER_SIGNS')
            # if template:
            #     create_danger_sign_reminder(instance)


# Note: To enable field tracking, you need django-model-utils
# Add to models.py:
# from model_utils import FieldTracker
# 
# class ANCVisit(models.Model):
#     # ... other fields ...
#     tracker = FieldTracker(fields=['has_danger_signs'])


# Example: Log when baby is registered
@receiver(post_save, sender=Baby)
def log_baby_registration(sender, instance, created, **kwargs):
    """
    Log when a new baby is registered in the system
    """
    if created:
        SystemLog.log_action(
            action_type='CREATE',
            description=f"Baby registered: {instance.display_name} (Mother: {instance.mother.full_name})",
            model_name='Baby',
            object_id=str(instance.id),
            facility=instance.facility,
            metadata={
                'mother_id': instance.mother.id,
                'birth_weight': str(instance.birth_weight_grams) if instance.birth_weight_grams else None,
                'birth_date': instance.delivery.delivery_date.isoformat(),
            }
        )


# To enable these signals, add to apps.py:
# 
# class RemindersConfig(AppConfig):
#     ...
#     def ready(self):
#         import apps.reminders.signals  # noqa