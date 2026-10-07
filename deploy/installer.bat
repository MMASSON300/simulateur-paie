@echo off
setlocal

rem ============================================================
rem  Installation du simulateur de salaire (hors-ligne)
rem  A executer une seule fois, avec des droits administrateur.
rem ============================================================

rem --- Elevation des privileges si necessaire ---
net session >nul 2>&1
if errorlevel 1 (
    echo Demande d'elevation des privileges...
    powershell -NoProfile -Command "Start-Process -FilePath '%~f0' -Verb RunAs"
    exit /b 0
)

echo ============================================================
echo  Simulateur de salaire - installation hors-ligne
echo ============================================================
echo.

rem --- Verification de Python ---
python --version >nul 2>&1
if errorlevel 1 (
    echo [ERREUR] Python n'est pas trouve dans le PATH.
    echo.
    echo Installez d'abord python-3.12.8-amd64.exe en cochant :
    echo   - "Add Python to PATH"
    echo   - "Install for all users" (recommande pour le service)
    echo Puis relancez ce script.
    echo.
    pause
    exit /b 1
)
echo [OK] Python detecte :
python --version

rem --- Installation des paquets (hors-ligne) ---
echo.
echo Installation des paquets Python (hors-ligne)...
python -m pip install --no-index --find-links "%~dp0backend\wheels" -r "%~dp0backend\requirements.txt"
if errorlevel 1 (
    echo [ERREUR] Echec de l'installation des paquets.
    pause
    exit /b 1
)
echo [OK] Paquets installes.

rem --- Initialisation de la base ---
echo.
echo Initialisation de la base de donnees...
pushd "%~dp0backend"
python -m app.seed
set "SEED_ERR=%errorlevel%"
popd
if not "%SEED_ERR%"=="0" (
    echo [ERREUR] Echec de l'initialisation de la base.
    pause
    exit /b 1
)
echo [OK] Base initialisee.

echo.
echo Installation terminee.
echo.
echo - Pour demarrer maintenant :  demarrer-serveur.bat
echo - Pour un demarrage auto au reboot : installer-service.bat
echo.
pause
