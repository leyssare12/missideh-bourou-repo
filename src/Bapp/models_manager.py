from django.contrib.messages import success
from django.forms import modelform_factory
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger
from django.contrib.auth.decorators import login_required
from django.utils.decorators import method_decorator
from django.views import View

from Bapp.forms import ParticipationAnnuelForm, ParticipationOccasionnelleForm, DonsForm, AddDepensesForm, \
    EvenementOccasionnelleForm, CotisationOccasionnelleForm, AmountContributionYearForm, EditorialCommunityForm
from Bapp.models import ParticipationAnnual, ParticipationOccasionnelle, Dons, AddDepenses, CotisationOccasionnelle, \
    BtestCustomUser, EvenementOccasionnelle, AmountContributionYear, EditorialCommunity
from Bapp.permissions import has_secretor_role


def get_crud_permissions(user, crud_type):
    """
    Retourne un dictionnaire de permissions basé sur le rôle et le type de contenu.
    """
    perms = {
        'can_add': False,
        'can_edit': False,
        'can_delete': False
    }

    if not user.is_authenticated:
        return perms

    # 1. ADMIN : Accès total partout
    if user.role == 'ADMIN':
        print('je suis admin')
        return {k: True for k in perms}

    if user.role == 'VICE_PRESIDENT' or user.role == 'PRESIDENT':
        print('je suis secretor')
        if crud_type == 'EVENEMENTOCCASIONNELLE' or crud_type == 'AMOUNTCONTRIBUTIONYEAR':
            perms['can_add'] = True
            perms['can_edit'] = True
            perms['can_delete'] = True
        return perms
    # 2. SECOND_SECRETOR : Gère uniquement les dépenses
    if user.role == 'SECOND_SECRETOR':
        print('je suis secretor')
        if crud_type == 'ADDDEPENSES':
            perms['can_add'] = True
            perms['can_edit'] = True
            perms['can_delete'] = True
        return perms
    # Le SECRETOR : Gère uniquement les dons et les cotisations
    if user.role == 'SECRETOR':
        print('je suis secretor')
        if crud_type == 'DONS' or crud_type == 'COTISATIONOCCASIONNELLE' or crud_type == 'PARTICIPATIONANNUAL':
            perms['can_add'] = True
            perms['can_edit'] = True
            perms['can_delete'] = True
        return perms
    # 3. EDITOR : Gère uniquement la partie éditoriale (INFO)
    if user.role == 'EDITOR':
        print('je suis editor')
        if crud_type == 'EDITORIALCOMMUNITY':
            perms['can_add'] = True
            perms['can_edit'] = True
            perms['can_delete'] = True
        return perms

    # 4. MODERATOR : Peut voir et éditer les utilisateurs mais pas forcément les finances
    if user.role == 'MODERATOR':
        print('je suis moderator')
        if crud_type == 'USER_LIST':
            perms['can_add'] = True
            perms['can_edit'] = True
        return perms

    return perms


