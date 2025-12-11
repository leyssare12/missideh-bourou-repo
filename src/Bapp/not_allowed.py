from django.shortcuts import render, redirect
from django.utils.http import url_has_allowed_host_and_scheme
from django.views.decorators.csrf import requires_csrf_token

from BTest import settings


@requires_csrf_token
def not_allowed_users(request, exception=None):
    """Gestionnaire optimisé pour l'erreur 403 (Accès refusé)"""
    template = "site/errors/not_allowed_users.html"
    next_url = request.GET.get('next')

    # Vérification sécurisée de l'URL de redirection
    if not url_has_allowed_host_and_scheme(next_url, allowed_hosts={request.get_host()}):
        next_url = settings.LOGIN_REDIRECT_URL
        return redirect(next_url)
    # Préparation du contexte d'erreur
    context = {
        'next': next_url,
        'error_code': '403',
        'error_title': 'Accès Refusé',
        'error_message': 'Vous n\'avez pas les permissions nécessaires pour accéder à cette page.',
        'error_details': str(exception) if exception else 'Vous devez vous connecter pour accéder à cette page.'
    }
    response = render(request, template, context)
    return response
