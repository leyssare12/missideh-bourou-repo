from django.conf import settings


# Utilitaires Telegram

def _get_telegram_api_base() -> str:
    bot_token = getattr(settings, "TELEGRAM_BOT_TOKEN", None)
    if not bot_token:
        raise ValueError("TELEGRAM_BOT_TOKEN n'est pas défini dans settings.")
    return f"https://api.telegram.org/bot{bot_token}"