class ModelCRUDManager:
    """
    Classe générique pour gérer les opérations CRUD sur différents modèles
    """

    def __init__(self, model,
                 template_folder,
                 items_per_page=10,
                 context_mapping=None,
                 success_url=None,
                 default_ordering=None,
                 template_names=None,
                 form_class=None,
                 user_field='created_by',
                 ):
        self.model = model
        self.user_field = user_field
        self.template_folder = template_folder
        self.items_per_page = items_per_page
        self.form_class = form_class
        self.success_url = success_url or 'Bapp:index'  # URL par défaut
        self.default_context_keys = {
            'form': 'form',
            'item': 'item',
            'page_obj': 'page_obj',
            'model_name': 'model_name'

        }
        self.default_ordering = default_ordering or ('-date_participation',)
        self.template_names = template_names or {
            'list': 'list_items_forms',
            'add_or_modify': 'template_forms',
            'delete': 'delete_forms'
        }  # Valeurs par défaut si non spécifiées

        #si ya une clé en parametre, on le prend en compte
        if context_mapping:
            self.default_context_keys.update(context_mapping)

    def get_ordering(self):
        return self.default_ordering

    def get_url_patterns(self):
        return f'{self.namespace}'

    def get_template_path(self, action):
        """Retourne le chemin complet du template en fonction de l'action"""
        template_name = self.template_names.get(action, action)
        return f"{self.template_folder}/{template_name}.html"

    def get_form_class(self, view_instance=None):
        """Retourne la classe de formulaire avec possibilité de surcharge"""
        # 1. Vérifie d'abord si le formulaire est défini dans l'instance de vue
        if view_instance and hasattr(view_instance, 'form_class'):
            return view_instance.form_class
        # 2. Sinon utilise le form_class du manager ou crée un ModelForm générique
        if self.form_class:
            return self.form_class
        # 3. Fallback sur un ModelForm générique
        return modelform_factory(self.model, fields='__all__')

    def handle_list(self, request):
        """Gestion de la liste des éléments"""
        if not request.user.is_authenticated:
            messages.warning(request, "Veuillez vous connecter pour accéder à cette page.")
            return redirect("Bapp:manager_login_page")
        try:
            if request.user.is_superuser:
                items = self.model.objects.all()
            else:
                pass
                # Utilise le filtrage dynamique
                # filter_kwargs = {self.user_field: request.user}
                # items = self.model.objects.filter(**filter_kwargs)
            items = self.model.objects.all()
            # Ajout du tri
            items = items.order_by(self.get_ordering())
            print('Je suis la liste des items')
            # Pagination
            page = request.GET.get('page', 1)
            paginator = Paginator(items, self.items_per_page)

            try:
                page_obj = paginator.page(page)
            except PageNotAnInteger:
                page_obj = paginator.page(1)
            except EmptyPage:
                page_obj = paginator.page(paginator.num_pages)
            # On récupère le nom du modèle pour construire les URLs dynamiquement
            # Ex: si model est Dons, url_base sera 'dons'
            model_name_lower = self.model._meta.model_name.lower()
            model_name_upper = self.model._meta.model_name.upper()
            # Appel de la méthode de permissions
            permissions = get_crud_permissions(request.user, model_name_upper)
            print(f'La permissions sont :{permissions}')
            context = {self.default_context_keys['page_obj']: page_obj,
                       'model_name': self.model._meta.verbose_name,
                       'url_edit': f'Bapp:edit_{model_name_lower}',
                       'url_delete': f'Bapp:delete_{model_name_lower}',
                       'url_add': f'Bapp:add_{model_name_lower}', 'page_obj': page_obj,
                       'crud_type': model_name_upper,  # L'IDENTIFIANT UNIQUE ICI
                       }
            # On fusionne les permissions dans le contexte
            context.update(permissions)
            return render(request, self.get_template_path('list'), context)

        except Exception as e:
            messages.error(request, f"Une erreur s'est produite : {str(e)}")
            return redirect('Bapp:dashboard2')

    def handle_edit_old(self, request, item_id, view_instance=None):
        """Gestion de la modification d'un élément"""
        print('je suis dans le handle_edit')
        try:
            item = get_object_or_404(self.model, id=item_id)
            FormClass = self.get_form_class(view_instance)

            # Vérification des permissions
            if not (request.user.is_superuser or item.created_by == request.user):
                messages.error(request, "Vous n'avez pas la permission de modifier cet élément.")
                return redirect('Bapp:manager_login_page')

            if request.method == 'POST':
                # Utilise get_form_class avec l'instance de la vue
                form = FormClass(request.POST, instance=item)
                if form.is_valid():
                    form.save()
                    messages.success(request, f"{self.model._meta.verbose_name} modifié avec succès.")
                    return redirect(self.success_url)
            else:
                print('pas de model model:', self.get_form_class(view_instance))
                form = FormClass(instance=item)
            context = {
                self.default_context_keys['form']: form,
                self.default_context_keys['items']: item,
                self.default_context_keys['model_name']: self.model._meta.verbose_name
            }

            return render(request, self.get_template_path('add_or_modify'), context)

        except Exception as e:
            messages.error(request, f"Une erreur s'est produite : {str(e)}")
            return redirect('Bapp:dashboard2')

    def handle_form_old(self, request, item_id=None, view_instance=None):
        """
        Détermine dynamiquement si on Ajoute ou on Modifie.
        Retourne un Redirect (Succès) ou un Render (Affichage/Erreur).
        """
        # DISTINCTION : Si item_id existe, c'est une modification (Modify), sinon c'est un ajout (Add)
        try:
            instance = get_object_or_404(self.model, id=item_id) if item_id else None
            FormClass = self.get_form_class(view_instance)

            # Action courante pour les messages
            action_name = "modifié" if instance else "ajouté"

            if request.method == 'POST':
                form = FormClass(request.POST, request.FILES, instance=instance)
                if form.is_valid():
                    obj = form.save(commit=False)
                    # Si c'est un ajout, on peut injecter l'utilisateur connecté
                    if not instance:
                        obj.created_by = request.user
                    obj.save()

                    messages.success(request, f"{self.model._meta.verbose_name} {action_name} avec succès.")

                    # RETOUR TYPE 1 : Redirection après succès (Valable pour Add et Modify)
                    return redirect(self.success_url)
                else:
                    messages.error(request, "Veuillez corriger les erreurs ci-dessous.")
            else:
                form = FormClass(instance=instance)

            # Configuration UI spécifique
            context = {
                'form': form,
                'item': instance,
                'title': f"{'Modifier' if instance else 'Nouveau'} {self.model._meta.verbose_name}",
                'cfg': getattr(form, 'ui_config', {}),
                'is_edit': bool(instance),
            }

            # RETOUR TYPE 2 : Rendu du template (Valable pour Add et Modify)
            # On utilise le template défini dans template_names['edit'] pour les deux actions
            return render(request, self.get_template_path('add_or_modify'), context)
        except Exception as e:
            messages.error(request, f"Une erreur s'est produite : {str(e)}")
            return redirect('Bapp:dashboard2')

    def handle_form(self, request, item_id=None, view_instance=None):
        """
        Détermine dynamiquement si on Ajoute ou on Modifie.
        Retourne un Redirect (Succès) ou un Render (Affichage/Erreur).
        """
        from django.db import IntegrityError  # Import nécessaire pour intercepter les erreurs DB

        try:
            instance = get_object_or_404(self.model, id=item_id) if item_id else None
            FormClass = self.get_form_class(view_instance)
            action_name = "modifié" if instance else "ajouté"

            if request.method == 'POST':
                form = FormClass(request.POST, request.FILES, instance=instance)
                if form.is_valid():
                    try:
                        obj = form.save(commit=False)
                        if not instance and hasattr(obj, 'created_by'):
                            obj.created_by = request.user
                        obj.save()

                        messages.success(request, f"{self.model._meta.verbose_name} {action_name} avec succès.")
                        return redirect(self.success_url)

                    except IntegrityError as e:
                        # Capture les erreurs de contraintes uniques SQL (ex: membre déjà inscrit cette année)
                        error_msg = str(e).lower()
                        if "unique" in error_msg or "dupliquée" in error_msg:
                            messages.error(request, "Erreur : Cet enregistrement existe déjà (doublon détecté).")
                        else:
                            messages.error(request, f"Erreur de base de données : {str(e)}")
                else:
                    # Ici, les erreurs du clean() du formulaire sont déjà dans form.errors
                    # et seront affichées automatiquement dans le template.
                    messages.error(request, "Veuillez corriger les erreurs dans le formulaire.")
            else:
                form = FormClass(instance=instance)

            # ... reste du contexte ...
            context = {
                'form': form,
                'item': instance,
                'title': f"{'Modifier' if instance else 'Nouveau'} {self.model._meta.verbose_name}",
                'cfg': getattr(form, 'ui_config', {}),
                'is_edit': bool(instance),
            }
            return render(request, self.get_template_path('add_or_modify'), context)

        except Exception as e:
            messages.error(request, f"Une erreur inattendue s'est produite : {str(e)}")
            return redirect('Bapp:dashboard2')

    def handle_delete(self, request, item_id):
        """Gestion de la suppression d'un élément"""
        try:
            item = get_object_or_404(self.model, id=item_id)

            # Vérification des permissions
            if not (request.user.is_superuser or item.created_by == request.user):
                messages.error(request, "Vous n'avez pas la permission de supprimer cet élément.")
                return redirect(self.success_url)

            if request.method == 'POST':
                item.delete()
                messages.success(request, f"{self.model._meta.verbose_name} supprimé avec succès.")
                return redirect(self.success_url)

            context = {
                self.default_context_keys['item']: item,
                self.default_context_keys['model_name']: self.model._meta.verbose_name,
                'item': item,  # Clé fixe pour delete_forms.html
                'model_name': self.model._meta.verbose_name,
            }

            return render(request, self.get_template_path('delete'), context)

        except Exception as e:
            messages.error(request, f"Une erreur s'est produite : {str(e)}")
            return redirect('Bapp:dashboard2')


