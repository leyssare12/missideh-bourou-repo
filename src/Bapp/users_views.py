import base64
import json
import time

from django.contrib.auth import get_user_model, login
from django.contrib.auth.decorators import login_required
from django.contrib.messages.api import success
from django.contrib import messages
from django.core.paginator import Paginator, PageNotAnInteger, EmptyPage
from django.db import connection
from django.db.models import Q
from django.http import JsonResponse, HttpResponse
from django.shortcuts import render, redirect
from django.urls import reverse
from django.utils.safestring import mark_safe

from .models import MissidehBourouMembersView, TwoFactorAuth, CotisationAnnuelleView, CotisationOccasionnelleView, \
    DonsView, TotauxView, DepensesView, StatusMemberAnnualParticipation, AnnoncesMembersView
from .permissions import login_required_by_urlname

PER_PAGE = 10  # constante utilisée partout pour garder la cohérence d'affichage par page

#Gestion de l'affichage côté utilisateurs'
Members = get_user_model()

#Point d'entré pour l'authetification de Membres Missideh Bourou
def member_login_view(request):
    template = "site/client/Login/member_login.html"
    if request.method == "POST":
        identifiant = (request.POST.get("identifiant") or "").strip()
        if not identifiant:
            messages.error(request, "Veuillez renseigner votre identifiant.")
            return render(request, template_name=template)
        try:
            user = Members.objects.get(identifiant__iexact=identifiant)
            # ✅ Renouveler la session pour limiter la fixation de session
            request.session.cycle_key()
            # ✅ AUTHENTIFIER l'utilisateur avec Django
            #On permet le login de l'utilsateur avec Django temporairement
            login(request, user)
            # ✅ Stocker temporairement l’utilisateur en session
            request.session["pending_user_id"] = user.id
            message = mark_safe(f"Salam, <strong> {user.prenoms}</strong>")
            messages.success(request, message)
            #On rediriger temporairement vers le user_menu
            return redirect('Bapp:users_menu')
            #return redirect("Bapp:load_2fa_method")
        except Members.MultipleObjectsReturned:
            messages.error(request, "Plusieurs comptes correspondent à cet identifiant. Contactez le support.")
            return render(request, template_name=template)
        except Members.DoesNotExist:
            messages.error(request, "Identifiant incorrect")
            return render(request, template_name=template)
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
    context['message_welcome'] = f'Salam, <strong>{request.user}, vous êtes dans le DASHBOARD Missideh-Bourou.</strong>'
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


#Les views de gestion de caisse

def cotisation_annuelles_view(request):
    template = "site/client/caisse/cotisation_annuelles_view.html"
    context = {}
    try:
        data = CotisationAnnuelleView.objects.all()

        paginator = Paginator(data, PER_PAGE)
        page_number = request.GET.get('page') or 1
        page_obj = paginator.get_page(page_number)
        context['page_obj'] = page_obj
        context['is_paginated'] = page_obj.has_other_pages()
        return render(request, template_name=template, context=context)
    except Exception as e:
        messages.error(request, f"Une erreur est survenue: {e}")
        return render(request, template_name=template, context=context)

def cotisation_occasionnelle_view(request):
    template = "site/client/caisse/cotisation_occasionnelles_view.html"
    context = {}

    try:
        data = CotisationOccasionnelleView.objects.all()

        paginator = Paginator(data, PER_PAGE)
        page_number = request.GET.get('page') or 1
        page_obj = paginator.get_page(page_number)
        context['page_obj'] = page_obj
        context['is_paginated'] = page_obj.has_other_pages()
        return render(request, template_name=template, context=context)
    except Exception as e:
        messages.error(request, f"Une erreur est survenue: {e}")
        return render(request, template_name=template, context=context)

def dons_view(request):
    template = "site/client/caisse/dons_view.html"
    context = {}

    try:
        data = DonsView.objects.all()

        paginator = Paginator(data, PER_PAGE)
        page_number = request.GET.get('page') or 1
        page_obj = paginator.get_page(page_number)
        context['page_obj'] = page_obj
        context['is_paginated'] = page_obj.has_other_pages()
        return render(request, template_name=template, context=context)
    except Exception as e:
        messages.error(request, f"Une erreur est survenue: {e}")
        return render(request, template_name=template, context=context)


