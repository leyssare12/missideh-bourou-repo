import hashlib
import os
import time
import uuid
import datetime
from dataclasses import field
from datetime import datetime, timedelta
from pathlib import Path

from django.conf import settings
from django.contrib import messages
from django.contrib.admin.templatetags.admin_list import results
from django.contrib.auth import get_user_model, authenticate, login, logout
from django.contrib.auth.decorators import login_required
from django.core.exceptions import PermissionDenied
from django.core.files import File
from django.core.mail import send_mail
from django.db.models import Q
from django.http import JsonResponse, HttpResponseRedirect, HttpResponseBadRequest
from django.shortcuts import render, redirect, get_object_or_404
from django.db import connection, transaction
from django.template.defaultfilters import title
from django.urls import reverse
from django.utils import timezone
from django.utils.html import strip_tags
from django.utils.http import url_has_allowed_host_and_scheme
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_GET


from Bapp.forms import BtestUserCreationsForms, ParticipationAnnuelForm, RechercheUserForm, \
    ParticipationOccasionnelleForm, DonsForm, UserSearchForm, AddDepensesForm, EditorialCommunityForm

import random

from Bapp.models import BTestCustomUser, ParticipationOccasionnelle, Dons, ParticipationAnnual, AddDepenses, PDFManager
from Bapp.pdf_manager import PDFGenerator
from Bapp.permissions import has_secretor_role, can_add_user, can_edit_article


CustomUser = get_user_model()
#Gestion de génération d'un code unique pour l'utilisateur
def generate_unique_short_id():
    def replace_zero(s):
        """Remplace les '0' par des caractères valides (1-9, A-F)"""
        zero_replacements = ['1', '2', '3', '4', '5', '6', '7', '8', '9', 'A', 'B', 'C', 'D', 'E', 'F']
        result = ''
        for char in s:
            if char == '0':
                result += random.choice(zero_replacements)
            else:
                result += char
        return result

    while True:
        # Combiner plusieurs sources d'entropie
        timestamp = str(time.time_ns())
        random_bytes = os.urandom(9)
        uuid_str = str(uuid.uuid4())

        # Créer un hash de toutes ces données
        combined = f"{timestamp}{random_bytes}{uuid_str}".encode()
        hash_object = hashlib.sha256(combined)

        # Prendre plus de caractères et ajouter un timestamp
        hash_part = hash_object.hexdigest()[:4].upper()
        time_part = str(int(time.time() * 1000))[-2:]

        # Remplacer les zéros dans les deux parties
        hash_part = replace_zero(hash_part)
        time_part = replace_zero(time_part)

        result = f"{time_part}{hash_part}"

        # Vérifier qu'il n'y a pas de zéros dans le résultat final
        if '0' not in result:
            return result
def generate_custom_id(prenom, ville):
    prenom = prenom.upper()
    ville = ville.upper()
    nom_part = prenom[:3]
    ville_part = ville[:4]
    if ville == 'LEYSORONDO':
        ville_part = 'LYSD'
    if ville == 'LEYPELLEL':
        ville_part = 'LEYP'
    #On récupère la méthode de mixin uuid, hash et timestamp
    random_number = generate_unique_short_id()
    random_part = f"{random_number:04}"[:5]  # Ex : '0423' → '042'
    print(f"{nom_part}-{random_part}-{ville_part}")
    return f"{nom_part}-{random_part}-{ville_part}"

#Gestion de verification d'email
def build_activation_link(request, token):
    return request.build_absolute_uri(reverse('Bapp:mail_confirmation', kwargs={'token': str(token)}))
def email_html_template():
    template_html = """
    <!doctype html>
<html lang="fr">
<head>
  <meta charset="utf-8">
  <title>Activation de compte</title>
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <!-- Empêche l’agrandissement des tailles sur iOS -->
  <meta name="x-apple-disable-message-reformatting">
  <style>
    /* Styles de secours pour quelques clients qui respectent <style> */
    @media (prefers-color-scheme: dark) {
      .email-body { background-color: #0f172a !important; }
      .card { background-color: #111827 !important; color: #e5e7eb !important; }
      .muted { color: #9ca3af !important; }
      .btn { background-color: #2563eb !important; }
    }
  </style>
</head>
<body style="margin:0; padding:0; background:#f3f4f6;" class="email-body">
  <div style="display:none; font-size:1px; color:#f3f4f6; line-height:1px; max-height:0; max-width:0; opacity:0; overflow:hidden;">
    Confirmez votre adresse email pour activer votre compte.
  </div>

  <table role="presentation" cellpadding="0" cellspacing="0" width="100%" style="background:#f3f4f6; padding:24px 0;">
    <tr>
      <td align="center">
        <table role="presentation" cellpadding="0" cellspacing="0" width="100%" style="max-width:600px;">
          <tr>
            <td style="padding:0 16px;">
              <table role="presentation" cellpadding="0" cellspacing="0" width="100%" class="card" style="background:#ffffff; border-radius:8px; overflow:hidden;">
                <tr>
                  <td style="padding:32px 24px; font-family:Arial, Helvetica, sans-serif; color:#111827;">
                    <h1 style="margin:0 0 8px; font-size:20px; line-height:28px; font-weight:700;">Activez votre compte <strong style='color:#1d4de8;'>Missideh-Bourou.online</strong></h1>
                    <p style="margin:0 0 16px; font-size:14px; line-height:20px;">
                      Bonjour <strong>{{ user_name }}</strong>,
                    </p>
                    <p style="margin:0 0 16px; font-size:14px; line-height:20px;">
                      Merci pour votre inscription. Pour finaliser la création de votre compte, veuillez confirmer votre adresse email en cliquant sur le bouton ci-dessous. Pour des raisons de sécurité, ce lien expirera bientôt.
                    </p>

                    <!-- Bouton principal -->
                    <table role="presentation" cellpadding="0" cellspacing="0" style="margin:24px 0;">
                      <tr>
                        <td align="center">
                          <a href="{{ verification_url }}"
                             class="btn"
                             style="background:#1d4ed8; color:#ffffff; display:inline-block; padding:12px 20px; text-decoration:none; border-radius:6px; font-family:Arial, Helvetica, sans-serif; font-size:14px; font-weight:600;">
                            Activer mon compte
                          </a>
                        </td>
                      </tr>
                    </table>

                    <p class="muted" style="margin:0 0 16px; font-size:12px; line-height:18px; color:#6b7280;">
                      Si le bouton ne fonctionne pas, copiez-collez ce lien dans votre navigateur:
                    </p>
                    <p style="word-break:break-all; margin:0 0 24px; font-size:12px; line-height:18px; color:#374151;">
                      <a href="{{ verification_url }}" style="color:#1d4ed8; text-decoration:underline;">{{ verification_url }}</a>
                    </p>

                    <p class="muted" style="margin:0; font-size:12px; line-height:18px; color:#6b7280;">
                      Si vous n’êtes pas à l’origine de cette demande, vous pouvez ignorer cet email.
                    </p>
                  </td>
                </tr>
                <tr>
                  <td style="padding:16px 24px; background:#f9fafb; font-family:Arial, Helvetica, sans-serif; text-align:center;">
                    <p style="margin:0; font-size:12px; line-height:18px; color:#6b7280;">
                      © {{ current_year }} Missideh-Bourou-Online. Tous droits réservés.
                    </p>
                  </td>
                </tr>
              </table>

              <!-- Lien de secours en pur texte pour certains clients -->
              <p style="font-family:Arial, Helvetica, sans-serif; color:#6b7280; font-size:11px; line-height:16px; margin:12px 0 0;">
                Astuce: ajoutez notre adresse email à votre carnet pour assurer la bonne réception de nos emails.
              </p>
            </td>
          </tr>
        </table>
      </td>
    </tr>
  </table>
</body>
</html>

    """
    return template_html

