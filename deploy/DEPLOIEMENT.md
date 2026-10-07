# Déploiement sur serveur Windows (hors-ligne)

Ce dossier contient tout ce qu'il faut pour installer le simulateur sur un serveur
Windows **sans accès Internet**. L'application écoute ensuite sur le port **8080** et est
accessible depuis les postes du réseau.

## Contenu

| Fichier / dossier | Rôle |
|-------------------|------|
| `python-3.12.8-amd64.exe` | Installateur Python (à installer une fois) |
| `installer.bat` | Installe les paquets Python (hors-ligne) et initialise la base |
| `demarrer-serveur.bat` | Démarre l'application (manuel) |
| `installer-service.bat` | Démarrage automatique au reboot + règle de pare-feu |
| `backend/` | Code de l'application + frontend compilé (`static/`) + paquets (`wheels/`) |
| `backend/.env` | Mot de passe de l'administration |

## Installation

### Étape 1 — Installer Python (une fois)

1. Double-cliquez sur `python-3.12.8-amd64.exe`.
2. Cochez **« Add Python to PATH »**.
3. Choisissez **« Install for all users »** (recommandé pour que le service au démarrage
   trouve Python), puis terminez l'installation.

### Étape 2 — Installer l'application (une fois)

Double-cliquez sur **`installer.bat`** (validez l'invite UAC). Ce script :
- vérifie Python,
- installe les paquets depuis `backend/wheels` (aucune connexion Internet),
- initialise la base de données.

### Étape 3 — Choisir le mode de démarrage

**Démarrage automatique au reboot (recommandé)** : double-cliquez sur
**`installer-service.bat`** (validez l'invite UAC). Il crée une tâche planifiée Windows qui
relance l'application à chaque démarrage du serveur, ouvre le port 8080 dans le pare-feu et
démarre l'application immédiatement.

**Démarrage manuel** : double-cliquez sur **`demarrer-serveur.bat`**. L'application tourne
tant que la fenêtre reste ouverte (Ctrl+C pour arrêter).

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
2. Redémarrez l'application (pour le mode service : `schtasks /End /TN SimulateurPaie`
   puis `schtasks /Run /TN SimulateurPaie`, ou redémarrez simplement le serveur).

## Administration courante

- **Arrêter** (mode service) : `schtasks /End /TN SimulateurPaie`
- **Redémarrer** (mode service) : `schtasks /Run /TN SimulateurPaie`
- **Voir les journaux** : la fenêtre de `demarrer-serveur.bat` affiche les requêtes ;
  la base est dans `backend\paie.db`.

## Mise à jour de l'application

Remplacez le dossier `backend\` par une nouvelle version, puis relancez `installer.bat`
(il réinstalle les paquets et préserve la base tant qu'elle est déjà remplie).
