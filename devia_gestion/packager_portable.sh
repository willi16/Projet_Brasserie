#!/usr/bin/env bash
#
# Crée une copie PORTABLE du projet, prête pour un stockage externe
# (clé USB, disque dur externe, ...) et pour être déployée ensuite sur
# n'importe quel poste du réseau (Linux / macOS).
#
# Sont EXCLUS : venv, node_modules, base de données locale, .env, .git,
# fichiers statiques collectés, médias et caches — la copie est légère et
# propre à la machine. Les scripts setup_local.sh / lancer.sh / README.md
# et instructions y sont inclus.
#
# Usage :  bash packager_portable.sh [dossier_destination]
#   Ex.  :  bash packager_portable.sh /media/USB_DEIVA/deiva_gestion
#
set -euo pipefail
cd "$(dirname "$0")"

PROJET="$(basename "$PWD")"
DEST="${1:-$(dirname "$PWD")/${PROJET}_portable}"

if [ -e "$DEST" ]; then
    echo "[ERREUR] Le dossier '$DEST' existe déjà."
    echo "Choisissez un autre nom ou supprimez-le, puis relancez."
    exit 1
fi

echo "=============================================="
echo "   Packaging portable — Deiva Gestion"
echo "   Destination : $DEST"
echo "=============================================="

mkdir -p "$DEST"
rsync -a \
    --exclude 'venv' \
    --exclude 'node_modules' \
    --exclude '__pycache__' \
    --exclude '.pytest_cache' \
    --exclude '*.pyc' \
    --exclude '.git' \
    --exclude '.env' \
    --exclude 'db.sqlite3*' \
    --exclude 'staticfiles' \
    --exclude 'letsencrypt' \
    --exclude 'media' \
    --exclude 'texput.log' \
    --exclude '.dockerignore' \
    ./ "$DEST/"

rm -f "$DEST"/*_portable
mkdir -p "$DEST/media/factures" "$DEST/media/photos" "$DEST/media/rapports"

echo
echo "[ OK ] Copie portable terminée."
echo
echo "Pour déployer sur un autre poste (Linux/macOS) :"
echo "  1. copiez ce dossier depuis le stockage externe vers le poste cible,"
echo "  2. ouvrez un terminal dans ce dossier et lancez :  bash setup_local.sh,"
echo "  3. choisissez le mode 'Réseau local (LAN)',"
echo "  4. depuis tout appareil du réseau, ouvrez : http://IP-DE-CET-ORDINATEUR:8000"
echo "  (Pour redémarrer ensuite : bash lancer.sh)"