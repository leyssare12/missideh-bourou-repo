from django import template

register = template.Library()

@register.filter
def get_item(dictionary, key):
    """Accéder à une clé dynamique dans un dict (ex: m.statut_par_annee|get_item:y)."""
    if not dictionary:
        return None
    return dictionary.get(str(key))
