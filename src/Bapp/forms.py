import re
import sys
from decimal import Decimal
from random import choices

import bleach
from PIL import Image
import io
from django import forms
from django.contrib.auth.forms import UserCreationForm, UserChangeForm
from django.contrib.auth.models import User
from django.core.exceptions import ValidationError
from django.core.files.uploadedfile import InMemoryUploadedFile
from django.core.validators import RegexValidator, EmailValidator

from Bapp.form_mixin import StyledFormMixin
from Bapp.models import BtestCustomUser, ParticipationAnnual, ParticipationOccasionnelle, Dons, AddDepenses, \
    EditorialCommunity, AmountContributionYear, EvenementOccasionnelle, CotisationOccasionnelle

# Détection des motifs suspects (injection JS)
SUSPICIOUS_PATTERNS = [
    r'<script.*?>',
    r'javascript:',
    r'onclick=',
    r'onerror=',
    r'onload=',
    r'eval\(',
    r'alert\(',
    r'document\.',
    r'window\.',
    r'setTimeout',
    r'setInterval',
]
# Vérification des caractères spéciaux suspects
SUSPICIOUS_CHARS = ['<!--', '-->', '`', '$', '{', '}']


class BtestUserCreationsForms(forms.ModelForm):
    QUARTIERS = [
        ('Leyssare', 'Leyssare'),
        ('Kowli', 'Kowli'),
        ('Gallé', 'Gallé'),
        ('Kouraboulou', 'Kouraboulou'),
        ('Leysorondo', 'Leysorondo'),
        ('Leypellel', 'Leypellel'),
        ('Dowssaré', 'Dowssaré'),
        ("Bhoulie", "Bhoulie"),
        ("Gadhabololl", "Gadhabololl"),
        ('Leybololl', 'Leybololl'),
        # Ajoutez d'autres quartiers ici
    ]
    PAYS = [
        ('Guinée', 'Guinée'),
        ('Sénégal', 'Senégal'),
        ("Côte d'ivoir", "Côte d'Ivoire"),
        ("Benin", "Benin"),
        ("Togo", "Togo"),
        ("Guinée Bissau", "Guinée Bissau"),
        ("Mali", "Mali"),
        ("Burkina Faso", "Burkina Faso"),
        ("Angola", "Angola"),
        ("Gambie", "Gambie"),
        ("Europe", "Europe"),
        ("Asie", "Asie"),
        ("USA", "USA"),
        ("Canada", "Canada")

    ]
    PROFESSION = [
        ('Professeur', 'Professeur'),
        ('Enseignant', 'Enseignant'),
        ('Etudiant', 'Etudiant'),
        ('Commerçant', 'Commerçant'),
        ('Autre', 'Autre'),
    ]

    confirm_password = forms.CharField(required=False,
                                       widget=forms.PasswordInput(attrs={
                                           'class': 'text-field w-input"',
                                           'id': 'confirm-password-id',
                                           'name': 'confirm_password',
                                           'placeholder': 'Confirmer le mot de passe'
                                       }))

    class Meta:
        model = BtestCustomUser
        fields = (
            'prenoms',
            'pays',
            'quartier',
            'email',
            'telephone',
            'city',
            'profile_picture',
            'profession',
            'role',
            'password',
        )

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Créer une nouvelle liste de choix en excluant ADMIN
        choices = [(role, label) for role, label in BtestCustomUser.ROLE_CHOICES if role != 'ADMIN']

        self.fields['role'] = forms.ChoiceField(choices=choices,
                                                required=True,
                                                initial='USER',  #comme valeur par defaut dans le select
                                                widget=forms.Select(attrs={
                                                    'class': 'text-field w-input"',
                                                    'id': 'role-id',
                                                    'name': 'role',
                                                }))
        self.fields['quartier'] = forms.ChoiceField(
            choices=self.QUARTIERS,
            required=True,
            initial="Leyssare",
            widget=forms.Select(attrs={
                'class': 'text-field w-input"',
                'id': 'quartier-id',
                'name': 'quartier',
            }))
        self.fields['pays'] = forms.ChoiceField(
            choices=self.PAYS,
            required=True,
            initial="Guinée",
            widget=forms.Select(attrs={
                'class': 'text-field w-input"',
                'id': 'pays-id',
                'name': 'Pays',
            })
        )
        self.fields['profession'] = forms.ChoiceField(choices=self.PROFESSION,
                                                      required=False,
                                                      initial="Professeur",
                                                      widget=forms.Select(attrs={
                                                          'class': 'text-field w-input"',
                                                          'id': 'profession-id',
                                                          'name': 'profession',
                                                      }))

    prenoms = forms.CharField(
        max_length=100,
        required=True,
        widget=forms.TextInput(attrs={
            'class': 'text-field w-input"',
            'id': 'firstName',
            'name': 'firstName',
            'placeholder': 'Votre prenom '
        })
    )

    email = forms.EmailField(
        validators=[EmailValidator(message="Please enter a valid email address.")],
        required=True,
        widget=forms.EmailInput(attrs={
            'class': 'text-field w-input"',
            'id': 'email-id',
            'name': 'email',
            'placeholder': 'Votre mail '
        })
    )
    telephone = forms.CharField(
        max_length=15,
        required=True,
        validators=[RegexValidator(regex=r'^\+?1?(?:[- .]?\d){9,20}$'
                                   ,
                                   message="Phone number must be entered in the format: '+999999999'. Up to 20 digits allowed.")],
        widget=forms.TextInput(attrs={
            'class': 'text-field w-input"',
            'id': 'telephone-id',
            'name': 'telephone',
            'placeholder': 'Votre numéro de Tél'
        })
    )
    city = forms.CharField(
        max_length=100,
        required=True,
        widget=forms.TextInput(attrs={
            'class': 'text-field w-input"',
            'id': 'cityId',
            'name': 'city',
            'placeholder': 'Ville de residence...'
        })
    )
    profile_picture = forms.ImageField(
        required=False,
        label="Image de profil:",
        widget=forms.ClearableFileInput(attrs={
            'class': 'text-field w-input',
        })
    )
    password = forms.CharField(
        widget=forms.PasswordInput(attrs={
            'class': 'text-field w-input',
            'id': 'password-id',
            'name': 'password',
            'placeholder': 'Mot de passe '
        }),
        required=False,
        min_length=6,
        max_length=100
    )

    def clean_email(self):
        email = self.cleaned_data.get('email')
        # Vérifie si l'email existe chez UN AUTRE utilisateur
        qs = BtestCustomUser.objects.filter(email=email)
        if self.instance.pk:
            qs = qs.exclude(pk=self.instance.pk)
        if qs.exists():
            raise ValidationError("Cet email est déjà utilisé.")
        # Regular expression for validating an email
        regex = r'^[A-Za-z0-9._%+-]{4,50}+@[A-Za-z0-9.-]+\.[A-Za-z]{2,4}$'
        # Check if email matches the regex
        if not re.match(regex, email):
            raise forms.ValidationError("Entrez un email au format valide.")
        return email

    def clean_telephone(self):
        telephone = self.cleaned_data.get('telephone')
        if not telephone.startswith('+'):
            raise forms.ValidationError("Le numéro de téléphone doit commencer par '+'.")
        return telephone

    def clean_image(self):
        image = self.cleaned_data.get('profile_picture')

        if image and image.size > 5 * 1024 * 1024:
            try:
                img = Image.open(image)
                img_format = img.format

                # Convert to RGB if needed
                if img.mode in ("RGBA", "P"):
                    img = img.convert("RGB")

                # Redimensionner si nécessaire (ex : max 1920px de large)
                max_size = (1920, 1080)
                img.thumbnail(max_size)

                output_io = io.BytesIO()
                img.save(output_io, format=img_format or 'JPEG', quality=85, optimize=True)

                # Recréer un fichier compatible Django
                new_image_file = InMemoryUploadedFile(
                    output_io,
                    'ImageField',
                    image.name,
                    f'image/{img_format.lower()}',
                    sys.getsizeof(output_io),
                    None
                )
                return new_image_file

            except Exception as e:
                raise forms.ValidationError("Erreur lors du traitement de l'image : " + str(e))

        return image

    def clean_password(self):
        """Validation spécifique pour le mot de passe"""
        password = self.cleaned_data.get('password')
        role = self.cleaned_data.get('role')

        if role in ['MODERATOR', 'EDITOR', 'SECRETOR', 'SECOND_SECRETOR']:
            if not password:
                raise forms.ValidationError('Le mot de passe est obligatoire pour ce rôle')
            if len(password) < 5:
                raise forms.ValidationError('Le mot de passe doit comporter au moins 5 caractères')
        return password

    def clean_confirm_password(self):
        """Validation spécifique pour la confirmation du mot de passe"""
        password = self.cleaned_data.get('password')
        confirm_password = self.cleaned_data.get('confirm_password')
        role = self.cleaned_data.get('role')

        if role in ['MODERATOR', 'EDITOR', 'SECRETOR', 'SECOND_SECRETOR']:
            if password and confirm_password and password != confirm_password:
                raise forms.ValidationError('Les mots de passe ne correspondent pas')
        return confirm_password

    def clean(self):
        """Validation globale du formulaire"""
        cleaned_data = super().clean()

        # Validation supplémentaire si nécessaire
        if not cleaned_data.get('role'):
            raise forms.ValidationError({'role': 'Le rôle est obligatoire'})
        if not cleaned_data.get('quartier'):
            raise forms.ValidationError({'quartier': 'Le quartier est obligatoire'})
        if not cleaned_data.get('pays'):
            raise forms.ValidationError({'pays': 'Le pays est obligatoire'})

        return cleaned_data

    def get_validated_data(self):
        """Récupération des données validées avec traitement supplémentaire si nécessaire"""
        if self.is_valid():
            data = self.cleaned_data.copy()
            print(data)
            # Retirer les champs qui ne sont pas dans le modèle si nécessaire
            if 'confirm_password' in data:
                data.pop('confirm_password')
            return data
        return None


