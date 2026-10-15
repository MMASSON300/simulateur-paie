# Déploiement sur serveur Windows (hors-ligne)

Ce dossier contient tout ce qu'il faut pour installer le simulateur sur un serveur
Windows **sans accès Internet**. L'application écoute sur le port **8080** et est accessible
depuis les postes du réseau.

## Contenu

| Fichier / dossier | Rôle |
|-------------------|------|
| `installer.bat` | **Installation tout-en-un** (à double-cliquer une seule fois) |
| `mettre-a-jour.bat` | **Mise à jour** d'une installation existante |
| `python-3.12.8-amd64.exe` | Installateur Python (utilisé automatiquement si besoin) |
| `demarrer-serveur.bat` | Démarre l'application (utilisé par la tâche planifiée) |
| `backend/wheels/` | Paquets Python hors-ligne pour **Python 3.12** (`cp312/`) et **3.13** (`cp313/`) |
| `backend/static/` | Frontend compilé (autonome, sans Google Fonts) |
| `backend/.env` | Mot de passe admin — **créé automatiquement** au 1er démarrage (`admin`) |

## Installation (en un clic)

Double-cliquez sur **`installer.bat`** (validez l'invite UAC). Le script fait tout :

1. **Détecte Python 3.12 / 3.13** (sans écraser une version plus récente ; l'installe sinon).
2. **Installe les paquets hors-ligne** correspondant à la version détectée.
3. **Crée `backend\.env`** s'il n'existe pas (mot de passe admin = `admin`).
4. **Initialise la base de données**.
5. **Configure le démarrage automatique** au reboot (tâche planifiée `SimulateurPaie`) et
   ouvre le port 8080 dans le pare-feu.
6. **Propose de démarrer** l'application puis affiche le récapitulatif.

## Accès depuis les postes

Depuis un poste du réseau, ouvrez un navigateur sur :

- **http://srvadmin3:8080** (si le nom est résolu par le DNS de l'entreprise), ou
- **http://<adresse-IP-du-serveur>:8080**

## Changer le mot de passe d'administration

1. Éditez `backend\.env` (créé automatiquement à l'installation) :
   ```
   ADMIN_PASSWORD=votre-mot-de-passe
   ```
2. Redémarrez l'application : `schtasks /End /TN SimulateurPaie` puis
   `schtasks /Run /TN SimulateurPaie` (ou redémarrez le serveur).

## Mise à jour

1. Téléchargez le nouveau zip de la Release et **extrayez-le dans un nouveau dossier**
   (ne l'écrasez pas sur l'installation en service).
2. Dans ce nouveau dossier, double-cliquez sur **`mettre-a-jour.bat`** (validez l'UAC).
3. Indiquez le **dossier de l'installation existante** (celui qui contient `backend`).

Le script :

- arrête le service ;
- copie les fichiers de la nouvelle version **sans toucher** à `backend\.env` (mot de passe)
  ni à `backend\paie.db` (base de données) ;
- réinstalle les paquets hors-ligne (au cas où ils changent) ;
- **propose** de réinitialiser les données de référence (⚠️ écrase les données modifiées via
  l'interface d'admin — à choisir uniquement si les grilles/IFSE ont changé) ;
- redémarre le service et vérifie qu'il répond.

## Administration courante

- **Arrêter** : `schtasks /End /TN SimulateurPaie`
- **Redémarrer** : `schtasks /Run /TN SimulateurPaie`
- **Démarrage manuel (test)** : double-cliquez sur `demarrer-serveur.bat`
- **Base de données** : `backend\paie.db`

## Repartir de zéro

Supprimez `backend\paie.db` (et éventuellement `backend\.env`) puis relancez `installer.bat`.

## Si le serveur boucle (port 8080 déjà utilisé)

Si le lanceur a été déclenché deux fois, deux instances se disputent le port 8080 et la
console répète `[Errno 10048] ... port 8080`. Depuis une console **administrateur** :

```powershell
schtasks /End /TN SimulateurPaie
Get-CimInstance Win32_Process | Where-Object { $_.CommandLine -match 'demarrer-serveur|uvicorn' } |
  ForEach-Object { Stop-Process -Id $_.ProcessId -Force }
schtasks /Run /TN SimulateurPaie
```

Le script `demarrer-serveur.bat` est depuis **mono-instance** : il ne démarre plus un second
serveur si le port 8080 est déjà occupé.
