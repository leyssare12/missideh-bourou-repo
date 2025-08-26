
import pyotp
import qrcode
import io
import base64

def generate_otp_secret():
    return pyotp.random_base32()

def get_qr_code_uri(user, secret):
    totp = pyotp.TOTP(secret)
    return totp.provisioning_uri(
        name=user.prenoms,        # ou user.prenoms
        issuer_name="Missideh-Bourou"   # nom affiché dans Google Authenticator
    )

def generate_qr_code_base64(uri):
    img = qrcode.make(uri)
    buf = io.BytesIO()
    img.save(buf, format='PNG')

    return base64.b64encode(buf.getvalue()).decode('utf-8')

def verify_otp(secret, code):
    totp = pyotp.TOTP(secret)
    return totp.verify(code)
