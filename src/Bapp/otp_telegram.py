import json

import secrets

import requests
from django.apps import apps
from django.contrib import messages
from django.core.cache import cache
from django.contrib.auth import login, get_user_model
from django.db import IntegrityError
from django.http import HttpResponseForbidden, HttpResponse, JsonResponse
from django.shortcuts import render, redirect
from django.utils import timezone
from django.views.decorators.csrf import csrf_exempt

from BTest import settings
from .models import BTestCustomUser, TelegramOTP2FA



#Retourne le token et l'url de base'
def _get_telegram_api_base() -> str:
    token = getattr(settings, "TELEGRAM_BOT_TOKEN", None)
    if not token:
        print('Le token n exsite pas. ')
        raise ValueError("TELEGRAM_BOT_TOKEN n'est pas défini dans settings.")
    print('Token envoyé:  ', token)
    return f"https://api.telegram.org/bot{token}"


#Creation d'une fonction de bienvenue
def create_welcome_text(name):
    return f"""
<b>🌸 Salam {name} !</b>

Je suis le bot officiel de <b>Missideh-Bourou</b>, votre compagnon de sécurité. 

🔒 <b>Pour activer la vérification en 2 étapes :</b>
1. Connectez-vous à votre compte Missideh-Bourou
2. Allez dans <i>Télégram → 2FA</i>
3. Tapez votre ID Missideh-Bourou dans le champ <b>"Identifiant"</b>
4. Cliquez sur <b>Lié mon compte</b>
5. Completez le formulaire de liaison
6. Si votre compte Télégram est dèjá lié à votre compte Mssideh Bourou!
    a. Tapez la commande: /moncode -> pour recevoir un nouveau code OTP
    b. Tapez le code OTP que vous recevrez par Telegram dans le champ <b>Code OTP</b> dans Missideh-Bourou online

💁 <b>Besoin d'aide ?</b>
Contactez notre équipe support pour vous guider.

<i>Restez connecté·e en toute sécurité !</i> 🌺
"""


#Normalise l'envoie du message via le bot Telegram
def send_telegram_message(chat_id, text, *, parse_mode: str | None = None, disable_notification: bool = True):
    """
    Envoie un message à l'utilisateur via le bot Telegram (version avec requests).
    """
    if not chat_id:
        raise ValueError("chat_id manquant pour l'envoi Telegram.")

    url = f"{_get_telegram_api_base()}/sendMessage"
    payload = {
        "chat_id": chat_id,
        "text": text,
        "disable_notification": disable_notification
    }
    if parse_mode:
        payload["parse_mode"] = parse_mode

    try:
        response = requests.post(url, json=payload, timeout=10)
        response.raise_for_status()  # Lève une exception pour les codes 4xx/5xx

        response_data = response.json()
        print(f"📤 Réponse Telegram: {response_data}")

        if response_data.get('ok'):
            print(f"✅ Message envoyé avec succès à {chat_id}")
            return response_data
        else:
            error_msg = response_data.get('description', 'Erreur inconnue')
            print(f"❌ Erreur Telegram: {error_msg}")
            raise RuntimeError(f"Erreur Telegram: {error_msg}")

    except requests.exceptions.RequestException as e:
        print(f"❌ Erreur lors de l'envoi Telegram: {e}")
        raise RuntimeError(f"Erreur envoi Telegram: {e}") from e
    except json.JSONDecodeError as e:
        print(f"❌ Erreur décodage JSON: {e}")
        raise RuntimeError(f"Erreur décodage réponse: {e}") from e

# Retourne le nonce
def generate_enrollment_nonce(user, *, ttl_seconds: int = 600) -> str:
    """
    Génère un jeton (nonce) d'enrôlement pour le deep-link Telegram (paramètre 'start'),
    et le stocke côté serveur (cache) avec une expiration courte.

    Stockage:
      Clé:   tg_enroll_nonce:{user_id}:{nonce}
      Valeur: { "user_id": <int>, "created_at": <iso8601> }

    - user: instance utilisateur (doit avoir un pk)
    - ttl_seconds: durée de validité du nonce (par défaut 10 minutes)

    Retour: le nonce (string) à passer dans https://t.me/<bot_username>?start=<nonce>
    """
    if not user or not getattr(user, "pk", None):
        raise ValueError("Utilisateur invalide pour la génération du nonce.")

    # Jeton aléatoire sûr, compact et compatible URL
    nonce = secrets.token_urlsafe(24)

    cache_key = f"tg_enroll_nonce:{nonce}"  # Clé simplifiée
    cache_value = user.pk  # Stockez juste l'ID
    cache.set(cache_key, cache_value, ttl_seconds)
    return nonce


