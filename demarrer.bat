@echo off
setlocal enabledelayedexpansion

rem ---------------------------------------------------------------------------
rem  Lanceur du simulateur de salaire
rem  - ajoute le nom http://simulateur-paie.local au fichier hosts
rem  - demarre l'application via Docker
rem  - ouvre le navigateur
rem ---------------------------------------------------------------------------

set "APP_HOST=simulateur-paie.local"
set "APP_PORT=80"
set "APP_URL=http://%APP_HOST%"

rem Se placer dans le repertoire du script
cd /d "%~dp0"

rem --- 1. Droits administrateur (necessaires pour modifier le fichier hosts) ---
net session >nul 2>&1
if errorlevel 1 (
    echo [1/4] Elevation des privileges requise pour le fichier hosts...
    powershell -NoProfile -Command "Start-Process -FilePath '%~f0' -Verb RunAs"
    exit /b 0
)

rem --- 2. Ajout de l'entree dans le fichier hosts ---
set "HOSTS=%SystemRoot%\System32\drivers\etc\hosts"
findstr /I /C:"%APP_HOST%" "%HOSTS%" >nul 2>&1
if errorlevel 1 (
    echo [2/4] Ajout de %APP_HOST% au fichier hosts...
    >> "%HOSTS%" echo 127.0.0.1    %APP_HOST%
) else (
    echo [2/4] Entree hosts deja presente pour %APP_HOST%.
)

rem --- 3. Demarrage de l'application (Docker) ---
echo [3/4] Demarrage de l'application (Docker)...
docker info >nul 2>&1
if errorlevel 1 (
    echo       Docker non lance, tentative de lancement de Docker Desktop...
    if exist "%ProgramFiles%\Docker\Docker\Docker Desktop.exe" start "" "%ProgramFiles%\Docker\Docker\Docker Desktop.exe"
    if exist "%LOCALAPPDATA%\Programs\DockerDesktop\Docker Desktop.exe" start "" "%LOCALAPPDATA%\Programs\DockerDesktop\Docker Desktop.exe"
    set /a _tries=0
    :wait_docker
    docker info >nul 2>&1
    if not errorlevel 1 goto docker_ok
    set /a _tries+=1
    if !_tries! geq 40 (
        echo       Docker n'a pas pu demarrer. Lancez Docker Desktop manuellement puis relancez ce script.
        pause
        exit /b 1
    )
    timeout /t 3 >nul
    goto wait_docker
    :docker_ok
)

docker compose up -d --build
if errorlevel 1 (
    echo       Erreur lors du demarrage de l'application.
    pause
    exit /b 1
)

rem --- 4. Ouverture du navigateur ---
echo [4/4] Ouverture de %APP_URL%
start "" "%APP_URL%"

echo.
echo L'application est accessible sur : %APP_URL%
timeout /t 3 >nul
