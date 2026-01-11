import logging
from os import getenv

import pyotp

import base64
import io


import qrcode
from django.contrib import messages
from django.contrib.auth import login
from django.http import HttpResponse, Http404
from django.shortcuts import redirect, render
from django.urls import reverse

from Bapp.models import BtestCustomUser

def generate_otp_secret():
    return pyotp.random_base32()

#Génère l'URL de l'image QR code
def get_qr_code_uri(user, secret):
    totp = pyotp.TOTP(secret)
    return totp.provisioning_uri(
        name=user.prenoms,        # ou user.prenoms
        issuer_name="Missideh-Bourou"   # nom affiché dans Google Authenticator
    )

#Génère l'image QR code
def qrcode_view(request, user_id):
    try:
        user = BtestCustomUser.objects.get(id=user_id)
    except BtestCustomUser.DoesNotExist:
        raise Http404("Utilisateur introuvable")

    uri = get_qr_code_uri(user, user.otp_secret)

    qr = qrcode.QRCode(error_correction=qrcode.constants.ERROR_CORRECT_M)
    qr.add_data(uri)
    qr.make(fit=True)
    img = qr.make_image(fill_color="black", back_color="white").convert("RGB")

    buf = io.BytesIO()
    img.save(buf, format="PNG")
    buf.seek(0)

    return HttpResponse(buf, content_type="image/png")


#Verifiaction de code entré par l'utilisateur
def verify_otp(secret, code):
    totp = pyotp.TOTP(secret)
    return totp.verify(code, valid_window=1)


#Méthode pricipale pour l'authentification via Qrcode'
#Méthode pricipale pour l'authentification via Qrcode'
def members_authentification_qrcode(request):
    template_name = 'site/client/Qrcode/members_authentification_qrcode.html'
    context = {}

    user_id = request.session.get("2fa_setup_user_id")
    if not user_id:
        return redirect("Bapp:identifiant_over_otp")

    user = BtestCustomUser.objects.get(id=user_id)
    print('On affiche le OTP secret', user.otp_secret)

    # 🔹 Ici, on donne directement l’URL de l’image
    qr_code_url = reverse("Bapp:qrcode", kwargs={"user_id": user.id})
    context["qr_code_url"] = qr_code_url
    messages.info(request, 'Veuillez saisir le code généré par Google Authenticator sur votre téléphone.')

    if request.method == "POST":
        code = request.POST.get("code")
        if not code:
            context["error"] = "Veuillez entrer le code de vérification."
            return render(request, template_name=template_name, context=context)

        # Utilisateur déjà activé
        if user.otp_enabled:
            print("L'utilisateur a déjà un QR code actif")
            if verify_otp(user.otp_secret, code):
                # Rendre la suppression tolérante à l'absence de clé
                request.session.pop("user_otp_enabled", None)
                request.session['user_prenom'] = user.prenoms
                login(request, user)
                return redirect("Bapp:users_menu")
            else:
                context["error"] = "Code invalide"
                return render(request, template_name=template_name, context=context)

        # Première activation
        if verify_otp(user.otp_secret, code):
            user.otp_enabled = True
            user.save()
            # Rendre la suppression tolérante à l'absence de clé
            request.session.pop("2fa_setup_user_id", None)
            messages.success(request, f'Bonjour {user.prenoms}, authentification réussie.')
            login(request, user)
            return redirect("Bapp:users_menu")
        else:
            context["error"] = "Code invalide"
            return render(request, template_name=template_name, context=context)

    return render(request, template_name=template_name, context=context)


def identifiant_otp(request):
    user_id = request.session.get("2fa_qrcode_user_id")
    print('debut de la session: ', user_id)
    if not user_id:
        messages.error(request, "Erreur de session")
        return redirect("Bapp:member_login_view")

    try:
        user = BtestCustomUser.objects.get(pk=user_id)
        print('L utilisateur est: ', user.prenoms)
        # Génération d’un secret si pas déjà défini
        if not user.otp_secret:
            user.otp_secret = generate_otp_secret()
            user.save()
        request.session["2fa_setup_user_id"] = user.id
        request.session["user_otp_enabled"] = user.otp_enabled
        # Stocker l'ID dans la session pour étape suivante
        print(request.session["2fa_setup_user_id"])
        return redirect("Bapp:two_fa_qrcode_auth")
    except BtestCustomUser.DoesNotExist:
        messages.error(request, "Utilisateur introuvable")
        return redirect("Bapp:member_login_view")



    return render(request, template_name=template_name)
