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
#FROM python:3.12-slim
#
#ENV PYTHONDONTWRITEBYTECODE=1 \
#    PYTHONUNBUFFERED=1 \
#    DJANGO_SETTINGS_MODULE=BTest.settings
#
#RUN apt-get update && apt-get install -y --no-install-recommends \
#    build-essential gcc libpq-dev libjpeg-dev zlib1g-dev netcat-openbsd curl \
#    && rm -rf /var/lib/apt/lists/*
#
#ARG USER=django
#ARG UID=1000
#RUN adduser --disabled-password --gecos "" --uid "${UID}" ${USER}
#
#WORKDIR /MBourou
#
#COPY requirements.txt .
#RUN pip install --upgrade pip \
# && pip install --no-cache-dir -r requirements.txt
#
#
### Créer le répertoire PDF dans l'image (pour éviter l'erreur au démarrage)
#RUN mkdir -p /MBourou/pdfs
#RUN mkdir -p /MBourou/Bapp/media/images
#
#COPY  . .
#
#RUN chown -R ${USER}:${USER} /MBourou
#
#COPY entrypoint.sh /MBourou/entrypoint.sh
#RUN chmod +x /MBourou/entrypoint.sh
#
#EXPOSE 8000
#
#USER ${USER}
#
#ENTRYPOINT ["/MBourou/entrypoint.sh"]
#CMD ["gunicorn", "--bind", "0.0.0.0:8000", "BTest.wsgi:application"]

# ... existing code ...
#FROM python:3.12-slim
#
#ENV PYTHONDONTWRITEBYTECODE=1 \
#    PYTHONUNBUFFERED=1 \
#    DJANGO_SETTINGS_MODULE=BTest.settings \
#    PYTHONPATH=/MBourou
#
#RUN apt-get update && apt-get install -y --no-install-recommends \
#    build-essential gcc libpq-dev libjpeg-dev zlib1g-dev netcat-openbsd curl \
#    && rm -rf /var/lib/apt/lists/*
#
#ARG USER=django
#ARG UID=1000
#RUN adduser --disabled-password --gecos "" --uid "${UID}" ${USER}
#
#WORKDIR /MBourou
#
#COPY requirements.txt .
#RUN pip install --upgrade pip \
# && pip install --no-cache-dir -r requirements.txt
## ... existing code ...
#RUN mkdir -p /MBourou/pdfs
#RUN mkdir -p /MBourou/Bapp/media/images
#RUN mkdir -p /MBourou/staticfiles
#
## Copie du code avec le bon owner en une seule fois (évite re-COPY de entrypoint)
#COPY --chown=${USER}:${USER} . .
#
## S'assurer que l'entrypoint est exécutable (si présent dans le repo)
#RUN chmod +x /MBourou/entrypoint.sh
#RUN chmod -R 775 /MBourou/staticfiles
## ... existing code ...
#EXPOSE 8000
#
#USER ${USER}
#
#ENTRYPOINT ["/MBourou/entrypoint.sh"]
#CMD ["gunicorn", "--bind", "0.0.0.0:8000", "BTest.wsgi:application"]

FROM python:3.12-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    DJANGO_SETTINGS_MODULE=BTest.settings \
    PYTHONPATH=/MBourou

RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential gcc libpq-dev libjpeg-dev zlib1g-dev netcat-openbsd curl \
    && rm -rf /var/lib/apt/lists/*

ARG USER=django
ARG UID=1000
RUN adduser --disabled-password --gecos "" --uid "${UID}" ${USER}

WORKDIR /MBourou

COPY requirements.txt .
RUN pip install --upgrade pip \
 && pip install --no-cache-dir -r requirements.txt

# Créer tous les répertoires nécessaires AVANT de passer en USER non-root
RUN mkdir -p /MBourou/pdfs \
    /MBourou/Bapp/media/images \
    /MBourou/staticfiles

# Copier tout le code avec le bon owner
COPY --chown=${USER}:${USER} . .

# S'assurer que l'utilisateur d'exécution possède /MBourou (parent compris)
# et que l'entrypoint est exécutable
RUN chown -R ${USER}:${USER} /MBourou \
 && chmod -R 775 /MBourou/staticfiles \
 && chmod +x /MBourou/entrypoint.sh

EXPOSE 8000

USER ${USER}

ENTRYPOINT ["/MBourou/entrypoint.sh"]
CMD ["gunicorn", "--bind", "0.0.0.0:8000", "BTest.wsgi:application"]