#Send activation email
def send_email_verification(request, user):
    template_name = 'site/admin/confirm_mail_sended.html'
    context = {}
    verification_url = build_activation_link(request, user.email_verification_token)
    user_name = getattr(user, 'Prenom', user.prenoms) or "Utilisateur"
    current_year = datetime.now().year
    text_message = (
        f"Bonjour {user_name},\n\n"
        """Vous êtes désormais inscrit dans le plateform Missideh Bourou\n"""
        f"{verification_url}\n\n"
    )
    # Creation d'un message HTML avec le contenu de l'email
    html_message = (
        #On appele la fonction email_html_template()
        email_html_template()
        #On replace les variables par les variables de la fonction email_html_template()
        .replace("{{ user_name }}", str(user_name))
        .replace("{{ verification_url }}", verification_url)
        .replace("{{ current_year }}", str(current_year))
    )

    subject = "Vérifiez votre email pour activer votre compte"
    # Envoie de l'email avec le contenu HTML'
    send_mail(
        subject=subject,
        message=text_message,  # Fallback texte
        from_email=getattr(settings, "EMAIL_HOST_USER", "no-reply@example.com"),
        recipient_list=[user.email],
        fail_silently=False,
        html_message=html_message,  # Contenu HTML

    )
    return True
#On renvoie un autre email en cas d'expiration de lien

def resend_email_verification(request):
    template_name = 'site/admin/confirm_mail_sended.html'
    context = {}
    user_id = request.GET.get('user_id')
    user = BTestCustomUser.objects.get(pk=user_id)

    # Si déjà vérifié, pas besoin de renvoyer
    if user.email_verified:
        #l'utilisateur sera redirigé vers la page dauthentification'
        return HttpResponseRedirect(reverse('Bapp:members_authentification'))

    # Générer un NOUVEAU token + expiration
    user.email_verification_token = uuid.uuid4()
    user.email_verification_expiration = timezone.now() + timedelta(days=20)
    user.save(update_fields=["email_verification_token", "email_verification_expiration"])

    # Construire le lien de vérification
    verification_url = build_activation_link(request, user.email_verification_token)
    # Envoyer l'email (texte simple pour l'exemple; remplacez par votre HTML si besoin)
    user_name = getattr(user, 'Prenom', user.prenoms) or "Utilisateur"
    current_year = datetime.now().year
    text_message = (
        f"Bonjour {user_name},\n\n"
        """Vous êtes désormais inscrit dans le plateform Missideh Bourou\n"""
        f"{verification_url}\n\n"
    )
    # Creation d'un message HTML avec le contenu de l'email
    html_message = (
        #On appele la fonction email_html_template()
        email_html_template()
        #On replace les variables par les variables de la fonction email_html_template()
        .replace("{{ user_name }}", str(user_name))
        .replace("{{ verification_url }}", verification_url)
        .replace("{{ current_year }}", str(current_year))
    )

    subject = "Vérifiez votre email pour activer votre compte"
    # Envoie de l'email avec le contenu HTML'
    send_mail(
        subject=subject,
        message=text_message,  # Fallback texte
        from_email=getattr(settings, "EMAIL_HOST_USER", "no-reply@example.com"),
        recipient_list=[user.email],
        fail_silently=False,
        html_message=html_message,  # Contenu HTML

    )
    context['user_email'] = user.email
    context['home_url'] = reverse('Bapp:home_page')
    context['support_email'] = getattr(settings, "EMAIL_HOST_USER", "no-reply@example.com")
    context['webmail_url'] = getattr(settings, "WEBMAIL_URL", "https://mail.google.com/mail/u/0/#inbox")

    return render(request, template_name=template_name, context=context)

#Mail confimation
def mail_confirmation(request, token):
    template_name = 'site/admin/mail_confirmation.html'
    context = {}
    if not token:
        return HttpResponseBadRequest('Token manquant.')
    # Récupération de l'utilisateur par le token
    try:
        user = BTestCustomUser.objects.get(email_verification_token=token)
    except BTestCustomUser.DoesNotExist:
        # Cas typique: lien cliqué une 2e fois après activation (token déjà supprimé)
        context['link_used'] = "Ce lien n’est plus valide ou a déjà été utilisé."
        context['home_url'] = reverse('Bapp:home_page')
        context['support_url'] = getattr(settings, "EMAIL_HOST_USER", "no-reply@example.com")
        # Optionnel: si l’utilisateur est déjà connecté, vous pouvez personnaliser ici
        return render(request, template_name=template_name, context=context)

    # 3) Section critique: éviter les doubles validations concurrentes
    with transaction.atomic():
        usr = BTestCustomUser.objects.select_for_update().get(pk=user.pk)
        if usr.email_verified:
            context = {
                'success': "Votre email est déjà vérifié. Vous pouvez vous connecter.",
                'user_name': usr.prenoms,
                'login_url': reverse('Bapp:manager_login_page'),
                'home_url': reverse('Bapp:home_page'),
            }
            return render(request, template_name=template_name, context=context)
        # 4) Lien expiré
        if user.email_verification_expiration and timezone.now() > user.email_verification_expiration:

            user.email_verification_token = None
            user.email_verification_expiration = None
            user.save(update_fields=["email_verification_token", "email_verification_expiration"])
            context = {
                'error':'Le lien de vérification a expiré',
                'resend_url': reverse('Bapp:resend_verification') + f"?user_id={user.pk}",
                'support_url': getattr(settings, "EMAIL_HOST_USER", "no-reply@example.com"),
            }

            return render(request, template_name=template_name, context=context)


        # Mise à jour de l'utilisateur
        usr.email_verified = True
        usr.email_verification_token = None  # pour éviter une réutilisation
        usr.email_verification_expiration = None

        usr.save(update_fields=["email_verified", "email_verification_token", "email_verification_expiration"])

    context = {
        'success': "Votre email a été vérifié avec succès.",
        'user_name': usr.prenoms,
        'login_url': reverse('Bapp:manager_login_page'),
        'home_url': reverse('Bapp:home_page'),
        'support_url': getattr(settings, "EMAIL_HOST_USER", "no-reply@example.com"),
    }
    return render(request, template_name=template_name, context=context)


# Create your views here.
def index(request):
    templates = 'index.html'
    context = {"message": "Hello World!"}
    return render(request, templates, context)
def inscription(request):
    templates = 'site/inscription.html'
    context = {}
    return render(request, templates, context)
def add_sume(request):
    templates = 'site/add-sume.html'
    context = {}
    return render(request, templates, context)
def subcribe(request):
    templates = 'site/subcribe.html'
    context = {}
    return render(request, templates, context)
def admin_subcribe_save(request):
    templates = 'site/admin/admin_subcribe.html'
    context = {}


    if request.method == 'POST':
        formulaire = BtestUserCreationsForms(request.POST)
        name = request.POST.get('name')
        prenom = request.POST.get('prenom')
        pays = request.POST.get('pays')
        quartier = request.POST.get('quartier')
        mail = request.POST.get('email')
        tel = request.POST.get('telephone')
        password = request.POST.get('password')
        confirm_password = request.POST.get('confirm_password')
        print(name, prenom, pays, quartier, mail, tel, password, confirm_password)


        identifiant = generate_custom_id(name, quartier)
        identifiant_exists = BTestCustomUser.objects.filter(identifiant=identifiant).exists()
        type_utilisateur = formulaire.cleaned_data.get("role")
        print(type_utilisateur)
        if password == confirm_password:
            user_create = BTestCustomUser.objects.create_user(
                nom=name,
                prenoms=prenom,
                pays=pays,
                quartier=quartier,
                email=mail,
                telephone=tel,
                identifiant=identifiant,
                role=type_utilisateur,
                password=password
            )
            if user_create:
                user_create.is_active = True
                #user_create.save()
                print(user_create)
                return render(request, templates, context)


        else:
            print("Passwords do not match")
            context["form"] = formulaire
            return render(request, templates, context)
    else:
        formulaire = BtestUserCreationsForms()
    context["form"] = formulaire
    print(context)
    return render(request, templates, context)