'''
    Participation annuelle manager
'''


class ParticipationAnnuelManager(View):
    crud_manager = ModelCRUDManager(
        model=ParticipationAnnual,
        form_class=ParticipationAnnuelForm,  # Définir le formulaire ici

        template_folder='site/admin',
        template_names={
            'add_or_modify': 'template_forms',
            'list': 'list_items_forms',
            'delete': 'delete_forms'
        },
        success_url="Bapp:list_participations_annuelles",
        default_ordering='-updated_at',
    )

    def dispatch(self, request, *args, **kwargs):
        # On centralise la redirection vers handle_form ou handle_list
        action = kwargs.get('action')
        item_id = kwargs.get('item_id')

        if action in ['edit', 'add']:
            return self.crud_manager.handle_form(request, item_id)
        elif action == 'delete':
            return self.crud_manager.handle_delete(request, item_id)

        return self.crud_manager.handle_list(request)


'''
    Cotisation occasionnelle
'''


class ParticipationOcasionnelleManager(View):
    crud_manager = ModelCRUDManager(
        model=CotisationOccasionnelle,
        form_class=CotisationOccasionnelleForm,  # Définir le formulaire ici

        template_folder='site/admin',
        template_names={
            'add_or_modify': 'template_forms',
            #'list': 'cotisation_occasionnel_manager/cotisation_occasionnel_list',
            'delete': 'delete_forms',
            'list': 'list_items_forms',
        },
        success_url="Bapp:list_participations_occasionnelles",
        default_ordering='-updated_at',
    )

    def dispatch(self, request, *args, **kwargs):
        # On centralise la redirection vers handle_form ou handle_list
        action = kwargs.get('action')
        item_id = kwargs.get('item_id')

        if action in ['edit', 'add']:
            return self.crud_manager.handle_form(request, item_id)
        elif action == 'delete':
            return self.crud_manager.handle_delete(request, item_id)

        return self.crud_manager.handle_list(request)


