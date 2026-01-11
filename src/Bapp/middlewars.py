# middleware.py
import os
from django.conf import settings
from django.http import HttpResponse
from django.shortcuts import redirect


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


class AuthRequiredMiddleware:
    """
    Middleware qui redirige les utilisateurs non connectés
    vers une page de connexion personnalisée
    si l’URL demandée est protégée.
    """

    def __init__(self, get_response):
        self.get_response = get_response
        # liste des préfixes d'URL à protéger
        self.protected_paths = [
            "/Bourou/menu/",
            "/Bourou/membres/",
            "/Bourou/cotisation-annuel-view/",
            "/Bourou/cotisation-occasionnelle-view/",
            "/Bourou/dons-view/",
            "/Bourou/depenses-view/",
            "/Bourou/bilan-totaux-view/",
            "/Bourou/has-annuel-participed/",
            "/Bourou/annonces/",
            "/album-view/",

        ]
        # page de login utilisateur (différente de settings.LOGIN_URL)
        self.login_url = "/Bourou/member-login/"

    def __call__(self, request):
        path = request.path
        # Vérifie si le chemin correspond à une zone protégée
        if any(path.startswith(p) for p in self.protected_paths):
            if not request.user.is_authenticated:
                print("DEBUG middleware: utilisateur NON authentifié → redirection")
                return redirect(f"{self.login_url}?next={path}")

        return self.get_response(request)