@can_add_user(['ADMIN', 'MODERATOR'])
def admin_subcribe(request):
    templates = 'site/admin/admin_subcribe.html'
    context = {}
    if request.method == 'POST':
        formulaire = BtestUserCreationsForms(request.POST, request.FILES)

        if formulaire.is_valid():  # Vérifiez d'abord si le formulaire est valide
            try:

                # Récupérer les données validées
                #donnees_validees = formulaire.cleaned_data  # Utilisez cleaned_data au lieu de get_validated_data
                donnees_validees = formulaire.get_validated_data()
                if not donnees_validees:
                    context["form"] = formulaire
                    print("Les données du formulaire n'est pas valide")
                    return render(request, templates, context)
                identifiant = generate_custom_id(donnees_validees['prenoms'], donnees_validees['quartier'])
                nom = donnees_validees['name'],
                prenoms = donnees_validees['prenoms'],
                pays = donnees_validees['pays'],
                quartier = donnees_validees['quartier'],
                email = donnees_validees['email'],
                telephone = donnees_validees['telephone'],
                role = donnees_validees['role'],
                profile_picture = donnees_validees['profile_picture'],
                password = donnees_validees['password'],

                print(nom[0], prenoms, pays, quartier, email, telephone, role, password)
                # Créer l'utilisateur
                user = BTestCustomUser.objects.create_user(
                    name=nom[0],
                    prenoms=prenoms[0],
                    pays=pays[0],
                    quartier=quartier[0],
                    email=email[0],
                    telephone=telephone[0],
                    role=role[0],
                    profile_picture=profile_picture[0],
                    identifiant=identifiant,
                    password=password[0],
                )
                user.email_verification_token = uuid.uuid4()
                user.email_verification_expiration = timezone.now() + timedelta(days=20)
                if user.role == 'USER':
                    user.password_changed = False
                    user.is_premium = False
                    user.is_moderator = False
                    user.is_public = False
                    user.is_active = True
                    user.is_staff = False
                    user.is_superuser = False
                elif user.role == 'MODERATOR':
                    user.is_moderator = True
                    user.is_active = True
                    user.is_staff = True
                    user.is_superuser = False
                elif user.role == "EDITOR":
                    user.is_active = True
                    user.is_staff = True
                elif user.role == 'SECRETOR':
                    user.is_moderator = True
                    user.is_active = True
                    user.is_staff = True
                    user.is_superuser = False
                elif user.role == 'SECOND_SECRETOR':
                    user.is_moderator = True
                    user.is_active = True
                    user.is_staff = True
                    user.is_superuser = False
                elif user.role == 'ADMIN':
                    user.is_active = True
                    user.is_staff = True
                    user.is_superuser = True
                    user.is_premium = True
                    user.is_moderator = True
                    user.is_public = True
                else:
                    messages.error(request, f"Impossible de crée un utilisateur qui n'est pas dans: {user.role}")
                print(donnees_validees)
                print(user)
                #On passe l'USER qui à crée le nouvelle utilisateur
                user.created_by = request.user
                user.save()
                #Envoie d'email d'activation du compte
                try:
                    if send_email_verification(request, user):
                        messages.success(request, "Email envoyé avec succées")
                except Exception as e:
                    messages.error(request, f"Erreur l'email n'a pas pu être envoyé: {e}")


                messages.success(request, 'Compte créé avec succès!')
                return redirect(request.path)

            except Exception as e:
                messages.error(request, f'Erreur lors de l\'inscription: {str(e)}')
                print(f"l'erreur suivante à été rencontrée: {e}")
        else:
            messages.error(request, 'Veuillez corriger les erreurs dans le formulaire.')
            print("corriger les erreurs dans le formulaire.")
            context["form"] = formulaire
    else:
        formulaire = BtestUserCreationsForms()

    context["form"] = formulaire
    return render(request, templates, context)
"""
Vues de gestion de connexion de utilisateurs avec des rôles
"""
def manager_login_page_save(request):
    template = "site/admin/manager_login_page.html"
    context = {'message': 'Bienvenue sur la page de connexion !'}
    # Redirection après connexion réussie
    next_url = request.GET.get('next') or request.POST.get('next')
    if not url_has_allowed_host_and_scheme(next_url, allowed_hosts={request.get_host()}):
        next_url = settings.LOGIN_REDIRECT_URL
    print(" Voici l'url: ", next_url)

    if request.method == 'POST':
        identifiant = request.POST.get('identifiant')
        password = request.POST.get('password')
        print(identifiant, password)
        if not (identifiant and password):
            context['error'] = "Veuillez remplir tous les champs."
            return render(request, template_name=template, context=context)

        # Vérification si l'utilisateur existe
        if CustomUser.objects.filter(identifiant=identifiant).exists():
            print("Ici ca passe.")
            user = authenticate(request, identifiant=identifiant, password=password)
            print(user)
            if user is not None:
                print(f"Bienvenue {user.prenoms} {user.name} {user.email}")
                if user.is_active:
                    login(request, user)
                    print("'L'utilsateur est connecé avec succés")
                    # Stockage des informations utilisateur en session
                    request.session['super_user'] = user.is_superuser
                    request.session['user_identifiant'] = user.identifiant
                    request.session['user_name'] = user.prenoms  # Supposant que 'user' est le champ du pseudo


                    if next_url:
                        return redirect(next_url)
                    return redirect("Bapp:index")  # Redirection vers la page d'accueil
                else:
                    context['error'] = "Votre compte n'est pas activé. Veuillez vérifier votre email."
            else:
                context['error'] = "L'identifiant ou mot de passe est incorrect, veuillez corriger les informations."
        else:
            context['next'] = next_url
            context['error'] = "L'identifiant n'est pas valide, veuillez revoir votre identifiant."
    return render(request, template_name=template, context=context)


def manager_login_page(request):
    template = "site/admin/manager_login_page.html"
    context = {
        'message': 'Bienvenue sur la page de connexion !',
        'next': request.GET.get('next', '')  # Toujours inclure next dans le contexte initial
    }

    # Gestion sécurisée de la redirection
    next_url = request.GET.get('next') or request.POST.get('next', '')
    if not url_has_allowed_host_and_scheme(next_url, allowed_hosts={request.get_host()}):
        next_url = settings.LOGIN_REDIRECT_URL

    if request.method == 'POST':
        identifiant = request.POST.get('identifiant', '').strip()
        password = request.POST.get('password', '').strip()
        context['next'] = next_url  # Maintien de next dans le contexte après POST

        # Validation des champs
        if not identifiant or not password:
            context['error'] = "Veuillez remplir tous les champs."
            return render(request, template, context)

        # Authentification
        user = authenticate(request, identifiant=identifiant, password=password)

        if user is None:
            # Message générique pour éviter les fuites d'information
            context['error'] = "Identifiants incorrects username ou mot de passe incorrect. Veuillez réessayer."
            return render(request, template, context)

        if not user.is_active:
            context['error'] = "Votre compte n'est pas activé. Veuillez vérifier votre email."
            return render(request, template, context)

        # Connexion réussie
        login(request, user)

        # Stockage minimal des informations en session
        request.session.update({
            'super_user': user.is_superuser,
            'user_identifiant': user.identifiant,
            'user_name': user.prenoms,
        })
        print(f"{user.prenoms} s'est connecté avec succés !")
        # Redirection sécurisée
        return redirect(next_url) if next_url else redirect("Bapp:index")

    return render(request, template, context)

def logout_view(request):
    #template_name = "site/admin/manager_login_page.html"
    logout(request)
    messages.success(request, f"Veillez vous reconnecter ici ")
    return redirect('Bapp:manager_login_page')