'''
    Dons manger
'''


class DonsManager(View):
    crud_manager = ModelCRUDManager(
        model=Dons,
        form_class=DonsForm,  # Définir le formulaire ici

        template_folder='site/admin',
        template_names={
            #'list': 'dons_manager/dons_list',
            'list': 'list_items_forms',
            'add_or_modify': 'template_forms',
            'delete': 'delete_forms'
        },
        success_url="Bapp:list_dons",
        default_ordering='-updated_at',
    )

    def dispatch(self, request, *args, **kwargs):
        # On centralise la redirection vers handle_form ou handle_list
        action = kwargs.get('action')
        item_id = kwargs.get('item_id')

        if action in ['edit', 'add']:
            return self.crud_manager.handle_form(request, item_id)
        elif action == 'delete':
            return self.crud_manager.handle_delete(request, item_id)

        return self.crud_manager.handle_list(request)


'''
    depenses manager
'''


class DepensesManager(View):
    crud_manager = ModelCRUDManager(
        model=AddDepenses,
        form_class=AddDepensesForm,  # Définir le formulaire ici

        template_folder='site/admin',
        template_names={
            'list': 'list_items_forms',
            #'list': 'depense_manager/list_depense',
            'add_or_modify': 'template_forms',
            'delete': 'delete_forms'
        },
        success_url="Bapp:list_adddepenses",
        default_ordering='-updated_at',
    )

    def dispatch(self, request, *args, **kwargs):
        # On centralise la redirection vers handle_form ou handle_list
        action = kwargs.get('action')
        item_id = kwargs.get('item_id')

        if action in ['edit', 'add']:
            return self.crud_manager.handle_form(request, item_id)
        elif action == 'delete':
            return self.crud_manager.handle_delete(request, item_id)

        return self.crud_manager.handle_list(request)