def depenses_view(request):
    template = "site/client/caisse/depenses_view.html"
    context = {}

    try:
        data = DepensesView.objects.all()

        paginator = Paginator(data, PER_PAGE)
        page_number = request.GET.get('page') or 1
        page_obj = paginator.get_page(page_number)
        context['page_obj'] = page_obj
        context['is_paginated'] = page_obj.has_other_pages()
        return render(request, template_name=template, context=context)
    except Exception as e:
        messages.error(request, f"Une erreur est survenue: {e}")
        return render(request, template_name=template, context=context)


def bilan_totaux_view(request):
    template = "site/client/caisse/bilan_totaux_view.html"
    context = {}

    try:
        data = TotauxView.objects.all()

        paginator = Paginator(data, PER_PAGE)
        page_number = request.GET.get('page') or 1
        page_obj = paginator.get_page(page_number)
        context['page_obj'] = page_obj
        context['is_paginated'] = page_obj.has_other_pages()
        return render(request, template_name=template, context=context)
    except Exception as e:
        messages.error(request, f"Une erreur est survenue: {e}")
        return render(request, template_name=template, context=context)

def has_participed_annuel_save(request):
    template = "site/client/caisse/has_participed_annuel.html"
    context = {}

    qs = StatusMemberAnnualParticipation.objects.all().order_by('id')
    members = list(qs.values('id', 'prenoms', 'quartier', 'statut_par_annee'))
    context['members'] = members
    # Construire la liste des années présentes
    all_years = set()
    for m in members:
        spa = m.get('statut_par_annee') or {}
        if isinstance(spa, dict):
            all_years.update(spa.keys())
    years = sorted(all_years, key=int)  # les clés sont des strings

    context['years'] = years

    return render(request, template_name=template, context=context)


def has_participed_annuel(request):
    template = "site/client/caisse/has_participed_annuel.html"
    context = {}

    qs = StatusMemberAnnualParticipation.objects.all().order_by('id')

    # Construire la liste des années présentes (sur tout l'ensemble pour garder des colonnes stables)
    all_years = set()
    for m in qs.values('statut_par_annee'):
        spa = (m.get('statut_par_annee') or {})
        if isinstance(spa, dict):
            all_years.update(spa.keys())
    years = sorted(all_years, key=int)  # les clés sont des strings
    context['years'] = years

    # Pagination des membres (slice affiché)
    paginator = Paginator(
        qs.values('id', 'prenoms', 'quartier', 'statut_par_annee'),
        PER_PAGE
    )
    page_number = request.GET.get('page') or 1
    page_obj = paginator.get_page(page_number)

    # Données pour le template
    context['members'] = list(page_obj.object_list)
    context['page_obj'] = page_obj
    context['is_paginated'] = page_obj.has_other_pages()

    return render(request, template_name=template, context=context)

def announce_view(request):
    template = "site/client/caisse/announce_view.html"
    context = {}
    """
    Liste paginée des articles et passage au template announce_view.html.
    Requiert un modèle Article avec les champs:
    - hauteur (auteur)
    - title
    - content
    - image (ImageField ou relation dotée d'une URL)
    - link (URLField/CharField)
    - published_at (DateTimeField)
    """
    # Récupération et tri (les plus récents en premier)
    queryset = AnnoncesMembersView.objects.all().order_by("-published_at")

    # Taille de page configurable via ?per_page=xx (avec garde-fous)
    try:
        per_page = int(request.GET.get("per_page", PER_PAGE))
        per_page = max(1, min(per_page, 100))
    except (TypeError, ValueError):
        per_page = 12

    paginator = Paginator(queryset, per_page)
    page = request.GET.get("page")

    try:
        page_obj = paginator.get_page(page)  # robuste: gère les valeurs invalides
    except (PageNotAnInteger, EmptyPage):
        page_obj = paginator.get_page(1)

    # Préserver les autres paramètres de requête (sans "page")
    params = request.GET.copy()
    params.pop("page", None)
    querystring = params.urlencode()
    if querystring:
        querystring = "&" + querystring

    # Plage de pages avec ellipses (Django 3.2+). Fallback si indisponible.
    try:
        page_range = paginator.get_elided_page_range(
            number=page_obj.number,
            on_each_side=1,
            on_ends=1,
        )
    except AttributeError:
        page_range = paginator.page_range

    context = {
        "articles": page_obj,  # itérable dans le template
        "page_obj": page_obj,
        "paginator": paginator,
        "is_paginated": page_obj.has_other_pages(),
        "page_range": page_range,
        "querystring": querystring,  # à suffixer après ?page=...
    }

    return render(request, template, context)