def data_recup(request):
    templates = "site/data.html"
    context = {}
    table_name = connection.ops.quote_name('Bapp_btestcustomuser')
    query = f"SELECT prenoms FROM {table_name} WHERE quartier = %s;"
    with connection.cursor() as cursor:
        cursor.execute(query, ['Leyssare'])

        row = cursor.fetchall()
        print(row)
        context["data"] = row
    return render(request, templates, context)


def enregistrer_participation(request):
    tamplate = 'site/participations/annual_participation.html'
    context = {}
    utilisateur_trouve = None

    if 'recherche' in request.GET:
        query = request.GET.get('recherche')
        utilisateur_trouve = BTestCustomUser.objects.filter(
            Q(identifiant__icontains=query) |
            Q(prenoms__icontains=query)
        ).first()
        context['utilisateur_trouve'] = utilisateur_trouve

    if request.method == 'POST' and 'user_id' in request.POST:
        form = ParticipationAnnuelForm(request.POST)
        user_id = request.POST.get('user_id')

        if form.is_valid():
            try:
                with transaction.atomic():  # Utiliser une transaction pour garantir l'intégrité des données
                    # Créer l'instance de participation sans la sauvegarder
                    participation = form.save(commit=False)

                    # Assigner l'ID du participant
                    participation.participant_id = user_id

                    # Récupérer le montant du formulaire
                    montant = form.cleaned_data.get('montant_participation')
                    participation.montant_participation = montant

                    # Sauvegarder la participation
                    participation.save()

                    # Message de succès
                    messages.success(
                        request,
                        f"Participation de {montant} FGN enregistrée avec succès!"
                    )

                    # Redirection vers la page d'index
                    return redirect('Bapp:index')

            except Exception as e:
                # Log l'erreur pour le débogage
                print(f"Erreur lors de l'enregistrement : {str(e)}")

                # Message d'erreur pour l'utilisateur
                messages.error(
                    request,
                    "Une erreur s'est produite lors de l'enregistrement de la participation."
                )
        else:
            # Afficher les erreurs de validation du formulaire
            for field, errors in form.errors.items():
                for error in errors:
                    print(f"Erreur dans le champ {field}: {error}")
                    messages.error(request, f"Erreur dans le champ {field}: {error}")

    context['recherche_form'] = RechercheUserForm()
    context['participation_form'] = ParticipationAnnuelForm()

    return render(request, template_name=tamplate, context=context)
def users_participations(request):
    template = "site/participations/participations.html"
    context = {}
    context["message"] = "Salam à toutes les utilisateurs !"
    print('debut de la fonction enregistrer_participation')
    utilisateur_trouve = None
    if 'recherche' in request.GET:
        query = request.GET.get('recherche')
        utilisateur_trouve = BTestCustomUser.objects.filter(
            Q(identifiant_id__icontains=query) |
            Q(prenoms__icontains=query)
        ).first()
        context['utilisateur_trouve'] = utilisateur_trouve
        print(utilisateur_trouve)
    else:
        print("User not found. Searching for all users instead.")

    if request.method == 'POST' and 'user_id' in request.POST:
        form = ParticipationAnnuelForm(request.POST)
        user_id = request.POST.get('user_id')

        if form.is_valid():
            try:
                with transaction.atomic():  # Utiliser une transaction pour garantir l'intégrité des données
                    # Créer l'instance de participation sans la sauvegarder
                    participation = form.save(commit=False)

                    # Assigner l'ID du participant
                    participation.participant_id = user_id

                    # Récupérer le montant du formulaire
                    montant = form.cleaned_data.get('montant_participation')
                    participation.montant_participation = montant

                    # Sauvegarder la participation
                    participation.save()

                    # Message de succès
                    messages.success(
                        request,
                        f"Participation de {montant} FGN enregistrée avec succès!"
                    )

                    # Redirection vers la page d'index
                    return redirect('Bapp:index')

            except Exception as e:
                # Log l'erreur pour le débogage
                print(f"Erreur lors de l'enregistrement : {str(e)}")

                # Message d'erreur pour l'utilisateur
                messages.error(
                    request,
                    "Une erreur s'est produite lors de l'enregistrement de la participation."
                )
        else:
            # Afficher les erreurs de validation du formulaire
            for field, errors in form.errors.items():
                for error in errors:
                    print(f"Erreur dans le champ {field}: {error}")
                    messages.error(request, f"Erreur dans le champ {field}: {error}")

    context['recherche_form'] = RechercheUserForm()
    context['participation_form'] = ParticipationAnnuelForm()
    return render(request, template_name=template, context=context)

"""
Creation des fonctions de gestion de participations
"""

def participation_page(request):
    template = "site/participations/index_participations.html"
    context = {'message': 'Bienvenue sur la page des participations !'}
    return render(request, template_name=template, context=context)

def search_user(request):
    form = RechercheUserForm(request.GET)
    if form.is_valid():
        query = form.cleaned_data['recherche']
        users = BTestCustomUser.objects.filter(identifiant__icontains=query) | BTestCustomUser.objects.filter(prenoms__icontains=query)
        results = [{'id': u.id, 'name': f'{u.prenoms} ({u.identifiant})'} for u in users]
        print(results)
        return JsonResponse({'results': results})
    return JsonResponse({'errors': form.errors}, status=400)

@csrf_exempt
def submit_participation(request):
    template = "site/participations/index_participations.html"
    context = {}
    if request.method == "POST":
        form = ParticipationAnnuelForm(request.POST)
        if form.is_valid():
            user = get_object_or_404(BTestCustomUser, id=form.cleaned_data['user_id'])
            montant_participation = form.cleaned_data['montant_participation']
            type_part = request.POST.get("participation_type")

            motif_participation = request.POST.get("motif_participation")

            nom_donateur = request.POST.get("nom_donateur")
            prenom_donateur = request.POST.get("prenom_donateur")
            motif_don = request.POST.get("motif_don")

            print(type_part)
            print(user)
            model_map = {
                "annuelle": ParticipationAnnual,
                "occasionnelle": ParticipationOccasionnelle,
                "don": Dons
            }

            model = model_map.get(type_part)
            print(f"Le type de participation est {type_part} et le model est {model}")
            if model:
                if model == "annuelle":
                    model.objects.create(participant_id=user, montant_participation=montant_participation)
                    return JsonResponse({"success": True})
                elif model == "occasionnelle":
                    model.objects.create(participant_id=user, motif_participation=motif_participation, montant_participation=montant_participation)
                    return JsonResponse({"success": True})
                elif model == "don":
                    model.objects.create(participant_id=user, nom_donateur=nom_donateur, prenom_donateur=prenom_donateur, motif_don=motif_don, montant_don=montant_participation)
                    return JsonResponse({"success": True})
                else:
                    return JsonResponse({"success": False, "error": "Type de participation invalide."}, status=400)
            else:
                context = {"form": model}
                return render(request, template_name=template, context=context)
        return render(request, template_name=template, context=context)
    return JsonResponse({"success": False, "error": "Méthode non autorisée"}, status=405)






@require_GET
def recherche_utilisateurs(request):
    try:
        # Récupérer le terme de recherche, term est un clé defini dans le fichier js
        search_term = request.GET.get('term', '').strip()

        # Logging pour debug
        print(f"Terme de recherche reçu: {search_term}")

        if len(search_term) < 2:
            return JsonResponse({
                'status': 'error',
                'message': 'Le terme de recherche doit contenir au moins 2 caractères',
                'results': []
            })

        # Effectuer la recherche du nom ou identifiant d'un utilisateur déjá inscrit
        users = CustomUser.objects.filter(
            Q(prenoms__icontains=search_term) |
            Q(identifiant__icontains=search_term)
        )[:5]  # Limiter à 5 résultats
        print(" Voci l'utilsateur trouvé ",users)

        # Formater les résultats
        results = [{
            'id': user.id,
            'prenom': user.prenoms,
            'identifiant': user.identifiant
        } for user in users]
        print(results)
        return JsonResponse({
            'status': 'success',
            'results': results
        })

    except Exception as e:
        print(f"Erreur lors de la recherche: {str(e)}")
        return JsonResponse({
            'status': 'error',
            'message': str(e),
            'results': []
        }, status=500)