class RechercheUserForm(forms.Form):
    recherche = forms.CharField(label='Code personnel ou prénom', max_length=100)

    def clean_query(self):
        query = self.cleaned_data['recherche']
        if len(query) < 2:
            raise forms.ValidationError("Veuillez entrer au moins 2 caractères.")
        return query


class UserSearchForm(forms.Form):
    search_term = forms.CharField(
        max_length=100,
        required=True,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Rechercher par prénom ou identifiant'
        })
    )

    def clean_search_term(self):
        search_term = self.cleaned_data.get('search_term')
        search_term = search_term.strip()
        if not search_term:
            raise forms.ValidationError("Veuillez entrer un nom ou identifiant.")
        if len(search_term) < 2:
            raise forms.ValidationError("Veuillez entrer au moins 2 caractères.")
        return search_term


class ParticipationAnnuelForm(StyledFormMixin, forms.ModelForm):
    ui_config = {
        'title': "Ajouter une cotisation annuelle",
        'icon': 'fas fa-calendar-plus',
        'btn_text': "Enregistrer l'événement",
        'btn_class': 'btn-primary',
        'header_class': 'bg-primary text-white'
    }

    class Meta:
        model = ParticipationAnnual
        fields = ['participant', 'montant_participation', 'year']
        widgets = {
            'montant_participation': forms.NumberInput(attrs={
                'class': 'form-control',
                'step': '0.01',
                'placeholder': 'Ex: 5000'
            }),
            'year': forms.Select(attrs={
                'class': 'form-control'
            })
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['participant'].label = "Nom de l'utilisateur"
        self.fields['montant_participation'].label = "Montant de participation"
        self.fields['year'].label = "Année de cotisation"
        # On s'assure que la liste des années est triée par la plus récente
        self.fields['year'].queryset = AmountContributionYear.objects.all().order_by('-year')
        self.fields['year'].empty_label = "-- Sélectionnez l'année --"
        self.fields['participant'].empty_label = "-- Sélectionnez un membre--"

    def clean_montant_participation(self):
        """
        Nettoie et valide le montant par rapport au montant fixé pour l'année choisie
        """
        montant_participation = self.cleaned_data.get('montant_participation')

        if montant_participation is None:
            raise forms.ValidationError("Le montant de participation ne peut pas être vide")

        # Conversion en Decimal pour la précision
        try:
            montant_participation = Decimal(str(montant_participation))
        except (TypeError, ValueError):
            raise forms.ValidationError("Le montant de participation doit être un nombre valide")
        if montant_participation > Decimal('20000.00'):
            self.add_error('montant_participation',
                           'Le montant ne peut pas depassé 20.000 fcfa')
        # Arrondir à 2 décimales pour la précision financière
        return montant_participation.quantize(Decimal('0.01'))

    def clean(self):
        """Validation croisée entre le montant et l'année sélectionnée"""
        cleaned_data = super().clean()
        montant = cleaned_data.get('montant_participation')
        year_obj = cleaned_data.get('year')
        participant = cleaned_data.get('participant')

        # On vérifie que les deux champs sont présents avant de comparer
        if montant and year_obj:
            # On vérifie si une participation existe déjà pour ce membre cette année
            # .exclude(pk=self.instance.pk) permet de ne pas bloquer lors d'une modification (edit)
            exists = ParticipationAnnual.objects.filter(
                participant=participant,
                year=year_obj
            ).exclude(pk=self.instance.pk).exists()

            if exists:
                raise ValidationError(
                    f"Action refusée : {participant.prenoms} a déjà validé sa participation pour l'année {year_obj.year}."
                )
            montant_requis = Decimal(str(year_obj.amount_to_paid_pro_year))

            if montant < montant_requis:
                # On ajoute l'erreur spécifiquement au champ montant_participation
                self.add_error('montant_participation',
                               f"Pour l'année {year_obj.year}, le montant doit être au minimum de {montant_requis} FGN."
                               )

        return cleaned_data


class ParticipationOccasionnelleForm(forms.ModelForm):
    class Meta:
        model = ParticipationOccasionnelle
        fields = ['montant_participation', "motif_participation"]
        widgets = {
            'montant_participation': forms.NumberInput(attrs={
                'class': 'form-control',
                'step': '0.01'
            })
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['montant_participation'].label = "Montant de participation"
        self.fields['motif_participation'].label = "Motif de  participation"

    def clean_montant_participation(self):
        """
        Méthode pour nettoyer et valider le montant_participation
        """
        montant_participation = self.cleaned_data.get('montant_participation')

        if montant_participation is None:
            raise forms.ValidationError("Le montant de participation ne peut pas être vide")

        # Conversion en Decimal pour une précision exacte
        try:
            montant_participation = Decimal(str(montant_participation))
        except (TypeError, ValueError):
            raise forms.ValidationError("Le montant de participation doit être un nombre valide")

        # Vérification du montant_participation minimal
        if montant_participation < Decimal('1000.01'):
            raise forms.ValidationError("Le montant de participation doit être supérieur à 1000 FGN")

        # Arrondir à 2 décimales
        montant_participation = montant_participation.quantize(Decimal('1000.01'))

        # Vérification du format (pas plus de 2 décimales)
        if str(montant_participation)[::-1].find('.') > 2:
            raise forms.ValidationError("Le montant de participation ne peut avoir que 2 décimales maximum")

        return montant_participation

    def clean_motif_participation(self):
        motif_participation = self.cleaned_data.get('motif_participation')
        motif_participation = motif_participation.capitalize()
        if motif_participation is None:
            raise forms.ValidationError("Le champs motif participation ne peut pas être vide")
        # S'assurer qu'il n'y ai pas de caractères non valide dans le textarea
        for pattern in SUSPICIOUS_PATTERNS:
            if re.search(pattern, motif_participation, re.IGNORECASE):
                raise ValidationError(
                    "Contenu non autorisé détecté dans le motif du don."
                )

        for char in SUSPICIOUS_PATTERNS:
            if char in motif_participation:
                raise ValidationError(
                    "Caractères non autorisés détectés dans le motif du don."
                )
        return motif_participation


class AmountContributionYearForm(StyledFormMixin, forms.ModelForm):
    ui_config = {
        'title': "Intialisation du montant annuel de contribution",
        'icon': 'fas fa-calendar-plus',
        'btn_text': "Enregistrer l'événement",
        'btn_class': 'btn-primary',
        'header_class': 'bg-primary text-white'
    }

    class Meta:
        model = AmountContributionYear
        fields = ['year', 'amount_to_paid_pro_year']
        widgets = {
            'amount_to_paid_pro_year': forms.NumberInput(attrs={
                'class': 'form-control',
                'step': '0.01',
                'placeholder': 'Montant annuel (ex: 5000)'
            }),
            'year': forms.NumberInput(attrs={
                'class': 'form-control',
                'placeholder': 'Année (ex: 2024)'
            })
        }

    def clean_year(self):
        year = self.cleaned_data.get('year')
        # Vérification de l'année (pas dans le futur lointain ou le passé trop lointain)
        from datetime import date
        current_year = date.today().year
        if year < 2000 or year > current_year + 5:
            raise forms.ValidationError(f"L'année {year} n'est pas valide.")
        # Vérification de l'unicité (le modèle a unique=True, mais un message personnalisé est mieux)
        if AmountContributionYear.objects.filter(year=year).exists():
            if not self.instance.pk:  # Si c'est une création
                raise forms.ValidationError("L'année existe déjà.")
        return year

    def clean_amount_to_paid_pro_year(self):
        amount = self.cleaned_data.get('amount_to_paid_pro_year')
        if amount is None:
            raise forms.ValidationError("Le montant est obligatoire.")
        try:
            amount = Decimal(str(amount))
        except (TypeError, ValueError):
            raise forms.ValidationError("Veuillez entrer un nombre valide.")
        # Sécurité : montant minimum (ex: 1000 fcfa)
        if amount < Decimal('1000'):
            raise forms.ValidationError("Le montant doit être au minimum de 1000 F.")
        # Arrondi à 2 décimales pour la sécurité financière
        amount = amount.quantize(Decimal('0.01'))
        return amount


class EvenementOccasionnelleForm(StyledFormMixin, forms.ModelForm):
    ui_config = {
        'title': "Création de Cotisation occasionnelle",
        'icon': 'fas fa-calendar-plus',
        'btn_text': "Enregistrer l'événement",
        'btn_class': 'btn-primary',
        'header_class': 'bg-primary text-white'
    }

    class Meta:
        model = EvenementOccasionnelle
        fields = ['event_name', 'event_description', 'date_event']
        widgets = {
            'event_name': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': "Nom de l'événement (ex: Mariage, Baptême)"
            }),
            'event_description': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 3,
                'placeholder': "Description détaillée..."
            }),
            'date_event': forms.DateInput(attrs={
                'class': 'form-control',
                'type': 'date'
            })
        }

    def clean_event_name(self):
        name = self.cleaned_data.get('event_name')
        if name:
            # Sécurité contre les scripts
            for pattern in SUSPICIOUS_PATTERNS:
                if re.search(pattern, name, re.IGNORECASE):
                    raise ValidationError("Le nom contient des motifs non autorisés.")
            return name.strip()
        return name

    def clean_event_description(self):
        description = self.cleaned_data.get('event_description')
        if description:
            # Utilisation de bleach pour nettoyer le HTML si présent
            cleaned_desc = bleach.clean(description, tags=[], strip=True)
            if len(cleaned_desc) < 10:
                raise ValidationError("La description doit faire au moins 10 caractères.")
            return cleaned_desc
        return description


