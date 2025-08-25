from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.core.exceptions import PermissionDenied
from django.http import JsonResponse, HttpResponseForbidden
from django.shortcuts import get_object_or_404, render, redirect
from django.views.decorators.csrf import csrf_exempt

from Bapp.forms import EditorialCommunityForm, UserEditForm, ParticipationAnnuelForm
from Bapp.models import EditorialCommunity, BTestCustomUser, ParticipationAnnual
from Bapp.permissions import auto_logout, can_edit_article, can_add_user

#Il faut être admin ou auteur du rôle pour pouvoir supprimer ou modifier le contenu de cette méthode
@can_edit_article(['ADMIN','EDITOR'])
def delete_article(request, post_id):
    templates = 'site/admin/delete_items/confirm_delete_publication.html'
    context={}
    article = get_object_or_404(EditorialCommunity, id=post_id)

    #S'assurer que c'est seul le superuser ou la personne qui a écrit l'article ont le droit de le supprimer
    if request.user.prenoms != article.author and not request.user.is_superuser:
        return HttpResponseForbidden("You are not authorized to delete this post.")

    if request.method == 'POST':
        article.delete()
        print("Article supprimé avec succés")
        messages.success(request, f"{article.title} Supprimé avec success ")
        return redirect('Bapp:list_articles')  # On redirige vers la listes des artilces
    context['article'] = article
    return render(request, template_name=templates, context=context)

#Il faut être admin ou auteur du rôle pour pouvoir supprimer ou modifier le contenu de cette méthode
@can_edit_article(['ADMIN','EDITOR'])
def modify_article(request, pk):
    templates = 'site/editions/editions.html'
    context = {}
    article = get_object_or_404(EditorialCommunity, pk=pk)
    print(article.author, request.user.prenoms, request.user.is_superuser)
    # Vérifier si l'utilisateur est l'auteur de l'article ou un superuser
    if request.user.prenoms != article.author and not request.user.is_superuser:
        raise PermissionDenied

    if request.method == "POST":
        form = EditorialCommunityForm(request.POST, request.FILES, instance=article)

        # Désactivez la validation du champ image si aucun fichier n'est téléchargé
        if form.is_valid():
            try:
                form_save = form.save(commit=False)
                form_save.author = request.user.prenoms
                form_save.save()
                print('formulaire poster avec succes')
                if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                    return JsonResponse({
                        'success': "L'article a été enregistré avec succès!"
                    })
                return redirect(request.path)
            except Exception as e:
                error_msg = f"Erreur lors de l'enregistrement : {str(e)}"
                if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                    return JsonResponse({
                        'errors': error_msg
                    }, status=400)
    else:
        print('formulaire non poster')
        form = EditorialCommunityForm(instance=article)
        context["form"] = form
    return render(request, template_name=templates, context=context)


#Il faut être admin ou auteur du rôle pour pouvoir supprimer ou modifier le contenu de cette méthode
@can_add_user(['ADMIN', 'MODERATOR'])
def edit_user(request, user_id=None):
    """
    Vue pour créer/modifier un utilisateur
    Si user_id est None: création d'un nouvel utilisateur
    """
    template_name = 'site/admin/delete_items/modify_users.html'
    context = {}
    # Gestion différenciée création/modification
    if user_id:
        user = get_object_or_404(BTestCustomUser, id=user_id)
        is_creation = False
    else:
        user = None
        is_creation = True

    # Vérification des permissions
    if not is_creation and not (request.user.is_superuser or request.user == user.created_by):
        messages.error(request, "Vous n'avez pas la permission de modifier cet utilisateur")
        return redirect('Bapp:list_users')

    if request.method == 'POST':
        form = UserEditForm(request.POST,  request.FILES, instance=user)
        if form.is_valid():
            user = form.save(commit=False)
            user.created_by = request.user
            print(f"modification effectué par {request.user}")
            user.save()
            form.save_m2m()  # Pour les champs many-to-many

            messages.success(request,
                             f"Utilisateur {'créé' if is_creation else 'mis à jour'} avec succès")
            return redirect('Bapp:list_users')
    else:
        form = UserEditForm(instance=user)

    # Pré-remplir certains champs pour la création
    if is_creation:
        form.fields['created_by'].initial = request.user
        form.fields['is_active'].initial = True
    context['form'] = form
    context['is_creation'] = is_creation
    context['user'] = user
    return render(request, template_name=template_name,  context=context)

#Il faut être admin ou auteur du rôle pour pouvoir supprimer ou modifier le contenu de cette méthode
@can_add_user(['ADMIN', 'MODERATOR'])
def delete_user(request, user_id):
    """
    Vue pour supprimer un utilisateur de manière asynchrone
    """
    if request.method == 'POST':
        user_to_delete = get_object_or_404(BTestCustomUser, id=user_id)
        try:
            print(user_to_delete)
            user_to_delete.delete()
            messages.success(request, f"L'utilisateur {user_to_delete} a été supprimé avec succès.")
            return redirect('Bapp:list_users')
        except Exception as e:
            messages.error(request, f"Erreur lors de la suppression : {str(e)}")
            return redirect('Bapp:confirm_delete_user', user_id=user_to_delete.id)

        # Si la méthode n'est pas POST, redirige vers la confirmation
    return redirect('Bapp:confirm_delete_user', user_id=user_id)

#Il faut être admin ou auteur du rôle pour pouvoir supprimer ou modifier le contenu de cette méthode
@can_add_user(['ADMIN', 'MODERATOR'])
def confirm_delete_user(request, user_id):
    template_name = 'site/admin/delete_items/confirm_delete_user.html'
    context = {}
    user = get_object_or_404(BTestCustomUser, id=user_id)
    context['user'] = user
    return render(request, template_name=template_name, context=context)


def edit_cotisation_annuel(request, pk):
    templates = 'site/admin/delete_items/modify_cotisation_annuel.html'
    context = {}

    cotisation = get_object_or_404(ParticipationAnnual, pk=pk)

    # Vérification des permissions (ajustez selon votre logique)
    if not (request.user.is_superuser or cotisation.created_by == request.user):
        messages.error(request, "Vous n'avez pas la permission de modifier cette cotisation.")
        return redirect('Bapp:manager_login_page')

    if request.method == 'POST':
        form = ParticipationAnnuelForm(request.POST, instance=cotisation)
        if form.is_valid():
            form.save()
            messages.success(request, "La cotisation a été mise à jour avec succès.")
            return redirect('Bapp:list_participations_annuelles')
    else:
        form = ParticipationAnnuelForm(instance=cotisation)
    context['form'] = form
    context['cotisation'] = cotisation

    return render(request, template_name=templates, context=context)


def delete_cotisation_annuel(request, pk):
    templates = 'site/admin/delete_items/delete_cotisation_annuel.html'
    context = {}

    cotisation = get_object_or_404(ParticipationAnnual, pk=pk)

    # Vérification des permissions
    if not (request.user.is_superuser or cotisation.created_by == request.user):
        messages.error(request, "Vous n'avez pas la permission de supprimer cette cotisation.")
        return redirect('Bapp:manager_login_page')

    if request.method == 'POST':
        cotisation.delete()
        messages.success(request, "La cotisation a été supprimée avec succès.")
        return redirect('Bapp:list_participations_annuelles')
    context['cotisation'] = cotisation

    return render(request, template_name=templates, context=context)