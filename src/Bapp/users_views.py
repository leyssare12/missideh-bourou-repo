import base64
import time

from django.contrib.auth import get_user_model, login
from django.contrib.messages.api import success
from django.contrib import messages
from django.core.paginator import Paginator
from django.db import connection
from django.db.models import Q
from django.http import JsonResponse, HttpResponse
from django.shortcuts import render, redirect
from django.urls import reverse
from django.utils.safestring import mark_safe

from .models import MissidehBourouMembersView, TwoFactorAuth

PER_PAGE = 10  # constante utilisée partout pour garder la cohérence d'affichage par page

#Gestion de l'affichage côté utilisateurs'
Members = get_user_model()

#Authetification de Membres Missideh Bourou
def members_login(request):
    template = "site/client/authentication_choices.html"
    context = {}
    if request.method == "POST":
        identifiant = request.POST.get("identifiant")
        user = Members.objects.filter(identifiant=identifiant).first()
        if user:
            context['user_exists'] = True
            message = mark_safe(f"Salam,  <strong> {user.prenoms}</strong>")
            messages.success(request, message)
            return redirect('Bapp:select_2fa_method')
        else:
            messages.error(request, "Identifiant incorrect")
    context['message_info'] = 'Veuillez entrer votre identifiant'
    return render(request, template_name=template, context=context)
def member_login_view(request):
    template = "site/client/Login/member_login.html"
    if request.method == "POST":
        identifiant = request.POST.get("identifiant")
        try:
            user = Members.objects.get(identifiant=identifiant)
            # ✅ Stocker temporairement l’utilisateur en session
            request.session["pending_user_id"] = user.id
            message = mark_safe(f"Salam, <strong> {user.prenoms}</strong>")
            messages.success(request, message)
            return redirect("Bapp:load_2fa_method")
        except Members.DoesNotExist:
            messages.error(request, "Identifiant incorrect")
    return render(request, template_name=template)


def load_2fa_method(request):
    template = "site/client/Login/login_choices.html"
    context = {}
    if "pending_user_id" not in request.session:
        return redirect("Bapp:member_login_view")  # sécurité

    if request.method == "POST":
        method = request.POST.get("method")
        if method in ["email", "telegram", "qrcode"]:
            # ✅ Sauvegarder le choix
            request.session["2fa_method"] = method
            return redirect("Bapp:select_2fa_method", method=method)
        messages.error(request, 'Vous devez choisir une méthode parmi ces trois en bas pour vous authentifier.')
    return render(request, template_name=template, context=context)
# views.py
def select_2fa_method(request, method):
    user_id = request.session.get("pending_user_id")
    if not user_id:
        return redirect('Bapp:member_login_view')
    # 'method' contiendra la valeur passée dans l'URL ('authenticator', 'telegram' ou 'email')
    if method == 'qrcode':
        # Traiter la méthode authenticator
        request.session["2fa_qrcode_user_id"] = user_id
        return redirect('Bapp:identifiant_over_otp')
    elif method == 'telegram':
        # Traiter la méthode telegram
        return redirect('Bapp:telegram_otp_login')
    elif method == 'email':
        # Traiter la méthode email
        print(f"Methode choisi: {method}")
        return redirect('Bapp:members_authentification_email')
    else:
        # Gérer une méthode inconnue
        messages.error(request, "Méthode d'authentification invalide")
        return redirect('Bapp:load_2fa_method')


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