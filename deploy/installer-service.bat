@echo off
setlocal

rem ============================================================
rem  Demarrage automatique au reboot (tache planifiee Windows)
rem  Cree aussi la regle de pare-feu et demarre l'application.
rem  A executer une fois, avec des droits administrateur.
rem ============================================================

rem --- Elevation des privileges si necessaire ---
net session >nul 2>&1
if errorlevel 1 (
    echo Demande d'elevation des privileges...
    powershell -NoProfile -Command "Start-Process -FilePath '%~f0' -Verb RunAs"
    exit /b 0
)

set "TASK_NAME=SimulateurPaie"
set "SCRIPT=%~dp0demarrer-serveur.bat"

echo ============================================================
echo  Configuration du demarrage automatique
echo ============================================================
echo.

rem --- Ouverture du port 8080 dans le pare-feu ---
echo [1/3] Ouverture du port 8080 dans le pare-feu Windows...
netsh advfirewall firewall delete rule name="Simulateur Paie" >nul 2>&1
netsh advfirewall firewall add rule name="Simulateur Paie" dir=in action=allow protocol=TCP localport=8080 >nul 2>&1
if errorlevel 1 (
    echo [ATTENTION] Impossible d'ajouter la regle de pare-feu.
) else (
    echo [OK] Regle de pare-feu ajoutee.
)

rem --- Creation de la tache planifiee ---
echo.
echo [2/3] Creation de la tache planifiee "%TASK_NAME%"...
schtasks /Create /TN "%TASK_NAME%" /TR "\"%SCRIPT%\"" /SC ONSTART /RU SYSTEM /F >nul 2>&1
if errorlevel 1 (
    echo [ERREUR] Impossible de creer la tache planifiee.
    pause
    exit /b 1
)
echo [OK] Tache planifiee creee.

rem --- Demarrage immediat ---
echo.
echo [3/3] Demarrage immediat de l'application...
schtasks /Run /TN "%TASK_NAME%" >nul 2>&1
echo [OK] Application lancee.

echo.
echo L'application se lancera automatiquement a chaque redemarrage
echo du serveur et sera accessible sur http://srvadmin3:8080
echo.
pause
