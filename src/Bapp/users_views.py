import base64
import json
import time
from datetime import date

from django.contrib.auth import get_user_model, settings, login
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
from django.views.generic import ListView

from .models import MissidehBourouMembersView, TwoFactorAuth, DonsView, DepensesView, CotisationOccasionnelleView, \
    CotisationAnnuelleView, AnnoncesMembersView, StatusMemberAnnualParticipation, TotauxView, AmountContributionYear, \
    AddDepenses, EditorialCommunity, Dons, CotisationOccasionnelle
from .permissions import login_required_by_urlname

PER_PAGE = 10  # constante utilisée partout pour garder la cohérence d'affichage par page

# Gestion de l'affichage côté utilisateurs'
Members = get_user_model()

# ... existing code ...
from django.db.models import Sum, Count, Q
from .models import AmountContributionYear, ParticipationAnnual, BtestCustomUser


class BaseCaisseListView(ListView):
    template_name = "site/client/caisse/template_generic_view.html"
    paginate_by = PER_PAGE

    # Par défaut, ces valeurs sont vides, elles seront remplies par les classes enfants
    title = ""
    icon_class = "fa-solid fa-folder-open"
    columns = []  # Liste de tuples: (label, champ_du_model, icone)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['title'] = self.title
        context['icon_class'] = self.icon_class
        context['columns'] = self.columns

        # Correction : On vérifie si page_obj existe dans le contexte
        # Django l'ajoute automatiquement si la pagination est activée
        page_obj = context.get('page_obj')
        if page_obj:
            context['is_paginated'] = page_obj.has_other_pages()
        else:
            context['is_paginated'] = False

        return context


class UserListView(BaseCaisseListView):
    model = MissidehBourouMembersView
    title = "Listes des Membres Missideh Bourou"
    icon_class = "fa-solid fa-users"
    ordering = ['prenoms']
    columns = [
        ("Prénom", "prenoms", "fa-user"),
        ("Identifiant", "identifiant", "fa-id-card"),
        ("Quartier", "quartier", "fa-location-dot"),
        ("Ville", "city", "fas fa-building"),
        ("Pays", "pays", "fa-globe"),
        ("Tel", "telephone", "fa-phone"),
        ("Email", "email", "fa-envelope"),
    ]

    def get_context_data(self, **kwargs):
        # On récupère le contexte de base (titre, colonnes, pagination...)
        context = super().get_context_data(**kwargs)

        # On ajoute le nombre total de membres
        # get_queryset() prend en compte le filtrage et l'ordre défini plus haut
        context['users_number'] = self.get_queryset().count()
        return context


# Classes enfants très simples
class CotisationOccasionnelleListView(BaseCaisseListView):
    model = CotisationOccasionnelleView
    title = "Cotisations Occasionnelles"
    icon_class = "fa-solid fa-hand-holding-dollar"
    columns = [
        ("Prénom", "prenom", "fa-user"),
        ("Quartier", "quartier", "fa-location-dot"),
        ("Montant", "montant", "fa-sack-dollar"),
        ("Motif", "motif_cotisation", "fa-comment"),
        ("Date", "date_cotisation", "fa-calendar-day"),
    ]

    def get_queryset(self):
        # On récupère toutes les données de la vue SQL
        queryset = super().get_queryset().order_by('-date_cotisation')

        # On regarde si un event_id est passé dans l'URL
        # On regarde si un event_id est passé dans l'URL
        event_id = self.request.GET.get('event_id')

        if event_id:
            from django.shortcuts import get_object_or_404
            from .models import EvenementOccasionnelle

            # Validation stricte : Si l'ID est invalide ou n'existe pas,
            # Django renverra une page 404 propre au lieu d'afficher n'importe quoi.
            event = get_object_or_404(EvenementOccasionnelle, id=event_id)

            # On filtre la vue SQL sur le nom de l'événement
            queryset = queryset.filter(motif_cotisation=event.event_name)
            # On change le titre de la page pour l'utilisateur
            self.title = f"Cotisations pour : {event.event_name}"

        return queryset


