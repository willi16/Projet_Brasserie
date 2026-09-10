#!/usr/bin/env bash
#
# Démarre simplement le serveur, accessible à tous les appareils du réseau
# local (LAN/WLAN), sans refaire l'installation.
#
# Usage :  bash lancer.sh
#
set -euo pipefail
cd "$(dirname "$0")"

if [ ! -d "venv" ]; then
    echo "[ERREUR] Environnement virtuel introuvable."
    echo "Lancez d'abord :  bash setup_local.sh"
    exit 1
fi
# shellcheck disable=SC1091
source venv/bin/activate

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

echo "Application accessible sur :"
echo "   - Réseau local :  http://${IP}:8000"
echo "   - Cette machine : http://127.0.0.1:8000"
echo "Autorisez le port 8000 dans le pare-feu du système."
exec python manage.py runserver 0.0.0.0:8000