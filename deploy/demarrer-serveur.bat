@echo off

rem ============================================================
rem  Demarrage du serveur (ecoute sur le port 8080)
rem  Mono-instance : refuse de demarrer si le port est deja pris.
rem  Redemarre automatiquement en cas d'arret inattendu.
rem ============================================================

rem Chemin de Python : renseigne par installer.bat (fallback : python).
set "PYTHON=python"
if exist "%~dp0backend\python-path.txt" set /p PYTHON=<"%~dp0backend\python-path.txt"

cd /d "%~dp0backend"

:loop
rem --- Ne pas demarrer si une autre instance ecoute deja sur 8080 ---
netstat -ano -p TCP | findstr "LISTENING" | findstr ":8080" >nul 2>&1
if not errorlevel 1 (
    echo [%date% %time%] Le port 8080 est deja utilise par une autre instance - arret.
    exit /b 0
)

echo [%date% %time%] Demarrage du serveur sur le port 8080...
"%PYTHON%" -m uvicorn app.main:app --host 0.0.0.0 --port 8080
echo [%date% %time%] Serveur arrete - redemarrage dans 5 secondes...
ping -n 6 127.0.0.1 >nul
goto loop
