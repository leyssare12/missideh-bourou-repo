import os
import uuid
from datetime import timedelta, date
from urllib import request

import pyotp
from django.conf import settings
from django.contrib.auth import get_user_model

from django_pgviews import view as pgview
from django.utils import timezone
from django.contrib.auth.base_user import AbstractBaseUser, BaseUserManager
from django.contrib.auth.models import AbstractUser, PermissionsMixin
from django.db import models

from BTest import settings
from secrets import randbelow
#cette methode permet d'ajouter un identifiant unique au nom de l'image et évite qu'un même non se retrouve deux fois dans la base
def get_profile_image_path(instance, filename):
    # Séparer le nom du fichier de son extension
    base_name, extension = os.path.splitext(filename)
    # Générer un UUID unique
    unique_id = str(uuid.uuid4())
    # Créer le nouveau nom de fichier
    new_filename = f"{base_name}_{unique_id}{extension}"
    # Retourner le chemin complet
    return os.path.join('images/profile_pictures', new_filename)


def current_year():
    # Fournit l'année courante sous forme d'entier pour les champs "year"
    return date.today().year


def default_email_verification_expiration():
    # Fournit un datetime dynamique à la création de l'objet
    return timezone.now() + timedelta(days=1)

# Create your models here.
"""User Manager"""
class BTestCustomUserManager(BaseUserManager):
    '''Creation de l'utilisateur normale'''
    def create_user(self, name,
                    prenoms,
                    quartier,
                    identifiant,
                    email,
                    pays,
                    telephone,
                    role,
                    profile_picture=None,
                    password=None,
                    created_by=None
                    ):
        if not identifiant:
            raise ValueError('Users must have an identifiant')
        if not email:
            raise ValueError('Users must have an email address')
        if not pays:
            raise ValueError('Users must have a country')
        if not telephone:
            raise ValueError('Users must have a phone number')
        user = self.model(
            name=name,
            prenoms=prenoms,
            quartier=quartier,
            identifiant=identifiant,
            email=self.normalize_email(email),
            pays=pays,
            telephone=telephone,
            role=role,
            profile_picture=profile_picture,
            password=password,
            created_by=created_by,
        )
        user.set_password(password)
        user.is_active = True
        user.email_verified = False
        user.save(using=self._db)
        return user
    '''Creation d'un utilisateur administrateur'''
    def create_superuser(self,
                         name,
                         prenoms,
                         quartier,
                         identifiant,
                         pays,
                         email,
                         telephone,
                         role,
                         profile_picture=None,
                         password=None):
        user = self.create_user(
            name=name,
            prenoms=prenoms,
            quartier=quartier,
            identifiant=identifiant,
            email=self.normalize_email(email),
            pays=pays,
            telephone=telephone,
            role=role,
            profile_picture=profile_picture,
            password=password,
            created_by=None,
        )
        user.is_premium = True
        user.is_admin = True
        user.is_superuser = True
        user.save(using=self._db)
        return user
