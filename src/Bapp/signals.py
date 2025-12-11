# myapp/signals.py
from os import getenv

import requests
from django.contrib.auth.signals import user_logged_in
from django.dispatch import receiver
from django.utils.timezone import now

from BTest import settings

TELEGRAM_URL = settings.TELEGRAM_API_URL_2
TELEGRAM_CHAT_ID = settings.TELEGRAM_CHAT_ID_2

@receiver(user_logged_in)
def notify_login(sender, request, user, **kwargs):
    # Exemple : créer une notification
    print(f"{user.prenoms} s'est connecté à {now()} depuis {get_client_ip(request)}")
    ip = get_client_ip(request)
    message = f"🔔 <b>Nouvelle connexion</b>\nsur Missidhe-bourou\n👤 Utilisateur : {user.prenoms}\n🌐 IP : {ip}\n⏰ {now().strftime('%d-%m-%Y %H:%M:%S')}"
    send_telegram_message(message)

def get_client_ip(request):
    x_forwarded_for = request.META.get("HTTP_X_FORWARDED_FOR")
    if x_forwarded_for:
        return x_forwarded_for.split(",")[0]
    return request.META.get("REMOTE_ADDR")
def send_telegram_message(message):
    url = f"{TELEGRAM_URL}/sendMessage"
    payload = {"chat_id": TELEGRAM_CHAT_ID, "text": message, 'parse_mode': 'HTML', 'disable_web_page_preview': True, 'disable_notification': False}
    try:
        print('Le chat_id: ', TELEGRAM_CHAT_ID)
        print('On essaie d envoyer le message! avec l url: ', url)
        requests.post(url, json=payload, timeout=30)
    except requests.exceptions.RequestException as e:
        print(f"Erreur lors de l'envoi du message Telegram: {e}")