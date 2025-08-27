import requests

import random

from django.contrib import messages
from django.core.cache import cache
from django.contrib.auth import authenticate, login
from django.shortcuts import render, redirect

from .models import TwoFactorAuth, BTestCustomUser
from .utils import get_or_create_2fa


# handler côté bot (hors Django)
def start(update, context):
    chat_id = update.message.chat_id
    context.bot.send_message(chat_id, "Bienvenue ! Donne ce code dans ton compte Django : 123456")


# views.py

def telegram_otp_login(request):
    template_name = "site/client/Telegram/telegram_login_otp.html"
    context = {}
    if request.method == "POST":
        identifiant = request.POST.get("identifiant")
        print(identifiant)
        if identifiant:
            try:
                user = BTestCustomUser.objects.get(identifiant=identifiant)
                channel = "email" if user.email_verified else "telegram"

                try:
                    get_or_create_2fa(user, channel=channel)
                    request.session["user_id"] = user.pk  # stockage temporaire
                    return redirect("Bapp:telegram_otp_confirm")
                except Exception as e:
                    messages.error(request, str(e))
            except BTestCustomUser.DoesNotExist:
                messages.error(request, "Identifiant invalide.")
    return render(request, template_name=template_name, context=context)


def cofirm_telegram_otp_login(request):
    template_name = "site/client/Telegram/valide_otp.html"
    context = {}
    if request.method == "POST":
        code = request.POST.get("otp")
        user_id = request.session.get("user_id")
        otp = TwoFactorAuth.objects.filter(user_id=user_id).first()
        if str(otp.token_code)  == str(code):
            user = BTestCustomUser.objects.get(id=user_id)
            login(request, user)
            context["success"] = "Bienvenue sur Missideh Bourou Dashboard"
            return render(request, template_name=template_name, context=context)
        context["error"] = "Code invalide ou expiré"
        return render(request, template_name=template_name, context=context)
    context['error'] = "Requete invalide"
    return render(request, template_name=template_name, context=context)