"""User model"""
class BTestCustomUser(AbstractBaseUser, PermissionsMixin):
    name = models.CharField(max_length=60, blank=True)
    prenoms = models.CharField(max_length=60, blank=False)
    quartier = models.CharField(max_length=60, blank=False, null=False, default='Kowli')
    identifiant = models.CharField(max_length=20, unique=True, blank=True, null=False)
    pays = models.CharField(max_length=30, blank=False)
    email = models.EmailField(unique=True, blank=False)
    telephone = models.CharField(max_length=20, blank=True)
    password = models.CharField(max_length=128, blank=True, null=True)
    profile_picture = models.ImageField(upload_to=get_profile_image_path, blank=True, null=True)
    created_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True, related_name='created_by_user')

    otp_secret = models.CharField(max_length=32, blank=True, null=True)
    otp_enabled = models.BooleanField(default=False)

    is_staff = models.BooleanField(default=False)
    is_active = models.BooleanField(default=True)
    is_superuser = models.BooleanField(default=False)

    is_public = models.BooleanField(default=False)

    date_joined = models.DateTimeField(auto_now_add=True)
    last_login = models.DateTimeField(auto_now=True)

    email_verified = models.BooleanField(default=False)
    email_verification_token = models.UUIDField(null=True, blank=True, unique=True)
    email_verification_expiration = models.DateTimeField(default=default_email_verification_expiration, blank=True, null=True)
    password_changed = models.BooleanField(default=False)

    #Est-ce-que l'utilisateur fait partie de ceux qui finance le maintien du site
    is_premium = models.BooleanField(default=False)
    is_moderator = models.BooleanField(default=False)

    USERNAME_FIELD = 'identifiant'
    REQUIRED_FIELDS = ['prenoms', 'quartier', 'email', 'pays', 'telephone']

    #Initialisation du Manager
    objects = BTestCustomUserManager()

    def __str__(self):
        return self.identifiant
    ADMIN = 'ADMIN'
    MODERATOR = 'MODERATOR' #Peut ajouter des utilisateurs
    EDITOR = 'EDITOR' # Peut ajouter des articles et de editions
    SECRETOR = 'SECRETOR' # peut ajouter des cotisations
    SECOND_SECRETOR = 'SECOND_SECRETOR' # peut ajouter les dépenses effectuées
    USER = 'USER' # Les membres de missidhé bourou

    ROLE_CHOICES = [
        (ADMIN, 'Administrateur'),
        (MODERATOR, 'Modérateur'),
        (EDITOR, 'Éditeur'),
        (USER, 'Utilisateur normal'),
        (SECRETOR, 'Gestionnaire des cotisations'),
        (SECOND_SECRETOR, 'Gestionnaire des dépenses'),
    ]

    role = models.CharField(max_length=20, choices=ROLE_CHOICES, default=USER)
    class Meta:
        permissions = [
            ('manager_adminstrators', 'Can manage administrators'),
            ('manage_users', 'Can manage users'),
            ('manage_articles', 'Can manage articles'),
            ('manager_cotisations', 'Can manage cotisations'),
            ('manager_depenses', 'Can manage depenses'),
   ]
    def save(self, *args, **kwargs):
        # Nettoyer et normaliser le prénom
        self.prenoms = self.prenoms.strip()  # Supprimer les espaces au début et à la fin
        base_prenom = ' '.join(self.prenoms.split())  # Normaliser les espaces multiples
        base_prenom = base_prenom.title()  # Première lettre en majuscule, reste en minuscule

        # Rechercher les utilisateurs existants avec le même prénom habitant le même quartier (insensible à la casse)
        # On exclut les suffixes (A, B, C...) dans la recherche
        existing_users = BTestCustomUser.objects.filter(
            prenoms__iregex=rf'^{base_prenom}(\s+[A-Z])?$',
            quartier__iexact=self.quartier
        ).order_by('prenoms')

        if self.pk:  # Si c'est une mise à jour
            # Récupérer l'ancienne image
            old_image = BTestCustomUser.objects.get(pk=self.pk)
            #On recupere l'utilisateur actuel
            existing_users = existing_users.exclude(pk=self.pk)


            # Si une nouvelle image est téléchargée
            if old_image.profile_picture and self.profile_picture != old_image.profile_picture:
                # Supprimer l'ancienne image
                old_image.profile_picture.delete(save=False)

        if existing_users.exists():
            # Extraire et trier les suffixes existants
            suffixes = []
            for user in existing_users:
                parts = user.prenoms.split()
                if len(parts) > 1 and len(parts[-1]) == 1:
                    suffixes.append(parts[-1])

            # Trouver le prochain suffixe disponible
            letters = 'ABCDEFGHIJKLMNOPQRSTUVWXYZ'
            next_suffix = None

            for letter in letters:
                if letter not in suffixes:
                    next_suffix = letter
                    break

            if next_suffix:
                self.prenoms = f"{base_prenom} {next_suffix}"
            else:
                # Si toutes les lettres sont utilisées, on peut ajouter un numéro
                self.prenoms = f"{base_prenom} ({existing_users.count() + 1})"
        else:
            self.prenoms = base_prenom

        super().save(*args, **kwargs)

