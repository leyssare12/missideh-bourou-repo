# app/urls.py
from django.conf.urls.static import static
from django.urls import path, include
from rest_framework.routers import DefaultRouter

from BTest import settings
from .views import ImageViewSet, upload_images, upload_success, carrousel_view, upload_images_api, \
    create_or_delete_image, delete_image, images_album, album_view

router = DefaultRouter()
router.register("images", ImageViewSet, basename="images")
app_name = "Caroussel"
urlpatterns = [
    # vues classiques Django (formulaires, templates)
    path("upload/", upload_images_api, name="upload_image"),
    path('album/', images_album, name='images_album'),
    path('delete-image/<int:pk>/', delete_image, name='delete_image'),
    path("upload/", upload_images, name='upload_images'),
    path("upload/success/", upload_success, name="upload_success"),
    path('caroussel/', carrousel_view, name='caroussel'),
    path('image-menu/', create_or_delete_image, name='image_menu'),

    path('album-view/', album_view, name='album_view'),

    # API DRF
    path("api/", include(router.urls)),
]

# Servir les fichiers médias en développement
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)