# Dockerfile pour l'environnement Python de migration
FROM python:3.11-slim

# Définir le répertoire de travail
WORKDIR /app

# Copier le fichier requirements.txt
COPY requirements.txt .

# Installer les dépendances
RUN pip install --no-cache-dir -r requirements.txt

# Copier tous les scripts Python
COPY *.py ./

# Créer le répertoire pour les données CSV
RUN mkdir -p /data/csv

# Volume pour les données CSV (sera monté depuis docker-compose)
VOLUME ["/data/csv"]

# Commande par défaut (peut être surchargée)
CMD ["python", "migrate_to_mongodb.py"]