#Gestion des permissions
"""
    def get_role_permissions(self):
        
        permissions = {
            self.ADMIN: [
                'add_article',
                'change_article',
                'delete_article',
                'view_article',
                'add_comment',
                'change_comment',
                'delete_comment',
                'view_comment',
                'manage_users',
                'publish_article',
                'moderate_comments',
            ],
            self.MODERATOR: [
                'view_article',
                'change_article',
                'view_comment',
                'change_comment',
                'delete_comment',
                'moderate_comments',
                'publish_article',
            ],
            self.EDITOR: [
                'add_article',
                'change_article',
                'view_article',
                'add_comment',
                'view_comment',
                'publish_article',
            ],
            self.USER: [
                'view_article',
                'add_comment',
                'view_comment',
            ]
        }
        return permissions.get(self.role, [])
    def has_perm(self, perm, obj=None):
     
        # Si c'est un superuser (ADMIN), il a toutes les permissions
        if self.is_superuser:
            return True

        # Récupère les permissions du rôle
        role_permissions = self.get_role_permissions()

        # Vérifie si la permission demandée est dans les permissions du rôle
        if perm in role_permissions:
            return True

        # Vérifications spécifiques pour les objets
        if obj is not None:
            # Pour les articles
            if isinstance(obj, 'Article'):
                # L'auteur peut modifier son propre article non publié
                if perm == 'change_article' and obj.auteur == self and not obj.est_publie:
                    return True
                # L'auteur peut supprimer son propre article
                if perm == 'delete_article' and obj.auteur == self:
                    return True

            # Pour les commentaires
            if isinstance(obj, 'Commentaire'):
                # L'auteur peut modifier/supprimer son propre commentaire
                if perm in ['change_comment', 'delete_comment'] and obj.auteur == self:
                    return True

        return False

    def has_module_perms(self, app_label):
      
        if self.is_superuser:
            return True

        return any(perm.startswith(f"{app_label}.") for perm in self.get_role_permissions())

   
"""

User = get_user_model() # on recupere un pointeur ver BtestCustomUser

class TwoFactorSettingsTelegram(models.Model):
    """
    Profil 2FA par utilisateur:
    - Stocke l'identité Telegram (chat_id) pour l'envoi de codes par bot.
    - Peut contenir le canal préféré et la date de liaison.
    """
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name="twofa_settings")
    telegram_chat_id = models.BigIntegerField(null=True, blank=True, unique=True)
    telegram_linked_at = models.DateTimeField(null=True, blank=True)

    def __str__(self):
        return f"2FA settings for {getattr(self.user, 'identifiant', self.user.pk)}"

class TwoFactorAuth(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='two_factor_auth')
    token_code = models.CharField(max_length=8)
    channel = models.CharField(max_length=20, choices=(('email', 'email'), ('whatsapp', 'whatsapp'), ('telegram', 'telegram')), default='email')
    created_at = models.DateTimeField(auto_now_add=True)
    expires_at = models.DateTimeField()
    is_used = models.BooleanField(default=False)

    @classmethod
    def create_token(cls, user, channel='email', ttl_minutes=5):
        # 6 chiffres
        code = f"{randbelow(10**6):06d}"
        return cls.objects.create(
            user=user,
            token_code=code,
            channel=channel,
            expires_at=timezone.now() + timedelta(minutes=ttl_minutes),
        )

    #Retourner le temps de vie du secret
    @property
    def token_expired(self):
        """Vérifie si le code a expiré et le marque comme utilisé."""
        return timezone.now() > self.expires_at
    @property
    def token_valid(self):
        return not self.is_used and not self.token_expired
    def mark_as_used(self):
        """Marque explicitement le token comme utilisé."""
        if not self.is_used:
            self.is_used = True
            self.save(update_fields=["is_used"])

    def __str__(self):
        return f"{self.user.identifiant} - {self.channel}"

