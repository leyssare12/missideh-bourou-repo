from django.apps import AppConfig


class CarousselConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'Caroussel'

class ImageConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'Caroussel'

    def ready(self):
        import Caroussel.signals
