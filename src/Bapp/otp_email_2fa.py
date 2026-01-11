import logging
from os import getenv

from django.contrib import messages
from django.shortcuts import redirect, render
from django.template.loader import render_to_string
from django.utils import timezone
from django.utils.safestring import mark_safe
#from twilio.rest import Client

from BTest import settings

from django.contrib.auth import login
from django.core.mail import send_mail

from Bapp.models import TwoFactorAuth, BtestCustomUser

logger = logging.getLogger(__name__)


def send_2fa_code_email(user, code):
    """Envoi d'un code 2FA par email"""
    prenom = getattr(user, 'prenoms', '') or ''
    subject = "Votre code de connexion (2FA)"
    html_message = render_to_string("site/client/Email/mail_template.html", {"code": code, "prenom": prenom})
    # Version texte simple (fallback)
    plain_message = f"Bonjour {prenom},\n\nVotre code 2FA est: {code}\n\nIl expire dans 5 minutes."
    recipient = [user.email]
    try:
        send_mail(subject=subject,
                  message=plain_message,
                  html_message=html_message,
                  from_email=settings.EMAIL_HOST_USER,
                  recipient_list=recipient,
                  fail_silently=False
                  )
        return True
    except Exception as e:
        logger.error(f"Erreur lors de l'envoi du code 2FA via email: {str(e)}")
        return False

#def send_2fa_code_whatsapp(user, code):
#    # Nécessite: pip install twilio et variables d'environnement
#    # TWILIO_ACCOUNT_SID, TWILIO_AUTH_TOKEN, TWILIO_WHATSAPP_FROM='whatsapp:+14155238886'
#
#    account_sid = getenv("TWILIO_ACCOUNT_SID")
#    auth_token = getenv("TWILIO_AUTH_TOKEN")
#    from_whatsapp = getenv("TWILIO_WHATSAPP_FROM")  # ex: 'whatsapp:+14155238886'
#    to_whatsapp = f"whatsapp:{user.telephone}"   # Assurez-vous que le numéro est au format E.164
#
#    client = Client(account_sid, auth_token)
#    client.messages.create(
#        from_=from_whatsapp,
#        to=to_whatsapp,
#        body=f"Votre code de vérification est {code}. Il expire dans 5 minutes."
#    )



#Gestion de creation et d'authentification
def get_or_create_2fa(request, user, channel='email'):
    """
    Prépare/retourne un token 2FA et l'envoie selon le canal.
    Retourne un tuple (token, error_message) où error_message est None si succès.
    """
    logger.info(f"Début de get_or_create_2fa pour l'utilisateur {user.id}, canal: {channel}")

    # 1. Vérifier si un code valide existe déjà
    existing_code = TwoFactorAuth.objects.filter(user=user).first()

    if existing_code and not existing_code.token_expired:
        logger.info("Code 2FA valide existant trouvé, réutilisation et renvoi")

        # Renvoyer le code existant via le canal demandé
        success = send_2fa_code_email(user, existing_code.token_code)

        if not success:
            error_msg = f"Échec du renvoi du code 2FA existant via {channel}"
            logger.error(error_msg)
            messages.error(request, error_msg)
            return None, error_msg

        return existing_code, None

    # 2. Supprimer les anciens codes expirés
    if existing_code:
        logger.info("Suppression de l'ancien code expiré")
        existing_code.delete()


    # 4. Création du nouveau token
    try:
        time_to_live = 5  # minutes
        token = TwoFactorAuth.create_token(user=user, channel=channel, ttl_minutes=time_to_live)
        logger.info(f"Nouveau token 2FA créé: {token.token_code}")

        # 5. Envoi du token via le canal approprié
        success = send_2fa_code_email(user, token.token_code)

        if not success:
            # En cas d'échec d'envoi, supprimer le token créé
            token.delete()
            error_msg = f"Échec de l'envoi du code 2FA via {channel}"
            logger.error(error_msg)
            messages.error(request, error_msg)
            return None, error_msg
        messages.success(request, f'Le code à 6 chiffres à été envoyé par {channel}.')
        return token, None

    except Exception as e:
        logger.error(f"Erreur lors de la création/envoi du token 2FA: {str(e)}")
        messages.error(request, 'Une erreur est survenu lors de la génération du code. Veuillez réessayer.')
        return None, f"Erreur technique: {str(e)}"


def members_authentification_email(request):
    template_name = 'site/client/Email/members_authentification.html'
    # Vérification de l'identité temporaire en session
    user_id = request.session.get("pending_user_id")
    if not user_id:
        return redirect("Bapp:member_login_view")  # sécurité : retour login

    # Récupération de l'utilisateur
    try:
        user = BtestCustomUser.objects.get(pk=user_id)
        #On verifies d'abord que l'utilisateur a un email déjà verifier
        if not user.email_verified:
            messages.error(request, "Vous n'avez pas un email dèjà validé, veuillez choisir un autre methode d'authentification.")
            return redirect("Bapp:load_2fa_method")  # sécurité : retour login
    except BtestCustomUser.DoesNotExist:
        messages.error(request, "Utilisateur introuvable")
        return redirect("Bapp:member_login_view")

    step = 2  # étape par défaut (affichage du formulaire de saisie)
    # --- Cas GET (premier affichage) ---
    if request.method == "GET":
        # Génération/envoi du code OTP si nécessaire
        get_or_create_2fa(request, user, channel="email")
        return render(request, template_name, {"step": step})

    # --- Cas POST (validation du code saisi) ---
    if request.method == "POST":
        code = request.POST.get("code")
        if not code:
            messages.error(request, "Veuillez saisir un code.")
            step = 2
            return render(request, template_name, {"step": step})

        try:
            two_fa = TwoFactorAuth.objects.get(user=user, token_code=code)
            if two_fa.token_expired:
                messages.error(request, "⚠️ Code expiré. Un nouveau code a été envoyé.")
                get_or_create_2fa(request, user, channel="email")
                step = 2
            elif two_fa.is_used:
                messages.error(request, "❌ Ce code a déjà été utilisé.")
            else:
                # ✅ Authentification validée
                two_fa.mark_as_used()
                login(request, user)
                request.session.pop("pending_user_id", None)
                request.session.pop("2fa_method", None)
                messages.success(
                    request,
                    mark_safe(f"Bonjour <strong>{user.prenoms}</strong>, bienvenue sur le Dashboard ✅")
                )
                request.session['user_prenom'] = user.prenoms
                #On connecte l'utilisateur au site
                login(request, user)
                return redirect("Bapp:users_menu")
        except TwoFactorAuth.DoesNotExist:
            message = mark_safe(" ❌ Code invalide, veuillez réessayer.")
            messages.error(request, message)
            step = 2

    # Retour si GET initial ou POST incorrect
    return render(request, template_name, {"step": step, "user": user})