class TelegramOTP2FA(models.Model):
    user = models.OneToOneField(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    secret_key = models.CharField(max_length=32, default=pyotp.random_base32)
    last_used = models.DateTimeField(null=True, blank=True)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def generate_otp(self):
        """Génère un code OTP temporaire  de 6 chiffres à partir du secret key de l'utilisateur."""
        totp = pyotp.TOTP(self.secret_key, interval=300)  # 5 minutes de validité
        return totp.now()

    def verify_otp_telegram(self, otp_code):
        """Vérifie un code OTP"""
        totp = pyotp.TOTP(self.secret_key, interval=300)
        is_valid = totp.verify(otp_code)
        if is_valid:
            self.last_used = timezone.now()
            self.save()
        return is_valid

    @classmethod
    def get_or_create_for_user(cls, user):
        obj, created = cls.objects.get_or_create(user=user)
        return obj

class PDFManager(models.Model):
    DOCUMENT_TYPES = [
        ('USER_LIST', 'Liste des utilisateurs'),
        ('ANNUAL_COTISATION', 'Cotisation annuelle'),
        ('OCCASIONNAL_COTISATION', 'Cotisation occasionnelle'),
        ('DONS', 'Rapport des ventes'),
        ('DEPENSES', 'Dépenses effectuées'),
        ('BILAN_CAISSE', 'Bilan financier'),
        ('INFO', 'Annonces ')
        # Ajoutez d'autres types selon vos besoins
    ]

    title = models.CharField(max_length=255, verbose_name="Titre")
    description = models.TextField(verbose_name="Description")
    file = models.FileField(upload_to='pdfs/%Y/%m/%d/', verbose_name="Fichier PDF")
    document_type = models.CharField(
        max_length=100,
        choices=DOCUMENT_TYPES,
        verbose_name="Type de document"
    )
    created_by = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        related_name='generated_pdfs',
        verbose_name="Créé par"
    )
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="Date de création")

    class Meta:
        ordering = ['-created_at']
        verbose_name = "PDF généré"
        verbose_name_plural = "PDFs générés"

    def __str__(self):
        return f"{self.title} - {self.created_at.strftime('%d/%m/%Y')}"

    @property
    def file_name(self):
        return self.file.name.split('/')[-1]



class DashboardModule(models.Model):
    name = models.CharField(max_length=100)
    icon = models.CharField(max_length=50)  # Classe Font Awesome
    description = models.TextField()
    url_name = models.CharField(max_length=100)
    required_role = models.CharField(max_length=20, choices=User.ROLE_CHOICES)
    order = models.IntegerField(default=0)
    is_active = models.BooleanField(default=True)

    class Meta:
        ordering = ['order']


class ResetPasswordToken(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    token = models.UUIDField(default=uuid.uuid4, editable=False)
    created_at = models.DateTimeField(auto_now_add=True)
    expiration = models.DateTimeField()
    used = models.BooleanField(default=False)

    def is_valid(self):
        return not self.used and self.expiration > timezone.now()


#Gestions de participations annuel

class ParticipationAnnual(models.Model):
    created_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True,
                                   related_name='manager_participation_annuel')
    participant_id = models.ForeignKey(User, on_delete=models.CASCADE, null=False, blank=False)
    montant_participation = models.DecimalField(max_digits=10, decimal_places=2, null=False, blank=False)
    year = models.PositiveIntegerField(default=current_year)
    date_participation = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True, null=True, blank=True)

    def __str__(self):
        return f"{self.participant_id} - {self.date_participation}"
class ParticipationOccasionnelle(models.Model):
    created_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True,
                                   related_name='manager_participation_occasionnelle')
    participant_id = models.ForeignKey(User, on_delete=models.CASCADE, null=False, blank=False)
    montant_participation = models.DecimalField(max_digits=10, decimal_places=2, null=False, blank=False)
    motif_participation = models.TextField(null=False, blank=False)
    year = models.PositiveIntegerField(default=current_year)
    date_participation = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.participant_id} - {self.montant_participation} - {self.motif_participation} - {self.date_participation}"

class Dons(models.Model):
    created_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True,
                                   related_name='manager_dons')
    nom = models.CharField(max_length=60, blank=True)
    prenom = models.CharField(max_length=60, blank=False, null=False)
    montant_don = models.DecimalField(max_digits=10, decimal_places=2, null=False, blank=False)
    motif_don = models.TextField(null=False, blank=False)
    date_don = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True, null=True, blank=True)

    def __str__(self):
        return f"{self.nom} - {self.prenom} - {self.montant_don} - {self.date_don}"
class AddDepenses(models.Model):
    # Manager est le nom  de la personne qui a inscrit les dépenses
    created_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True)
    montant_depense = models.DecimalField(max_digits=10, decimal_places=2, null=False, blank=False)
    motif_depense = models.TextField(null=False, blank=False)
    date_depense = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True, null=True, blank=True)

class EditorialCommunity(models.Model):
    title = models.CharField(max_length=255, blank=False, null=False)
    content = models.TextField(blank=False, null=False)
    image = models.ImageField(upload_to='images/missidhe_bourou_img', blank=True, null=True)
    extra_links = models.URLField(blank=True, null=True)
    author = models.CharField(max_length=60, blank=False, null=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True, null=True, blank=True)



'Geestion de model view postgresql'

