from django.contrib.messages import success
from django.forms import modelform_factory
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger
from django.contrib.auth.decorators import login_required
from django.utils.decorators import method_decorator
from django.views import View

from Bapp.forms import ParticipationAnnuelForm, ParticipationOccasionnelleForm, DonsForm, AddDepensesForm
from Bapp.models import ParticipationAnnual, ParticipationOccasionnelle, Dons, AddDepenses
from Bapp.permissions import has_secretor_role


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
                 ):
        self.model = model
        self.template_folder = template_folder
        self.items_per_page = items_per_page
        self.form_class = form_class
        self.success_url = success_url or 'Bapp:index'  # URL par défaut
        self.default_context_keys = {
            'form': 'form',
            'item': 'item',
            'items': 'items',
            'page_obj': 'page_obj',
            'model_name': 'model_name'

        }
        self.default_ordering = default_ordering or ('-date_participation',)
        self.template_names = template_names or {
            'list': 'list',
            'edit': 'edit',
            'delete': 'delete'
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
                items = self.model.objects.filter(created_by=request.user)

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

            context = {self.default_context_keys['page_obj']: page_obj,}

            return render(request, self.get_template_path('list'), context)

        except Exception as e:
            messages.error(request, f"Une erreur s'est produite : {str(e)}")
            return redirect('Bapp:dashboard2')

    def handle_edit(self, request, item_id, view_instance=None):
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

            return render(request, self.get_template_path('edit'), context)

        except Exception as e:
            messages.error(request, f"Une erreur s'est produite : {str(e)}")
            return redirect('Bapp:dashboard2')

    def handle_delete(self, request, item_id):
        """Gestion de la suppression d'un élément"""
        try:
            item = get_object_or_404(self.model, id=item_id)

            # Vérification des permissions
            if not (request.user.is_superuser or item.created_by == request.user):
                messages.error(request, "Vous n'avez pas la permission de supprimer cet élément.")
                return redirect('Bapp:manager_login_page')

            if request.method == 'POST':
                item.delete()
                messages.success(request, f"{self.model._meta.verbose_name} supprimé avec succès.")
                return redirect(self.success_url)

            context = {
                self.default_context_keys['items']: item,
                self.default_context_keys['model_name']: self.model._meta.verbose_name
            }

            return render(request, self.get_template_path('delete'), context)

        except Exception as e:
            messages.error(request, f"Une erreur s'est produite : {str(e)}")
            return redirect('Bapp:dashboard2')

class ParticipationAnnuelManager(View):
    crud_manager = ModelCRUDManager(
        model=ParticipationAnnual,
        form_class=ParticipationAnnuelForm,  # Définir le formulaire ici

        template_folder='site/admin/cotisation_annuel_manager',
        context_mapping={
            'form': 'form',
            'item': 'item',
            'items': 'cotisation',
            'page_obj': 'page_obj',
            'model_name': 'model_name',
        },
        template_names={
            'list': 'cotisation_annuel_list',
            'edit': 'modify_cotisation_annuel',
            'delete': 'delete_cotisation_annuel'
        },
        success_url="Bapp:list_participations_annuelles",
        default_ordering='-updated_at',
    )

    #Pour les methodes de types GET
    @method_decorator(has_secretor_role(['ADMIN', 'SECRETOR']))
    def get(self, request, item_id=None, action=None):
        try:
            if action == 'edit':
                return self.crud_manager.handle_edit(request, item_id)
            elif action == 'delete':
                return self.crud_manager.handle_delete(request, item_id)
            #messages.warning(request, "Action non reconnue")
            return self.crud_manager.handle_list(request)
        except Exception as e:
            messages.error(request, f"Une erreur s'est produite : {str(e)}")
        return self.crud_manager.handle_list(request)

    # Pour les methodes de type POST
    @method_decorator(has_secretor_role(['ADMIN', 'SECRETOR']))
    def post(self, request, item_id=None, action=None):
        try:
            if action == 'edit':
                return self.crud_manager.handle_edit(request, item_id)
            elif action == 'delete':
                return self.crud_manager.handle_delete(request, item_id)
            #messages.warning(request, "Action non reconnue")
            return self.crud_manager.handle_list(request)
        except Exception as e:
            messages.error(request, f"Une erreur s'est produite : {str(e)}")
        return self.crud_manager.handle_list(request)
'''Cotisation occasionnelle'''
class ParticipationOcasionnelleManager(View):
    crud_manager = ModelCRUDManager(
        model=ParticipationOccasionnelle,
        form_class=ParticipationOccasionnelleForm,  # Définir le formulaire ici

        template_folder='site/admin/cotisation_occasionnel_manager',
        context_mapping={
            'form': 'form',
            'item': 'item',
            'items': 'cotisation',
            'page_obj': 'page_obj',
            'model_name': 'model_name',
        },
        template_names={
            'list': 'cotisation_occasionnel_list',
            'edit': 'modify_cotisation_occasionnel',
            'delete': 'delete_cotisation_occasionnel'
        },
        success_url="Bapp:list_participations_occasionnelles",
        default_ordering='-updated_at',
    )

    #Pour les methodes de types GET
    @method_decorator(has_secretor_role(['ADMIN', 'SECRETOR']))
    def get(self, request, item_id=None, action=None):
        try:
            if action == 'edit':
                return self.crud_manager.handle_edit(request, item_id)
            elif action == 'delete':
                return self.crud_manager.handle_delete(request, item_id)
            #messages.warning(request, "Action non reconnue")
            return self.crud_manager.handle_list(request)
        except Exception as e:
            messages.error(request, f"Une erreur s'est produite : {str(e)}")
        return self.crud_manager.handle_list(request)

    # Pour les methodes de type POST
    @method_decorator(has_secretor_role(['ADMIN', 'SECRETOR']))
    def post(self, request, item_id=None, action=None):
        try:
            if action == 'edit':
                return self.crud_manager.handle_edit(request, item_id)
            elif action == 'delete':
                return self.crud_manager.handle_delete(request, item_id)
            #messages.warning(request, "Action non reconnue")
            return self.crud_manager.handle_list(request)
        except Exception as e:
            messages.error(request, f"Une erreur s'est produite : {str(e)}")
        return self.crud_manager.handle_list(request)

'''Dons manger'''


class DonsManager(View):
    crud_manager = ModelCRUDManager(
        model=Dons,
        form_class=DonsForm,  # Définir le formulaire ici

        template_folder='site/admin/dons_manager',
        context_mapping={
            'form': 'form',
            'item': 'item',
            'items': 'dons',
            'page_obj': 'page_obj',
            'model_name': 'model_name',
        },
        template_names={
            'list': 'dons_list',
            'edit': 'modify_dons',
            'delete': 'delete_dons'
        },
        success_url="Bapp:list_dons",
        default_ordering='-updated_at',
    )

    #Pour les methodes de types GET
    @method_decorator(has_secretor_role(['ADMIN', 'SECRETOR']))
    def get(self, request, item_id=None, action=None):
        try:
            if action == 'edit':
                return self.crud_manager.handle_edit(request, item_id)
            elif action == 'delete':
                return self.crud_manager.handle_delete(request, item_id)
            #messages.warning(request, "Action non reconnue")
            return self.crud_manager.handle_list(request)
        except Exception as e:
            messages.error(request, f"Une erreur s'est produite : {str(e)}")
        return self.crud_manager.handle_list(request)

    # Pour les methodes de type POST
    @method_decorator(has_secretor_role(['ADMIN', 'SECRETOR']))
    def post(self, request, item_id=None, action=None):
        try:
            if action == 'edit':
                return self.crud_manager.handle_edit(request, item_id)
            elif action == 'delete':
                return self.crud_manager.handle_delete(request, item_id)
            #messages.warning(request, "Action non reconnue")
            return self.crud_manager.handle_list(request)
        except Exception as e:
            messages.error(request, f"Une erreur s'est produite : {str(e)}")
        return self.crud_manager.handle_list(request)


#Depenses manager


class DepensesManager(View):
    crud_manager = ModelCRUDManager(
        model=AddDepenses,
        form_class=AddDepensesForm,  # Définir le formulaire ici

        template_folder='site/admin/depense_manager',
        context_mapping={
            'form': 'form',
            'item': 'item',
            'items': 'depense',
            'page_obj': 'page_obj',
            'model_name': 'model_name',
        },
        template_names={
            'list': 'list_depense',
            'edit': 'modify_depense',
            'delete': 'delete_depense'
        },
        success_url="Bapp:list_depenses",
        default_ordering='-updated_at',
    )

    #Pour les methodes de types GET
    @method_decorator(has_secretor_role(['ADMIN', 'SECOND_SECRETOR', "MODERATOR"]))
    def get(self, request, item_id=None, action=None):
        try:
            if action == 'edit':
                return self.crud_manager.handle_edit(request, item_id)
            elif action == 'delete':
                return self.crud_manager.handle_delete(request, item_id)
            #messages.warning(request, "Action non reconnue")
            return self.crud_manager.handle_list(request)
        except Exception as e:
            messages.error(request, f"Une erreur s'est produite : {str(e)}")
        return self.crud_manager.handle_list(request)

    # Pour les methodes de type POST
    @method_decorator(has_secretor_role(['ADMIN', 'SECOND_SECRETOR', "MODERATOR"]))
    def post(self, request, item_id=None, action=None):
        try:
            if action == 'edit':
                return self.crud_manager.handle_edit(request, item_id)
            elif action == 'delete':
                return self.crud_manager.handle_delete(request, item_id)
            #messages.warning(request, "Action non reconnue")
            return self.crud_manager.handle_list(request)
        except Exception as e:
            messages.error(request, f"Une erreur s'est produite : {str(e)}")
        return self.crud_manager.handle_list(request)



