import json
import re
import subprocess
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen

import requests
from django.contrib import messages

from django.utils import timezone
import time
from django.core.mail import send_mail
from os import getenv

from BTest import settings

from twilio.rest import Client

from .models import TwoFactorAuth

def send_2fa_code_email(user, code):
    subject = "Votre code de connexion (2FA)"
    message = f"Bonjour {getattr(user, 'prenoms', '') or ''},\n\nVotre code de vérification est: {code}\n  Il expire dans 5 minutes."
    recipient = [user.email]
    send_mail(subject, message, settings.EMAIL_HOST_USER, recipient, fail_silently=False)

def send_2fa_code_whatsapp(user, code):
    # Nécessite: pip install twilio et variables d'environnement
    # TWILIO_ACCOUNT_SID, TWILIO_AUTH_TOKEN, TWILIO_WHATSAPP_FROM='whatsapp:+14155238886'

    account_sid = getenv("TWILIO_ACCOUNT_SID")
    auth_token = getenv("TWILIO_AUTH_TOKEN")
    from_whatsapp = getenv("TWILIO_WHATSAPP_FROM")  # ex: 'whatsapp:+14155238886'
    to_whatsapp = f"whatsapp:{user.telephone}"   # Assurez-vous que le numéro est au format E.164

    client = Client(account_sid, auth_token)
    client.messages.create(
        from_=from_whatsapp,
        to=to_whatsapp,
        body=f"Votre code de vérification est {code}. Il expire dans 5 minutes."
    )


# Utilitaires Telegram

def _get_telegram_api_base() -> str:
    bot_token = getattr(settings, "TELEGRAM_BOT_TOKEN", None)
    if not bot_token:
        raise ValueError("TELEGRAM_BOT_TOKEN n'est pas défini dans settings.")
    return f"https://api.telegram.org/bot{bot_token}"


def get_or_create_2fa(user, channel='email'):
    """
    Prépare/retourne un token 2FA et l'envoie selon le canal:
    - email: envoi du code par mail
    - telegram: envoi du code par bot Telegram (DM)
    Hypothèses:
      - TwoFactorAuth.create_token(user, channel, ttl_minutes) existe et retourne un objet avec token_code
      - user.telegram_chat_id contient l'ID Telegram si le compte est lié (via /start)
      - send_2fa_code_email(user, message) existe pour l'envoi email
    """
    print('Dans la fonction get_or_create_2fa :')
    now = timezone.now()
    print('now : ', now)

    existing_code = TwoFactorAuth.objects.filter(user=user).first()
    print('Le code existe. ', existing_code)
    if existing_code:
        # 1) S'il est encore valide (ex: propriété .token_expired)
        if not existing_code.token_expired:
            return existing_code

        # 3) Sinon → on supprime l'ancien et on génère un nouveau
        existing_code.delete()

    print("'Le code n'existe pas d'abord'")

    try:
        if channel == "telegram":
            # Vérifier que l'utilisateur a bien lié son compte Telegram
            chat_id = getattr(user, "telegram_chat_id", None)
            if not chat_id:
                # Donnez une erreur claire au flux appelant (qui réaffichera le lien /start)
                raise Exception("Votre compte Telegram n'est pas encore lié. Démarrez le bot et réessayez.")

            # Durée de vie (ex: 30 jours si vous voulez un code longue durée; ajustez selon votre sécurité)
            time_to_live = 43200  # minutes (30 jours)
            token = TwoFactorAuth.create_token(user=user, channel=channel, ttl_minutes=time_to_live)
            print("'l'utilisateur a Telegram comme option")
            message = f"Votre code 2FA est: {token.token_code}\nNe le partagez jamais."

            # Import local pour éviter l'import circulaire
            from .otp_telegram import send_telegram_message

            send_telegram_message(chat_id, message)

        else:
            # Duree de vie plus courte pour email
            time_to_live = 3  # minutes
            token = TwoFactorAuth.create_token(user=user, channel=channel, ttl_minutes=time_to_live)
            print("L'utilisateur a email comme option")
            message = f"Votre code 2FA est: {token.token_code}"
            send_2fa_code_email(user, message)

        print("Nouveau token créé", token.token_code)
        return token

    except Exception as e:
        print(e)
        return e


