@echo off
setlocal enabledelayedexpansion

rem ============================================================
rem  Mise a jour du simulateur de salaire
rem  Copie la nouvelle version (dossier de ce script) vers une
rem  installation existante, SANS ecraser .env / paie.db.
rem ============================================================

rem --- Elevation admin ---
net session >nul 2>&1
if errorlevel 1 (
    echo Demande d'elevation des privileges...
    powershell -NoProfile -Command "Start-Process -FilePath '%~f0' -Verb RunAs"
    exit /b 0
)

title Mise a jour - Simulateur de salaire
set "SRC=%~dp0"
set "SRCDIR=%SRC:~0,-1%"

echo ============================================================
echo   Mise a jour du simulateur de salaire
echo ============================================================
echo.
echo  Source (nouvelle version) : %SRCDIR%
echo.
echo  Indiquez le dossier de l'installation existante (celui qui
echo  contient le sous-dossier "backend").
echo.
set "TARGET="
set /p "TARGET=Dossier de l'installation : "
if "%TARGET%"=="" (
    echo [ERREUR] Aucun dossier saisi.
    pause
    exit /b 1
)
if "%TARGET:~-1%"=="\" set "TARGET=%TARGET:~0,-1%"

if not exist "%TARGET%\backend\app" (
    echo.
    echo [ERREUR] Dossier invalide ^(sous-dossier "backend\app" introuvable^) : %TARGET%
    pause
    exit /b 1
)

rem --- 1. Arret du service ---
echo.
echo [1/5] Arret du service...
schtasks /End /TN "SimulateurPaie" >nul 2>&1
ping -n 3 127.0.0.1 >nul

rem --- Python cible (memorise a l'installation) ---
set "PYTHON=python"
if exist "%TARGET%\backend\python-path.txt" set /p PYTHON=<"%TARGET%\backend\python-path.txt"

rem --- 2. Copie des fichiers (on preserve .env, paie.db, python-path.txt) ---
echo [2/5] Copie des fichiers...
if /i "%TARGET%"=="%SRCDIR%" (
    echo       Source = cible : fichier deja en place, copie ignoree.
) else (
    robocopy "%SRCDIR%" "%TARGET%" /E /XF .env paie.db python-path.txt server.lock /NFL /NDL /NJH /NJS /NP >nul
    if !ERRORLEVEL! GEQ 8 (
        echo [ERREUR] Echec de la copie des fichiers.
        pause
        exit /b 1
    )
    echo       Fichiers mis a jour.
)

rem --- 3. Paquets Python (hors-ligne, idempotent) ---
echo [3/5] Verification des paquets Python...
for /f %%V in ('"%PYTHON%" -c "import sys; print(sys.version_info.minor)" 2^>nul') do set "PYMINOR=%%V"
if "!PYMINOR!"=="13" (set "WHEELS=%TARGET%\backend\wheels\cp313") else (set "WHEELS=%TARGET%\backend\wheels\cp312")
"%PYTHON%" -m pip install --no-index --find-links "%WHEELS%" -r "%TARGET%\backend\requirements.txt" >nul 2>&1
echo       Termine.

rem --- 4. Donnees de reference (a la demande) ---
echo.
echo [4/5] Donnees de reference
echo       NB : reinitialiser ECRASE les donnees de reference
echo       (perte des modifications faites via l'interface d'admin).
choice /C ON /M "Reinitialiser les donnees de reference ? [O]ui [N]on"
if errorlevel 2 goto no_reseed
pushd "%TARGET%\backend"
"%PYTHON%" -m app.seed --force
popd
echo       Donnees de reference reinitialisees.
goto reseed_done
:no_reseed
echo       Donnees existantes conservees.
rem S'assurer que les constantes/taux manquants sont ajoutes (sans rien ecraser).
pushd "%TARGET%\backend"
"%PYTHON%" -m app.seed >nul 2>&1
popd
:reseed_done

rem --- 5. Redemarrage du service ---
echo.
echo [5/5] Redemarrage du service...
powershell -NoProfile -ExecutionPolicy Bypass -Command "$a = New-ScheduledTaskAction -Execute '%TARGET%\demarrer-serveur.bat'; $t = New-ScheduledTaskTrigger -AtStartup; $p = New-ScheduledTaskPrincipal -UserId 'SYSTEM' -LogonType ServiceAccount -RunLevel Highest; $s = New-ScheduledTaskSettingsSet -MultipleInstances IgnoreNew; Register-ScheduledTask -TaskName 'SimulateurPaie' -Action $a -Trigger $t -Principal $p -Settings $s -Force" >nul 2>&1
schtasks /Run /TN "SimulateurPaie" >nul 2>&1

echo       Attente du demarrage...
set /a _t=0
:wait
curl.exe -s -o nul "http://localhost:8080/api/health" >nul 2>&1
if not errorlevel 1 goto ready
set /a _t+=1
if !_t! geq 20 goto done
timeout /t 2 /nobreak >nul
goto wait

:ready
echo.
echo  Application disponible : http://%COMPUTERNAME%:8080
:done

echo.
echo ============================================================
echo   Mise a jour terminee
echo ============================================================
echo.
echo  Dossier : %TARGET%
echo.
pause
