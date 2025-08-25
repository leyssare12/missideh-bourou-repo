# Utiliser l'image Python officielle
FROM python:3.12-slim

# Définir le répertoire de travail
WORKDIR /Btest

# Installer les dépendances système nécessaires (postgresql-client + netcat)
RUN apt-get update && apt-get install -y postgresql-client netcat-openbsd && rm -rf /var/lib/apt/lists/*

# Copier les fichiers de dépendances
COPY requirements.txt .

# Installer les dépendances Python
RUN pip install --no-cache-dir -r requirements.txt

# Copier le reste du code source
COPY . .
# Créer le répertoire PDF dans l'image (pour éviter l'erreur au démarrage)
RUN mkdir -p /Btest/pdf
RUN mkdir -p /Btest/Bapp/media/images
# Exposer le port sur lequel Django va tourner
#EXPOSE 8000

# Définir la commande par défaut (ex : Gunicorn ou Django runserver)
CMD ["python", "manage.py", "runserver", "0.0.0.0:8000"]

