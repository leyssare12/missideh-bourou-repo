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


@login_required
def list_participations_annuel(request):
    template = 'site/admin/list_items/cotisation_annuel_list.html'
    context = {}

    if not request.user.is_authenticated:
        messages.warning(request, "Veuillez vous connecter pour accéder à cette page.")
        return redirect("Bapp:manager_login_page")

    try:
        if request.user.is_superuser:
            # Les super-utilisateurs voient toutes les participations
            cotisations = ParticipationAnnual.objects.all().order_by('-date_participation')
        else:
            # Les utilisateurs normaux voient leurs propres participations
            cotisations = ParticipationAnnual.objects.filter(
                created_by=request.user
            ).order_by('-date_participation')
            print(cotisations)

        # Pagination
        page = request.GET.get('page', 1)
        paginator = Paginator(cotisations, 10)  # 10 éléments par page

        try:
            context['page_obj'] = paginator.page(page)
        except PageNotAnInteger:
            context['page_obj'] = paginator.page(1)
        except EmptyPage:
            context['page_obj'] = paginator.page(paginator.num_pages)

    except Exception as e:
        messages.error(request, f"Une erreur s'est produite lors de la récupération des données : {str(e)}")
        context['page_obj'] = []

    return render(request, template_name=template, context=context)


#On peut consulter la liste d'utilisateurs inscrits si on fait partie du STAFF
#Mais on ne va pas pourvoir les modifier ou supprimer.
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
            # Attention ici: User.objects.get(identifiant=request.user) est risqué si request.user est déjà une instance User
            # On préfère utiliser request.user directement s'il est authentifié
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
#On peut consulter les articles publiers si on fait partie du STAFF
#Mais on ne va pas pourvoir les modifier ou supprimer.
@login_required
def list_articles_save(request):
    templane_name = "site/admin/list_items/articles_list.html"
    context = {}
    if not request.user.is_authenticated:
        print("Vous devez-vous connecter pour accéder à cette page.")
        return redirect('Bapp:manager_login_page')
    #On recupère la session de l'utilisateur
    user_session = request.session.get('user_name', "Votre session a expiré")
    session_expired = request.session.get('session_expired', False)
    if request.user.is_superuser:
        #Si c'est le superuser, on recupére tous les articles
        articles = EditorialCommunity.objects.all().order_by('-updated_at')
        context['articles'] = articles
    else:
        #On recupére uniquement les articles écrit par cet utilisateur
        print(request.user)
        articles = EditorialCommunity.objects.filter(author=request.user.prenoms)
        context['articles'] = articles
        request.session['user_name'] = request.user.prenoms
    #On vérifie si l'utilsateur a dèjá d'Articles écrit à son compte
    user_has_published_articles = articles.exists()
    context['user_has_published_articles'] = user_has_published_articles

    context['user_session'] = user_session
    context['session_expired'] = session_expired
    #on récupère le nom de l'utilsateur connecté
    context['user_name'] = request.user.prenoms
    return render(request, template_name=templane_name, context=context)



# Liste des articles (avec pagination)
@can_edit_article(['ADMIN', 'EDITOR', 'MODERATOR'])
def list_articles(request):
    templane_name = "site/admin/gestion_articles/article_list.html"
    context = {}
    if request.user.is_superuser:
        articles = EditorialCommunity.objects.all().order_by('-updated_at')
    else:
        articles = EditorialCommunity.objects.filter(author=request.user.prenoms).order_by('-updated_at')

    paginator = Paginator(articles, 5)  # 5 articles par page
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    context['page_obj'] = page_obj
    return render(request, template_name=templane_name, context=context)

# Modifier un article
@can_edit_article(['ADMIN', 'EDITOR', "MODERATOR"])
def edit_article(request, pk):
    templane_name = "site/admin/gestion_articles/edit_article.html"
    context = {}
    article = get_object_or_404(EditorialCommunity, pk=pk)
    if not (request.user.is_superuser or article.author == request.user):
        return redirect('Bapp:article_list')  # Accès refusé si non-auteur/non-superuser

    if request.method == 'POST':
        form = EditorialCommunityForm(request.POST, request.FILES, instance=article)
        if form.is_valid():
            form.save()
            messages.success(request, 'Formulaire modifié avec succès.')
            print('formulaire poster avec succes')
            return redirect('Bapp:article_list')
    else:
        form = EditorialCommunityForm(instance=article)
    context['form'] = form
    return render(request, template_name=templane_name, context=context)

# Supprimer un article
@can_edit_article(['ADMIN', 'EDITOR'])
def delete_article(request, pk):
    templane_name = "site/admin/gestion_articles/delete_article.html"
    context = {}
    article = get_object_or_404(EditorialCommunity, pk=pk)
    if not (request.user.is_superuser or article.author == request.user):
        return redirect('Bapp:article_list')

    if request.method == 'POST':
        article.delete()
        return redirect('Bapp:article_list')
    context['article'] = article
    return render(request, template_name=templane_name, context=context)