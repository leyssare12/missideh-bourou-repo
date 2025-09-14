# app/forms.py
from django import forms

from django import forms
from django.utils.text import slugify

from .models import Image
from PIL import Image as PILImage
from io import BytesIO
from django.core.files.base import ContentFile
from PIL import ImageOps  # ajout: pour corriger orientation EXIF



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
#
# ... existing code ...

class MultiImageUploadForm(forms.Form):
    titres = forms.CharField(
        required=False,
        widget=forms.TextInput(attrs={"placeholder": "Titre(s) séparés par des virgules, Exp: image 1, image 2"})
    )
    fichiers = MultiImageField()

    # Contraintes et formats acceptés
    MAX_SIZE_BYTES = 10 * 1024 * 1024  # 5 Mo
    ALLOWED_FORMATS = {"JPEG", "JPG", "PNG", "WEBP"}

    # Cibles de compression (en Ko) pour minimiser le poids
    TARGET_ORIGINAL_KB = 300
    TARGET_MOBILE_KB = 120
    TARGET_THUMB_KB = 35

    # Bornes de qualité pour la recherche binaire WEBP
    MIN_QUALITY = 35
    MAX_QUALITY = 90
    SEARCH_STEPS = 5  # itérations max de recherche (réduit)

    # Limites pixels pour éviter explosion mémoire
    MAX_PIXELS = 36_000_000  # ex: 6k x 6k
    MAX_SIDE = 12000  # largeur/hauteur max acceptée

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._validated_files = None  # sera rempli après clean()

    def _has_alpha(self, img: PILImage.Image) -> bool:
        mode = img.mode
        if mode in ("RGBA", "LA"):
            return True
        if mode == "P":
            return "transparency" in (img.info or {})
        return False

    def _exif_transpose(self, img: PILImage.Image) -> PILImage.Image:
        try:
            return ImageOps.exif_transpose(img)
        except Exception:
            return img

    def _prepare_img(self, f) -> PILImage.Image:
        f.seek(0)
        img = PILImage.open(f)
        # Hint: pour JPEG énormes, réduire résolution décodée
        try:
            if img.format and img.format.upper() in ("JPEG", "JPG"):
                img.draft("RGB", (4096, 4096))
        except Exception:
            pass
        img = self._exif_transpose(img)
        return img

    def _encode_webp_bytes(self, img: PILImage.Image, quality: int, lossless: bool) -> bytes:
        buf = BytesIO()
        img.save(
            buf,
            format="WEBP",
            quality=int(quality),
            method=6,  # compression plus lente mais plus efficace
            lossless=bool(lossless)
        )
        return buf.getvalue()

    def _resize_keep_ratio(self, img: PILImage.Image, max_w: int, max_h: int) -> PILImage.Image:
        out = img.copy()
        out.thumbnail((max_w, max_h), PILImage.LANCZOS)
        return out

    def _contentfile_target_webp(self, img: PILImage.Image, max_w: int, max_h: int, target_kb: int) -> ContentFile:
        # Redimensionne
        work = self._resize_keep_ratio(img, max_w, max_h)

        # Gestion alpha: WEBP supporte l'alpha
        lossless = False  # privilégier lossy pour poids minimal

        # Essai rapide à qualité basse: early exit si déjà sous la cible
        first_q = max(self.MIN_QUALITY, 40)
        first_bytes = self._encode_webp_bytes(work, first_q, lossless=lossless)
        if len(first_bytes) // 1024 <= target_kb:
            return ContentFile(first_bytes)

        # Recherche binaire de qualité pour approcher target_kb
        lo, hi = self.MIN_QUALITY, self.MAX_QUALITY
        best_bytes = None
        for _ in range(self.SEARCH_STEPS):
            q = (lo + hi) // 2
            data = self._encode_webp_bytes(work, q, lossless=lossless)
            size_kb = len(data) // 1024
            if size_kb <= target_kb:
                best_bytes = data
                hi = q - 1
            else:
                lo = q + 1

        if best_bytes is None:
            # si aucune tentative n'est sous la cible, garder la version la plus basse raisonnable
            best_bytes = self._encode_webp_bytes(work, lo, lossless=lossless)

        return ContentFile(best_bytes)

    def clean(self):
        cleaned = super().clean()

        # Utiliser la valeur nettoyée du champ, pas self.files.getlist()
        files = cleaned.get("fichiers") or []
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

            # 2) Taille brute
            if f.size > self.MAX_SIZE_BYTES:
                size_mo = round(self.MAX_SIZE_BYTES / 1024 / 1024, 2)
                errors.append(f"Le fichier #{idx} dépasse {size_mo} Mo ({round(f.size / 1024 / 1024, 2)} Mo).")
                continue

            # 3) Validation de base via PIL (sans double ouverture/verify)
            try:
                f.seek(0)
                with PILImage.open(f) as img:
                    fmt = (img.format or "").upper()
                    if fmt == "JPG":
                        fmt = "JPEG"
                    if fmt not in self.ALLOWED_FORMATS:
                        errors.append(
                            f"Format non supporté pour le fichier #{idx} ({fmt or 'inconnu'}). "
                            f"Formats autorisés: JPEG, PNG, WEBP."
                        )
                        continue

                    # Limite de dimensions pour éviter OOM
                    w, h = img.size
                    if w > self.MAX_SIDE or h > self.MAX_SIDE or (w * h) > self.MAX_PIXELS:
                        errors.append(
                            f"Le fichier #{idx} a des dimensions trop grandes ({w}x{h}). "
                            f"Maximum autorisé: {self.MAX_SIDE}px de côté et {self.MAX_PIXELS} pixels au total."
                        )
                        continue
            except Exception:
                errors.append(f"Le fichier #{idx} est corrompu ou non lisible en tant qu'image.")
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
            titre = titres_list[i] if i < len(titres_list) else f"Image {i + 1}"
            safe_name = slugify(titre) or f"image-{i + 1}"

            # Ouvre pour traitement (image unique à la fois pour limiter mémoire)
            img = None
            try:
                img = self._prepare_img(uploaded)

                # Conversion couleur si nécessaire (éviter CMYK etc.)
                if img.mode not in ("RGB", "L", "RGBA", "LA", "P"):
                    img = img.convert("RGB")

                # 1) Original optimisé (max 1920x1080) vers WEBP cible ~300 Ko
                original_content = self._contentfile_target_webp(
                    img, max_w=1920, max_h=1080, target_kb=self.TARGET_ORIGINAL_KB
                )

                # 2) Version mobile (max 800x800) vers WEBP cible ~120 Ko
                mobile_content = self._contentfile_target_webp(
                    img, max_w=800, max_h=800, target_kb=self.TARGET_MOBILE_KB
                )

                # 3) Thumbnail carré 300x300 (crop center) vers WEBP cible ~35 Ko
                thumb = img.copy()
                w, h = thumb.size
                min_side = min(w, h)
                left = max(0, (w - min_side) // 2)
                top = max(0, (h - min_side) // 2)
                thumb = thumb.crop((left, top, left + min_side, top + min_side))
                thumb = thumb.resize((300, 300), PILImage.LANCZOS)
                thumb_content = self._contentfile_target_webp(
                    thumb, max_w=300, max_h=300, target_kb=self.TARGET_THUMB_KB
                )

                # Création instance
                instance = ImageModel(titre=titre)

                # Noms de fichiers sûrs (.webp)
                original_name = f"{safe_name}.webp"
                mobile_name = f"{safe_name}-mobile.webp"
                thumb_name = f"{safe_name}-thumb.webp"

                if commit:
                    instance.fichier.save(original_name, original_content, save=False)
                    instance.fichier_mobile.save(mobile_name, mobile_content, save=False)
                    instance.fichier_thumbnail.save(thumb_name, thumb_content, save=False)
                    instance.save()
                else:
                    instance.fichier.save(original_name, original_content, save=False)
                    instance.fichier_mobile.save(mobile_name, mobile_content, save=False)
                    instance.fichier_thumbnail.save(thumb_name, thumb_content, save=False)

                instances.append(instance)
            finally:
                try:
                    if img is not None:
                        img.close()
                except Exception:
                    pass

        return instances
