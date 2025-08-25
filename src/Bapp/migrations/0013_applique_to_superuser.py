# votre_app/migrations/XXXX_data_migration.py

from django.db import migrations


def ajouter_superuser_par_defaut(apps, schema_editor):
    # Récupérer les modèles
    ParticipationAnnual = apps.get_model('Bapp', 'ParticipationAnnual')
    ParticipationOccasionnelle = apps.get_model('Bapp', 'ParticipationOccasionnelle')
    Dons = apps.get_model('Bapp', 'Dons')
    CustomUser = apps.get_model('Bapp', 'BtestCustomUser')

    # Récupérer le premier superuser
    superuser = CustomUser.objects.filter(is_superuser=True).first()

    if superuser:
        # Mettre à jour tous les enregistrements où created_by est null
        ParticipationAnnual.objects.filter(created_by__isnull=True).update(created_by=superuser)
        ParticipationOccasionnelle.objects.filter(created_by__isnull=True).update(created_by=superuser)
        Dons.objects.filter(created_by__isnull=True).update(created_by=superuser)


def reverse_migration(apps, schema_editor):
    # Code pour annuler la migration si nécessaire
    ParticipationAnnual = apps.get_model('Bapp', 'ParticipationAnnual')
    ParticipationOccasionnelle = apps.get_model('Bapp', 'ParticipationOccasionnelle')
    Dons = apps.get_model('Bapp', 'Dons')

    ParticipationOccasionnelle.objects.all().update(created_by=None)
    ParticipationAnnual.objects.all().update(created_by=None)
    Dons.objects.all().update(created_by=None)



class Migration(migrations.Migration):
    dependencies = [
        ('Bapp', '0012_dons_created_by_participationannual_created_by_and_more'),  # Remplacez par le nom de votre dernière migration
    ]

    operations = [
        migrations.RunPython(ajouter_superuser_par_defaut, reverse_migration),
    ]