class MissidehBourouMembersView(pgview.View):
    id = models.IntegerField(primary_key=True)
    identifiant = models.CharField(max_length=100)
    prenoms = models.CharField(max_length=100)
    quartier = models.CharField(max_length=100)
    pays = models.CharField(max_length=100)
    telephone = models.CharField(max_length=100)
    email = models.CharField(max_length=100)

    sql = """
        SELECT
            id,
            identifiant,
            prenoms,
            quartier,
            pays,
            telephone,
            email
            FROM "Bapp_btestcustomuser";
    """
    class Meta:
        managed = False
        db_table = 'missideh_bourou_members_view'

class CotisationOccasionnelleView(pgview.View):
    prenom = models.CharField(max_length=100)
    quartier = models.CharField(max_length=100)
    montant = models.DecimalField(max_digits=10, decimal_places=2)
    motif_cotisation = models.TextField()
    date_cotisation = models.DateTimeField()

    sql = """
    select b.prenoms,
    b.quartier,  
    p.montant_participation, 
    p.motif_participation, 
    to_char(p.updated_at, 'DD/MM/YYYY')
    from "Bapp_btestcustomuser" b 
    inner join "Bapp_participationoccasionnelle" p on b.id = p.participant_id_id
    order by p.updated_at desc;
    """
    class Meta:
        managed = False
        db_table = 'cotisation_occasionnelle_view'

class CotisationAnnuelleView(pgview.View):
    prenom = models.CharField(max_length=100)
    quartier = models.CharField(max_length=100)
    montant = models.DecimalField(max_digits=10, decimal_places=2)
    date_cotisation = models.DateTimeField()

    sql = """
    select b.prenoms, 
    b.quartier,  
    p.montant_participation,  
    to_char(p.updated_at, 'DD/MM/YYYY')
    from "Bapp_btestcustomuser" b 
    inner join "Bapp_participationannual" p on b.id = p.participant_id_id
    order by p.updated_at desc;
    """
    class Meta:
        managed = False
        db_table = 'cotisation_annuelle_view'

class DonsView(pgview.View):
    nom = models.CharField(max_length=100)
    prenom = models.CharField(max_length=100)
    montant = models.DecimalField(max_digits=10, decimal_places=2)
    motif_don = models.TextField()
    date_don = models.DateTimeField()

    sql = """
    select prenom, 
    nom, 
    montant_don, 
    motif_don, 
    to_char(updated_at, 'DD/MM/YYY') as date_don
    from "Bapp_dons" 
    order by updated_at desc;
    """
    class Meta:
        managed = False
        db_table = 'dons_view'
class DepensesView(pgview.View):
    montant = models.DecimalField(max_digits=10, decimal_places=2)
    motif_depense = models.TextField()
    date_depense = models.DateTimeField()

    sql = """
        select montant_depense, 
        motif_depense, 
        to_char(date_depense, 'DD/MM/YYYY') as date_depense
        from "Bapp_adddepenses"
        order by date_depense desc;
    """
    class Meta:
        managed = False
        db_table = 'depenses_view'
class TotauxView(pgview.View):
    montant_cotisationannuel = models.DecimalField(max_digits=10, decimal_places=2)
    montant_cotisationoccasionnelle = models.DecimalField(max_digits=10, decimal_places=2)
    montant_dons = models.DecimalField(max_digits=10, decimal_places=2)
    montant_depenses = models.DecimalField(max_digits=10, decimal_places=2)

    sql = """
    select 'TOTAL COTISATION ANNUEL' as type_total, coalesce(sum(montant_participation), 0) as total,
    to_char(current_date, 'DD/MM/YYYY') as aujourdhui
    from "Bapp_participationannual"
    union all
    select 'TOTAL COTISATION OCCASIONNELLE' as type_total, coalesce(sum(montant_participation), 0) as total,
    to_char(current_date, 'DD/MM/YYYY') as aujourdhui
    from "Bapp_participationoccasionnelle"
    union all
    select 'TOTAL DONS ' as type_total, coalesce(sum(montant_don), 0) as total,
    to_char(current_date, 'DD/MM/YYYY') as aujourdhui
    from "Bapp_dons"
    union all
    select 'TOTAL DEPENSE' as type_total, coalesce(sum(montant_depense), 0) as total,
    to_char(current_date, 'DD/MM/YYYY') as aujourdhui
    from "Bapp_adddepenses";
    """
    class Meta:
       managed = False
       db_table = 'totaux_view'