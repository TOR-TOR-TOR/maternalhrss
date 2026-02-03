# apps/reminders/apps.py
from django.apps import AppConfig


class RemindersConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'apps.reminders'
    verbose_name = 'SMS Reminders & Notifications'
    
    def ready(self):
        """
        Import signals when app is ready
        (For future use if we add signals for automatic reminder creation)
        """
        pass