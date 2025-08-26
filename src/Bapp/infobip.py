import http.client
import json
import os
from pathlib import Path

import requests
from dotenv import load_dotenv
from infobip_api_client.models import SmsRequest, SmsMessage, SmsMessageContent, SmsTextContent, SmsDestination, \
    SmsResponse
from infobip_api_client.api.sms_api import SmsApi
# myapp/services.py
import json
from django.conf import settings

BASE_DIR = Path(__file__).resolve().parent.parent



load_dotenv(BASE_DIR / '.infobipenv')



# Python

import os
import requests
from typing import Optional

# Renseignez vos valeurs ici ou via variables d'environnement (sans espaces ni commentaires à la fin des lignes)
BASE_URL = (os.getenv("INFOBIP_BASE_URL") or "https://1g4lyx.api.infobip.com").strip().rstrip("/")
API_KEY = (os.getenv("INFOBIP_API_KEY") or "App YOUR_API_KEY").strip()
APP_ID = (os.getenv("INFOBIP_2FA_APP_ID") or "YOUR_APP_ID").strip()
SENDER = (os.getenv("INFOBIP_WHATSAPP_SENDER") or "447860099299").strip()
MESSAGE_ID = (os.getenv("INFOBIP_2FA_MESSAGE_ID") or "").strip()  # peut être vide si on va le créer
TO = (os.getenv("INFOBIP_TOP") or "whatsapp:+4915778590981").strip()  # destinataire
DJANGO_APP_OTP = (os.getenv("DJANGO_APP_OTP") or "YOUR_APP_OTP").strip()

print(f"BASE_URL: {BASE_URL}")
print(f"API_KEY: {API_KEY}")
print(f"APP_ID: {APP_ID}")
print(f"SENDER: {SENDER}")
print(f"MESSAGE_ID: {MESSAGE_ID}")
print(f"TO: {TO}")

def send_whatsapp_template():
    conn = http.client.HTTPSConnection('1g4lyx.api.infobip.com')
    payload = json.dumps({
        "messages": [
            {
                "from": SENDER,
                "to": TO,
                "messageId": MESSAGE_ID,
                "content": {
                    "templateName": "test_whatsapp_template_en",
                    "templateData": {
                        "body": {
                            "placeholders": ["test"]
                        }
                    },
                    "language": "en"
                }
            }
        ]
    })
    headers = {
        'Authorization': API_KEY,
        'Content-Type': 'application/json',
        'Accept': 'application/json'
    }
    conn.request("POST", "/whatsapp/1/message/template", payload, headers)
    res = conn.getresponse()
    data = res.read()
    print(data.decode("utf-8"))

def send_sms():
    #On configure l'API client
    from infobip_api_client.api_client import ApiClient, Configuration

    client_config = Configuration(
        host=BASE_URL,
        api_key={"APIKeyHeader": DJANGO_APP_OTP},
        api_key_prefix={"APIKeyHeader": "App"},
    )
    #On initialise l'API client'
    api_client = ApiClient(client_config)

    sms_request = SmsRequest(
        messages=[
            SmsMessage(
                destinations=[
                    SmsDestination(
                        to="4915778590981",
                    ),
                ],
                sender=SENDER,
                content=SmsMessageContent(actual_instance=SmsTextContent(text="This is a dummy SMS message sent using Python library"))
            )
        ]
    )

    api_instance = SmsApi(api_client)

    api_response: SmsResponse = api_instance.send_sms_messages(sms_request=sms_request)
    print(api_response)

if __name__ == "__main__":
    #send_whatsapp_template()
    send_sms()

