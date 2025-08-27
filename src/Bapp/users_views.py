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

from .models import MissidehBourouMembersView, TwoFactorAuth, BTestCustomUser
from .otp_authentication import verify_otp, generate_otp_secret, get_qr_code_uri, generate_qr_code_base64, qrcode_view
from .utils import get_or_create_2fa

PER_PAGE = 10  # constante utilisée partout pour garder la cohérence d'affichage par page

#Gestion de l'affichage côté utilisateurs'
Members = get_user_model()

#Authetification de Membres Missideh Bourou

def members_authentification_qrcode_save(request):
    template_name = 'site/client/members_authentification_qrcode.html'
    context = {}
    user_id = request.session.get("2fa_setup_user_id")
    if not user_id:
        return redirect("Bapp:'identifiant_over_otp")

    user = BTestCustomUser.objects.get(id=user_id)
    print('On affiche le OTP secret', user.otp_secret)
    uri = get_qr_code_uri(user, user.otp_secret)
    qr_b64 = generate_qr_code_base64(uri)
    with open(f"{user.prenoms}.png", "wb") as f:
        f.write(base64.b64decode(qr_b64))
    if request.method == "POST":
        code = request.POST.get("code")
        #Si l'utilisateur a dèjà activé l'authentification 2FA via Authentification QRCode'
        #On redirige vers la page de confirmation de l'authentification 2FA'
        if user.otp_enabled:
            print("L'utilisateur a dèjà un QRcode actif ")
            if verify_otp(user.otp_secret, code):
                del request.session["user_otp_enabled"]
                return redirect("Bapp:two_fa_auth_success")
        #Si c'est la première fois on generer le QRCode et on l'affiche dans le template'
        if verify_otp(user.otp_secret, code):
            user.otp_enabled = True
            user.save()
            del request.session["2fa_setup_user_id"]
            messages.success(request, f'Bonjour {user.prenoms} Authentification reussi.')
            return redirect("Bapp:two_fa_auth_success")
        else:
            context["error"] = "Code invalide"
            context["qr_b64"] = qr_b64
            print('Voici les 100 premiers caractères du QRCODE:', qr_b64[:100])
            return render(request, template_name=template_name, context=context)

    return render(request, template_name=template_name, context=context)

def members_authentification_qrcode(request):
    template_name = 'site/client/members_authentification_qrcode.html'
    context = {}

    user_id = request.session.get("2fa_setup_user_id")
    if not user_id:
        return redirect("Bapp:identifiant_over_otp")

    user = BTestCustomUser.objects.get(id=user_id)
    print('On affiche le OTP secret', user.otp_secret)

    # 🔹 Ici, on donne directement l’URL de l’image
    qr_code_url = reverse("Bapp:qrcode", kwargs={"user_id": user.id})
    context["qr_code_url"] = qr_code_url

    if request.method == "POST":
        code = request.POST.get("code")

        # Utilisateur déjà activé
        if user.otp_enabled:
            print("L'utilisateur a déjà un QR code actif")
            if verify_otp(user.otp_secret, code):
                del request.session["user_otp_enabled"]
                return redirect("Bapp:two_fa_auth_success")

        # Première activation
        if verify_otp(user.otp_secret, code):
            user.otp_enabled = True
            user.save()
            del request.session["2fa_setup_user_id"]
            messages.success(request, f'Bonjour {user.prenoms}, authentification réussie.')
            return redirect("Bapp:two_fa_auth_success")
        else:
            context["error"] = "Code invalide"
            return render(request, template_name=template_name, context=context)

    return render(request, template_name=template_name, context=context)
def verify_2fa(request):

    template_name = 'site/client/verify_2fa.html'
    context = {}
    return render(request, template_name=template_name, context=context)

def identifiant_otp(request):
    template_name = 'site/client/identifiant_enter.html'
    context = {}
    if request.method == "POST":
        identifiant = request.POST.get("identifiant")
        print(identifiant)
        try:
            user = BTestCustomUser.objects.get(identifiant=identifiant)
        except BTestCustomUser.DoesNotExist:
            context["error"] = "Utilisateur introuvable, veillez revoyez votre identifiant."
            return render(request, template_name=template_name, context=context)

        # Génération d’un secret si pas déjà défini
        if not user.otp_secret:
            user.otp_secret = generate_otp_secret()
            user.save()

        request.session["2fa_setup_user_id"] = user.id
        request.session["user_otp_enabled"] = user.otp_enabled
        # Stocker l'ID dans la session pour étape suivante
        print(request.session["2fa_setup_user_id"])
        return redirect("Bapp:two_fa_auth")

    return render(request, template_name=template_name)

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