# app/forms.py
from django import forms
from django.utils.text import slugify

from .models import Image
from PIL import Image as PILImage
from io import BytesIO
from django.core.files.base import ContentFile



class MultiFileInput(forms.ClearableFileInput):
    allow_multiple_selected = True  # ⚡ active "multiple"

class MultiImageField(forms.FileField):
    def __init__(self, *args, **kwargs):
        kwargs["widget"] = MultiFileInput()
        super().__init__(*args, **kwargs)

    def clean(self, data, initial=None):
        if not data:
            return []
        if not isinstance(data, (list, tuple)):
            data = [data]
        return data

# ... existing code ...

class MultiImageUploadForm(forms.Form):
    titres = forms.CharField(
        required=True,
        widget=forms.TextInput(attrs={"placeholder": "Titre(s) séparés par des virgules"})
    )
    fichiers = MultiImageField()

    # Contraintes et formats acceptés
    MAX_SIZE_BYTES = 5 * 1024 * 1024  # 5 Mo
    ALLOWED_FORMATS = {"JPEG", "JPG", "PNG", "WEBP"}

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._validated_files = None  # sera rempli après clean()

    def clean(self):
        cleaned = super().clean()

        # Récupère tous les fichiers du champ multiupload
        files = self.files.getlist("fichiers")
        if not files:
            raise forms.ValidationError("Veuillez sélectionner au moins une image.")

        validated = []
        errors = []

        for idx, f in enumerate(files, start=1):
            # 1) Type MIME basique
            ctype = (getattr(f, "content_type", "") or "").lower()
            if not ctype.startswith("image/"):
                errors.append(f"Le fichier #{idx} n'est pas une image (type: {ctype or 'inconnu'}).")
                continue

            # 2) Taille
            if f.size > self.MAX_SIZE_BYTES:
                errors.append(f"Le fichier #{idx} dépasse 5 Mo ({round(f.size/1024/1024, 2)} Mo).")
                continue

            # 3) Validation PIL + format
            try:
                f.seek(0)
                img = PILImage.open(f)
                img.verify()  # vérifie l’intégrité
            except Exception:
                errors.append(f"Le fichier #{idx} est corrompu ou non lisible en tant qu'image.")
                continue

            # Ré-ouvrir après verify()
            f.seek(0)
            try:
                img = PILImage.open(f)
            except Exception:
                errors.append(f"Impossible d’ouvrir le fichier #{idx} pour traitement.")
                continue

            fmt = (img.format or "").upper()
            if fmt == "JPG":
                fmt = "JPEG"
            if fmt not in self.ALLOWED_FORMATS:
                errors.append(f"Format non supporté pour le fichier #{idx} ({fmt or 'inconnu'}). "
                              f"Formats autorisés: JPEG, PNG, WEBP.")
                continue

            validated.append((f, fmt))

        if errors:
            raise forms.ValidationError(errors)

        self._validated_files = validated
        return cleaned

    def save(self, commit=True):
        """
        Traite et enregistre les images uniquement si toutes les validations sont passées.
        Retourne une liste d’instances Image persistées.
        """
        from Caroussel.models import Image as ImageModel  # import local pour éviter conflits de nom

        if self._validated_files is None:
            raise RuntimeError("Le formulaire doit être validé (is_valid) avant l’enregistrement.")

        titres = self.cleaned_data.get("titres", "")
        titres_list = [t.strip() for t in titres.split(",")] if titres else []

        instances = []

        for i, (uploaded, fmt) in enumerate(self._validated_files):
            # Titre
            titre = titres_list[i] if i < len(titres_list) else f"Image {i+1}"
            safe_name = slugify(titre) or f"image-{i+1}"

            # Ouvre pour traitement
            uploaded.seek(0)
            img = PILImage.open(uploaded)

            # Conversion couleur
            if img.mode not in ("RGB", "L"):  # L = niveaux de gris (ok), sinon converti en RGB
                img = img.convert("RGB")

            # 1) Original optimisé (max 1920x1080)
            original = img.copy()
            original.thumbnail((1920, 1080))
            original_buf = BytesIO()
            # On normalise en JPEG pour la compat globale
            original.save(original_buf, format="JPEG", quality=85, optimize=True)
            original_content = ContentFile(original_buf.getvalue())

            # 2) Version mobile (max 800 px côté large)
            mobile = img.copy()
            mobile.thumbnail((800, 800))
            mobile_buf = BytesIO()
            mobile.save(mobile_buf, format="JPEG", quality=80, optimize=True)
            mobile_content = ContentFile(mobile_buf.getvalue())

            # 3) Thumbnail carré 300x300 (crop center)
            thumb = img.copy()
            # Fit carré
            thumb_ratio = 300
            w, h = thumb.size
            min_side = min(w, h)
            left = max(0, (w - min_side) // 2)
            top = max(0, (h - min_side) // 2)
            thumb = thumb.crop((left, top, left + min_side, top + min_side))
            thumb = thumb.resize((thumb_ratio, thumb_ratio), PILImage.LANCZOS)
            thumb_buf = BytesIO()
            thumb.save(thumb_buf, format="JPEG", quality=80, optimize=True)
            thumb_content = ContentFile(thumb_buf.getvalue())

            # Création instance
            instance = ImageModel(titre=titre)

            # Noms de fichiers sûrs
            original_name = f"{safe_name}.jpg"
            mobile_name = f"{safe_name}-mobile.jpg"
            thumb_name = f"{safe_name}-thumb.jpg"

            if commit:
                instance.fichier.save(original_name, original_content, save=False)
                instance.fichier_mobile.save(mobile_name, mobile_content, save=False)
                instance.fichier_thumbnail.save(thumb_name, thumb_content, save=False)
                instance.save()
            else:
                # Si commit=False, on attache quand même les File
                instance.fichier.save(original_name, original_content, save=False)
                instance.fichier_mobile.save(mobile_name, mobile_content, save=False)
                instance.fichier_thumbnail.save(thumb_name, thumb_content, save=False)

            instances.append(instance)

        return instances

# ... existing code ...