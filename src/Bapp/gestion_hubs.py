# ... existing code ...
from datetime import date

from django.db.models import Sum, F
from django.shortcuts import render
from django.urls import reverse
from django.views import View

from Bapp.models import EvenementOccasionnelle, CotisationOccasionnelle, AmountContributionYear, ParticipationAnnual, \
    BtestCustomUser, Dons, AddDepenses


class BaseHubView(View):
    """Classe de base pour générer n'importe quel Hub (Annuel, Occasionnel, etc.)"""
    template_name = "site/client/template_generic_hub.html"
    title = ""
    subtitle = ""
    icon_class = "fa-hubspot"

    # Configuration du modèle pivot (ex: AmountContributionYear ou EvenementOccasionnelle)
    pivot_model = None
    contribution_model = None
    pivot_filter_field = ""  # Le champ dans le modèle contribution qui pointe vers le pivot

    # Configuration des colonnes des cartes
    item_columns = []

    def get_pivot_queryset(self):
        return self.pivot_model.objects.all().order_by('-id')

    def get_item_data(self, pivot_obj, total_members):
        """Méthode à surcharger pour personnaliser les calculs par carte"""
        raise NotImplementedError("Vous devez implémenter get_item_data")

    def get_top_stats(self, items, total_members):
        """Méthode à surcharger pour les stats globales du haut"""
        return []

    def get(self, request, *args, **kwargs):
        total_members = BtestCustomUser.objects.count()
        pivot_qs = self.get_pivot_queryset()

        items = []
        for pivot_obj in pivot_qs:
            item_data = self.get_item_data(pivot_obj, total_members)
            items.append(item_data)

        context = {
            'title': self.title,
            'subtitle': self.subtitle,
            'icon_class': f"fa-solid {self.icon_class}",
            'items': items,
            'top_stats': self.get_top_stats(items, total_members),
            'item_columns': self.item_columns,
        }
        return render(request, self.template_name, context)


# --- IMPLÉMENTATION : HUB ANNUEL ---
class AnnualHubView(BaseHubView):
    pivot_model = AmountContributionYear
    contribution_model = ParticipationAnnual
    title = "Hub des Contributions Annuelles"
    subtitle = "Suivi de la participation membre par année"
    icon_class = "fa-calendar-check"
    item_columns = [
        ("Collecté", "montant_collecte", "fa-sack-dollar"),
        ("Contributeurs", "contributeurs", "fa-users"),
        ("Taux", "taux", "fa-chart-pie"),
    ]

    def get_item_data(self, pivot_obj, total_members):
        # On extrait l'année numérique pour être sûr de la comparaison
        target_year = pivot_obj.year

        # On filtre par la valeur de l'année liée à la FK pour plus de sûreté
        contributions = self.contribution_model.objects.filter(year__year=target_year)
        total_year = contributions.aggregate(Sum('montant_participation'))['montant_participation__sum'] or 0
        count = contributions.values('participant').distinct().count()
        print('Les participants sont: ', count)
        return {
            'display_title': f"Exercice {pivot_obj.year}",
            'description': f"Cotisation fixée à {pivot_obj.amount_to_paid_pro_year} FGN.",
            'badge_text': "Actuel" if pivot_obj.year == date.today().year else "Archive",
            'montant_collecte': total_year,
            'contributeurs': count,
            'taux': f"{(count / total_members * 100):.1f}%" if total_members > 0 else "0%",
            'detail_url': reverse('Bapp:cotisation_annuelles_view') + f"?year={pivot_obj.year}"
        }

    def get_top_stats(self, items, total_members):
        total_global = sum(item['montant_collecte'] for item in items)
        return [
            {'label': 'Total Caisse', 'value': total_global, 'is_currency': True},
            {'label': 'Membres', 'value': total_members, 'is_currency': False},
        ]


