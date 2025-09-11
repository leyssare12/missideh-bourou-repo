from django.contrib import messages
from django.http import JsonResponse
from django.shortcuts import render, redirect

# app/views.py
from rest_framework.viewsets import ReadOnlyModelViewSet

from .forms import MultiImageUploadForm
from .models import Image
from .serializers import ImageSerializer

class ImageViewSet(ReadOnlyModelViewSet):
    queryset = Image.objects.all().order_by("-date_creation")
    serializer_class = ImageSerializer
def upload_images(request):
    templates = "upload_images.html"
    if request.method == "POST":
        form = MultiImageUploadForm(request.POST, request.FILES)
        if form.is_valid():
            titre = form.cleaned_data["titres"]
            fichiers = form.cleaned_data["fichiers"]
            for f in fichiers:
                Image.objects.create(titre=titre, fichier=f)
            return redirect("Caroussel:upload_success")
    else:
        form = MultiImageUploadForm()
    return render(request, templates, {"form": form})

def upload_images_api(request):
    templates = "upload_images.html"
    if request.method == "POST":
        form = MultiImageUploadForm(request.POST, request.FILES)
        if form.is_valid():
            try:
                images = form.save()
                messages.success(request, f"{len(images)} image(s) enregistrée(s).")
                return redirect("Caroussel:upload_success")
            except Exception as e:
                # Erreur inattendue pendant save()
                messages.error(request, f"Erreur lors de l’enregistrement: {e}")
        else:
            # Optional: transformer en JSON si besoin de debug
            # print(form.errors.get_json_data())
            messages.error(request, "Le formulaire contient des erreurs, corrigez-les puis réessayez.")
    else:
        form = MultiImageUploadForm()

    return render(request, templates, {"form": form})
def upload_success(request):
    templates = "upload_success.html"
    return render(request, templates)
def carrousel_view(request):
    templates = "caroussel.html"
    return render(request, templates)