def participation_view_save(request):
    template = "site/participations/test_participations.html"
    context = {
        'search_form': UserSearchForm(),
        'form1': ParticipationAnnuelForm(),
        'form2': ParticipationOccasionnelleForm(),
        'form3': DonsForm(),
    }

    if request.method == 'POST':
        form_type = request.POST.get('user_type')
        user_id = request.POST.get('user_id')

        formulaire = None
        selected_user = None
        #Preparation de la reponse JSON
        response_data = {
            'status': 'error',
            'errors': {},
            'form_type': form_type
        }

        print(form_type)
        print(f"Le type de participation est {form_type} l'utilisateur est {user_id}")

        if form_type in ['user1', 'user2']:
            if not user_id:
                response_data['errors']["user_id"] = "Utilisateur non sélectionné"
                return JsonResponse(response_data)

            try:
                selected_user = CustomUser.objects.get(id=user_id)
            except CustomUser.DoesNotExist:
                return JsonResponse({
                    'status': 'error',
                    'errors': {'user_id': 'Utilisateur non trouvé'}
                })

            form_data = request.POST.copy()
            form_data['user_id'] = user_id

            print(form_data)

            if form_type == 'user1':
                formulaire = ParticipationAnnuelForm(form_data)
                if formulaire.is_valid():
                    # Validation personnalisée
                    try:
                        # Création de l'objet Model1
                        ParticipationAnnual.objects.create(
                            participant_id=selected_user,
                            montant_participation=formulaire.cleaned_data['montant_participation']
                        )
                        print(f"participation {form_type} enregistré avec succés")
                        return JsonResponse({
                            'status': 'success',
                            'message': 'Formulaire enregistré avec succès'
                        })
                    except Exception as e:
                        print(f"Erreur lors de l'enregistrement: {str(e)}")
                        return JsonResponse({
                            'status': 'error',
                            'errors': str(e)
                        })

                else:
                    error = context.get("form1")
                    print(error)
                    return render(request, template_name=template, context=context)
            elif form_type == 'user2':
                formulaire = ParticipationOccasionnelleForm(form_data)
                if formulaire.is_valid():
                    print(formulaire.cleaned_data)
                    montant_participation = formulaire.cleaned_data['montant_participation']
                    motif_participation = formulaire.cleaned_data['motif_participation']
                    print(montant_participation, "--", motif_participation)
                    try:
                        ParticipationOccasionnelle.objects.create(
                            participant_id=selected_user,
                            montant_participation=montant_participation,
                            motif_participation=motif_participation
                        )
                        print(f"participation {form_type} enregistré avec succés")
                        return JsonResponse({
                            'status': 'success',
                            'message': 'Formulaire enregistré avec succès'
                        })
                    except Exception as e:

                        print(f"Erreur lors de l'enregistrement: {str(e)}")
                        return JsonResponse({
                            'status': 'error',
                            'errors': str(e)
                        })
                else:
                    context['error'] = formulaire.errors
                    for error in context.values():
                        print(error)
                    return render(request, template_name=template, context=context)
        elif form_type == 'user3':
            formulaire = DonsForm(request.POST)
            if formulaire.is_valid():
                print(formulaire.cleaned_data)
                try:
                    Dons.objects.create(
                        nom=formulaire.cleaned_data['nom'],
                        prenom=formulaire.cleaned_data['prenom'],
                        montant_don=formulaire.cleaned_data['montant_don'],
                        motif_don=formulaire.cleaned_data['motif_don']

                    )
                    print(f"participation {form_type} enregistré avec succés")
                    return JsonResponse({
                        'status': 'success',
                        'message': 'Formulaire enregistré avec succès'
                    })
                except Exception as e:
                    print(f"Erreur lors de l'enregistrement: {str(e)}")
                    return JsonResponse({
                        'status': 'error',
                        'errors': str(e)
                    })
            else:
                context['error'] = formulaire.errors
                print(formulaire.errors)
                return render(request, template_name=template, context=context)
        if form_type is None:
            context['error'] = "Le type de participation est invalide."
            print("Le type de participation est invalide.")
            return JsonResponse({
                'status': 'error',
                'errors': {'user_type': 'Type utilisateur invalide'}
            })
        context['form'] = formulaire  # Pour afficher les erreurs

    return render(request, template_name=template, context=context)
"""
    if request.method == 'POST':
        user_type = request.POST.get('user_type')
        user_id = request.POST.get('user_id')

        selected_user = None
        form = None

        if user_type in ['user1', 'user2']:
            if not user_id:
                return JsonResponse({
                    'status': 'error',
                    'errors': {'user_id': 'Utilisateur non sélectionné'}
                })

            try:
                selected_user = CustomUser.objects.get(id=user_id)
            except CustomUser.DoesNotExist:
                return JsonResponse({
                    'status': 'error',
                    'errors': {'user_id': 'Utilisateur non trouvé'}
                })

            form_data = request.POST.copy()
            form_data['id_user'] = user_id

            if user_type == 'user1':
                form = ParticipationAnnuelForm(form_data)
            else:
                form = ParticipationOccasionnelleForm(form_data)
        elif user_type == 'user3':
            form = DonsForm(request.POST)

        if form is None:
            return JsonResponse({
                'status': 'error',
                'errors': {'user_type': 'Type utilisateur invalide'}
            })

        if form.is_valid():
            participation = form.save(commit=False)
            if user_type in ['user1', 'user2']:
                participation.id_user = selected_user
            participation.save()
            return JsonResponse({
                'status': 'success',
                'message': 'Formulaire enregistré avec succès'
            })
        else:
            return JsonResponse({
                'status': 'error',
                'errors': form.errors
            }) """
"""
On appelle la fonction decorative défini dans le fichier permission.py 
pour verifier si l'utilisateur a le droit d'accès sur le view """

