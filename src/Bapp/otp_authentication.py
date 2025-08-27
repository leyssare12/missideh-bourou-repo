from functools import lru_cache

import pyotp

import base64
import io
from functools import lru_cache

from PIL import Image
import qrcode
from django.http import HttpResponse, Http404
from qrcode.constants import ERROR_CORRECT_M

from Bapp.models import BTestCustomUser


def generate_otp_secret():
    return pyotp.random_base32()

def get_qr_code_uri(user, secret):
    totp = pyotp.TOTP(secret)
    return totp.provisioning_uri(
        name=user.prenoms,        # ou user.prenoms
        issuer_name="Missideh-Bourou"   # nom affiché dans Google Authenticator
    )
def qrcode_view(request, user_id):
    try:
        user = BTestCustomUser.objects.get(id=user_id)
    except BTestCustomUser.DoesNotExist:
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
def generate_qr_code_base64(uri):
    img = qrcode.make(uri)
    buf = io.BytesIO()
    img.save(buf, format='PNG')

    return base64.b64encode(buf.getvalue()).decode('utf-8')

def verify_otp(secret, code):
    totp = pyotp.TOTP(secret)
    return totp.verify(code)
