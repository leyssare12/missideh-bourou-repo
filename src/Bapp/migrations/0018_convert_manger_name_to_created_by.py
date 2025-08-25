from django.db import migrations, models
import django.db.models.deletion



def transfer_manager_to_user(apps, schema_editor):
    # Récupérer les modèles
    AddDepenses = apps.get_model('Bapp', 'AddDepenses')
    BTestCustomUser = apps.get_model('Bapp', 'BTestCustomUser')

    # Pour chaque items
    for items in AddDepenses.objects.all():
        try:
            # Rechercher l'utilisateur correspondant par son nom
            user = BTestCustomUser.objects.filter(prenoms=items.manager_name).first()
            # Assigner l'utilisateur trouvé au nouveau champ
            items.created_by = user
            items.save()
        except BTestCustomUser.DoesNotExist:
            print(f"Attention : Aucun utilisateur trouvé pour manager_name: {items.manager_name}")


def reverse_transfer(apps, schema_editor):
    # Fonction de retour en arrière si nécessaire
    Adddepenses = apps.get_model('Bapp', 'AddDepenses')

    for items in Adddepenses.objects.all():
        if items.created_by:
            items.manager_name = items.created_by.user
            items.save()


class Migration(migrations.Migration):
    dependencies = [
        ('Bapp', '0017_alter_btestcustomuser_email_verification_expiration_and_more'),  # Remplacer par le nom de votre dernière migration
    ]

    operations = [
        # Ajouter la nouvelle colonne created_by
        migrations.AddField(
            model_name='AddDepenses',
            name='created_by',
            field=models.ForeignKey(
                null=True,
                on_delete=django.db.models.deletion.SET_NULL,
                to='Bapp.btestcustomuser',
            ),
        ),
        # Exécuter la fonction de transfert de données
        migrations.RunPython(transfer_manager_to_user, reverse_transfer),
        # Supprimer l'ancienne colonne manager_name
        migrations.RemoveField(
            model_name='AddDepenses',
            name='manager_name',
        ),
    ]