#Peut ajouter des participations
@has_secretor_role(["ADMIN","SECRETOR", "MODERATOR"])
def participation_view(request):
    template = "site/participations/test_participations.html"
    context = {
        'search_form': UserSearchForm(),
        'form1': ParticipationAnnuelForm(),
        'form2': ParticipationOccasionnelleForm(),
        'form3': DonsForm(),
    }

    if request.method == 'POST':
        form_type = request.POST.get('user_type')
        user_id = request.POST.get('user_id')
        #On verifie si la requete vien d'AJAX
        is_ajax = request.headers.get('x-requested-with') == 'XMLHttpRequest'
        if is_ajax:
            print("La requete est AJAX")
        else:
            print("La requete n'est pas AJAX")

        # Préparation de la réponse JSON
        response_data = {
            'status': 'error',
            'errors': "",
            'form_type': form_type
        }

        if form_type in ['user1', 'user2']:
            if not user_id:
                response_data['errors']['user_id'] = 'Utilisateur non sélectionné'
                return JsonResponse(response_data)
            try:
                selected_user = CustomUser.objects.get(id=user_id)
                form_data = request.POST.copy()
                form_data['user_id'] = user_id

                if form_type == 'user1':
                    formulaire = ParticipationAnnuelForm(form_data)
                    if formulaire.is_valid():
                        try:
                            ParticipationAnnual.objects.create(
                                created_by=request.user,
                                participant_id=selected_user,
                                montant_participation=formulaire.cleaned_data['montant_participation']
                            )

                            if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                                return JsonResponse({
                                    'status': 'success',
                                    'message': 'Participation annuelle enregistrée avec succès',
                                    'form_type': form_type
                                })
                            else:
                                messages.success(request, 'Participation annuelle enregistrée avec succès')
                                return redirect(request.path)

                        except Exception as e:
                            if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                                response_data['errors']['db_error'] = str(e)
                                return JsonResponse(response_data)
                            else:
                                messages.error(request, f"Une erreur s'est produite : {str(e)}")
                                return redirect(request.path)
                    else:
                        if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                            errors = formulaire.errors.get_json_data()
                            response_data['errors'] = errors
                            return JsonResponse(response_data)
                        else:
                            for field, error_list in formulaire.errors.items():
                                for error in error_list:
                                    messages.error(request, f"{field}: {error}")
                            return redirect(request.path)

                elif form_type == 'user2':
                    formulaire = ParticipationOccasionnelleForm(form_data)
                    if formulaire.is_valid():
                        try:
                            ParticipationOccasionnelle.objects.create(
                                created_by=request.user,
                                participant_id=selected_user,
                                montant_participation=formulaire.cleaned_data['montant_participation'],
                                motif_participation=formulaire.cleaned_data['motif_participation']
                            )

                            if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                                return JsonResponse({
                                    'status': 'success',
                                    'message': 'Participation occasionnelle enregistrée avec succès'
                                })
                            else:
                                messages.success(request, 'Participation occasionnelle enregistrée avec succès')
                                return redirect(request.path)

                        except Exception as e:
                            if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                                response_data['errors']['db_error'] = str(e)
                                return JsonResponse(response_data)
                            else:
                                messages.error(request, f"Une erreur s'est produite : {str(e)}")
                                return redirect(request.path)
                    else:
                        if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                            errors = formulaire.errors.get_json_data()
                            response_data['errors'] = errors
                            return JsonResponse(response_data)
                        else:
                            for field, error_list in formulaire.errors.items():
                                for error in error_list:
                                    messages.error(request, f"{field}: {error}")
                            return redirect(request.path)

            except CustomUser.DoesNotExist:
                if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                    response_data['errors']['user_id'] = "Cet utilisateur n'existe pas."
                    return JsonResponse(response_data)
                else:
                    messages.error(request, "Cet utilisateur n'existe pas.")
                    return redirect(request.path)
        elif form_type == 'user3':
            formulaire = DonsForm(request.POST)
            if formulaire.is_valid():
                try:
                    #Dons.objects.create(**formulaire.cleaned_data)
                    form = formulaire.save(commit=False)
                    form.created_by = request.user
                    form.save()
                    if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                        return JsonResponse({
                            'status': 'success',
                            'message': 'Dons enregistrée avec succès'
                        })
                    else:
                        messages.success(request, 'Dons enregistrée avec succès')
                        return redirect(request.path)
                except Exception as e:
                    if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                        response_data['errors']['db_error'] = str(e)
                        return JsonResponse(response_data)
                    else:
                        messages.error(request, f"Une erreur s'est produite : {str(e)}")
                        return redirect(request.path)

            else:
                if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                    errors = formulaire.errors.get_json_data()
                    response_data['errors'] = errors
                    return JsonResponse(response_data)
                else:
                    for field, error_list in formulaire.errors.items():
                        for error in error_list:
                            messages.error(request, f"{field}: {error}")
                    return redirect(request.path)
        else:
            if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                response_data['errors']['form_type'] = 'Type de formulaire invalide'
                return JsonResponse(response_data)
            else:
                messages.error(request, "Type de formulaire invalide")
                return redirect(request.path)

    return render(request, template_name=template, context=context)

#Peut ajouter des dépenses
@has_secretor_role([ "ADMIN", "SECOND_SECRETOR" "MODERATOR" ])
@csrf_exempt
def add_depenses_view(request):
    template = "site/depenses/depenses.html"
    context = {"message": "Bienvenue sur la page d'ajout de depenses"}

    messages = {
        'success': {},
        'errors': {},
        'status': False
    }

    if request.method == 'POST':
        form = AddDepensesForm(request.POST)
        if form.is_valid():
            #Le nom de la personne chargé d'inscrire la dépense
            selected_user = request.user
            print(selected_user)
            try:
                AddDepenses.objects.create(
                    created_by=selected_user,
                    montant_depense=form.cleaned_data["montant_depense"],
                    motif_depense=form.cleaned_data['motif_depense']
                )
                messages['success'] = {
                    'global': 'Dépense enregistrée avec succès',
                    'montant': f"Montant de {form.cleaned_data["montant_depense"]} FGN enregistré",
                    'motif': 'Motif: ' + form.cleaned_data['motif_depense']
                }
                messages['status'] = True
            except Exception as e:
                messages['errors']['global'] = f"L'Erreur {e} est survenue lors de l'enregistrement de la dépense"
        else:
            # Récupération des erreurs spécifiques à chaque champ
            for field, field_errors in form.errors.items():
                messages['errors'][field] = [strip_tags(str(error)) for error in field_errors]
                print(messages['errors'])

            if messages['errors']:
                messages['errors']['global'] = "Veuillez corriger les erreurs ci-dessous"

    if request.method == 'GET':
        form = AddDepensesForm()
        context['form'] = form

    if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
        return JsonResponse(messages)


    return render(request, template_name=template, context=context)

# Methodes de recuperations de données.
def get_data(request):
    template = "site/client/data/show_data.html"
    context = {}
    depenses = AddDepenses.objects.all().values()
    print(depenses)

    context['donnees'] = depenses
    return render(request, template_name=template, context=context)


def gestion_totaux(request):
    template = "site/client/data/bilan_totaux.html"
    context = {}
    try:
        with connection.cursor() as cursor:
            cursor.execute(
                "SELECT * FROM view_bilan_totaux"
            )
            row = cursor.fetchall()
            columns = [col[0] for col in cursor.description]
            resultat = [dict(zip(columns, row)) for row in row]
            context['resultat'] = resultat
    except Exception as e:
        context['error'] = f" L'erreure suivate s'est produit : {str(e)}"
    return  render(request, template_name=template, context=context)

@can_edit_article(['ADMIN','EDITOR', "MODERATOR"])
def editorial_view(request):
    if request.method == 'POST':
        form = EditorialCommunityForm(request.POST, request.FILES)
        if form.is_valid():
            try:
                form_save = form.save(commit=False)
                form_save.author = request.user.prenoms
                form_save.save()

                if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                    return JsonResponse({
                        'success': "L'article a été enregistré avec succès!"
                    })
                return redirect(request.path)
            except Exception as e:
                error_msg = f"Erreur lors de l'enregistrement : {str(e)}"
                if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                    return JsonResponse({
                        'errors': error_msg
                    }, status=400)
                # Gestion non-AJAX...
        else:
            # Formatage des erreurs pour la réponse AJAX
            errors = {}
            for field, error_list in form.errors.items():
                errors[field] = error_list

            if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                return JsonResponse({
                    'errors': errors
                }, status=400)
            # Gestion non-AJAX...

    else:
        form = EditorialCommunityForm()

    context = {'form': form}
    return render(request, "site/editions/editions.html", context)

def editorial_view_save(request):
    template = "site/editions/editions.html"
    context = {}
    messages = {
        'success': {},
        'errors': {},
        'status': False
    }

    if request.method == 'POST':
        form = EditorialCommunityForm(request.POST, request.FILES)
        if form.is_valid():
            selected_user = request.user.prenoms
            print("Le formulaire est valide")

            try:
                form_save = form.save(commit=False)
                author = selected_user
                form_save.author = author
                form_save.save()

                messages['status'] = True
                context['success'] = "Formulaire enregistré avec succés. "
                print(context['message'])
                return redirect(request.path)
            except Exception as e:
                context['errors'] = f"L'Erreur {e} est survenue lors de l'enregistrement de l'article"
    else:
        print("Le formulaire n'est pas valide")
        form = EditorialCommunityForm()
        context['form'] = form
    return render(request, template_name=template, context=context)

def dashboard_view(request):
    template = 'Dashboard/dashboard.html'
    context = {}
    return render(request, template_name=template, context=context)