def _link_telegram_chat_id(user, chat_id: int):
    """
    Enregistre le chat_id Telegram sur l'utilisateur et horodate la liaison.
    """
    print('Le chat_id est ', chat_id, ' et l utilisateur est:', user)
    TwoFactorSettingsTelegram = apps.get_model("Bapp", "TwoFactorSettingsTelegram")

    try:
        # Essayer de créer ou mettre à jour
        obj, created = TwoFactorSettingsTelegram.objects.update_or_create(
            user=user,
            defaults={
                'telegram_chat_id': chat_id,
                'telegram_linked_at': timezone.now()
            }
        )
        return obj
    except IntegrityError:
        # Si violation d'unicité sur telegram_chat_id
        print(f"IntegrityError: chat_id {chat_id} existe déjà")

        # Trouver l'entrée existante avec ce chat_id
        existing_obj = TwoFactorSettingsTelegram.objects.get(telegram_chat_id=chat_id)

        if existing_obj.user != user:
            print(f"Transfert du chat_id {chat_id} de {existing_obj.user} à {user}")
            # Transférer le chat_id à l'utilisateur actuel
            existing_obj.user = user
            existing_obj.telegram_linked_at = timezone.now()
            existing_obj.save()

        return existing_obj

#Recupère les messages à envoyer et les transmet à la methode send_telegram_message()
def _safe_send(chat_id, text, parse_mode=None):
    """Envoi Telegram tolérant, pour ne pas casser le webhook."""
    try:
        print(f"🔄 Tentative d'envoi à {chat_id}: '{text}'")
        result = send_telegram_message(chat_id, text, disable_notification=False, parse_mode=parse_mode)

        if result and result.get('ok'):
            print(f"✅ Message envoyé avec succès")
            return True
        else:
            print(f"❌ Échec envoi message (réponse: {result})")
            return False

    except Exception as e:
        print(f"❌ Erreur envoi message: {e}")
        # Ne pas raise pour ne pas casser le webhook
        return False


def get_user_by_chat_id(chat_id):
    """Trouve l'utilisateur associé à un chat_id"""
    TwoFactorSettingsTelegram = apps.get_model("Bapp", "TwoFactorSettingsTelegram")
    try:
        settings_obj = TwoFactorSettingsTelegram.objects.get(telegram_chat_id=chat_id)
        return settings_obj.user
    except TwoFactorSettingsTelegram.DoesNotExist:
        return None