'''
if not API_KEY.startswith("App "):
    API_KEY = f"App {API_KEY}"

HEADERS = {
    "Authorization": API_KEY,
    "Content-Type": "application/json",
    "Accept": "application/json",
}

def create_2fa_message(
    application_id: str,
    sender_id: str,
    message_text: str = "Votre code de vérification est {{pin}}",
    pin_length: int = 6,
    pin_type: str = "NUMERIC",
    language: str = "fr"
) -> str:
    """
    Crée un template 2FA et retourne son messageId.
    Endpoint: POST /2fa/2/messages
    """
    url = f"{BASE_URL}/2fa/2/messages"
    payload = {
        "applicationId": application_id,
        "messageText": message_text,
        "pinLength": pin_length,
        "pinType": pin_type,
        "language": language,
        "senderId": sender_id
    }
    r = requests.post(url, headers=HEADERS, json=payload, timeout=30)
    print("CREATE MESSAGE ->", r.status_code, r.text)
    r.raise_for_status()
    data = r.json()
    # Selon la réponse, messageId peut se trouver sous data["messageId"]
    return data.get("messageId") or data.get("id") or ""

def send_pin(application_id: str, message_id: str, to: str) -> str:
    """
    Envoie un PIN au destinataire. Retourne le pinId (utile pour renvoyer).
    Endpoint: POST /2fa/2/pin
    """
    url = f"{BASE_URL}/2fa/2/pin"
    payload = {
        "applicationId": application_id,
        "messageId": message_id,
        "to": to
    }
    r = requests.post(url, headers=HEADERS, json=payload, timeout=30)
    print("SEND PIN ->", r.status_code, r.text)
    r.raise_for_status()
    data = r.json()
    # Généralement, pinId est renvoyé
    return data.get("pinId", "")

def verify_pin(pin_id: Optional[str] = None, to: Optional[str] = None, pin: str = "") -> bool:
    """
    Vérifie un PIN.
    Deux façons:
      - via pinId: POST /2fa/2/pin/verify/{pinId}
      - via to:    POST /2fa/2/pin/verify
    """
    if pin_id:
        url = f"{BASE_URL}/2fa/2/pin/verify/{pin_id}"
        payload = {"pin": pin}
    else:
        url = f"{BASE_URL}/2fa/2/pin/verify"
        payload = {"to": to, "pin": pin}

    r = requests.post(url, headers=HEADERS, json=payload, timeout=30)
    print("VERIFY PIN ->", r.status_code, r.text)
    if r.status_code == 200:
        return True
    # Certaines implémentations renvoient 200 pour success, 400 pour WRONG_PIN, etc.
    return False

def resend_pin(pin_id: str) -> None:
    """
    Renvoie le PIN sur le même canal.
    Endpoint: POST /2fa/2/pin/resend/{pinId}
    """
    url = f"{BASE_URL}/2fa/2/pin/resend/{pin_id}"
    r = requests.post(url, headers=HEADERS, timeout=30)
    print("RESEND PIN ->", r.status_code, r.text)
    r.raise_for_status()

if __name__ == "__main__":
    # 1) Si vous n'avez pas encore de template/messageId, créez-le:
    if not MESSAGE_ID:
        print("Création d’un template 2FA...")
        MESSAGE_ID = create_2fa_message(
            application_id=APP_ID,
            sender_id=SENDER,
            message_text="Votre code de vérification est {{pin}}",
            pin_length=6,
            pin_type="NUMERIC",
            language="fr",
        )
        print("MESSAGE_ID créé:", MESSAGE_ID)

    # 2) Envoyer un PIN au destinataire
    print("Envoi du PIN...")
    pin_id = send_pin(application_id=APP_ID, message_id=MESSAGE_ID, to=TO)
    print("PIN envoyé. pinId:", pin_id)

    # 3) Demander à l’utilisateur le code reçu (pour l’exemple on simule une saisie)
    user_pin = input("Entrez le code reçu: ").strip()

    # 4) Vérifier le PIN
    ok = verify_pin(pin_id=pin_id, pin=user_pin)
    if ok:
        print("PIN correct. Authentification 2FA validée.")
    else:
        print("PIN incorrect. Voulez-vous renvoyer le code ? (o/N)")
        ans = input().strip().lower()
        if ans == "o":
            resend_pin(pin_id)
            print("Code renvoyé. Vérifiez à nouveau votre messagerie.") '''