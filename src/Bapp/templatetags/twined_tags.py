from django import template
from django.utils import timezone
from datetime import datetime

register = template.Library()


@register.filter
def time_until(date_value):
    """
    Retourne une chaîne formatée du temps restant jusqu'à la date
    Exemple: "2 mois, 3 jours" ou "5 jours, 3 heures"
    """
    if not date_value:
        return ""

    now = timezone.now()
    if isinstance(date_value, datetime):
        difference = date_value - now
    else:
        # Si c'est juste une date, ajouter l'heure
        difference = datetime.combine(date_value, datetime.min.time()) - now.replace(tzinfo=None)

    days = difference.days
    seconds = difference.seconds

    if days < 0:
        return "Date passée"

    # Calculer les mois approximatifs (30 jours)
    months = days // 30
    remaining_days = days % 30

    # Calculer les heures
    hours = seconds // 3600

    # Formatage conditionnel
    if months > 0:
        if remaining_days > 0:
            return f"{months} mois, {remaining_days} jour{'s' if remaining_days > 1 else ''}"
        return f"{months} mois"
    elif days > 7:
        weeks = days // 7
        remaining_days = days % 7
        if remaining_days > 0:
            return f"{weeks} semaine{'s' if weeks > 1 else ''}, {remaining_days} jour{'s' if remaining_days > 1 else ''}"
        return f"{weeks} semaine{'s' if weeks > 1 else ''}"
    elif days > 0:
        if hours > 0:
            return f"{days} jour{'s' if days > 1 else ''}, {hours} heure{'s' if hours > 1 else ''}"
        return f"{days} jour{'s' if days > 1 else ''}"
    elif hours > 0:
        minutes = (seconds % 3600) // 60
        return f"{hours} heure{'s' if hours > 1 else ''}, {minutes} minute{'s' if minutes > 1 else ''}"
    else:
        minutes = seconds // 60
        return f"{minutes} minute{'s' if minutes > 1 else ''}"


@register.filter
def time_since(date_value):
    """
    Pour les dates passées - temps écoulé depuis
    """
    if not date_value:
        return ""

    now = timezone.now()
    if isinstance(date_value, datetime):
        difference = now - date_value
    else:
        difference = now.replace(tzinfo=None) - datetime.combine(date_value, datetime.min.time())

    days = difference.days
    seconds = difference.seconds

    if days < 0:
        return "Date future"

    months = days // 30
    remaining_days = days % 30
    hours = seconds // 3600

    if months > 0:
        if remaining_days > 0:
            return f"il y a {months} mois, {remaining_days} jour{'s' if remaining_days > 1 else ''}"
        return f"il y a {months} mois"
    elif days > 7:
        weeks = days // 7
        return f"il y a {weeks} semaine{'s' if weeks > 1 else ''}"
    elif days > 0:
        return f"il y a {days} jour{'s' if days > 1 else ''}"
    elif hours > 0:
        return f"il y a {hours} heure{'s' if hours > 1 else ''}"
    else:
        minutes = seconds // 60
        return f"il y a {minutes} minute{'s' if minutes > 1 else ''}"


@register.filter
def format_currency(value):
    """
    Formate un nombre décimal en format monétaire
    Exemple: 12900.00 -> 12 900
    Usage: {{ montant|format_currency }}
    """
    if value is None:
        return "0"

    try:
        # Convertir en entier pour enlever les décimales
        amount = int(float(value))

        # Formater avec des espaces comme séparateur de milliers
        return f"{amount:,}".replace(',', ' ')
    except (ValueError, TypeError):
        return value


@register.filter
def split_long_text(value, max_words=10):
    """
    Insère un retour à la ligne après un certain nombre de mots
    pour éviter d'allonger les champs de type texte.
    Usage: {{ description|split_long_text:5 }}
    """
    if not value or not isinstance(value, str):
        return value

    words = value.split()
    if len(words) <= max_words:
        return value

    lines = []
    for i in range(0, len(words), max_words):
        lines.append(" ".join(words[i:i + max_words]))

    return "\n".join(lines)