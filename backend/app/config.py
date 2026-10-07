"""Configuration de l'application."""

from __future__ import annotations

import os
from pathlib import Path

from dotenv import load_dotenv

BASE_DIR = Path(__file__).resolve().parent.parent

# Charge les variables d'environnement depuis backend/.env (si présent).
load_dotenv(BASE_DIR / ".env")

# Base SQLite par défaut (facilement remplaçable par Postgres via DATABASE_URL).
DATABASE_URL = os.getenv("DATABASE_URL", f"sqlite:///{BASE_DIR / 'paie.db'}")

# Mot de passe d'accès à l'administration (modifiable via la variable d'environnement).
ADMIN_PASSWORD = os.getenv("ADMIN_PASSWORD", "admin")

# Durée de validité d'une session d'administration (en secondes).
SESSION_TTL = int(os.getenv("SESSION_TTL", "86400"))
