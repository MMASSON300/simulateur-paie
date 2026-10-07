# Simulateur de salaire — Fonction publique territoriale

Application web de simulation de bulletin de paie pour les agents de la fonction publique
territoriale (titulaires et contractuels), transcrite fidèlement depuis le classeur Excel
`Simulateur de salaire 2026.10.xlsm`.

Elle calcule le traitement indiciaire brut, les primes (NBI, IFSE, SFT, Ségur/CTI, prime grand
âge, prime de fin d'année), les indemnités (résidence, différentielle SMIC, compensatrice CSG)
et les cotisations salariales (CNRACL, RAFP, IRCANTEC, SS vieillesse, CSG/RDS), jusqu'au net
à payer.

## Sommaire

- [Fonctionnalités](#fonctionnalités)
- [Architecture](#architecture)
- [Prérequis](#prérequis)
- [Déploiement avec Docker (recommandé)](#déploiement-avec-docker-recommandé)
- [Installation locale (développement)](#installation-locale-développement)
- [Configuration](#configuration)
- [Interface d'administration](#interface-dadministration)
- [API](#api)
- [Tests](#tests)
- [Fidélité au classeur Excel](#fidélité-au-classeur-excel)
- [Mise à jour des données de référence](#mise-à-jour-des-données-de-référence)

## Fonctionnalités

- **Simulation en temps réel** : saisie des paramètres de l'agent (statut, filière → cadre
  d'emploi → grade, échelon, quotité de temps de travail, NBI, nombre d'enfants, régime IFSE,
  primes) et calcul instantané du bulletin.
- **Bulletin détaillé** : éléments de rémunération, cotisations salariales, net à payer
  (avant prélèvement à la source), montants mensuels et annuels (prime de fin d'année incluse).
- **Titulaires et contractuels** : régimes CNRACL/RAFP ou régime général + IRCANTEC selon le
  statut.
- **Administration protégée par mot de passe** : édition des grilles indiciaires, régimes IFSE,
  supplément familial, constantes et paramètres de temps partiel, avec filtres et recherche.
- **Déploiement conteneurisé** : une seule image Docker contenant l'application complète.

## Architecture

| Composant | Technologie | Rôle |
|-----------|-------------|------|
| Backend | Python 3.12+, FastAPI, SQLAlchemy (SQLite) | API REST, moteur de calcul, persistance |
| Frontend | React, TypeScript, Vite | Interface de simulation et d'administration |
| Données | SQLite + JSON de seed | Grilles, régimes IFSE, SFT, constantes |

Structure du dépôt :

```
.
├── Dockerfile               # image unique (backend + frontend compilé)
├── docker-compose.yml       # déploiement simplifié
├── docker-entrypoint.sh     # init base + lancement
├── .env                     # variables docker-compose (mot de passe, port)
├── .dockerignore
├── backend/
│   ├── app/
│   │   ├── main.py          # point d'entrée FastAPI
│   │   ├── engine.py        # moteur de calcul (miroir des formules Excel)
│   │   ├── models.py        # modèles ORM
│   │   ├── schemas.py       # schémas Pydantic
│   │   ├── auth.py          # jeton d'administration
│   │   ├── seed.py          # chargement des données (idempotent)
│   │   ├── extract.py       # extraction des données depuis le .xlsm
│   │   ├── reference.py     # construction des données de référence
│   │   ├── config.py        # configuration (env / .env)
│   │   ├── database.py      # session SQLAlchemy
│   │   ├── routers/         # routes simulation / référence / auth
│   │   └── seed_data/       # JSON extraits du classeur Excel
│   ├── tests/test_engine.py # tests de validation du moteur
│   ├── requirements.txt
│   └── .env                 # mot de passe admin (dev local)
└── frontend/
    └── src/                 # application React
```

## Prérequis

- **Docker** (recommandé) — aucune autre installation requise, ou
- **Python 3.12+** et **Node.js 20+** pour le développement local.

## Déploiement avec Docker (recommandé)

L'image contient à la fois le backend et le frontend compilé. Un seul conteneur suffit.

### Lanceur Windows (double-clic)

Sous Windows, double-cliquez sur **`demarrer.bat`** : il ajoute automatiquement le nom
`simulateur-paie.local` au fichier `hosts` (droits administrateur demandés), démarre
l'application via Docker puis ouvre le navigateur sur **http://simulateur-paie.local/**.

Ce nom d'hôte est plus lisible que `localhost` et peut être modifié en tête du script
(`APP_HOST` et `APP_PORT`).

### 1. Configurer le mot de passe

Éditez le fichier `.env` à la racine :

```env
ADMIN_PASSWORD=mon-mot-de-passe-solide
PORT=80
```

### 2. Lancer l'application

```bash
docker compose up -d --build
```

L'application est alors accessible sur **http://localhost/** (port 80), ou sur
**http://simulateur-paie.local/** après ajout de l'entrée dans le fichier `hosts` :

```
127.0.0.1    simulateur-paie.local
```

### 3. Arrêter / mettre à jour

```bash
docker compose down          # arrête et supprime le conteneur
docker compose up -d --build # reconstruit et relance
```

La base de données est conservée dans un volume Docker (`paie_data`) : les modifications
effectuées dans l'administration survivent aux redémarrages.

### Sans docker-compose

```bash
docker build -t simulateur-paie .
docker run -d \
  -p 80:8000 \
  -e ADMIN_PASSWORD=admin \
  -v simulateur-paie-data:/data \
  --name simulateur-paie \
  simulateur-paie
```

## Installation locale (développement)

### Backend

```powershell
cd backend
python -m venv .venv
.venv\Scripts\Activate.ps1
pip install -r requirements.txt
python -m app.seed
python -m uvicorn app.main:app --reload
```

Le backend écoute sur **http://localhost:8000**.

### Frontend

```powershell
cd frontend
npm install
npm run dev
```

Le frontend écoute sur **http://localhost:5173** et redirige `/api` vers le backend.

## Configuration

Variables d'environnement (lues depuis `backend/.env` en local, ou transmises au conteneur) :

| Variable | Défaut | Description |
|----------|--------|-------------|
| `ADMIN_PASSWORD` | `admin` | Mot de passe de l'interface d'administration |
| `SESSION_TTL` | `86400` | Durée de validité d'une session admin (secondes) |
| `DATABASE_URL` | `sqlite:///paie.db` | URL de connexion à la base de données |
| `STATIC_DIR` | `static/` | Répertoire du frontend compilé (déploiement) |

> **Important** : changez `ADMIN_PASSWORD` avant toute mise en production.

## Interface d'administration

Accessible via l'onglet **Administration**. Le mot de passe est demandé **à chaque accès**.

Permet de modifier en direct :

- **Grades** — grille indiciaire (filière, cadre d'emploi, grade, échelon, indice majoré,
  catégorie), avec filtres par filière, cadre et catégorie ;
- **IFSE** — régimes indemnitaires, avec filtre par régime ;
- **SFT** — supplément familial de traitement (élément fixe et proportionnel par nombre d'enfants) ;
- **Constantes** — valeur du point, plafond SS, SMIC, montants des primes ;
- **Temps partiel** — quotités et facteurs ;
- **Transfert prime point** — montants annuels par catégorie.

Les modifications sont appliquées immédiatement à la simulation.

## API

| Méthode | Endpoint | Description | Accès |
|---------|----------|-------------|-------|
| `POST` | `/api/simuler` | Calcule un bulletin de paie | public |
| `GET`  | `/api/options` | Listes de référence pour les listes déroulantes | public |
| `GET`  | `/api/health` | Vérification de l'état | public |
| `POST` | `/api/auth/login` | Connexion administration (renvoie un jeton) | public |
| `GET`  | `/api/auth/verify` | Vérifie la validité d'un jeton | jeton |
| `GET/POST/PUT/DELETE` | `/api/reference/*` | CRUD des données de référence | jeton |

Les routes protégées attendent l'en-tête `Authorization: Bearer <jeton>`.

## Tests

### Moteur de calcul (backend)

```powershell
cd backend
python -m tests.test_engine
```

Le test vérifie le moteur contre les valeurs calculées et mises en cache par Excel
(brut, net, cotisations, SFT, indemnité CSG, etc.).

### Frontend

```powershell
cd frontend
npm run build   # vérification TypeScript + build
npm run lint    # lint
```

## Fidélité au classeur Excel

Le moteur (`backend/app/engine.py`) est une transcription ligne à ligne des formules du
classeur `Simulateur de salaire 2026.10.xlsm`. Le VBA du classeur ne contient qu'un bouton de
réinitialisation (aucun calcul) : toute la logique est dans les formules, reproduites à
l'identique et validées par les tests.

## Mise à jour des données de référence

Les données de référence proviennent de fichiers JSON (`backend/app/seed_data/`) extraits
automatiquement du classeur Excel. **Le fichier `.xlsm` n'est pas nécessaire au fonctionnement
du site** (seules les données JSON de seed le sont) et n'est pas versionné dans ce dépôt.

Pour régénérer les données après modification du classeur Excel (fichier à fournir localement) :

```powershell
cd backend
python -m app.extract "chemin\vers\Simulateur de salaire 2026.10.xlsm"
python -m app.seed --force
```

`--force` réinitialise la base ; sans l'option, le seed est ignoré si la base est déjà remplie.
