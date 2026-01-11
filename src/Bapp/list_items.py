from django.contrib import messages
from django.contrib.auth import get_user_model
from django.contrib.auth.decorators import login_required
from django.core.paginator import Paginator, PageNotAnInteger, EmptyPage
from django.db.models import Q
from django.shortcuts import redirect, render, get_object_or_404

from Bapp.forms import EditorialCommunityForm
from Bapp.models import EditorialCommunity, ParticipationAnnual
from Bapp.permissions import can_edit_article, can_add_user

User = get_user_model()


# On peut consulter la liste d'utilisateurs inscrits si on fait partie du STAFF
# Mais on ne va pas pourvoir les modifier ou supprimer.
@can_add_user(['ADMIN', 'MODERATOR'])
def list_subscribed_users_old(request):
    template_name = "site/admin/list_items/users_list.html"  # Chemin vers le nouveau template
    context = {}

    # Vérification d'authentification
    if not request.user.is_authenticated:
        return redirect("Bapp:manager_login_page")

    # Configuration de la pagination
    items_per_page = 12  # Nombre optimal pour le design en grille
    page_number = request.GET.get('page', 1)
    # 1. Récupération du terme de recherche depuis l'URL (ex: ?q=mamadou)
    search_query = request.GET.get('q', '').strip()
    # Gestion différenciée selon le type d'utilisateur
    if request.user.is_superuser:
        # Superuser voit tous les utilisateurs
        users_queryset = User.objects.select_related('created_by').all().order_by('-date_joined')
    else:
        # Les autres voient seulement les utilisateurs qu'ils ont créés
        try:
            creator = User.objects.get(identifiant=request.user)
            users_queryset = creator.created_by_user.all().select_related('created_by').order_by('-date_joined')
        except User.DoesNotExist:
            users_queryset = User.objects.none()

    # Pagination optimisée
    paginator = Paginator(users_queryset, items_per_page)
    users_page = paginator.get_page(page_number)
    # 2. Application du filtre de recherche (si 'q' existe)
    if search_query:
        users_queryset = users_queryset.filter(
            Q(prenoms__icontains=search_query) |
            Q(email__icontains=search_query) |
            Q(identifiant__icontains=search_query)
        )
    # Préparation du contexte enrichi
    context.update({
        'users_list': users_page,  # Contient déjà la pagination
        'total_users': users_queryset.count(),
        'current_user': request.user,
        'is_superuser': request.user.is_superuser,
        # Ajout pour les fonctionnalités avancées du template
        'page_title': "Gestion de membres  Missidhé Bourou",
        'can_delete': True,  # Autorisation pour les boutons de suppression
        'search_query': search_query,
    })

    # Debug: vérification des données envoyées au template
    print(f"Users envoyés au template: {users_page.object_list.count()}")
    print(f"Total users: {users_queryset.count()}")

    return render(request, template_name, context)


@can_add_user(['ADMIN', 'MODERATOR'])
def list_subscribed_users(request):
    template_name = "site/admin/list_items/users_list.html"
    context = {}

    # Vérification d'authentification
    if not request.user.is_authenticated:
        return redirect("Bapp:manager_login_page")

    # Configuration de la pagination
    items_per_page = 12
    page_number = request.GET.get('page', 1)

    # --- PARTIE CRITIQUE POUR LA RECHERCHE ---
    # 1. On récupère ce qui est écrit dans l'URL (?q=...)
    search_query = request.GET.get('q', '').strip()

    # 2. On définit la requête de base selon les droits
    if request.user.is_superuser:
        users_queryset = User.objects.select_related('created_by').all().order_by('-date_joined')
    else:
        try:
            # Attention ici: User.objects.get(identifiant=request.user) est risqué si request.user est déjà une
            # instance User On préfère utiliser request.user directement s'il est authentifié
            users_queryset = request.user.created_by_user.all().select_related('created_by').order_by('-date_joined')
        except Exception:
            users_queryset = User.objects.none()

    # 3. On applique le filtre SI une recherche existe
    if search_query:
        users_queryset = users_queryset.filter(
            Q(prenoms__icontains=search_query) |
            Q(email__icontains=search_query) |
            Q(identifiant__icontains=search_query) |
            Q(telephone__icontains=search_query)
        )
        # Optionnel : On reset la pagination à 1 lors d'une recherche pour éviter les pages vides
        page_number = 1

    # Pagination
    paginator = Paginator(users_queryset, items_per_page)
    users_page = paginator.get_page(page_number)

    # Context
    context.update({
        'users_list': users_page,
        'total_users': users_queryset.count(),
        'current_user': request.user,
        'is_superuser': request.user.is_superuser,
        'page_title': "Gestion de membres Missidhé Bourou",
        'can_delete': True,
        'search_query': search_query,  # Important pour réafficher le texte dans l'input
    })

    return render(request, template_name, context)