# --- IMPLÉMENTATION : HUB OCCASIONNEL ---
class OccasionalHubView(BaseHubView):
    pivot_model = EvenementOccasionnelle
    contribution_model = CotisationOccasionnelle
    title = "Cotisations évenementielles "
    subtitle = "Listes des participations par événements de Missideh Bourou"
    icon_class = "fa-hand-holding-heart"
    item_columns = [
        ("Collecté", "montant_collecte", "fa-coins"),
        ("Contributeurs", "participants", "fa-users-line"),
        ("Date", "date", "fa-calendar-day"),
    ]

    def get_item_data(self, pivot_obj, total_members):
        contributions = self.contribution_model.objects.filter(event_name=pivot_obj)
        total_event = contributions.aggregate(Sum('montant_cotisation'))['montant_cotisation__sum'] or 0
        count = contributions.values('member').distinct().count()

        return {
            'display_title': pivot_obj.event_name,
            'description': pivot_obj.event_description,
            'badge_text': "Événement",
            'montant_collecte': total_event,
            'participants': count,
            'date': pivot_obj.date_event.strftime('%d/%m/%Y'),
            'detail_url': reverse('Bapp:cotisation_occasionnelle_view') + f"?event_id={pivot_obj.id}"
        }

    def get_top_stats(self, items, total_members):
        return [
            {'label': 'Total Collecté', 'value': sum(i['montant_collecte'] for i in items), 'is_currency': True},
            {'label': 'Événements', 'value': len(items), 'is_currency': False},
        ]


class DonsHubView(BaseHubView):
    pivot_model = AmountContributionYear
    contribution_model = Dons
    title = "Dons extérieurs reçus"
    subtitle = "Statistiques des dons reçus par Missideh Bourou par exercice"
    icon_class = "fa-gift"
    item_columns = [
        ("Total Dons", "montant_collecte", "fa-sack-dollar"),
        ("Nombre de Dons", "contributeurs", "fa-hand-holding-heart"),
    ]

    def get_item_data(self, pivot_obj, total_members):
        # Correction : Filtrer les dons dont l'année de 'date_don' correspond à pivot_obj.year
        contributions = self.contribution_model.objects.filter(date_don__year=pivot_obj.year)

        # Correction : Utiliser les bons noms de champs (montant_don au lieu de montant_participation)
        total_year = contributions.aggregate(Sum('montant_don'))['montant_don__sum'] or 0
        count = contributions.count()

        return {
            'display_title': f"Dons {pivot_obj.year}",
            'description': f"Récapitulatif des générosités de l'année {pivot_obj.year}.",
            'badge_text': "Année en cours" if pivot_obj.year == date.today().year else "Archive",
            'montant_collecte': total_year,
            'contributeurs': count,
            'detail_url': reverse('Bapp:dons_view') + f"?year={pivot_obj.year}"
        }

    def get_top_stats(self, items, total_members):
        total_global = sum(item['montant_collecte'] for item in items)
        total_dons = sum(item['contributeurs'] for item in items)
        return [
            {'label': 'Cumul des Dons', 'value': total_global, 'is_currency': True},
            {'label': 'Total de Dons reçus', 'value': total_dons, 'is_currency': False},
        ]


class DepensesHubView(BaseHubView):
    pivot_model = AmountContributionYear
    contribution_model = AddDepenses
    title = "Dépenses par an effectuées par Missideh Bourou"
    subtitle = "Listes des montants et motifs de dépenses"
    icon_class = "fa-gift"
    item_columns = [
        ("TTL", "montant_collecte", "fa-sack-dollar"),
        ("Dépenses", "contributeurs", "fa-hand-holding-heart"),
    ]

    def get_item_data(self, pivot_obj, total_members):

        try:
            target_year = int(str(pivot_obj.year))
        except (ValueError, TypeError):
            target_year = 0

        # On filtre le DateTimeField par l'année extraite
        contributions = self.contribution_model.objects.filter(
            date_depense__year=target_year
        )
        print(type(target_year))
        contributions = self.contribution_model.objects.filter(date_depense__year=target_year)
        # Correction du champ de somme : montant_depense
        total_year = contributions.aggregate(Sum('montant_depense'))['montant_depense__sum'] or 0

        count = contributions.count()
        print(count)

        return {
            'display_title': f"Dépenses {pivot_obj.year}",
            'description': f"Récapitulatif des dépenses pour l'année {pivot_obj.year}.",
            'badge_text': "Année en cours" if pivot_obj.year == date.today().year else "Archive",
            'montant_collecte': total_year,
            'contributeurs': count,
            'detail_url': reverse('Bapp:depenses_view') + f"?year={pivot_obj.year}"
        }

    def get_top_stats(self, items, total_members):
        total_global = sum(item['montant_collecte'] for item in items)
        total_dons = sum(item['contributeurs'] for item in items)
        return [
            {'label': 'Cumul des Dépenses', 'value': total_global, 'is_currency': True},
            {'label': 'Total de Dépenses effectuées', 'value': total_dons, 'is_currency': False},
        ]