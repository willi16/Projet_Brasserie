@echo off
rem ============================================================
rem  Deiva Gestion - Packaging portable (Windows)
rem  Copie le projet (sans venv, base, .env, caches) vers un
rem  stockage externe, prêt à être déployé sur un autre poste.
rem
rem  Usage : packager_portable.bat [dossier_destination]
rem  Ex.   : packager_portable.bat D:\portable_deiva
rem ============================================================
setlocal enabledelayedexpansion
chcp 65001 >nul
cd /d "%~dp0"
set "DEST=%~1"
if "%DEST%"=="" set "DEST=%~dp0..\deiva_portable"

if exist "%DEST%\" (
    echo [ERREUR] Le dossier %DEST% existe deja.
    echo Choisissez un autre nom ou supprimez-le, puis relancez.
    exit /b 1
)

echo ==============================================
echo   Packaging portable - Deiva Gestion
echo   Destination : %DEST%
echo ==============================================
mkdir "%DEST%"

robocopy "%~dp0." "%DEST%" /E /NFL /NDL /NJH /NJS /NP /R:0 /W:0 ^
    /XD venv node_modules __pycache__ .pytest_cache .git media staticfiles letsencrypt ^
    /XF *.pyc db.sqlite3 db.sqlite3-journal texput.log .env .dockerignore

mkdir "%DEST%\media\factures" "%DEST%\media\photos" "%DEST%\media\rapports"

echo.
echo [ OK ] Copie portable terminee.
echo.
echo Pour deploier sur un autre poste (Windows) :
echo   1. copiez ce dossier depuis le stockage externe vers le poste cible,
echo   2. double-cliquez sur setup_local.bat,
echo   3. choisissez le mode 'Reseau local (LAN)',
echo   4. depuis tout appareil du reseau, ouvrez : http://IP-DE-CET-ORDINATEUR:8000
echo   Pour redemarrer ensuite : lancer.bat
pause