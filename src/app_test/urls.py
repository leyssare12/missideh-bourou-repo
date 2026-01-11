from django.urls import path
from .views import creer_evenement, creer_cotisation, configurer_montant_annuel, enregistrer_participation_annuelle

app_name = 'app_test'
urlpatterns = [
    path('evenement/', creer_evenement, name='creer_evenement'),
    path('cotisation/', creer_cotisation, name='creer_cotisation'),
    path('config-annuelle/', configurer_montant_annuel, name='configurer_montant_annuel'),
    path('participation-annuelle/', enregistrer_participation_annuelle,
         name='enregistrer_participation_annuelle'),
]