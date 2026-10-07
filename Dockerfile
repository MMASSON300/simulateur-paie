# ------------------------------------------------------------------------------
# Simulateur de salaire — image unique (backend FastAPI + frontend compilé)
# ------------------------------------------------------------------------------

# Étape 1 : compilation du frontend React/Vite
FROM node:24-alpine AS frontend-build
WORKDIR /frontend
COPY frontend/package.json frontend/package-lock.json ./
RUN npm ci
COPY frontend/ ./
RUN npm run build

# Étape 2 : backend Python (sert l'API + les fichiers statiques du frontend)
FROM python:3.12-slim
WORKDIR /app

COPY backend/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY backend/app ./app
COPY --from=frontend-build /frontend/dist ./static

COPY docker-entrypoint.sh /docker-entrypoint.sh
RUN chmod +x /docker-entrypoint.sh

# Base de données SQLite dans un volume (persistance).
ENV DATABASE_URL=sqlite:////data/paie.db
VOLUME ["/data"]

EXPOSE 8000

ENTRYPOINT ["/docker-entrypoint.sh"]