class CotisationOccasionnelleForm(StyledFormMixin, forms.ModelForm):
    ui_config = {
        'title': "Ajouter une cotisation occasionnelle",
        'icon': 'fas fa-calendar-plus',
        'btn_text': "Enregistrer les données",
        'btn_class': 'btn-primary',
        'header_class': 'bg-primary text-white'
    }

    class Meta:
        model = CotisationOccasionnelle
        fields = ['member', 'event_name', 'montant_cotisation']
        widgets = {
            'member': forms.Select(attrs={'class': 'form-control select2'}),
            # On change 'year' par 'event_name' ici aussi
            'event_name': forms.Select(attrs={'class': 'form-control'}),
            'montant_cotisation': forms.NumberInput(attrs={
                'class': 'form-control',
                'step': '0.01',
                'placeholder': 'Montant en FGN'
            })
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['member'].queryset = BtestCustomUser.objects.filter(is_active=True).order_by('prenoms')
        self.fields['member'].empty_label = "Sélectionnez un membre"

        # On remplace self.fields['year'] par self.fields['event_name']
        self.fields['event_name'].queryset = EvenementOccasionnelle.objects.all().order_by('-date_event')
        self.fields['event_name'].empty_label = "Sélectionnez l'événement"
        self.fields['event_name'].label = "Événement"

        # On rend les champs obligatoires
        self.fields['member'].required = True
        self.fields['event_name'].required = True
        self.fields['montant_cotisation'].required = True

    def clean_montant_cotisation(self):
        montant = self.cleaned_data.get('montant_cotisation')

        if montant is None:
            raise ValidationError("Le montant est obligatoire.")

        try:
            montant = Decimal(str(montant))
        except (TypeError, ValueError):
            raise ValidationError("Le format du montant est invalide.")

        if montant < Decimal('10000.00'):
            raise ValidationError("Le montant minimum de cotisation est de 10.000 FGN.")

        # Précision financière
        return montant.quantize(Decimal('0.01'))

    def clean(self):
        cleaned_data = super().clean()
        member = cleaned_data.get('member')
        event_name = cleaned_data.get('event_name')

        # Vérification si une cotisation existe déjà pour ce membre et cet événement
        if member and event_name:
            exists = CotisationOccasionnelle.objects.filter(
                member=member,
                event_name=event_name
            ).exclude(pk=self.instance.pk).exists()

            if exists:
                raise ValidationError(
                    f"Ce membre ({member}) a déjà enregistré une cotisation pour l'événement '{event_name}'."
                )

        return cleaned_data


class DonsForm(StyledFormMixin, forms.ModelForm):
    ui_config = {
        'title': "Ajout d'un nouveau don",
        'icon': 'fas fa-calendar-plus',
        'btn_text': "Enregistrer l'événement",
        'btn_class': 'btn-primary',
        'header_class': 'bg-primary text-white'
    }

    class Meta:
        model = Dons
        fields = ['nom', 'prenom', 'montant_don', 'motif_don']
        widgets = {
            'nom': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Le nom du donateur'
            }),
            'prenom': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Le prénom du donateur'
            }),
            'montant_don': forms.NumberInput(attrs={
                'class': 'form-control',
                'placeholder': 'Montant du don'
            }),
            'motif_don': forms.Textarea(attrs={
                'class': 'form-control',
                'placeholder': 'Motif du don',
                'rows': 4
            })
        }

    def clean_montant_don(self):
        montant = self.cleaned_data['montant_don']

        # Conversion en Decimal pour une précision exacte
        try:
            montant_don = Decimal(str(montant))
        except (TypeError, ValueError):
            raise forms.ValidationError("Le montant de participation doit être un nombre valide")

        # Vérification du montant_participation minimal
        if montant_don < Decimal('1000.01'):
            raise forms.ValidationError("Le montant de participation doit être supérieur à 1000 FGN")

        # Arrondir à 2 décimales
        montant_don = montant_don.quantize(Decimal('1000.01'))

        # Vérification du format (pas plus de 2 décimales)
        if str(montant_don)[::-1].find('.') > 2:
            raise forms.ValidationError("Le montant de participation ne peut avoir que 2 décimales maximum")

        return montant

    def clean_nom(self):
        nom = self.cleaned_data['nom']
        if len(nom.strip()) < 2:
            raise forms.ValidationError("Le prénom doit contenir au moins 2 caractères")
        for pattern in SUSPICIOUS_PATTERNS:
            if re.search(pattern, nom, re.IGNORECASE):
                raise ValidationError(
                    "Contenu non autorisé détecté dans le motif du don."
                )
        for char in SUSPICIOUS_PATTERNS:
            if char in nom:
                raise ValidationError(
                    "Caractères non autorisés détectés dans le motif du don."
                )

        return nom.strip()

    def clean_prenom(self):
        prenom = self.cleaned_data['prenom']
        if len(prenom.strip()) < 4:
            raise forms.ValidationError("Le prénom doit contenir au moins 4 caractères")
        for pattern in SUSPICIOUS_PATTERNS:
            if re.search(pattern, prenom, re.IGNORECASE):
                raise ValidationError(
                    "Contenu non autorisé détecté dans le motif du don."
                )
        for char in SUSPICIOUS_PATTERNS:
            if char in prenom:
                raise ValidationError(
                    "Caractères non autorisés détectés dans le motif du don."
                )

        return prenom.strip()

    def clean_motif_don(self):
        """
        Nettoie et valide le champ motif_don :
        - Supprime les balises HTML dangereuses
        - Vérifie la longueur du texte
        - Détecte les tentatives d'injection JS
        - Vérifie le contenu pour les caractères spéciaux suspects
        """
        motif = self.cleaned_data['motif_don']

        # Configuration de bleach pour le nettoyage HTML
        allowed_tags = []  # Aucune balise HTML autorisée
        allowed_attributes = {}  # Aucun attribut autorisé
        allowed_styles = []  # Aucun style autorisé

        # Nettoie le texte avec bleach
        cleaned_text = bleach.clean(
            motif,
            tags=allowed_tags,
            attributes=allowed_attributes,
            strip=True
        )

        # Vérification de la longueur
        if len(cleaned_text.strip()) < 10:
            raise ValidationError(
                "Le motif du don doit contenir au moins 10 caractères."
            )

        if len(cleaned_text) > 1000:
            raise ValidationError(
                "Le motif du don ne peut pas dépasser 1000 caractères."
            )

        for pattern in SUSPICIOUS_PATTERNS:
            if re.search(pattern, motif, re.IGNORECASE):
                raise ValidationError(
                    "Contenu non autorisé détecté dans le motif du don."
                )

        for char in SUSPICIOUS_PATTERNS:
            if char in motif:
                raise ValidationError(
                    "Caractères non autorisés détectés dans le motif du don."
                )

        # Nettoyage supplémentaire
        cleaned_text = re.sub(r'[\x00-\x08\x0B\x0C\x0E-\x1F\x7F]', '',
                              cleaned_text)  # Supprime les caractères de contrôle
        cleaned_text = cleaned_text.strip()  # Supprime les espaces en début et fin

        return cleaned_text

    def clean(self):
        """Validation globale du formulaire"""
        cleaned_data = super().clean()

        # Vérification supplémentaire pour les champs interdépendants
        motif = cleaned_data.get('motif_don', '')
        montant = cleaned_data.get('montant_don')

        if montant and montant > 10000 and len(motif) < 10:
            raise ValidationError(
                "Pour les dons supérieurs à 10000 FGN, veuillez fournir un motif plus détaillé (minimum 10 caractères)."
            )

        return cleaned_data