@login_required
def dashboard_view2(request):
    template = 'Dashboard/dashboard2.html'
    context = {}
    if not request.user.is_authenticated:
        return redirect('Bapp:manager_login_page')
    print(request.user.role, request.user.profile_picture)
    context['user'] = request.user
    return render(request, template_name=template, context=context)


def pdf_listings(request):
    print(request.user.prenoms, request.user.role)
    if not request.user.is_authenticated:
        raise PermissionDenied

    template = 'site/documents/pdf_listings.html'
    context = {}
    success = False
    auteur = request.user.prenoms

    # Si l'utilisateur est admin, on génère les deux types de documents
    if request.user.role == 'ADMIN':
        # Génération de la liste des utilisateurs
        title = "Liste des utilisateurs"
        description = "Liste des membres de Missidhé Bourou"
        query = "SELECT * FROM bourou_users_list"
        headers = ['Identifiant', 'Prenoms', 'Quartier', 'Telephone', 'Role', 'Pays']
        document_type = 'USER_LIST'
        #on recupere l'etat et le path retourner dans generate_pdf
        vrais, document_path = generate_pdf(title, description, auteur, query, headers)
        if vrais and document_path:
            # Création de l'entrée dans la base de données
            if save_pdf_on_model(description, document_path, document_type, request, title):

                messages.success(request, 'Le document PDF a été généré avec succès')
                success = True
            else:
                messages.error(request, 'Erreur lors de la génération du PDF')
                success = False

        # Génération du bilan financier
        document_type = 'BILAN_CAISSE'
        title = "Total montant en FGN"
        description = "Le montant total disponible dans la caisse Missidhé Bourou"
        query = "SELECT * FROM view_bilan_totaux"
        headers = ['Montant cotisation annuel', 'Montant cotisation occasionnel', 'Montant dons', 'Total montants', 'Mise à jour']

        vrais, document_path = generate_pdf(title, description, auteur, query, headers)
        if vrais and document_path:
            # Création de l'entrée dans la base de données
            if save_pdf_on_model(description, document_path, document_type, request, title):

                messages.success(request, 'Le document PDF a été généré avec succès')
                success = True
            else:
                messages.error(request, 'Erreur lors de la génération du PDF')
                success = False
        #Pour genererer un doument pour les depenses effectués
        document_type = 'DEPENSES'
        title = "Dépenses effectuées"
        description = "Les dépenses effectuées ce dernier mois"
        query = "SELECT * FROM liste_depense_view"
        headers = ['Dépenses', 'Motif dépense', 'Mise à jour',]

        vrais, document_path = generate_pdf(title, description, auteur, query, headers)
        if vrais and document_path:
            # Création de l'entrée dans la base de données
            if save_pdf_on_model(description, document_path, document_type, request, title):

                messages.success(request, 'Le document PDF a été généré avec succès')
                success = True
            else:
                messages.error(request, 'Erreur lors de la génération du PDF')
                success = False
            # Pour les cotisations occasionnelle
            # Pour genererer un doument pour les depenses effectués
            document_type = 'OCCASIONNAL_COTISATION'
            title = "Cotisations occasionnelle"
            description = "La liste des personnes qui ont participé à cette cotisation occasionnelle"
            query = "SELECT * FROM liste_participation_occasionnelle_view"
            headers = ['Identifiants', 'Prénoms', 'Montant', 'Motif participations', 'Mise à jour', ]
            vrais, document_path = generate_pdf(title, description, auteur, query, headers)
            if vrais and document_path:
                # Création de l'entrée dans la base de données
                if save_pdf_on_model(description, document_path, document_type, request, title):
                    messages.success(request, 'Le document PDF a été généré avec succès')
                    success = True
                else:
                    messages.error(request, 'Erreur lors de la génération du PDF')
                    success = False
            # Pour les dons
            document_type = 'DONS'
            title = "Dons re¢u"
            description = "Les donations envers Missidhé Bourou re¢u "
            query = "SELECT * FROM liste_don_view"
            headers = ['Noms Donateurs', 'Prénoms', 'Montant don', 'Motif don', 'Mise à jour', ]
            vrais, document_path = generate_pdf(title, description, auteur, query, headers)
            if vrais and document_path:
                # Création de l'entrée dans la base de données
                if save_pdf_on_model(description, document_path, document_type, request, title):
                    messages.success(request, 'Le document PDF a été généré avec succès')
                    success = True
                else:
                    messages.error(request, 'Erreur lors de la génération du PDF')
                    success = False
        document_type = 'ANNUAL_COTISATION'
        title = "Cotisation annuelle"
        description = "La liste des cotisations annuelle accomplie par les membres"
        query = "SELECT * FROM liste_participation_annuel_view"
        headers = ['Identifiants', 'Prénoms','Montant participations', 'Mise à jour', ]

        vrais, document_path = generate_pdf(title, description, auteur, query, headers)
        if vrais and document_path:
            # Création de l'entrée dans la base de données
            if save_pdf_on_model(description, document_path, document_type, request, title):

                messages.success(request, 'Le document PDF a été généré avec succès')
                success = True
            else:
                messages.error(request, 'Erreur lors de la génération du PDF')
                success = False

        document_type = 'INFO'
        title = "Publications"
        description = "Annonces faits aux membres de Missidhé Bourou"
        query = "SELECT * FROM liste_publication_view"
        headers = ['Titre', 'Publications', 'Mise à jour', ]

        vrais, document_path = generate_pdf(title, description, auteur, query, headers)
        if vrais and document_path:
            # Création de l'entrée dans la base de données
            if save_pdf_on_model(description, document_path, document_type, request, title):

                messages.success(request, 'Le document PDF a été généré avec succès')
                success = True
            else:
                messages.error(request, 'Erreur lors de la génération du PDF')
                success = False
        if success:
            return redirect('Bapp:documents_pdf')
        else:
            return redirect('Bapp:documents_pdf')


    # Pour les autres rôles (MODERATOR ou SECRETOR)
    elif request.user.role == 'MODERATOR':
        title = "Liste des utilisateurs"
        description = "Liste des membres de Missidhé Bourou"
        query = "SELECT * FROM bourou_users_list"
        headers = ['Identifiant', 'Prenoms', 'Quartier', 'Telephone', 'Role', 'Pays']
        document_type = 'USER_LIST'
        #on recupere l'etat et le path retourner dans generate_pdf
        vrais, document_path = generate_pdf(title, description, auteur, query, headers)
        if vrais and document_path:
            # Création de l'entrée dans la base de données
            if save_pdf_on_model(description, document_path, document_type, request, title):

                messages.success(request, 'Le document PDF a été généré avec succès')
                success = True
            else:
                messages.error(request, 'Erreur lors de la génération du PDF')
                success = False
        if success:
            return redirect('Bapp:documents_pdf')
        else:
            return redirect('Bapp:documents_pdf')

    elif request.user.role == "SECOND_SECRETOR":
        # Pour genererer un doument pour les depenses effectués
        document_type = 'DEPENSES'
        title = "Dépenses effectuées"
        description = "Les dépenses effectuées ce dernier mois"
        query = "SELECT * FROM liste_depense_view"
        headers = ['Dépenses', 'Motif dépense', 'Mise à jour', ]

        vrais, document_path = generate_pdf(title, description, auteur, query, headers)
        if vrais and document_path:
            # Création de l'entrée dans la base de données
            if save_pdf_on_model(description, document_path, document_type, request, title):

                messages.success(request, 'Le document PDF a été généré avec succès')
                success = True
            else:
                messages.error(request, 'Erreur lors de la génération du PDF')
                success = False
        if success:
            return redirect('Bapp:documents_pdf')
        else:
            return redirect('Bapp:documents_pdf')

    elif request.user.role == "SECRETOR":
        # Genérations de plusieurs document par le secreteur
        success = False
        document_type = 'ANNUAL_COTISATION'
        title = "Cotisation annuelle"
        description = "La liste des cotisations annuelle accomplie par les membres"
        query = "SELECT * FROM liste_participation_annuel_view"
        headers = ['Identifiants', 'Prénoms','Montant participations', 'Mise à jour', ]

        vrais, document_path = generate_pdf(title, description, auteur, query, headers)
        if vrais and document_path:
            # Création de l'entrée dans la base de données
            if save_pdf_on_model(description, document_path, document_type, request, title):

                messages.success(request, 'Le document PDF a été généré avec succès')
                success = True
            else:
                messages.error(request, 'Erreur lors de la génération du PDF')
                success = False

        #Pour les cotisations occasionnelle
        # Pour genererer un doument pour les depenses effectués
        document_type = 'OCCASIONNAL_COTISATION'
        title = "Cotisations occasionnelle"
        description = "La liste des personnes qui ont participé à cette cotisation occasionnelle"
        query = "SELECT * FROM liste_participation_occasionnelle_view"
        headers = ['Identifiants', 'Prénoms', 'Montant', 'Motif participations', 'Mise à jour', ]
        vrais, document_path = generate_pdf(title, description, auteur, query, headers)
        if vrais and document_path:
            # Création de l'entrée dans la base de données
            if save_pdf_on_model(description, document_path, document_type, request, title):
                messages.success(request, 'Le document PDF a été généré avec succès')
                success = True
            else:
                messages.error(request, 'Erreur lors de la génération du PDF')
                success = False
        #Pour les dons
        document_type = 'DONS'
        title = "Dons re¢u"
        description = "Les donations envers Missidhé Bourou re¢u "
        query = "SELECT * FROM liste_don_view"
        headers = ['Noms Donateurs', 'Prénoms', 'Montant don', 'Motif don', 'Mise à jour', ]
        vrais, document_path = generate_pdf(title, description, auteur, query, headers)
        if vrais and document_path:
            # Création de l'entrée dans la base de données
            if save_pdf_on_model(description, document_path, document_type, request, title):
                messages.success(request, 'Le document PDF a été généré avec succès')
                success = True
            else:
                messages.error(request, 'Erreur lors de la génération du PDF')
                success = False
        document_type = 'BILAN_CAISSE'
        # Génération du bilan financier
        title = "Total montant en FGN"
        description = "Le montant total disponible dans la caisse Missidhé Bourou"
        query = "SELECT * FROM view_bilan_totaux"
        headers = ['Montant cotisation annuel', 'Montant cotisation occasionnel', 'Montant dons', 'Total montants',
                   'Mise à jour']

        vrais, document_path = generate_pdf(title, description, auteur, query, headers)
        if vrais and document_path:
            # Création de l'entrée dans la base de données
            if save_pdf_on_model(description, document_path, document_type, request, title):

                messages.success(request, 'Le document PDF a été généré avec succès')
                success = True
            else:
                messages.error(request, 'Erreur lors de la génération du PDF')
                success = False
        if success:
            return redirect('Bapp:documents_pdf')
        else:
            return redirect('Bapp:documents_pdf')
    elif request.user.role == "EDITOR":
        # Pour genererer un doument pour les depenses effectués
        document_type = 'INFO'
        title = "Publications"
        description = "Annonces faits aux membres de Missidhé Bourou"
        query = "SELECT * FROM liste_publication_view"
        headers = ['Titre', 'Publications', 'Mise à jour', ]

        vrais, document_path = generate_pdf(title, description, auteur, query, headers)
        if vrais and document_path:
            # Création de l'entrée dans la base de données
            if save_pdf_on_model(description, document_path, document_type, request, title):

                messages.success(request, 'Le document PDF a été généré avec succès')
                success = True
            else:
                messages.error(request, 'Erreur lors de la génération du PDF')
                success = False
        if success:
            return redirect('Bapp:documents_pdf')
        else:
            return redirect('Bapp:documents_pdf')
    else:

        messages.error(request, "Vous n'avez pas de role dans l'équipe de managers")
    return render(request, template_name=template, context=context)

