from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.core.exceptions import PermissionDenied
from django.http import JsonResponse, HttpResponseForbidden
from django.shortcuts import get_object_or_404, render, redirect
from django.views.decorators.csrf import csrf_exempt

from Bapp.forms import EditorialCommunityForm, UserEditForm, ParticipationAnnuelForm, BtestUserCreationsForms
from Bapp.models import EditorialCommunity, BtestCustomUser, ParticipationAnnual
from Bapp.permissions import auto_logout, can_edit_article, can_add_user


# Il faut être admin ou auteur du rôle pour pouvoir supprimer ou modifier le contenu de cette méthode

def edit_user_old(request, user_id=None):
    """
    Vue pour créer/modifier un utilisateur
    Si user_id est None: création d'un nouvel utilisateur
    """
    #template_name = 'site/admin/delete_items/modify_users.html'
    template_name = 'site/admin/admin_subcribe.html'
    context = {}
    # Gestion différenciée création/modification
    if user_id:
        user = get_object_or_404(BtestCustomUser, id=user_id)
        is_creation = False
    else:
        user = None
        is_creation = True

    # Vérification des permissions
    if not is_creation and not (request.user.is_superuser or request.user == user.created_by):
        messages.error(request, "Vous n'avez pas la permission de modifier cet utilisateur")
        return redirect('Bapp:list_users')

    if request.method == 'POST':
        form = UserEditForm(request.POST, request.FILES, instance=user)
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
    return render(request, template_name=template_name, context=context)

@can_add_user(['ADMIN', 'MODERATOR'])
def edit_user(request, user_id=None):
    """
    Vue pour créer/modifier un utilisateur en utilisant BtestUserCreationsForms
    """
    template_name = 'site/admin/delete_items/modify_users.html'
    context = {}

    if user_id:
        user = get_object_or_404(BtestCustomUser, id=user_id)
        is_creation = False
    else:
        user = None
        is_creation = True

    # Vérification des permissions pour l'édition
    if not is_creation and not (request.user.is_superuser or request.user.role == 'ADMIN'):
        # Optionnel : permettre à l'auteur de modifier
        pass

    if request.method == 'POST':
        # On passe l'instance pour que le formulaire sache quel utilisateur modifier
        form = BtestUserCreationsForms(request.POST, request.FILES, instance=user)

        # ASTUCE : En mode édition, on retire la validation d'email unique si c'est le même email
        if not is_creation:
            # On peut supprimer dynamiquement des validateurs ou gérer dans clean_email
            pass

        if form.is_valid():
            user_obj = form.save(commit=False)

            # Gestion du mot de passe (ne pas écraser s'il est vide en édition)
            password = form.cleaned_data.get('password')
            if password:
                user_obj.set_password(password)
            elif is_creation:
                # Gérer un mot de passe par défaut ou erreur si création sans password
                messages.error(request, "Le mot de passe est requis pour la création.")
                return render(request, template_name, {'form': form, 'is_creation': is_creation})

            user_obj.save()
            form.save_m2m()

            messages.success(request, f"Utilisateur {'créé' if is_creation else 'mis à jour'} avec succès")
            return redirect('Bapp:list_users')
        else:
            print(form.errors)  # Pour le debug
    else:
        form = BtestUserCreationsForms(instance=user)
        # En mode édition, on rend le mot de passe non obligatoire visuellement
        if not is_creation:
            form.fields['password'].required = False

    context['form'] = form
    context['is_creation'] = is_creation
    context['user'] = user
    return render(request, template_name, context)

# Il faut être admin ou auteur du rôle pour pouvoir supprimer ou modifier le contenu de cette méthode


@can_add_user(['ADMIN', 'MODERATOR'])
def delete_user(request, user_id):
    """
    Vue pour supprimer un utilisateur de manière asynchrone
    """
    if request.method == 'POST':
        user_to_delete = get_object_or_404(BtestCustomUser, id=user_id)
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


# Il faut être admin ou auteur du rôle pour pouvoir supprimer ou modifier le contenu de cette méthode

@can_add_user(['ADMIN', 'MODERATOR'])
def confirm_delete_user(request, user_id):
    template_name = 'site/admin/delete_items/confirm_delete_user.html'
    context = {}
    user = get_object_or_404(BtestCustomUser, id=user_id)
    context['user'] = user
    return render(request, template_name=template_name, context=context)
