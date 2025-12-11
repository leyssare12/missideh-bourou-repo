# app/tests/test_clean_orphans.py
import os
from django.test import TestCase
from django.core.management import call_command
from django.conf import settings
from Caroussel.models import Image
from django.core.files.base import ContentFile

class CleanOrphansCommandTest(TestCase):

    def setUp(self):
        """Prépare des fichiers valides et orphelins"""
        self.media_root = settings.MEDIA_ROOT

        # Créer une image en base avec un fichier simulé
        self.image = Image.objects.create(titre="Test")
        self.image.fichier.save("test_original.jpg", ContentFile(b"contenu original"), save=True)
        self.image.fichier_mobile.save("test_mobile.jpg", ContentFile(b"contenu mobile"), save=True)
        self.image.fichier_thumbnail.save("test_thumbnail.jpg", ContentFile(b"contenu thumb"), save=True)

        # Créer un fichier orphelin (non référencé en base)
        self.orphan_path = os.path.join(self.media_root, "images/originals/orphan.jpg")
        os.makedirs(os.path.dirname(self.orphan_path), exist_ok=True)
        with open(self.orphan_path, "wb") as f:
            f.write(b"fichier orphelin")

    def test_clean_orphans_removes_only_orphan_files(self):
        """Vérifie que seuls les fichiers orphelins sont supprimés"""
        # Vérifier que l'orphelin existe
        self.assertTrue(os.path.exists(self.orphan_path))

        # Exécuter la commande
        call_command("clean_orphans")

        # L’orphelin doit être supprimé
        self.assertFalse(os.path.exists(self.orphan_path))

        # Les fichiers liés à l’image doivent toujours exister
        self.assertTrue(os.path.exists(self.image.fichier.path))
        self.assertTrue(os.path.exists(self.image.fichier_mobile.path))
        self.assertTrue(os.path.exists(self.image.fichier_thumbnail.path))