class AddDepensesForm(StyledFormMixin, forms.ModelForm):
    ui_config = {
        'title': "Ajouter une nouvelle dépense",
        'icon': 'fas fa-calendar-plus',
        'btn_text': "Enregistrer l'événement",
        'btn_class': 'btn-primary',
        'header_class': 'bg-primary text-white'
    }

    class Meta:
        model = AddDepenses
        fields = ['montant_depense', 'motif_depense']

    montant_depense = forms.DecimalField(
        label='Montant dépense',
        required=True,
        widget=forms.TextInput(
            attrs={
                'id': 'depense-numberInput',
                'class': 'depense-input',
                'placeholder': 'Entrez le montant ici (doit être superieure à 1000 FGN)'
            }
        )
    )

    motif_depense = forms.CharField(
        label='Motif dépense',
        required=True,
        widget=forms.Textarea(
            attrs={
                'id': 'depense-textInput',
                'class': 'depense-textarea',
                'placeholder': 'Entrez au moins une phrase (texte uniquement)'
            }
        )
    )

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Personnalisation des labels
        for field in self.fields.values():
            field.label_attrs = {'class': 'depense-label'}
            field.error_css_class = 'depense-error'

    def clean_montant_depense(self):
        montant = self.cleaned_data.get('montant_depense')

        # Conversion en Decimal pour une précision exacte
        try:
            montant_depense = Decimal(str(montant))
        except (TypeError, ValueError):
            raise forms.ValidationError("Le montant de la dépense doit être un nombre valide")

        # Vérification du montant_participation minimal
        if montant_depense < Decimal('1000.01'):
            raise forms.ValidationError("Le montant de la dépense doit être supérieur à 1000 FGN")

        # Arrondir à 2 décimales
        montant_don = montant_depense.quantize(Decimal('1000.01'))

        # Vérification du format (pas plus de 2 décimales)
        if str(montant_don)[::-1].find('.') > 2:
            raise forms.ValidationError("Le montant de la dépense ne peut avoir que 2 décimales maximum")

        return montant_depense

    def clean_motif_depense(self):
        """
        Nettoie et valide le champ motif_ddepense :
        - Supprime les balises HTML dangereuses
        - Vérifie la longueur du texte
        - Détecte les tentatives d'injection JS
        - Vérifie le contenu pour les caractères spéciaux suspects
        """
        motif = self.cleaned_data.get('motif_depense')

        # Configuration de bleach pour le nettoyage HTML
        allowed_tags = []  # Aucune balise HTML autorisée
        allowed_attributes = {}  # Aucun attribut autorisé
        allowed_styles = []  # Aucun style autorisé

        # Nettoie le texte avec bleach
        cleaned_text = bleach.clean(
            motif,
            tags=allowed_tags,
            attributes=allowed_attributes,
            strip=True
        )

        # Vérification de la longueur
        if len(cleaned_text.strip()) < 10:
            raise ValidationError(
                "Le motif du don doit contenir au moins 10 caractères."
            )

        if len(cleaned_text) > 1000:
            raise ValidationError(
                "Le motif du don ne peut pas dépasser 1000 caractères."
            )

        for pattern in SUSPICIOUS_PATTERNS:
            if re.search(pattern, motif, re.IGNORECASE):
                raise ValidationError(
                    "Contenu non autorisé détecté dans le motif du don."
                )

        for char in SUSPICIOUS_PATTERNS:
            if char in motif:
                raise ValidationError(
                    "Caractères non autorisés détectés dans le motif du don."
                )

        # Nettoyage supplémentaire
        cleaned_text = re.sub(r'[\x00-\x08\x0B\x0C\x0E-\x1F\x7F]', '',
                              cleaned_text)  # Supprime les caractères de contrôle
        cleaned_text = cleaned_text.strip()  # Supprime les espaces en début et fin

        return cleaned_text


