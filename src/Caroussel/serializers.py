# app/serializers.py
from rest_framework import serializers
from .models import Image

class ImageSerializer(serializers.ModelSerializer):
    class Meta:
        model = Image
        fields = ["id", "titre", "fichier", "fichier_mobile", "fichier_thumbnail", "date_creation"]
