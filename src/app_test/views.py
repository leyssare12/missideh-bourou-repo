from django.contrib import messages
from django.db import transaction, IntegrityError
from django.shortcuts import render, redirect

from Bapp.forms import EvenementOccasionnelleForm, CotisationOccasionnelleForm, AmountContributionYearForm, \
    UserSearchForm, ParticipationAnnuelForm
from Bapp.models import CotisationOccasionnelle, AmountContributionYear, BtestCustomUser, ParticipationAnnual


# Create your views here.

def creer_evenement(request):
    if request.method == 'POST':
        form = EvenementOccasionnelleForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, "L'événement a été créé avec succès !")
            return redirect('app_test:creer_cotisation')
    else:
        form = EvenementOccasionnelleForm()

    return render(request, 'template_harmoniser.html', {'form': form, 'title': "Créer un Événement"})


def creer_cotisation(request):
    if not request.user.is_authenticated:
        return redirect('Bapp:manager_login_page')
    if request.method == 'POST':
        form = CotisationOccasionnelleForm(request.POST)
        if form.is_valid():
            cotisation = form.save(commit=False)
            cotisation.created_by_id = request.user
            cotisation.save()
            messages.success(request, "La cotisation a été enregistrée !")
            return redirect('app_test:creer_cotisation')
    else:
        form = CotisationOccasionnelleForm()

    # Récupérer les dernières cotisations pour les afficher
    cotisations = CotisationOccasionnelle.objects.all().order_by('-date_cotisation')[:5]
    for c in cotisations:
        print(c.member_id)
        print(c.event_name_id)
        print(c.montant_cotisation)
    return render(request, 'template_harmoniser.html', {
        'form': form,
        'cotisations': cotisations,
        'title': "Enregistrer une Cotisation"
    })


def configurer_montant_annuel(request):
    """Définit le montant à payer pour une année donnée (ex: 2024 -> 5000 FGN)"""
    if request.method == 'POST':
        form = AmountContributionYearForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, "Le montant annuel a été configuré !")
            return redirect('app_test:configurer_montant_annuel')
    else:
        form = AmountContributionYearForm()

    configurations = AmountContributionYear.objects.all().order_by('-year')
    return render(request, 'template_harmoniser.html', {
        'form': form,
        'configurations': configurations,
        'title': "Configuration des Montants Annuels"
    })


def enregistrer_participation_annuelle(request):
    """Enregistre le paiement d'un membre avec tous les champs du modèle"""
    if not request.user.is_authenticated:
        return redirect('Bapp:manager_login_page')
    membres = BtestCustomUser.objects.filter(is_active=True).order_by('prenoms')

    if request.method == 'POST':
        form = ParticipationAnnuelForm(request.POST)
        user_id = request.POST.get('user_id')

        if form.is_valid():
            if not user_id:
                messages.error(request, "Veuillez sélectionner un membre.")
            else:
                try:
                    with transaction.atomic():
                        # 1. Récupérer le membre
                        member = BtestCustomUser.objects.get(id=int(user_id))

                        # 2. Préparer l'objet sans sauvegarder
                        participation = form.save(commit=False)

                        # 3. Injecter les données manquantes
                        participation.participant_id = member
                        participation.created_by = request.user

                        # 4. Sauvegarde finale
                        participation.save()

                        messages.success(request,
                                         f"Succès ! Cotisation de {participation.montant_participation} FGN enregistrée pour {member.prenoms}.")
                        return redirect('app_test:enregistrer_participation_annuelle')
                except BtestCustomUser.DoesNotExist:
                    messages.error(request, "Le membre sélectionné n'existe pas.")
                except IntegrityError:
                    # C'est ici que l'on capture la violation de la contrainte unique_participation_annuel
                    messages.error(request, f"Opération impossible : Ce membre a déjà enregistré sa participation pour l'année {form.cleaned_data['year_id'].year_id}.")
                except Exception as e:
                    messages.error(request, f"Une erreur imprévue est survenue : {str(e)}")

        else:
            messages.error(request, "Le formulaire contient des données invalides.")
    else:
        form = ParticipationAnnuelForm()

    participations = ParticipationAnnual.objects.all().order_by('-date_participation')[:10]
    return render(request, 'template_harmoniser.html', {
        'form': form,
        'membres': membres,
        'participations': participations,
        'title': "Cotisations Annuelles"
    })