#Méthode appelé par la route /telegram_webhook
@csrf_exempt
def telegram_webhook(request):
    print(f"=== NOUVELLE REQUÊTE RECUE ===")
    print(f"Path: {request.path}")
    print(f"Méthode: {request.method}")



    # Vérifier le secret token
    expected = getattr(settings, "TELEGRAM_WEBHOOK_SECRET", None)
    if expected:
        got = request.headers.get("X-Telegram-Bot-Api-Secret-Token")
        if got != expected:
            print(f"Secret mismatch: expected {expected}, got {got}")
            return HttpResponseForbidden("Invalid secret")
        else:
            print("✅ Secret token validé")

    # Lire l'update
    try:
        body = request.body.decode('utf-8')
        print(f"Raw body: {body}")
        update = json.loads(body)
        print(f"Update JSON: {update}")
    except Exception as e:
        print(f"Error parsing webhook: {e}")
        return HttpResponse(status=400)

    # Vérifier si c'est un message
    message = update.get("message")
    if not message:
        print("❌ Aucun 'message' dans l'update")
        print("L'update contient peut-être autre chose (callback_query, etc.)")
        print(f"Clés de l'update: {update.keys()}")
        return HttpResponse("ok")

    # Vérifier le type de chat
    chat_type = message.get("chat", {}).get("type")
    print(f"Chat type: {chat_type}")

    if chat_type != "private":
        print(f"❌ Message non privé (type: {chat_type}), ignoré")
        return HttpResponse("ok")

    # Extraire le texte et le chat_id
    text = message.get("text") or ""
    chat_id = message.get("chat", {}).get("id")
    print(f"Private message: '{text}' from chat_id: {chat_id}")

    # Extraire les informations de l'utilisateur pour lui envoyer un message
    from_user = message.get("from", {})
    first_name = from_user.get('first_name', '')
    last_name = from_user.get('last_name', '')
    username = from_user.get('username', '')

    # Créer un nom d'affichage personnalisé
    if first_name and last_name:
        display_name = f"{first_name} {last_name}"
    elif first_name:
        display_name = first_name
    elif username:
        display_name = f"@{username}"
    else:
        display_name = "cher utilisateur"

    message_welcome = create_welcome_text(display_name)
    print(f"Display name: {display_name}")

    # Vérifier si c'est une commande /start
    if text.startswith("/start"):
        print("✅ Commande /start détectée")

        if " " in text:
            nonce = text.split(" ", 1)[1].strip()
            print(f"Processing nonce: {nonce}")

            # Chercher l'user_id dans le cache
            user_id = cache.get(f"tg_enroll_nonce:{nonce}")
            print(f"Found user_id: {user_id} for nonce: {nonce}")

            if not user_id:
                print("❌ Invalid or expired nonce")
                _safe_send(chat_id, "Lien invalide ou expiré. Merci de relancer la liaison depuis votre compte Missideh-Bourou.online")
                return HttpResponse("ok")

            # Charger l'utilisateur
            try:
                user = BTestCustomUser.objects.get(pk=user_id)
                print(f"✅ Utilisateur trouvé: {user}")
                _safe_send(chat_id, f'Salam {display_name}')
            except BTestCustomUser.DoesNotExist:
                print(f"❌ User {user_id} not found")
                _safe_send(chat_id, "Utilisateur introuvable.")
                return HttpResponse("ok")

            # Lier et confirmer
            try:
                _link_telegram_chat_id(user, chat_id)
                cache.delete(f"tg_enroll_nonce:{nonce}")
                print("✅ Compte lié avec succès")

                _safe_send(chat_id,
                           "Votre compte est maintenant lié à ce bot. Vous pouvez désormais recevoir vos codes OTP via ce Chat Telegram.")
                print("✅ Message de confirmation envoyé")

            except Exception as e:
                print(f"❌ Erreur lors de la liaison: {e}")
                _safe_send(chat_id, "Erreur lors de la liaison. Veuillez réessayer.")

            return HttpResponse("ok")
        else:
            # /start sans paramètre
            print("⚠️ /start sans paramètre (nonce manquant)")
            _safe_send(chat_id, message_welcome, parse_mode="HTML")
            return HttpResponse("ok")
    elif text.startswith("/otp") or text.startswith("/moncode"):
        # Demander un nouveau code OTP
        user = get_user_by_chat_id(chat_id)
        if user:
            if send_otp_code(request, user):
                _safe_send(chat_id, "✅ Code OTP envoyé! Vérifiez vos messages.")
            else:
                _safe_send(chat_id, "❌ Impossible de générer un code OTP.")
        else:
            _safe_send(chat_id, "❌ Aucun compte lié à ce chat.")

    elif text.strip().isdigit() and len(text.strip()) == 6:
        # Code OTP entré manuellement
        user = get_user_by_chat_id(chat_id)
        if user:
            telegram_otp = TelegramOTP2FA.get_or_create_for_user(user)
            if telegram_otp.verify_otp_telegram(text.strip()):
                _safe_send(chat_id, "✅ Code OTP valide!")
            else:
                _safe_send(chat_id, "❌ Code OTP invalide ou expiré.")
        else:
            _safe_send(chat_id, "❌ Aucun compte lié à ce chat.")

    else:
        _safe_send(chat_id,
                   "🤖 Commandes disponibles:\n/start - Lier votre compte\n/otp - Générer un code OTP\n/moncode - Générer un code OTP")

    return HttpResponse("ok")
def _get_telegram_chat_id_for_user(user):
    """
    Récupère le chat_id Telegram via le modèle dédié TwoFactorSettingsTelegram.
    Retourne None si non lié.
    """
    if user is None:
        return None
    TwoFactorSettingsTelegram = apps.get_model("Bapp", "TwoFactorSettingsTelegram")
    settings_obj = TwoFactorSettingsTelegram.objects.filter(user=user).only("telegram_chat_id").first()
    return getattr(settings_obj, "telegram_chat_id", None)

def is_telegram_linked(user) -> bool:
    """
    Teste la liaison Telegram via TwoFactorSettingsTelegram.
    """
    return bool(_get_telegram_chat_id_for_user(user))


