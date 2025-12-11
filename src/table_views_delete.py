import os
import sys
import django
from django.db import connection


def fix_database_views():
    """
    Supprime les vues qui bloquent les migrations Django.
    Cela est nécessaire car PostgreSQL empêche la modification des colonnes
    (ex: prenoms) utilisées par des vues existantes.
    """
    # Configuration de l'environnement Django
    # On suppose que ce script est lancé depuis le dossier src/
    current_dir = os.path.dirname(os.path.abspath(__file__))
    sys.path.append(current_dir)

    os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'BTest.settings')
    django.setup()

    # Liste des vues susceptibles de bloquer la migration.
    # On inclut celle de l'erreur et les autres qui dépendent probablement de 'prenoms'
    views_to_drop = [
        "cotisation_occasionnelle_view",
        "cotisation_annuelle_view",
        "missideh_bourou_members_view",
        "status_member_annual_participation",
        "dons_view",
        "depenses_view",
        "totaux_view",
        "annonces_members_view",
        "bourou_users_list",
        "liste_depense_view",
        "liste_don_view",
        "liste_participation_annuel_view",
        "liste_participation_occasionnelle_view",
        "liste_publication_view",
        "view_bilan_totaux",
        "view_totale_restante"
    ]

    print(f"--- Connexion à la base de données via Django ---")

    with connection.cursor() as cursor:
        print("--- Début du nettoyage des vues ---")
        for view_name in views_to_drop:
            try:
                print(f"Tentative de suppression de la vue : {view_name}")
                # CASCADE est crucial ici pour supprimer les règles associées
                cursor.execute(f"DROP VIEW IF EXISTS {view_name} CASCADE")
                print(f"✅ Vue '{view_name}' supprimée (ou n'existait pas).")
            except Exception as e:
                print(f"❌ Erreur lors de la suppression de '{view_name}' : {e}")

        print("--- Nettoyage terminé ---")
        print("Vous pouvez maintenant relancer la commande : python manage.py migrate")


if __name__ == "__main__":
    fix_database_views()