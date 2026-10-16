# AGENTS.md — consignes de travail

Simulateur de bulletin de paie (fonction publique territoriale, Mairie d'Ivry-sur-Seine).
Monorepo : `backend/` (FastAPI + moteur de calcul), `frontend/` (React/Vite), `deploy/`
(package serveur hors-ligne). Documentation complète dans `README.md`.

## Règles non négociables
- `backend/app/engine.py` est une **transcription fidèle des formules du classeur Excel**.
  Toute modification de calcul doit être couverte par `backend/tests/test_engine.py`.
- **Jamais de table de correspondance d'exceptions** : corriger la **donnée**
  (`backend/app/seed_data/*.json`), pas le code.
- **Ne rien committer sans demande explicite.** **Toujours demander validation avant `git push`.**
- Ne jamais versionner : `.env`, `*.db`, `*.xlsm`, `deploy/backend/`, `deploy/*.exe`,
  `simulateur-paie-serveur.zip`, `HANDOFF.md`.
- Version interne `V1.2026.10` : à mettre à jour dans **`backend/app/main.py`** (`FastAPI(version=…)`)
  **et** `frontend/src/App.tsx` (pastille `version-pill`).
- UI en **français**, nombres au format `fr-FR` (`1 234,56 €`, `5,00 %` ; `pct()` multiplie par 100).
- **Aucune dépendance externe à l'exécution** : l'app doit fonctionner hors-ligne (aucun CDN).

## Commandes
Backend (depuis `backend/`) :
- Tests moteur : `python -m tests.test_engine`
- Seed : `python -m app.seed` (idempotent) / `python -m app.seed --force` (réinitialise)

Frontend (depuis `frontend/`) :
- Build : `npm run build` · Lint : `npm run lint` · Dev : `npm run dev` (proxy `/api` → :8000)

Docker (racine) :
- `docker compose up -d --build` → http://localhost/
- `docker compose down -v` pour **purger la base** si schéma ou seed modifié

## Livraison d'une modification (Release serveur hors-ligne)
1. `python -m tests.test_engine` + `npm run build` + `npm run lint` → tout OK.
2. Synchroniser le package : `robocopy backend\app deploy\backend\app /E /XD __pycache__`,
   vider `deploy\backend\static` puis `robocopy frontend\dist deploy\backend\static /E`.
3. Régénérer le zip avec **`tar`** (PAS `Compress-Archive`) :
   `tar -a -c -f simulateur-paie-serveur.zip -C deploy backend demarrer-serveur.bat DEPLOIEMENT.md installer.bat mettre-a-jour.bat python-3.12.8-amd64.exe`
4. `gh release create vX.Y "simulateur-paie-serveur.zip" --title "…" --notes-file <notes.md>`.
5. Commit (message court, style existant) puis **push après accord**.

## Environnement
- **Windows / PowerShell 5.1** : pas de `&&` → utiliser `;` et `if ($?) { … }`.
- Le `git push` écrit sur **stderr** : l'affichage rouge de PowerShell est **normal**, le push réussit.
