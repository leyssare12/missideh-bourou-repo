from datetime import datetime
from functools import wraps

from BTest import settings
from django.contrib import messages
from django.contrib.auth import logout
from django.core.exceptions import PermissionDenied
from django.shortcuts import redirect
import logging

from django.urls import reverse
from django.utils.http import urlencode
from django.utils.timezone import now

from Bapp.error_views import ErrorHandlerView
from Bapp.not_allowed import not_allowed_users

logger = logging.getLogger(__name__)

"""
On vérifie si l'utilisateur a le droit de faire une action
"""""""""
def has_secretor_role(required_roles):
    def decorator(func):
        def wrapper(request, *args, **kwargs):
            # 🔒 Vérifie si l'utilisateur est connecté
            if not request.user.is_authenticated:
                message = PermissionError("Vous devez vous authentifier avant de pouvoir accéder à cette page.")
                # 🔁 Redirige vers la page d'accès refusé avec ?next=current_url
                request.GET = request.GET.copy()
                request.GET['next'] = request.get_full_path()
                return not_allowed_users(request, exception=message)

            # 🔐 Vérifie si l'utilisateur a les rôles requis
            if request.user.role not in required_roles:
                userole = request.user.role
                user_name = request.user.prenoms
                message = PermissionError(f"Bonjour {user_name}, vous faites partie de l'équipe '{userole}', vous n'avez donc pas les permissions nécessaires pour accéder à cette page.")
               # 🔁 Redirige aussi vers acces_refuse avec message personnalisé si besoin
                request.GET = request.GET.copy()
                request.GET['next'] = request.get_full_path()
                return not_allowed_users(request ,exception=message)

            # ✅ L'utilisateur est autorisé
            print('Vous avez le droit de faire cette action.')
            return func(request, *args, **kwargs)
        return wrapper
    return decorator

'''
on vérifie si l'utilisateur a le droit d'inscrire d'autres utilisateurs
'''
def can_add_user(required_roles):
    def decorator(func):
        def wrapper(request, *args, **kwargs):
            # 🔒 Vérifie si l'utilisateur est connecté
            print(request.user)
            if not request.user.is_authenticated:
                print('page d identification')
                message = PermissionError('Vous devez vous authentifier pour accéder à cette page.')       # 🔁 Redirige vers la page d'accès refusé avec ?next=current_url
                request.GET = request.GET.copy()
                request.GET['next'] = request.get_full_path()
                return not_allowed_users(request, exception=message)

            # 🔐 Vérifie si l'utilisateur a les rôles requis
            if request.user.role not in required_roles:
                userole = request.user.role
                user_name = request.user.prenoms
                message = PermissionError(f"Bonjour {user_name}, vous faites partie de l'équipe '{userole}', vous n'avez donc pas les permissions nécessaires pour accéder à cette page.")
                # 🔁 Redirige aussi vers acces_refuse avec message personnalisé si besoin
                request.GET = request.GET.copy()
                request.GET['next'] = request.get_full_path()
                return not_allowed_users(request ,exception=message)

            # ✅ L'utilisateur est autorisé
            print('Vous avez le droit de faire cette action.')
            return func(request, *args, **kwargs)
        return wrapper
    return decorator


def can_add_user_save(required_roles):
    def decorator(view_func):
        def wrapper(request, *args, **kwargs):
            # Vérification de l'authentification
            if not request.user.is_authenticated:
                # Construction de l'URL de redirection sécurisée
                login_url = reverse(f'{settings.LOGIN_URL}') + f"?next={request.path}"
                return redirect(login_url)

            # Vérification des rôles
            if request.user.role not in required_roles:
                # Utilisation directe du handler403 pour éviter les boucles
                raise PermissionDenied("Vous ne faites pas partie de l'équipe Moderateurs")

            return view_func(request, *args, **kwargs)

        return wrapper

    return decorator

'''ON vérifie si l'utilsateur a le droit de publier un article sur le site
'''

def can_edit_article(required_roles):
    def decorator(func):
        def wrapper(request, *args, **kwargs):
            # 🔒 Vérifie si l'utilisateur est connecté
            if not request.user.is_authenticated:
                message = PermissionError("Vous devez vous authentifier avant de pouvoir accéder à cette page.")
                # 🔁 Redirige vers la page d'accès refusé avec ?next=current_url
                request.GET = request.GET.copy()
                request.GET['next'] = request.get_full_path()
                return not_allowed_users(request, exception=message)

            # 🔐 Vérifie si l'utilisateur a les rôles requis
            if request.user.role not in required_roles:
                userole = request.user.role
                user_name = request.user.prenoms
                message = PermissionError(f"Bonjour {user_name}, vous faites partie de l'équipe '{userole}', vous n'avez donc pas les permissions nécessaires pour accéder à cette page.")
                # 🔁 Redirige aussi vers acces_refuse avec message personnalisé si besoin
                request.GET = request.GET.copy()
                request.GET['next'] = request.get_full_path()
                return not_allowed_users(request ,exception=message)

            # ✅ L'utilisateur est autorisé
            print('Vous avez le droit de faire cette action.')
            return func(request, *args, **kwargs)
        return wrapper
    return decorator

#Gestion de deconnexion via les sessions
def auto_logout(view_func):
    @wraps(view_func)
    def wrapper(request, *args, **kwargs):
        if request.user.is_authenticated:
            last_activity = request.session.get('last_activity')

            if last_activity:
                last_activity = datetime.fromisoformat(last_activity)
                inactive_time = (now() - last_activity).seconds

                # Avertissement à 90 secondes (30 secondes avant expiration)
                if inactive_time > 90:
                    messages.warning(request, "Attention: Votre session expirera dans 30 secondes")

                # Déconnexion après 120 secondes (2 minutes)
                if inactive_time > 500:
                    logout(request)
                    # Stocker le message de session expirée
                    request.session['session_expired'] = True
                    messages.error(request, "Session expirée après 2 minutes d'inactivité")

                    # Sauvegarder l'URL courante
                    next_url = request.get_full_path()
                    return redirect(f"{reverse('Bapp:manager_login_page')}?next={next_url}")
            # Mise à jour du timestamp d'activité
            request.session['last_activity'] = now().isoformat()

            # Comme SESSION_SAVE_EVERY_REQUEST est True, on peut vérifier et prolonger la session
            request.session.modified = True

        return view_func(request, *args, **kwargs)

    return wrapper







