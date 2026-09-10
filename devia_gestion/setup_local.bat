@echo off
rem ============================================================
rem  Deploiement local simplifie - Windows
rem  Cree l'environnement virtuel, installe les dependances,
rem  configure .env, applique les migrations, cree un compte
rem  administrateur et lance le serveur.
rem
rem  Usage : double-clic sur ce fichier, ou :  setup_local.bat
rem ============================================================
setlocal enabledelayedexpansion
chcp 65001 >nul
cd /d "%~dp0"
title Deiva Gestion - Installation locale

echo ==============================================
echo    Installation locale - Deiva Gestion
echo    (Windows)
echo ==============================================
echo.

rem --- 1/8 Verifier Python ------------------------------
set "PY_CMD=python"
where py >nul 2>nul && set "PY_CMD=py -3"
%PY_CMD% --version >nul 2>nul
if errorlevel 1 (
    echo [ERREUR] Python est introuvable.
    echo Installez Python 3.10 a 3.12 depuis https://www.python.org/downloads/
    echo et cochez "Add Python to PATH", puis relancez ce script.
    pause
    exit /b 1
)
echo [1/8] Python detecte : %PY_CMD%

rem --- 2/8 Environnement virtuel -------------------------
if not exist "venv\Scripts\python.exe" (
    echo [2/8] Creation de l'environnement virtuel...
    %PY_CMD% -m venv venv
) else (
    echo [2/8] Environnement virtuel deja present, on le conserve.
)
call "venv\Scripts\activate.bat"

rem --- 3/8 Dependances Python ----------------------------
echo [3/8] Installation des dependances Python...
python -m pip install --upgrade pip
python -m pip install -r requirements.txt
if errorlevel 1 (
    echo [ERREUR] L'installation des dependances a echoue.
    pause
    exit /b 1
)

rem --- 4/8 Fichier .env -----------------------------------
if not exist ".env" (
    echo [4/8] Creation du fichier .env ...
    for /f "delims=" %%i in ('python -c "import secrets; print(secrets.token_urlsafe(50))"') do set "CLE=%%i"
    > ".env"   echo # ===== Django =====
    >> ".env"  echo DEBUG=True
    >> ".env"  echo SECRET_KEY=!CLE!
    >> ".env"  echo ALLOWED_HOSTS=localhost,127.0.0.1
    >> ".env"  echo USE_HTTPS=False
    >> ".env"  echo.
    >> ".env"  echo # ===== Base de donnees (local = SQLite) =====
    >> ".env"  echo DB_ENGINE=sqlite
    >> ".env"  echo.
    >> ".env"  echo # ===== Email (obligatoire pour demarrer, a adapter) =====
    >> ".env"  echo EMAIL_HOST=smtp.gmail.com
    >> ".env"  echo EMAIL_PORT=587
    >> ".env"  echo EMAIL_USE_TLS=True
    >> ".env"  echo EMAIL_HOST_USER=votre@email.com
    >> ".env"  echo EMAIL_HOST_PASSWORD=votre-mot-de-passe
    >> ".env"  echo DEFAULT_FROM_EMAIL=votre@email.com
    echo        .env cree.
) else (
    echo [4/8] Un fichier .env existe deja : on le conserve tel quel.
)

rem --- 5/8 Migrations --------------------------------------
echo [5/8] Application des migrations...
python manage.py migrate
if errorlevel 1 (
    echo [ERREUR] Les migrations ont echoue.
    pause
    exit /b 1
)

rem --- 6/8 Fichiers statiques -----------------------------
echo [6/8] Regroupement des fichiers statiques...
python manage.py collectstatic --noinput

rem --- 7/8 Compte administrateur --------------------------
echo.
echo [7/8] Compte administrateur :
echo   1. Donnees de demonstration (seed_data - SUPPRIME l'existant)
echo   2. Roles uniquement (create_groups)
echo   3. Super-utilisateur (createsuperuser)
echo   4. Passer cette etape
set /p CHOIX=   Votre choix [1-4] (Entree = 4) : 
if "%CHOIX%"=="1" python manage.py seed_data
if "%CHOIX%"=="2" python manage.py create_groups
if "%CHOIX%"=="3" python manage.py createsuperuser

rem --- 8/8 Lancement du serveur ---------------------------
echo.
echo [8/8] Lancement du serveur :
echo   1. Local uniquement    (http://127.0.0.1:8000)
echo   2. Reseau local (LAN)  (http://IP-DE-VOTRE-ORDINATEUR:8000) - recommande
set /p MODE=   Votre choix [1-2] (Entree = 2) : 
if "%MODE%"=="1" (
    start "" http://127.0.0.1:8000
    python manage.py runserver
) else (
    echo Autorisez le port 8000 dans le pare-feu Windows.
    echo.
    start "" http://127.0.0.1:8000
    python manage.py runserver 0.0.0.0:8000
)