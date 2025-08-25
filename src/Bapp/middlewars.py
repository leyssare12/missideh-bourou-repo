# middleware.py
import os
from django.conf import settings
from django.http import HttpResponse


class MediaDebugMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        if request.path.startswith(settings.MEDIA_URL):
            relative_path = request.path[len(settings.MEDIA_URL):]
            absolute_path = os.path.join(settings.MEDIA_ROOT, relative_path)

            if os.path.exists(absolute_path):
                print(f"Le fichier existe à : {absolute_path}")
            else:
                print(f"Fichier non trouvé : {absolute_path}")
                print(f"MEDIA_ROOT : {settings.MEDIA_ROOT}")
                print(f"Chemin relatif demandé : {relative_path}")

        return self.get_response(request)
