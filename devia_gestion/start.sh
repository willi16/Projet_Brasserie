#!/bin/sh
set -e
# start.sh

# Exécuter collectstatic et migrate AU DÉMARRAGE (quand les variables env sont disponibles)
python manage.py collectstatic --noinput
python manage.py migrate --noinput

# Lancer Gunicorn
exec gunicorn --bind 0.0.0.0:8000 --workers 2 deiva_gestion.wsgi:application