class CotisationAnnuelListView(BaseCaisseListView):
    model = CotisationAnnuelleView
    title = "Annuelles Cotisations"
    icon_class = "fa-solid fa-hand-holding-dollar"
    columns = [
        ("Prénom", "prenom", "fa-user"),
        ("Quartier", "quartier", "fa-location-dot"),
        ("Montant", "montant", "fa-sack-dollar"),
        ("Date", "date_cotisation", "fa-calendar-day"),
    ]
    ordering = ['-id']

    def get_queryset(self):
        # On s'assure d'avoir un ordre pour la pagination
        queryset = super().get_queryset().order_by('-id')
        year = self.request.GET.get('year')

        if year:
            queryset = queryset.filter(year__year=year)
            self.title = f"Cotisations Annuelles pour: - {year}"
        return queryset


class DonsListView(BaseCaisseListView):
    model = DonsView
    title = "Liste des Dons"
    icon_class = "fa-solid fa-gift"
    columns = [
        ("Prénom", "prenom", "fa-user"),
        ("Nom", "nom", "fa-id-card"),
        ("Montant", "montant_don", "fa-sack-dollar"),
        ("Motif", "motif_don", "fa-comment"),
        ("Date", "date_don", "fa-calendar-day"),
    ]
    ordering = ['-id']

    def get_queryset(self):
        # On s'assure d'avoir un ordre pour la pagination
        queryset = super().get_queryset()
        year = self.request.GET.get('year')
        print(f'/{year}', queryset.query, queryset.query.where)
        if year:
            # Comme date_cotisation est du texte 'DD/MM/YYYY' (via to_char en SQL)
            # On filtre avec __icontains pour chercher l'année à la fin de la chaîne
            queryset = queryset.filter(date_don__icontains=year)
            self.title = f"Dons recues pour: - {year}"
            print(queryset)
        return queryset


class BilanListView(BaseCaisseListView):
    model = TotauxView
    title = "Bilan Financier Global"
    icon_class = "fa-solid fa-chart-pie"
    # Comme TotauxView n'a que 4 lignes fixes, on peut désactiver la pagination ou l'augmenter
    paginate_by = 20

    # Nous utilisons des noms de champs qui existent dans le modèle SQL
    columns = [
        ("Désignation du Caisse", "designation", "fa-tag"),
        ("Montant Total", "montant_total", "fa-money-bill-wave"),
        ("Date de mise à jour", "aujourdhui", "fa-clock"),
    ]

    def get_queryset(self):
        """
        On surcharge le QuerySet pour créer des champs virtuels 'designation'
        et 'montant_total' car le SQL original sépare tout en 8 colonnes.
        """
        from django.db.models.functions import Coalesce
        from django.db.models import Value, DecimalField

        return super().get_queryset().annotate(
            designation=Coalesce(
                'type_annuel', 'type_occasionnelle', 'type_dons', 'type_depenses'
            ),
            montant_total=Coalesce(
                'montant_cotisationannuel',
                'montant_cotisationoccasionnelle',
                'montant_dons',
                'montant_depenses',
                output_field=DecimalField()
            )
        )


class DepensesListView(BaseCaisseListView):
    model = DepensesView
    title = "Liste des Depenses"
    icon_class = "fa-solid fa-money-bill-wave"
    ordering = ['-date_depense']
    columns = [
        ("Montant", "montant_depense", "fa-sack-dollar"),
        ("Motif", "motif_depense", "fa-comment"),
        ("Date", "date_depense", "fa-calendar-day"),
    ]

    def get_queryset(self):
        # On s'assure d'avoir un ordre pour la pagination
        queryset = super().get_queryset()
        year = self.request.GET.get('year')
        print(f'/{year}', queryset.query, queryset.query.where)
        if year:
            # Comme date_cotisation est du texte 'DD/MM/YYYY' (via to_char en SQL)
            # On filtre avec __icontains pour chercher l'année à la fin de la chaîne
            queryset = queryset.filter(date_depense__icontains=year)
            self.title = f"Dons recues pour: - {year}"
            print(queryset)
        return queryset


# Point d'entré pour l'authetification de Membres Missideh Bourou
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
            # On permet le login de l'utilsateur avec Django temporairement
            login(request, user)
            # ✅ Stocker temporairement l’utilisateur en session
            request.session["pending_user_id"] = user.id
            message = mark_safe(f"Salam, <strong> {user.prenoms}</strong>")
            messages.success(request, message)
            # On rediriger temporairement vers le user_menu
            return redirect('Bapp:users_menu')
            # return redirect("Bapp:load_2fa_method")
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