class EditorialCommunityForm(StyledFormMixin, forms.ModelForm):
    ui_config = {
        'title': "Publier une information !",
        'icon': 'fas fa-calendar-plus',
        'btn_text': "Enregistrer l'événement",
        'btn_class': 'btn-primary',
        'header_class': 'bg-primary text-white'
    }

    class Meta:
        model = EditorialCommunity
        fields = ['title', 'content', 'image', 'extra_links']
        labels = {
            'title': "Le titre de l'article :",
            'content': "Contenu de l'article:",
            'image': "Image d'illustration :",
            'extra_links': "Liens complémentaires :"
        }
        widgets = {
            'title': forms.TextInput(attrs={
                'class': 'form-group form-control',
                'placeholder': "Titre de l'article",
                'required': True,
                'maxlength': 200,
            }),
            'content': forms.Textarea(attrs={
                'class': 'form-control form-group',
                'placeholder': "Contenu de l'article",
                'required': True,
                'rows': 6,
            }),
            'extra_links': forms.URLInput(attrs={
                'class': 'form-control form-group',
                'placeholder': "Lien utile (ex: https://...)",
            }),
        }

    image = forms.ImageField(
        required=False,
        label="Image d'illustration:",
        widget=forms.ClearableFileInput(attrs={
            'class': 'form-control-file form-group'
        })
    )

    def clean_title(self):
        title = self.cleaned_data.get('title')
        if '<' in title or '>' in title:
            raise forms.ValidationError("Le titre contient des caractères interdits.")
        return title

    def clean_extra_links(self):
        link = self.cleaned_data.get('extra_links')
        if link and not link.startswith(('http://', 'https://')):
            raise forms.ValidationError("Le lien doit commencer par http:// ou https://")
        return link

    def clean_content(self):
        """
        Nettoie et valide le champ motif_ddepense :
        - Supprime les balises HTML dangereuses
        - Vérifie la longueur du texte
        - Détecte les tentatives d'injection JS
        - Vérifie le contenu pour les caractères spéciaux suspects
        """
        content = self.cleaned_data.get('content')

        # Configuration de bleach pour le nettoyage HTML
        allowed_tags = []  # Aucune balise HTML autorisée
        allowed_attributes = {}  # Aucun attribut autorisé
        allowed_styles = []  # Aucun style autorisé

        # Nettoie le texte avec bleach
        cleaned_text = bleach.clean(
            content,
            tags=allowed_tags,
            attributes=allowed_attributes,
            strip=True
        )

        # Vérification de la longueur
        if len(cleaned_text.strip()) < 10:
            raise ValidationError(
                "L'article doit contenir au moins 10 caractères."
            )

        if len(cleaned_text) > 2000:
            raise ValidationError(
                "L'article ne peut pas dépasser 1000 caractères."
            )

        for pattern in SUSPICIOUS_PATTERNS:
            if re.search(pattern, content, re.IGNORECASE):
                raise ValidationError(
                    "Contenu non autorisé détecté dans le motif du don."
                )

        for char in SUSPICIOUS_PATTERNS:
            if char in content:
                raise ValidationError(
                    "Caractères non autorisés détectés dans le motif du don."
                )

        return cleaned_text

    def clean_image(self):
        image = self.cleaned_data.get('image')

        if image and image.size > 5 * 1024 * 1024:
            try:
                img = Image.open(image)
                img_format = img.format

                # Convert to RGB if needed
                if img.mode in ("RGBA", "P"):
                    img = img.convert("RGB")

                # Redimensionner si nécessaire (ex : max 1920px de large)
                max_size = (1920, 1080)
                img.thumbnail(max_size)

                output_io = io.BytesIO()
                img.save(output_io, format=img_format or 'JPEG', quality=85, optimize=True)

                # Recréer un fichier compatible Django
                new_image_file = InMemoryUploadedFile(
                    output_io,
                    'ImageField',
                    image.name,
                    f'image/{img_format.lower()}',
                    sys.getsizeof(output_io),
                    None
                )
                return new_image_file

            except Exception as e:
                raise forms.ValidationError("Erreur lors du traitement de l'image : " + str(e))

        return image


class UserEditForm(UserChangeForm):
    class Meta:
        model = BtestCustomUser
        fields = [
            'prenoms', 'name', 'identifiant', 'email', 'profile_picture',
            'is_active', 'groups', 'user_permissions',
            'created_by'  # À masquer dans le template si nécessaire
        ]
        widgets = {
            'created_by': forms.HiddenInput(),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Personnalisations supplémentaires
        self.fields['email'].required = True
        self.fields['identifiant'].required = True
        self.fields['prenoms'].required = True
        self.fields['name'].required = True
        self.fields['profile_picture'].required = False
        if not self.instance.pk:  # Si création
            self.fields['password'] = forms.CharField(
                widget=forms.PasswordInput,
                help_text="Définir un mot de passe sécurisé"
            )