#On sauvegarde les données dans le model PDFManager
def save_pdf_on_model(description, document_path, document_type, request, title):
    try:
        pdf_doc = PDFManager.objects.create(
            title=title,
            description=description,
            document_type=document_type,
            created_by=request.user
        )
        # Ouverture et sauvegarde du fichier
        with open(document_path, 'rb') as pdf_file:
            # File() prend comme paramètre un fichier ouvert en mode binaire
            # On sauvegarde le pdf dans le model
            pdf_doc.file.save(
                os.path.basename(document_path),  # Nom du fichier
                File(pdf_file),  # Objet File qui wrap le fichier
                save=True  # Sauvegarde automatique du modèle
            )
        # Suppression du fichier temporaire
        os.remove(document_path)
        return True
    except Exception as e:
        return False

#Générer un fichier pdf
def generate_pdf(title, description, auteur, query, headers):
    # On instentie ici la classe PDFGenerator avec ses attributs
    pdf_creator = PDFGenerator(title=title, auteur=auteur, paragraph=description)
    #On recuère la base données
    requete = request_database(query)
    #on s'assure que la requete s'est bien passé
    if requete["success"]:
        # Traiter les données
        data = requete["data"]
        print(f"Succès : {requete['message']}")

        #on recupère le chemin où le document est stocké, et on passe les données dont la fonction a besoin pour créer le PDF
        # Utilisation
        try:
            document_path = pdf_creator.pdfs_file_generator(data, headers)
            validated_path = verify_pdf_file(document_path)
            print(f"Répertoire validé : {validated_path}")
            # on retourne true et le path
            return True, validated_path
        except (TypeError, ValueError, PermissionError) as e:
            print(f"Erreur lors de la vérification du fichier pdf : {e}")
        #La création du fichier pdf a échoué
        requete['success'] = False
        return requete['success']
    else:
        # Gérer l'erreur
        print(f"Erreur : {requete['message']}")
        return requete['message']


def request_database(query):
    try:
        with connection.cursor() as cursor:
            cursor.execute(query)
            return_query = cursor.fetchall()
            # Transformation des données après fetchall()
            modified_data = []
            if not return_query:  # Vérifie si les données sont vides
                return {"success": False, "message": "Aucune donnée trouvée", "data": None}
            for row in return_query:
                row_list = list(row)
                # Parcourir chaque élément du row pour trouver les datetime
                for i, value in enumerate(row_list):
                    if isinstance(value, datetime):  # Vérifie si le champ est de type datetime
                        row_list[i] = value.date().strftime('%d/%m/%Y')   # Convertit en date

                modified_data.append(tuple(row_list))
            return {"success": True, "message": "Données récupérées avec succès", "data": modified_data}

    except Exception as e:
        # Log l'erreur pour le débogage
        print('Une erreur s\'est produite : ', e)
        return {
            "success": False,
            "message": f"Une erreur est survenue: {str(e)}",
            "error": str(e)
        }


def verify_pdf_file(pdf_path):
    """
    Vérifie qu'un chemin de fichier PDF est valide et accessible.
    """
    if not isinstance(pdf_path, (str, Path)):
        raise TypeError("Le chemin doit être une chaîne ou un objet Path")

    # Conversion en Path object
    pdf_file = Path(pdf_path).resolve()

    # Vérification de l'extension
    if pdf_file.suffix.lower() != '.pdf':
        raise ValueError(f"Le fichier '{pdf_file}' n'est pas un fichier PDF")

    # Vérification de l'existence du fichier
    if not pdf_file.exists():
        raise FileNotFoundError(f"Le fichier PDF '{pdf_file}' n'existe pas")

    # Vérification que c'est bien un fichier (pas un répertoire)
    if not pdf_file.is_file():
        raise ValueError(f"'{pdf_file}' n'est pas un fichier")

    # Vérification des permissions de lecture
    if not os.access(str(pdf_file), os.R_OK):
        raise PermissionError(f"Le fichier '{pdf_file}' n'est pas accessible en lecture")

    return pdf_file
