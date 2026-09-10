@echo off
rem ============================================================
rem  Deva Gestion - Lancement du serveur (Windows)
rem  Serveur accessible a tous les appareils du reseau local.
rem  Usage : double-clic sur ce fichier.
rem ============================================================
setlocal
chcp 65001 >nul
cd /d "%~dp0"
title Deiva Gestion - Serveur (reseau local)

if not exist "venv\Scripts\python.exe" (
    echo [ERREUR] Environnement virtuel introuvable.
    echo Lancez d'abord ceci :  setup_local.bat
    pause
    exit /b 1
)
call "venv\Scripts\activate.bat"

echo Application accessible sur :
echo    - Reseau local :  http://IP-DE-CET-ORDINATEUR:8000
echo    - Cette machine : http://127.0.0.1:8000
echo Autorisez le port 8000 dans le pare-feu Windows.
echo.
start "" http://127.0.0.1:8000
python manage.py runserver 0.0.0.0:8000