from django.apps import AppConfig


class GestionDepotConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'gestion_depot'
    
    def ready(self):
        import gestion_depot.signals 
