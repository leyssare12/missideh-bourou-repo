# app/signals.py
from django.db.models.signals import post_save, post_delete
from django.dispatch import receiver
from .models import Image
from PIL import Image as PILImage
from io import BytesIO
from django.core.files.base import ContentFile
import os

@receiver(post_save, sender=Image)
def generate_resized_versions(sender, instance, created, **kwargs):
    """ Génération automatique des versions mobile et thumbnail """
    if created and instance.fichier:
        tailles = {
            "mobile": (800, 600),      # smartphone
            "thumbnail": (300, 200),   # miniature
        }

        for version, size in tailles.items():
            try:
                img = PILImage.open(instance.fichier)
                if img.mode != "RGB":
                    img = img.convert("RGB")

                img.thumbnail(size)

                buffer = BytesIO()
                img.save(buffer, format="JPEG", quality=85)

                nom_base, ext = os.path.splitext(os.path.basename(instance.fichier.name))
                new_filename = f"{nom_base}_{version}.jpg"

                if version == "mobile":
                    instance.fichier_mobile.save(new_filename, ContentFile(buffer.getvalue()), save=False)
                elif version == "thumbnail":
                    instance.fichier_thumbnail.save(new_filename, ContentFile(buffer.getvalue()), save=False)

            except Exception as e:
                print(f"Erreur traitement {version}: {e}")

        instance.save()


@receiver(post_delete, sender=Image)
def delete_files(sender, instance, **kwargs):
    """ Supprimer les fichiers liés lorsqu'une image est supprimée """
    storage = instance.fichier.storage

    # Supprimer l'original
    if instance.fichier and storage.exists(instance.fichier.name):
        storage.delete(instance.fichier.name)

    # Supprimer la version mobile
    if instance.fichier_mobile and storage.exists(instance.fichier_mobile.name):
        storage.delete(instance.fichier_mobile.name)

    # Supprimer la version miniature
    if instance.fichier_thumbnail and storage.exists(instance.fichier_thumbnail.name):
        storage.delete(instance.fichier_thumbnail.name)
