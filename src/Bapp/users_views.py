import time

from django.contrib.auth import get_user_model, login
from django.contrib.messages.api import success
from django.contrib import messages
from django.core.paginator import Paginator
from django.db import connection
from django.db.models import Q
from django.http import JsonResponse
from django.shortcuts import render, redirect
from django.utils.safestring import mark_safe

from .models import MissidehBourouMembersView, TwoFactorAuth
from .utils import get_or_create_2fa

PER_PAGE = 10  # constante utilisée partout pour garder la cohérence d'affichage par page

#Gestion de l'affichage côté utilisateurs'
Members = get_user_model()

#Authetification de Membres Missideh Bourou

def members_authentification_save(request):
    step = 1  # par défaut on est à l’étape 1
    template_name = 'site/client/members_authentification.html'
    context = {}
    user_id = request.session.get("user_id")
    channel = ''
    if request.method == "POST":
        identifiant = request.POST.get("identifiant")
        if 'identifiant' in request.POST: #Etape 1 : saisie identifiant
            #channel = request.POST.get("channel")
            print(user_id)
            print(identifiant)
            context['step'] = 1
            try:
                user = Members.objects.get(identifiant=identifiant)
                print(user.pk)
                # On selectionne l'option email pour les membres qui ont un email verifié
                if user.email_verified:
                    channel = 'email'
                else:
                    channel = 'whatsapp'
                try:
                    get_or_create_2fa(user, channel=channel)  # ou "email"
                    request.session["user_id"] = user.pk
                    step = 2
                except Exception as e:
                    messages.error(request, str(e))  # message "Veuillez attendre 5 minutes..."
            except Members.DoesNotExist:
                messages.error(request, "Identifiant invalide.")

        elif "code" in request.POST and user_id:  # Étape 2 : saisie code
            code = request.POST.get("code")
            user = Members.objects.get(id=user_id)
            try:
                two_fa = TwoFactorAuth.objects.get(user=user, token_code=code)
                if two_fa.token_expired:
                    messages.error(request, "⚠️ Code expiré. Un nouveau code vous a été envoyé.")
                    get_or_create_2fa(user, channel=channel)
                    step = 2
                else:
                    messages.success(request, "✅ Connexion réussie !")
                    # ici on connecte l'utilisateur'
                    login(request, user)
                    return redirect("Bapp:users_menu")
            except TwoFactorAuth.DoesNotExist:
                messages.error(request, "❌ Code invalide.")
                step = 2

    elif user_id or request.user.is_authenticated:
        #Si l'utilisateur est déjà en session on le redirige vers le panel
        message = mark_safe(f'Bonjour <strong>{request.user.prenoms}</strong> Bienvenue sur Missideh Bourou Dashboard')
        messages.success(request, message)
        return redirect("Bapp:users_menu")
    else:
        context["step"] = step
        print('On est à l etatpe:', step)
        return render(request, template_name=template_name, context=context)


