# Site/error_views.py
#from django.conf import settings
from django.shortcuts import render, redirect
from django.utils.http import url_has_allowed_host_and_scheme
from django.views import View
from django.utils.decorators import method_decorator
from django.views.decorators.csrf import requires_csrf_token

from BTest import settings


class ErrorHandlerView:
    """Classe pour gérer les différentes erreurs HTTP"""

    @staticmethod
    @requires_csrf_token
    def handler403_save(request, exception=None):
        """Gestionnaire pour l'erreur 403 (Accès refusé)"""
        template = "site/errors/errors_handler.html"
        next_url = request.GET.get('next')

        # Vérification de l'authentification
        if request.user.is_authenticated:
            # Si l'utilisateur est authentifié, on vérifie l'URL de redirection
            if not url_has_allowed_host_and_scheme(next_url, allowed_hosts={request.get_host()}):
                next_url = settings.LOGIN_REDIRECT_URL
            # Redirection vers l'URL appropriée avec un code 200
            print("L'url dans les methode d'erreur:", next_url)
            return redirect(next_url)

        # Si l'utilisateur n'est pas authentifié ou n'a pas les permissions
        context = {
            'next': next_url,
            'error_code': '403',
            'error_title': 'Accès Refusé',
            'error_message': 'Vous n\'avez pas les permissions nécessaires pour accéder à cette page.',
            'error_details': str(exception) if exception else 'Vous devez vous connecter pour accéder à cette page.'
        }
        response = render(request, template_name=template, context=context)
        response.status_code = 403  # Code 403 uniquement pour les accès réellement non autorisés
        return response

    @staticmethod
    @requires_csrf_token
    def handler403(request, exception=None):
        """Gestionnaire optimisé pour l'erreur 403 (Accès refusé)"""
        template = "site/errors/errors_handler.html"
        next_url = request.GET.get('next')

        # Vérification sécurisée de l'URL de redirection
        safe_next_url = next_url if url_has_allowed_host_and_scheme(next_url,
                                                                    allowed_hosts={request.get_host()}) else None

        # Si l'utilisateur est authentifié mais n'a pas les permissions
        if request.user.is_authenticated:
            return redirect(safe_next_url or settings.LOGIN_URL)

        # Préparation du contexte d'erreur
        context = {
            'next': safe_next_url,
            'error_code': '403',
            'error_title': 'Accès Refusé',
            'error_message': 'Vous n\'avez pas les permissions nécessaires pour accéder à cette page.',
            'error_details': str(exception) if exception else 'Vous devez vous connecter pour accéder à cette page.'
        }

        response = render(request, template, context)
        response.status_code = 403
        return response

    @staticmethod
    @requires_csrf_token
    def handler404(request, exception=None):
        """Gestionnaire pour l'erreur 404 (Page non trouvée)"""
        template = "site/errors/errors_handler.html"
        # On recupére l'url ici
        next_url = request.GET.get('next')
        # On s'assure que l'url est interne pour empecher une modification de celci
        if not url_has_allowed_host_and_scheme(next_url, allowed_hosts={request.get_host()}):
            next_url = settings.LOGIN_REDIRECT_URL
        print("L'url dans les methode d'erreur:", next_url)
        context = {
            'next': next_url,
            'error_code': '404',
            'error_title': 'Page Non Trouvée',
            'error_message': 'La page que vous recherchez n\'existe pas ou a été déplacée.',
            'error_details': str(exception) if exception else 'Vous devez vous connecter pour accéder à cette page.'
        }
        response = render(request, template_name=template, context=context)
        response.status_code = 404
        return response

    @staticmethod
    @requires_csrf_token
    def handler500(request, exception=None):
        """Gestionnaire pour l'erreur 500 (Erreur serveur)"""
        template = "site/errors/errors_handler.html"
        # On recupére l'url ici
        next_url = request.GET.get('next')
        # On s'assure que l'url est interne pour empecher une modification de celci
        if not url_has_allowed_host_and_scheme(next_url, allowed_hosts={request.get_host()}):
            next_url = settings.LOGIN_REDIRECT_URL
        print("L'url dans les methode d'erreur:", next_url)
        context = {
            'next': next_url,
            'error_code': '500',
            'error_title': 'Erreur Serveur',
            'error_message': 'Une erreur interne s\'est produite sur le serveur.',
            'error_details': str(exception) if exception else 'Vous devez vous connecter pour accéder à cette page.'
        }
        response = render(request, template_name=template, context=context)
        response.status_code = 500
        return response

    @staticmethod
    @requires_csrf_token
    def handler400(request, exception=None):
        """Gestionnaire pour l'erreur 400 (Mauvaise requête)"""
        template = "site/errors/errors_handler.html"
        #On recupére l'url ici
        next_url = request.GET.get('next')
        #On s'assure que l'url est interne pour empecher une modification de celci
        if not url_has_allowed_host_and_scheme(next_url, allowed_hosts={request.get_host()}):
            next_url = settings.LOGIN_REDIRECT_URL
        print("L'url dans les methode d'erreur:" , next_url)
        context = {
            'next': next_url,
            'error_code': '400',
            'error_title': 'Mauvaise Requête',
            'error_message': 'La requête envoyée au serveur est invalide.',
            'error_details': str(exception) if exception else 'Vous devez vous connecter pour accéder à cette page.'
        }
        response = render(request, template_name=template, context=context)
        response.status_code = 400
        return response