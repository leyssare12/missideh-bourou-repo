import datetime

from django.shortcuts import redirect, render
from django.utils import timezone
from django.core.mail import send_mail
from django.urls import reverse
from django.core.exceptions import ObjectDoesNotExist

import uuid
from .models import ResetPasswordToken
from .models import BtestCustomUser


def request_password_reset(request):
    template_name = 'site/admin/password/reset_password_request.html'
    context = {}

    if request.method == 'POST':
        identifiant = request.POST.get('identifiant')
        try:
            user = BtestCustomUser.objects.get(identifiant=identifiant)

            # Créer un token de réinitialisation
            token = ResetPasswordToken.objects.create(
                user=user,
                expiration=timezone.now() + datetime.timedelta(hours=24)
            )

            # Générer l'URL de réinitialisation
            reset_url = request.build_absolute_uri(
                reverse('Bapp:password_reset_confirm', kwargs={'token': token.token})
            )
            print(f" Voici l'email de l'utilisateur: {user.email}")
            # Envoyer l'email
            message = f"Veuillez vérifier votre email en cliquant sur ce lien: {reset_url}"
            print(token, message)
            # Envoyer l'email de vérification
            mail_sender = send_mail(
                "Vérifiez votre email",
                message,
                "m-cherif@leyssare.net",
                [user.email],
                fail_silently=False,
            )
            if mail_sender:
                request.session['user_mail'] = user.email
                context['mail'] = "L'email a été envoyé avec succès."
                print("Email envoyé avec succés.")
            else:
                context['error'] = "Une erreur s'est produite pendant l'envoi de l'email."
                print("Une erreur s'est produite pendant l'envoi de l'email.")

            return redirect('Bapp:password_reset_email_sent')

        except ObjectDoesNotExist:
            context['error'] = "Aucun compte n'est associé à ce numéro d'identifiant."

    return render(request, template_name, context)


def password_reset_confirm(request, token):
    template_name = 'site/admin/password/confirm_new_password.html'
    context = {}

    try:
        token_obj = ResetPasswordToken.objects.get(token=token)

        if not token_obj.is_valid():
            context['error'] = "Ce lien de réinitialisation est expiré ou a déjà été utilisé."
            return render(request, template_name, context)

        if request.method == 'POST':
            password = request.POST.get('password')
            confirm_password = request.POST.get('confirm_password')

            if password != confirm_password:
                context['error'] = "Les mots de passe ne correspondent pas."
            elif len(password) < 8:
                context['error'] = "Le mot de passe doit contenir au moins 8 caractères."
            else:
                user = token_obj.user
                user.set_password(password)
                user.save()

                # Marquer le token comme utilisé
                token_obj.used = True
                token_obj.save()

                return redirect('Bapp:password_reset_success')

    except ObjectDoesNotExist:
        context['error'] = "Lien de réinitialisation invalide."

    return render(request, template_name, context)


def password_reset_email_sent(request):
    context = {'user_mail': request.session.get('user_mail', '')}
    if "user_mail" in request.session:
        del request.session['user_mail']

    return render(request, 'site/admin/password/send_mail_by_reseting_password.html', context=context)


def password_reset_success(request):
    return render(request, 'site/admin/password/reset_password_succes.html')
