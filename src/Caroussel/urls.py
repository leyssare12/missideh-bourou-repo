# app/urls.py
from django.conf.urls.static import static
from django.urls import path, include
from rest_framework.routers import DefaultRouter

from BTest import settings
from .views import ImageViewSet, upload_images, upload_success, carrousel_view, upload_images_api

router = DefaultRouter()
router.register("images", ImageViewSet, basename="images")
app_name = "Caroussel"
urlpatterns = [
    # vues classiques Django (formulaires, templates)
    path("upload/", upload_images_api, name="upload_image"),
    path("upload/success/", upload_success, name="upload_success"),
    path('caroussel/', carrousel_view, name='caroussel'),
    # API DRF
    path("api/", include(router.urls)),
]

# Servir les fichiers médias en développement
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)