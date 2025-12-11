from django.apps import AppConfig


class BappConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'Bapp'
    def ready(self):
        import Bapp.signals