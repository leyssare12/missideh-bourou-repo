import requests
from django.contrib import messages

from django.utils import timezone
from datetime import timedelta

from django.core.mail import send_mail
from os import getenv

from BTest import settings

from twilio.rest import Client

from Bapp.models import TwoFactorAuth

TELEGRAM_TOKEN = "7954170802:AAHh-TBDEKagGbxZLd_1sjyr93Sn9d8EW3M"
TELEGRAM_API = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}"

def send_telegram_message(chat_id, text):
    url = f"{TELEGRAM_API}/sendMessage"
    data = {"chat_id": chat_id, "text": text}
    requests.post(url, data=data)




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


def get_or_create_2fa(user, channel='email'):
    print('Dans la fonction get_or_create_2fa :')
    now = timezone.now()
    print('now : ', now)
    existing_code =  TwoFactorAuth.objects.filter(user=user).first()
    print('Le code existe. ', existing_code)
    if existing_code:
        # 1️⃣ S'il est encore valide (24h)
        if not existing_code.token_expired:
            return existing_code

        # 2️⃣ S'il est expiré mais généré il y a < 5 min → refus
        #if (now - existing_code.created_at) < timedelta(minutes=5):
        #    raise Exception("Veuillez attendre 5 minutes avant de redemander un nouveau code.")

        # 3️⃣ Sinon → on supprime l'ancien et on génère un nouveau
        existing_code.delete()
    print("'Le code n'existe pas d'abord'")
    # Nouveau code
    try:
        if channel == "telegram":
            # Duré de vie de code  d'un mois pour les utilisateurs whatsapp
            time_to_live = 43200
            token = TwoFactorAuth.create_token(user=user, channel=channel, ttl_minutes=time_to_live)
            print("'l'utilisateur a Telegram comme option")
            send_telegram_message(user, token.token_code)
        else:
            #Durer de vie de code de 5mn pour les utilisateurs ayant des emails verifiés
            time_to_live = 3
            token = TwoFactorAuth.create_token(user=user, channel=channel, ttl_minutes=time_to_live)
            print("L'utilisateur a email comme option")
            message = f"Votre code est : {token.token_code}"
            send_2fa_code_email(user, message)
        print("Nouvelle token crée", token.token_code)
        return token
    except Exception as e:
        print(e)
        return e


