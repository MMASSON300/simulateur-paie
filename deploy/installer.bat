@echo off
setlocal enabledelayedexpansion

rem ============================================================
rem  Simulateur de salaire - installation hors-ligne (tout-en-un)
rem  - detecte ou installe Python 3.12 / 3.13 (sans ecraser
rem    une version plus recente deja presente)
rem  - installe les paquets hors-ligne
rem  - initialise la base
rem  - configure le demarrage automatique au reboot
rem  - propose de demarrer maintenant puis affiche le recap
rem ============================================================

rem --- Elevation admin ---
net session >nul 2>&1
if errorlevel 1 (
    echo Demande d'elevation des privileges...
    powershell -NoProfile -Command "Start-Process -FilePath '%~f0' -Verb RunAs"
    exit /b 0
)

title Installation - Simulateur de salaire
set "ROOT=%~dp0"
set "PF=%ProgramFiles%"
if defined ProgramW6432 set "PF=%ProgramW6432%"

echo ============================================================
echo   Simulateur de salaire - installation
echo ============================================================
echo.

rem --- 1. Detection / installation de Python ---
echo [1/6] Detection de Python...
set "PY="

if not defined PY for /f "delims=" %%P in ('py -3.12 -c "import sys; print(sys.executable)" 2^>nul') do set "PY=%%P"
if not defined PY for /f "delims=" %%P in ('py -3.13 -c "import sys; print(sys.executable)" 2^>nul') do set "PY=%%P"

if not defined PY if exist "%PF%\Python312\python.exe" set "PY=%PF%\Python312\python.exe"
if not defined PY if exist "%PF%\Python313\python.exe" set "PY=%PF%\Python313\python.exe"
if not defined PY if exist "%LocalAppData%\Programs\Python\Python312\python.exe" set "PY=%LocalAppData%\Programs\Python\Python312\python.exe"
if not defined PY if exist "%LocalAppData%\Programs\Python\Python313\python.exe" set "PY=%LocalAppData%\Programs\Python\Python313\python.exe"

if not defined PY (
    python --version >nul 2>&1
    if not errorlevel 1 (
        for /f "tokens=2 delims= " %%V in ('python --version 2^>^&1') do set "VER=%%V"
        echo !VER! | findstr /b "3.12 3.13" >nul
        if not errorlevel 1 for /f "delims=" %%P in ('where python') do set "PY=%%P"
    )
)

if not defined PY (
    echo       Python 3.12/3.13 non trouve - installation de Python 3.12...
    start /wait "" "%ROOT%python-3.12.8-amd64.exe" /quiet InstallAllUsers=1 PrependPath=0 Include_pip=1
    set "PY=%PF%\Python312\python.exe"
)

if not exist "%PY%" (
    echo.
    echo [ERREUR] Impossible de localiser Python : %PY%
    echo Verifiez que Python est bien installe puis relancez ce script.
    pause
    exit /b 1
)
echo       Python detecte : %PY%
"%PY%" --version

rem --- 2. Choix des paquets selon la version ---
for /f %%V in ('"%PY%" -c "import sys; print(sys.version_info.minor)"') do set "PYMINOR=%%V"
if "!PYMINOR!"=="13" (set "WHEELS=%ROOT%backend\wheels\cp313") else (set "WHEELS=%ROOT%backend\wheels\cp312")

rem --- 3. Installation des paquets ---
echo.
echo [2/6] Installation des paquets Python (hors-ligne)...
"%PY%" -m pip install --no-index --find-links "%WHEELS%" -r "%ROOT%backend\requirements.txt"
if errorlevel 1 (
    echo [ERREUR] Echec de l'installation des paquets.
    pause
    exit /b 1
)

rem --- 4. Initialisation de la base ---
echo.
echo [3/6] Initialisation de la base de donnees...
pushd "%ROOT%backend"
"%PY%" -m app.seed
set "SEED_ERR=%errorlevel%"
popd
if not "%SEED_ERR%"=="0" (
    echo [ERREUR] Echec de l'initialisation de la base.
    pause
    exit /b 1
)

rem --- 5. Memoriser le chemin Python (pour le service) ---
> "%ROOT%backend\python-path.txt" echo %PY%

rem --- 6. Demarrage automatique + pare-feu ---
echo.
echo [4/6] Configuration du demarrage automatique...
netsh advfirewall firewall delete rule name="Simulateur Paie" >nul 2>&1
netsh advfirewall firewall add rule name="Simulateur Paie" dir=in action=allow protocol=TCP localport=8080 >nul 2>&1
if errorlevel 1 (
    echo       [ATTENTION] Impossible d'ouvrir le port 8080 dans le pare-feu.
) else (
    echo       Port 8080 ouvert dans le pare-feu.
)
schtasks /Create /TN "SimulateurPaie" /TR "\"%ROOT%demarrer-serveur.bat\"" /SC ONSTART /RU SYSTEM /F >nul 2>&1
if errorlevel 1 (
    echo       [ATTENTION] Impossible de creer la tache planifiee.
) else (
    echo       Tache planifiee "SimulateurPaie" creee (demarrage au boot).
)

rem --- 7. Demarrer maintenant ? ---
echo.
echo [5/6] Demarrage
choice /C ON /M "Demarrer l'application maintenant ? [O]ui [N]on"
if errorlevel 2 goto summary
schtasks /Run /TN "SimulateurPaie" >nul 2>&1
echo       Application lancee (demarrage en quelques secondes).

:summary
rem --- 8. Recapitulatif ---
echo.
echo [6/6] Recapitulatif
echo ============================================================
echo   Installation terminee
echo ============================================================
echo.
echo  Acces depuis les postes du reseau :
echo    http://%COMPUTERNAME%:8080
echo    http://localhost:8080   ^(test sur le serveur^)
echo.
echo  Demarrage automatique au reboot : ACTIVE ^(tache "SimulateurPaie"^)
echo    - arreter   : schtasks /End /TN SimulateurPaie
echo    - relancer  : schtasks /Run /TN SimulateurPaie
echo.
echo  Mot de passe d'administration par defaut : admin
echo    -> a changer dans le fichier  backend\.env  ^(ADMIN_PASSWORD=...^)
echo.
echo  Journaux : lancer demarrer-serveur.bat affiche les requetes.
echo.
pause
