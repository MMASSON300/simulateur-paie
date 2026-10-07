@echo off
setlocal enabledelayedexpansion

rem ---------------------------------------------------------------------------
rem  Lanceur du simulateur de salaire (Windows)
rem  - demarre l'application via Docker
rem  - ouvre le navigateur sur http://localhost
rem ---------------------------------------------------------------------------

set "APP_URL=http://localhost"

rem Se placer dans le repertoire du script
cd /d "%~dp0"

rem --- 1. Demarrage de l'application (Docker) ---
echo [1/2] Demarrage de l'application (Docker)...
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

rem --- 2. Ouverture du navigateur ---
echo [2/2] Ouverture de %APP_URL%
start "" "%APP_URL%"

echo.
echo L'application est accessible sur : %APP_URL%
timeout /t 3 >nul