# Home page

def home_page(request):
    template = "site/client/home_page.html"
    context = {'message_info': 'Bienvenue sur la page d\'accueil.'}
    return render(request, template_name=template, context=context)


def users_menu(request):
    template = "site/client/users_menu.html"

    # 1. Récupérer la dernière info publiée
    last_news = EditorialCommunity.objects.order_by('-created_at').first()

    # 2. Trouver la dernière opération financière parmi les 4 modèles
    # On récupère le dernier objet de chaque catégorie
    last_depense = AddDepenses.objects.order_by('-date_depense').first()
    last_don = Dons.objects.order_by('-date_don').first()
    last_occ = CotisationOccasionnelle.objects.order_by('-updated_at').first()
    last_ann = ParticipationAnnual.objects.order_by('-updated_at').first()

    # Liste des opérations pour comparaison
    operations = []
    if last_depense: operations.append({'obj': last_depense, 'date': last_depense.date_depense, 'type': 'Dépense', 'icon': '💸'})
    if last_don: operations.append({'obj': last_don, 'date': last_don.date_don, 'type': 'Don reçu', 'icon': '🎁'})
    if last_occ: operations.append({'obj': last_occ, 'date': last_occ.updated_at, 'type': 'Cotisation Occasionnelle', 'icon': '🤝'})
    if last_ann: operations.append({'obj': last_ann, 'date': last_ann.updated_at, 'type': 'Cotisation Annuelle', 'icon': '💰'})

    # On trie par date descendante et on prend le premier
    last_op = None
    if operations:
        last_op = sorted(operations, key=lambda x: x['date'], reverse=True)[0]

    context = {
        'last_news': last_news,
        'last_op': last_op,
    }

    return render(request, template_name=template, context=context)


# Rechercher d'un membre par son identifiant

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


def has_participed_annuel(request):
    template = "site/client/caisse/has_participed_annuel.html"
    context = {}

    qs = StatusMemberAnnualParticipation.objects.all().order_by('id')
    print('DEbut de la fontion has_participed_annuel')

    # On récupère toutes les années configurées dans la table AmountContributionYear
    # On les trie par année croissante ou décroissante selon votre besoin
    years = list(AmountContributionYear.objects.values_list('year', flat=True).order_by('year'))
    context['years'] = [str(y) for y in years]  # On convertit en string pour le mapping JSON du template

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
    print('fin de la fontion has_participed_annuel')
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


# ... existing code ...
from django.shortcuts import render
from .models import BtestCustomUser


def contact_page(request):
    """Affiche les contacts triés par hiérarchie de rôles"""
    # On récupère les utilisateurs ayant un rôle, triés par le poids du rôle
    # S'assurer que les ROLE_CHOICES sont ordonnés ou utilisez une logique de tri
    contacts = BtestCustomUser.objects.filter(role__isnull=False).exclude(role='USER').order_by('-role')

    # On regroupe par libellé de rôle pour le template
    from itertools import groupby

    # Il est préférable de trier explicitement si ROLE_CHOICES n'est pas alphabétique
    # Ici on utilise groupby pour créer des sections par rôle
    contacts_grouped = {}
    for role_code, group in groupby(contacts, lambda x: x.get_role_display()):
        contacts_grouped[role_code] = list(group)

    return render(request, 'site/client/contacts.html', {
        'contacts_grouped': contacts_grouped,
        'title': "Bureau & Contacts"
    })


def mb_monde_view(request):
    """Affiche la liste des pays et les membres filtrés par pays"""
    # Liste python des pays (basée sur vos choix dans forms.py)
    countries_list = [
        'Guinée', 'Senégal', "Côte d'ivoir", "Benin", "Togo",
        "Guinée Bissau", "Mali", "Burkina Faso", "Angola",
        "Gambie", "Europe", "Asie", "USA", "Canada"
    ]

    selected_country = request.GET.get('country')
    members = None

    if selected_country:
        # Sélectionne toutes les personnes ayant ce pays
        members = BtestCustomUser.objects.filter(pays__iexact=selected_country).order_by('prenoms')

    context = {
        'countries': countries_list,
        'selected_country': selected_country,
        'members': members,
        'title': f"Membres en {selected_country}" if selected_country else "Missideh Bourou dans le Monde"
    }
    return render(request, 'site/client/mb_monde.html', context)