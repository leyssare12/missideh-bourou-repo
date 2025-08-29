from django.core.management import BaseCommand


import requests
import os

from BTest import settings

# Configuration du destinataire (remplacez par vos valeurs)
CHAT_ID = 1951265242

def _get_telegram_api_base() -> str:
    """
    Construit la base de l'API Telegram à partir de la variable d'environnement TELEGRAM_BOT_TOKEN.
    Cette fonction ne dépend pas de Django et évite les imports des modules de l'app.
    """

    token = getattr(settings, "TELEGRAM_BOT_TOKEN", None)
    if not token or not token.strip():
        raise RuntimeError(
            "TELEGRAM_BOT_TOKEN est manquant. "
            "Définissez la variable d'environnement TELEGRAM_BOT_TOKEN avant d'exécuter ce script."
        )
    return f"https://api.telegram.org/bot{token.strip()}"

def send_telegram_message_direct(chat_id: int | str, text: str):
    """Envoi direct sans dépendre de Django."""
    url = f"{_get_telegram_api_base()}/sendMessage"
    payload = {
        "chat_id": chat_id,
        "text": text,
        "disable_notification": False,
    }
    try:
        resp = requests.post(url, json=payload, timeout=10)
        resp.raise_for_status()
        return resp.json()
    except requests.exceptions.RequestException as e:
        print(f"Erreur lors de l'envoi Telegram: {e}")
        return None

if __name__ == "__main__":
    result = send_telegram_message_direct(CHAT_ID, "Salam à toi")
    print("Résultat:", result)