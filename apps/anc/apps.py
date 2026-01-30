# apps/anc/apps.py
from django.apps import AppConfig


class AncConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'apps.anc'
    verbose_name = 'Antenatal Care (ANC)'
    
    def ready(self):
        """
        Import signals when app is ready
        This ensures the auto-generation of ANC visits works
        """
        import apps.anc.models  # Import models to register signals