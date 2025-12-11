from django.db import models

# Create your models here.
class Image(models.Model):
    id = models.BigAutoField(primary_key=True)
    titre = models.CharField(max_length=200, blank=True)
    fichier = models.ImageField(upload_to="images/originals/")
    fichier_mobile = models.ImageField(upload_to="images/mobile/", blank=True, null=True)
    fichier_thumbnail = models.ImageField(upload_to="images/thumbnails/", blank=True, null=True)
    date_creation = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.titre or f"Image {self.id}"