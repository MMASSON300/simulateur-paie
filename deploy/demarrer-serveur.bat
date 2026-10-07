@echo off

rem ============================================================
rem  Demarrage du serveur (ecoute sur le port 8080)
rem  Redemarre automatiquement en cas d'arret inattendu.
rem ============================================================

cd /d "%~dp0backend"

:loop
echo [%date% %time%] Demarrage du serveur sur le port 8080...
python -m uvicorn app.main:app --host 0.0.0.0 --port 8080
echo [%date% %time%] Serveur arrete - redemarrage dans 5 secondes...
ping -n 6 127.0.0.1 >nul
goto loop