#Methode view principale de la route /telegram_otp_login
def login_with_2fa_by_telegram(request):
    template_name = "site/client/Telegram/login_view.html"
    context = {}

    user_id = request.session.get("pending_user_id")

    # Étape 1: Vérifier les identifiants
    if not user_id:
        messages.error(request, "Identifiant invalide")
        return redirect("Bapp:member_login_view")  # sécurité : retour login
    if request.method == 'POST':

        otp_code = request.POST.get('otp_code')
        action = request.POST.get('action')
        user = BTestCustomUser.objects.filter(pk=user_id).first()
        identifiant = user.identifiant
        if user is not None:
            # Vérifier si l'utilisateur a le 2FA activé
            if is_telegram_linked(user):
                if not otp_code:
                    # Demander le code OTP
                    try:
                        # Envoyer immédiatement un code OTP
                        send_otp_code(request, user)
                    except Exception as e:
                        print(f"Erreur envoi OTP: {e}")
                    context['identifiant'] = identifiant
                    context['user_id'] = user.id
                    context['telegram_linked'] = True
                    context['show_otp'] = True
                    return render(request, template_name, context)

                # Vérifier le code OTP
                telegram_otp = TelegramOTP2FA.get_or_create_for_user(user)
                if telegram_otp.verify_otp_telegram(otp_code):
                    login(request, user)
                    messages.success(request, "Connexion réussie avec 2FA!")
                    request.session['user_prenom'] = user.prenoms
                    return redirect('Bapp:users_menu')
                else:
                    messages.error(request, "Code OTP invalide")
                    context['identifiant'] = identifiant
                    context['user_id'] = user.id
                    context['telegram_linked'] = True
                    context['show_otp'] = True
                    context['error'] = 'Code OTP invalide'
                    return render(request, template_name, context)
            else:
                # Utilisateur non lié - proposer la liaison
                if action == 'link_telegram':
                    # Générer un nonce pour la liaison
                    nonce = generate_enrollment_nonce(user)
                    bot_username = getattr(settings, "TELEGRAM_BOT_USERNAME", "")
                    context['identifiant'] = identifiant
                    context['nonce'] = nonce
                    context['show_link_qr'] = True
                    context['bot_username'] = bot_username
                    context['user_id'] = user.id

                    return render(request, template_name, context)

                # Première visite - proposer les options
                context['identifiant'] = identifiant
                context['show_options'] = True
                context['user_id'] = user.id
                return render(request, template_name, context)
        else:
            messages.error(request, "Identifiants invalides")
    #Si on vient d'arrivé sur la page
    context['show_options'] = True
    return render(request, template_name=template_name, context=context)


# telegram_utils.py
def send_otp_code(request, user):
    """Génère et envoie un code OTP à l'utilisateur via Telegram"""
    if not is_telegram_linked(user):
        messages.error(request, "Vous n'avez pas encore lié votre compte Telegram. Veuillez le faire avant d'utiliser ce service.")
        return False

    chat_id = _get_telegram_chat_id_for_user(user)
    if not chat_id:
        messages.error(request, "Vous n'avez pas encore lié votre compte Telegram. Veuillez le faire avant d'utiliser ce service.")
        return False

    # Générer le code OTP
    telegram_otp = TelegramOTP2FA.get_or_create_for_user(user)
    otp_code = telegram_otp.generate_otp()

    # Envoyer le code
    message = f"🔐 Votre code de vérification est:  {otp_code}\n\nCe code expire dans 5 minutes."
    try:
        #On appel la méthode _save_send() qui elle même appelle la méthode send_telegram_message()
        _safe_send(chat_id, message)
        return True
    except Exception as e:
        messages.error(request, f"Erreur lors de l'envoi du code OTP: {e}")
        print(f"Erreur envoi OTP: {e}")
        return False


def check_telegram_link_status(request):
    """Vue AJAX pour vérifier si l'utilisateur a lié Telegram"""
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            user_id = data.get('user_id')

            from django.contrib.auth import get_user_model
            User = get_user_model()

            try:
                user = User.objects.get(id=user_id)
                is_linked = is_telegram_linked(user)

                return JsonResponse({
                    'success': True,
                    'is_linked': is_linked
                })
            except User.DoesNotExist:
                return JsonResponse({'success': False, 'error': 'Utilisateur non trouvé'})

        except json.JSONDecodeError:
            return JsonResponse({'success': False, 'error': 'Données invalides'})

    return JsonResponse({'success': False, 'error': 'Méthode non autorisée'})

#Demande de renvoie de code OTP
def request_new_otp_telegram(request):
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            user_id = data.get('user_id')
            User = get_user_model()
            try:
                user = User.objects.get(pk=user_id)
                print(f"user: {user}")
                if send_otp_code(request, user):
                    return JsonResponse({'success': True})
                else:
                    return JsonResponse({'success': False, 'error': 'Impossible d\'envoyer le code'})
            except User.DoesNotExist:
                return JsonResponse({'success': False, 'error': 'Utilisateur non trouvé'})

        except json.JSONDecodeError:
            return JsonResponse({'success': False, 'error': 'Données invalides'})

    return JsonResponse({'success': False, 'error': 'Méthode non autorisée'})