def members_authentification(request):
    step = 1  # étape par défaut
    template_name = 'site/client/members_authentification.html'
    context = {}
    user_id = request.session.get("user_id")  # clé temporaire 2FA
    channel = ''

    # 🔹 Si utilisateur déjà connecté (via login), on le redirige direct
    if request.user.is_authenticated:
        message = mark_safe(f'Bonjour <strong>{request.user.prenoms}</strong> Bienvenue sur Missideh Bourou Dashboard')
        messages.success(request, message)
        return redirect("Bapp:users_menu")

    if request.method == "POST":
        identifiant = request.POST.get("identifiant")

        # Étape 1 : saisie identifiant
        if identifiant:
            try:
                user = Members.objects.get(identifiant=identifiant)
                channel = "email" if user.email_verified else "whatsapp"

                try:
                    get_or_create_2fa(user, channel=channel)
                    request.session["user_id"] = user.pk  # stockage temporaire
                    step = 2
                except Exception as e:
                    messages.error(request, str(e))
            except Members.DoesNotExist:
                messages.error(request, "Identifiant invalide.")

        # Étape 2 : saisie code
        elif "code" in request.POST and user_id:
            code = request.POST.get("code")
            user = Members.objects.get(id=user_id)
            try:
                two_fa = TwoFactorAuth.objects.get(user=user, token_code=code)
                if two_fa.token_expired:
                    messages.error(request, "⚠️ Code expiré. Un nouveau code vous a été envoyé.")
                    get_or_create_2fa(user, channel=channel)
                    step = 2
                else:
                    # ✅ connexion définitive
                    login(request, user)
                    request.session.pop("user_id", None)  # on supprime l’ID temporaire

                    message = mark_safe(
                        f'Bonjour <strong>{request.user.prenoms}</strong> Bienvenue sur Missideh Bourou Dashboard ✅')
                    messages.success(request, message)
                    return redirect("Bapp:users_menu")
            except TwoFactorAuth.DoesNotExist:
                messages.error(request, "❌ Code invalide.")
                step = 2

    # Sinon (GET ou POST échoué)
    context["step"] = step
    return render(request, template_name=template_name, context=context)

#Home page
def home_page(request):
    template = "site/client/home_page.html"
    context = {}
    context['message_info'] = 'Bienvenue sur la page d\'accueil.'
    return render(request, template_name=template, context=context)
def users_menu(request):
    template = "site/client/users_menu.html"
    context = {}
    return render(request, template_name=template, context=context)

#Rechercher d'un membre par son identifiant
def search_member_save(request):
    template = "site/client/search_member.html"




def search_member(request):
    search_term = request.GET.get("q", "").strip()
    if not search_term:
        return JsonResponse({"found": False, "error": "Paramètre q manquant"})

    user = None
    match_type = "fuzzy"

    # Recherche exacte sur identifiant
    try:
        user = MissidehBourouMembersView.objects.get(identifiant__iexact=search_term)
        match_type = "exact"
    except MissidehBourouMembersView.DoesNotExist:
        # Recherche floue (quartier ou prénom)
        user = (
            MissidehBourouMembersView.objects.filter(
                Q(identifiant__icontains=search_term)
                | Q(prenoms__icontains=search_term)
                | Q(quartier__icontains=search_term)
            )
            .order_by("identifiant")
            .first()
        )

    if not user:
        return JsonResponse({"found": False})

    # Trouver la page dans le paginator
    users = MissidehBourouMembersView.objects.all().order_by("identifiant")
    paginator = Paginator(users, PER_PAGE)

    # position exacte de l'utilisateur dans la liste triée
    user_ids = list(users.values_list("identifiant", flat=True))
    try:
        user_position = user_ids.index(user.identifiant)
    except ValueError:
        return JsonResponse({"found": False, "error": "Utilisateur introuvable dans la pagination"})

    page_number = (user_position // paginator.per_page) + 1

    # Réponse JSON cohérente
    return JsonResponse({
        "found": True,
        "id": user.identifiant,
        "name": user.prenoms,
        "quartier": user.quartier,
        "page": page_number,
        "match_type": match_type,
    })
# Recuperation des membres de Missideh Bourou
def missideh_bourou_members(request):
    template = "site/client/missideh_bourou_members.html"
    context = {}
    membres_qs = MissidehBourouMembersView.objects.all().order_by('prenoms')
    # Préchargement des IDs pour le frontend
    if request.headers.get('X-Requested-With') == 'XMLHttpRequest' and request.GET.get('get_ids'):
        user_ids = list(membres_qs.values_list('identifiant', flat=True))
        return JsonResponse({'ids': user_ids})

    # Pagination

    paginator = Paginator(membres_qs, PER_PAGE)
    page_number = request.GET.get('page') or 1
    page_obj = paginator.get_page(page_number)  # gère les pages invalides
    context['page_obj'] = page_obj
    context['is_paginated'] = page_obj.has_other_pages()
    return render(request, template_name=template, context=context)