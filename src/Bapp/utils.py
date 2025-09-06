import json
import re
import subprocess
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen

import requests
from django.contrib import messages

from django.utils import timezone
import time
from django.core.mail import send_mail
from os import getenv

from django.utils.safestring import mark_safe

from BTest import settings

from twilio.rest import Client

from .models import TwoFactorAuth


# Utilitaires Telegram

def _get_telegram_api_base() -> str:
    bot_token = getattr(settings, "TELEGRAM_BOT_TOKEN", None)
    if not bot_token:
        raise ValueError("TELEGRAM_BOT_TOKEN n'est pas défini dans settings.")
    return f"https://api.telegram.org/bot{bot_token}"



