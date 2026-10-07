#!/bin/sh
set -e

# Répertoire de données (base SQLite persistante).
mkdir -p /data

# Initialise la base au premier démarrage (idempotent : ignoré si déjà remplie).
python -m app.seed

# Lance l'application.
exec uvicorn app.main:app --host 0.0.0.0 --port 8000
