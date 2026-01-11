from django import template

register = template.Library()


@register.filter
def get_item(obj, key):
    """
    Filtre polyvalent pour accéder dynamiquement à une donnée.
    - Si 'obj' est un dictionnaire, utilise .get(key)
    - Si 'obj' est une instance de modèle, utilise getattr(obj, key)
    """
    if not obj:
        return ""

    # Cas d'un dictionnaire (ex: statut_par_annee)
    if isinstance(obj, dict):
        return obj.get(str(key), "")

    # Cas d'un objet / instance de modèle (ex: item.prenom)
    try:
        return getattr(obj, str(key), "")
    except (AttributeError, TypeError):
        return ""


@register.filter
def multiply(value, arg):
    """Multiplie la valeur par l'argument"""
    try:
        return float(value) * float(arg)
    except (ValueError, TypeError):
        return 0