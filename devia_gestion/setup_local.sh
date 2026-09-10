#!/usr/bin/env bash
#
# Déploiement local simplifié — Linux / macOS
# Crée l'environnement virtuel, installe les dépendances, configure .env,
# applique les migrations, crée un compte administrateur et lance le serveur.
#
# Usage :  bash setup_local.sh
#
set -euo pipefail
cd "$(dirname "$0")"

VERT='\033[0;32m'; JAUNE='\033[0;33m'; ROUGE='\033[0;31m'; NEUTRE='\033[0m'
info() { printf "${VERT}[1/8]${NEUTRE} %s\n" "$*"; }
ok()   { printf "${VERT}[ OK ]${NEUTRE} %s\n" "$*"; }
warn() { printf "${JAUNE}[INFO]${NEUTRE} %s\n" "$*"; }
err()  { printf "${ROUGE}[ERREUR]${NEUTRE} %s\n" "$*" >&2; exit 1; }

echo "=============================================="
echo "   Installation locale — Deiva Gestion"
echo "   (Linux / macOS)"
echo "=============================================="

# --- 1/8 Vérifier Python ------------------------------------------------
if command -v python3 >/dev/null 2>&1; then PYTHON_BIN="python3"
elif command -v python  >/dev/null 2>&1; then PYTHON_BIN="python"
else err "Python introuvable. Installez Python 3.10 à 3.12, puis relancez ce script."; fi

if ! "$PYTHON_BIN" -c 'import sys; sys.exit(0 if (3,10) <= (sys.version_info.major, sys.version_info.minor) <= (3,12) else 1)' 2>/dev/null; then
    VERSION="$("$PYTHON_BIN" -c 'import sys; print(sys.version.split()[0])' 2>/dev/null || echo '?')"
    err "Version de Python détectée : ${VERSION}. Requis : 3.10, 3.11 ou 3.12."
fi
info "Python détecté : $("$PYTHON_BIN" -V 2>&1)"

# --- 2/8 Environnement virtuel -----------------------------------------
if [ ! -x "venv/bin/python" ]; then
    info "Création de l'environnement virtuel..."
    "$PYTHON_BIN" -m venv venv
else
    warn "Environnement virtuel déjà présent (venv/), on le conserve."
fi
# shellcheck disable=SC1091
source venv/bin/activate

# --- 3/8 Dépendances Python --------------------------------------------
info "Installation des dépendances Python..."
python -m pip install --upgrade pip
pip install -r requirements.txt
ok "Dépendances installées."

# --- 4/8 Fichier .env ---------------------------------------------------
if [ ! -f ".env" ]; then
    info "Création du fichier .env (avec une clé SECRET_KEY aléatoire)..."
    SECRET_KEY="$(python -c 'import secrets; print(secrets.token_urlsafe(50))')"
    cat > ".env" <<EOF
# ===== Django =====
DEBUG=True
SECRET_KEY=$SECRET_KEY
ALLOWED_HOSTS=localhost,127.0.0.1
USE_HTTPS=False

# ===== Base de données (local = SQLite) =====
DB_ENGINE=sqlite

# ===== Email (obligatoire pour démarrer, à adapter) =====
EMAIL_HOST=smtp.gmail.com
EMAIL_PORT=587
EMAIL_USE_TLS=True
EMAIL_HOST_USER=votre@email.com
EMAIL_HOST_PASSWORD=votre-mot-de-passe
DEFAULT_FROM_EMAIL=votre@email.com
EOF
    ok ".env créé. (SECRET_KEY générée automatiquement)"
else
    warn "Un fichier .env existe déjà : on le conserve tel quel."
fi

# --- 5/8 Migrations + fichiers statiques -------------------------------
info "Application des migrations (base de données)..."
python manage.py migrate
info "Regroupement des fichiers statiques..."
python manage.py collectstatic --noinput
ok "Base de données et fichiers statiques prêts."

# --- 6/8 Compte administrateur -----------------------------------------
echo
echo "Compte administrateur :"
echo "  1) Données de démonstration (seed_data — SUPPRIME les données existantes)"
echo "  2) Créer seulement les rôles (create_groups)"
echo "  3) Créer un super-utilisateur (createsuperuser)"
echo "  4) Passer cette étape"
read -r -p "Votre choix [1-4] (Entrée = 4) : " choix
case "${choix:-4}" in
    1) python manage.py seed_data ;;
    2) python manage.py create_groups ;;
    3) python manage.py createsuperuser ;;
esac
ok "Étape compte administrateur terminée."

# --- 7/8 Choix du mode de lancement -------------------------------------
echo
echo "Lancement du serveur :"
echo "  1) Local uniquement    -> http://127.0.0.1:8000"
echo "  2) Réseau local (LAN)  -> http://IP-DE-VOTRE-ORDINATEUR:8000 (recommandé)"
read -r -p "Votre choix [1-2] (Entrée = 2) : " mode

# --- 8/8 Démarrer --------------------------------------------------------
if [ "${mode:-2}" = "1" ]; then
    ok "Application prête. Ouvrez http://127.0.0.1:8000 dans votre navigateur."
    exec python manage.py runserver
else
    warn "Autorisez le port 8000 dans le pare-feu du système."
    echo
    info "Serveur accessible sur le réseau. Ouvrez http://IP-DE-VOTRE-ORDINATEUR:8000"
    exec python manage.py runserver 0.0.0.0:8000
fi