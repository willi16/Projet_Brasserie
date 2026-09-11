#!/usr/bin/env bash
#
# Démarre l'application en mode PRODUCTION locale (Linux / macOS) :
#   - Gunicorn avec plusieurs workers/threads -> gère plusieurs personnes
#     qui utilisent l'application en même temps,
#   - fichiers statiques servis par WhiteNoise (déjà configuré),
#   - port 8000 ouvert sur le réseau local (LAN/WLAN).
#
# Usage :  bash production.sh
#
set -euo pipefail
cd "$(dirname "$0")"

if [ ! -d "venv" ] && [ -d "../venv" ]; then
    echo "Environnement virtuel détecté à la racine (../venv)."
    VENV_DIR="../venv"
elif [ -d "venv" ]; then
    VENV_DIR="venv"
else
    echo "[ERREUR] Environnement virtuel introuvable."
    echo "Lancez d'abord :  bash setup_local.sh"
    exit 1
fi
# shellcheck disable=SC1091
source "$VENV_DIR/bin/activate"

echo "Préparation (migrations + fichiers statiques)..."
python manage.py migrate --noinput
python manage.py collectstatic --noinput

# Nombre de workers selon le nombre de cœurs (au moins 2)
CORES="$(getconf _NPROCESSORS_ONLN 2>/dev/null || echo 2)"
WORKERS="$((CORES * 2 + 1))"
if [ "$WORKERS" -lt 2 ]; then WORKERS=2; fi

IP="$(python - <<'PY'
import socket
try:
    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    s.connect(('8.8.8.8', 80))
    print(s.getsockname()[0])
    s.close()
except OSError:
    print('IP-DE-CET-ORDINATEUR')
PY
)"

echo
echo "Application en production, accessible sur :"
echo "   - Réseau local :  http://${IP}:8000"
echo "   - Cette machine : http://127.0.0.1:8000"
echo "Workers : $WORKERS (gunicorn) | Autorisez le port 8000 dans le pare-feu."
echo "(Ctrl-C pour arrêter)"
exec gunicorn --bind 0.0.0.0:8000 \
    --workers "$WORKERS" \
    --threads 2 \
    --timeout 120 \
    --graceful-timeout 30 \
    deiva_gestion.wsgi:application