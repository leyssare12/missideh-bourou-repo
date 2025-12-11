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
    templates = "admin/upload_images.html"
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
    templates = "admin/upload_images.html"
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

def images_album(request):
    """Affiche la galerie d’images avec sélection et suppression via modale."""
    templates = "admin/images_album.html"
    context = {}
    try:
        context["images"] = Image.objects.all().order_by("-date_creation")
        for image in context["images"]:
            print("ORIGINAL:", image.fichier.url if image.fichier else "—",
          "THUMB:", image.fichier_thumbnail.url if image.fichier_thumbnail else "—")

    except Exception as e:
        context["error"] = str(e)
    return render(request, templates, context)


def create_or_delete_image(request):
    templates = "admin/create_or_delete_image.html"
    context = {}
    return render(request, templates, context)
from django.http import JsonResponse, Http404
from django.views.decorators.http import require_POST
from .models import Image

@require_POST
def delete_image(request, pk):
    try:
        img = Image.objects.get(pk=pk)
        img.delete()
        return JsonResponse({"success": True})
    except Image.DoesNotExist:
        return JsonResponse({"success": False}, status=404)


def upload_success(request):
    templates = "admin/upload_success.html"
    return render(request, templates)
def carrousel_view(request):
    templates = "caroussel.html"
    return render(request, templates)

def album_view(request):
    templates = "bourou/album_image.html"
    return render(request, templates)