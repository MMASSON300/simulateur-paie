# Déploiement sur serveur Windows (hors-ligne)

Ce dossier contient tout ce qu'il faut pour installer le simulateur sur un serveur
Windows **sans accès Internet**. L'application écoute ensuite sur le port **8080** et est
accessible depuis les postes du réseau.

## Contenu

| Fichier / dossier | Rôle |
|-------------------|------|
| `installer.bat` | **Installation tout-en-un** (à double-cliquer une seule fois) |
| `python-3.12.8-amd64.exe` | Installateur Python (utilisé automatiquement si besoin) |
| `demarrer-serveur.bat` | Démarre l'application (utilisé par la tâche planifiée) |
| `backend/wheels/` | Paquets Python hors-ligne pour **Python 3.12** (`cp312/`) et **3.13** (`cp313/`) |
| `backend/static/` | Frontend compilé (autonome, sans Google Fonts) |
| `backend/.env` | Mot de passe de l'administration |

## Installation (en un clic)

Double-cliquez sur **`installer.bat`** (validez l'invite UAC). Le script fait tout
automatiquement :

1. **Détecte Python 3.12 / 3.13** (via le lanceur `py`, les chemins d'installation ou le PATH).
   - Si une version compatible est déjà présente, il l'utilise **sans rien écraser**.
   - Si une version **plus récente** (3.14+) est présente, il **n'y touche pas** et installe
     Python 3.12 à côté (dossier séparé, sans modifier le PATH).
   - Si aucun Python n'est présent, il installe silencieusement `python-3.12.8-amd64.exe`.
2. **Installe les paquets hors-ligne** correspondant à la version détectée.
3. **Initialise la base de données**.
4. **Configure le démarrage automatique** au reboot (tâche planifiée `SimulateurPaie`) et
   ouvre le port 8080 dans le pare-feu.
5. **Propose de démarrer** l'application immédiatement.
6. **Affiche le récapitulatif** : adresse d'accès, état du démarrage auto, commandes utiles,
   emplacement du mot de passe.

## Accès depuis les postes

Depuis un poste du réseau, ouvrez un navigateur sur :

- **http://srvadmin3:8080** (si le nom est résolu par le DNS de l'entreprise), ou
- **http://<adresse-IP-du-serveur>:8080**

Le simulateur s'ouvre. L'onglet **Administration** demande le mot de passe (voir plus bas).

## Changer le mot de passe d'administration

1. Éditez `backend\.env` :
   ```
   ADMIN_PASSWORD=votre-mot-de-passe
   ```
2. Redémarrez l'application : `schtasks /End /TN SimulateurPaie` puis
   `schtasks /Run /TN SimulateurPaie` (ou redémarrez le serveur).

## Administration courante

- **Arrêter** : `schtasks /End /TN SimulateurPaie`
- **Redémarrer** : `schtasks /Run /TN SimulateurPaie`
- **Démarrage manuel (test)** : double-cliquez sur `demarrer-serveur.bat`
- **Voir les journaux** : la fenêtre de `demarrer-serveur.bat` affiche les requêtes ;
  la base est dans `backend\paie.db`.

## Réinstaller / réparer

Relancez simplement `installer.bat` : il réinstalle les paquets et préserve la base
(tant qu'elle est déjà remplie). Pour repartir de zéro, supprimez `backend\paie.db` avant.

## Mise à jour de l'application

Remplacez le dossier `backend\` par une nouvelle version (code + `wheels/` + `static/`),
puis relancez `installer.bat`.