class EvenementOccasionnelleManager(View):
    crud_manager = ModelCRUDManager(
        model=EvenementOccasionnelle,
        form_class=EvenementOccasionnelleForm,  # Définir le formulaire ici

        template_folder='site/admin',
        template_names={
            'list': 'list_items_forms',
            #'list': 'depense_manager/list_depense',
            'add_or_modify': 'template_forms',
            'delete': 'delete_forms'
        },
        success_url="Bapp:list_occasionalcontribution",
        default_ordering='-date_event',
    )

    def dispatch(self, request, *args, **kwargs):
        # On centralise la redirection vers handle_form ou handle_list
        action = kwargs.get('action')
        item_id = kwargs.get('item_id')

        if action in ['edit', 'add']:
            return self.crud_manager.handle_form(request, item_id)
        elif action == 'delete':
            return self.crud_manager.handle_delete(request, item_id)

        return self.crud_manager.handle_list(request)


class AmountContributionYearManager(View):
    crud_manager = ModelCRUDManager(
        model=AmountContributionYear,
        form_class=AmountContributionYearForm,  # Définir le formulaire ici

        template_folder='site/admin',
        template_names={
            'list': 'list_items_forms',
            #'list': 'depense_manager/list_depense',
            'add_or_modify': 'template_forms',
            'delete': 'delete_forms'
        },
        success_url="Bapp:list_amountcontributionyear",
        default_ordering='-year',
    )

    def dispatch(self, request, *args, **kwargs):
        # On centralise la redirection vers handle_form ou handle_list
        action = kwargs.get('action')
        item_id = kwargs.get('item_id')

        if action in ['edit', 'add']:
            return self.crud_manager.handle_form(request, item_id)
        elif action == 'delete':
            return self.crud_manager.handle_delete(request, item_id)

        return self.crud_manager.handle_list(request)


class EditorialCommunityManager(View):
    crud_manager = ModelCRUDManager(
        model=EditorialCommunity,
        form_class=EditorialCommunityForm,  # Définir le formulaire ici

        template_folder='site/admin',
        template_names={
            'list': 'gestion_articles/article_list',
            # 'list': 'depense_manager/list_depense',
            'add_or_modify': 'template_forms',
            'delete': 'delete_forms'
        },
        success_url="Bapp:list_editorialcommunity",
        default_ordering='-updated_at',
    )

    def dispatch(self, request, *args, **kwargs):
        # On centralise la redirection vers handle_form ou handle_list
        action = kwargs.get('action')
        item_id = kwargs.get('item_id')

        if action in ['edit', 'add']:
            return self.crud_manager.handle_form(request, item_id)
        elif action == 'delete':
            return self.crud_manager.handle_delete(request, item_id)

        return self.crud_manager.handle_list(request)
