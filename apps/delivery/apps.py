from django.apps import AppConfig

class DeliveryConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'apps.delivery'
    verbose_name = 'Delivery & Babies'
    
    def ready(self):
        """Import signals when app is ready"""
        import apps.delivery.models  # This registers the signal!