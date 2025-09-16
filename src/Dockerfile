# Utiliser l'image Python officielle
#FROM python:3.12-slim
#
## Définir le répertoire de travail
#WORKDIR /Btest
#
## Installer les dépendances système nécessaires (postgresql-client + netcat)
#RUN apt-get update && apt-get install -y postgresql-client netcat-openbsd && rm -rf /var/lib/apt/lists/*
#
## Copier les fichiers de dépendances
#COPY requirements.txt .
#
## Installer les dépendances Python
#RUN pip install --no-cache-dir -r requirements.txt
#
## Copier le reste du code source
#COPY . .
## Créer le répertoire PDF dans l'image (pour éviter l'erreur au démarrage)
#RUN mkdir -p /Btest/pdf
#RUN mkdir -p /Btest/Bapp/media/images
## Exposer le port sur lequel Django va tourner
##EXPOSE 8000
#
## Définir la commande par défaut (ex : Gunicorn ou Django runserver)
#CMD ["python", "manage.py", "runserver", "0.0.0.0:8000"]


# ---- Image de base ----
FROM python:3.12-slim

# Variables d'environnement utiles
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    POETRY_VIRTUALENVS_CREATE=false

# Installer dépendances système (ajoute ce dont tes libs ont besoin: libjpeg, zlib, etc.)
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    gcc \
    libpq-dev \
    libjpeg-dev \
    zlib1g-dev \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Créer user non-root
ARG USER=MBApp
ARG UID=1000
RUN adduser --disabled-password --gecos "" --uid "${UID}" ${USER}

WORKDIR /MBApp

# Copier requirements et installer (cache minimal)
COPY requirements.txt .
RUN pip install --upgrade pip \
 && pip install --no-cache-dir -r requirements.txt

# Copier le code de l'application
COPY . /MBApp

# Donner les droits à l'utilisateur non-root
RUN chown -R ${USER}:${USER} /MBApp

# Copier entrypoint
COPY ./entrypoint.sh /entrypoint.sh
RUN chmod +x /entrypoint.sh

# Exposer le port d'écoute (Gunicorn / Uvicorn)
EXPOSE 8000

# Switch vers user non-root (sécurité)
USER ${USER}

# Entrypoint gérer migrations/collectstatic et lancement du serveur
ENTRYPOINT ["/entrypoint.sh"]

# Commande par défaut (sera remplacée par l'entrypoint qui exécute le serveur)
CMD ["gunicorn", "--bind", "0.0.0.0:8000", "BTest.wsgi:application"]

