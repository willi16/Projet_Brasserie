#!/bin/sh
set -e

# Génére le rapport quotidien au démarrage puis à 23:55 (heure du conteneur)
run_report() {
  echo "[$(date '+%Y-%m-%d %H:%M:%S')] Génération du rapport quotidien"
  python manage.py generer_rapport_quotidien
}

# Exécution immédiate au démarrage (valide aussi le bon fonctionnement)
run_report

while true; do
  NEXT_HOUR=23
  NEXT_MIN=55
  NOW_MIN=$(( $(date +%H) * 60 + $(date +%M) ))
  TARGET_MIN=$(( NEXT_HOUR * 60 + NEXT_MIN ))
  if [ "$NOW_MIN" -ge "$TARGET_MIN" ]; then
    SLEEP_MIN=$(( 1440 - NOW_MIN + TARGET_MIN ))
  else
    SLEEP_MIN=$(( TARGET_MIN - NOW_MIN ))
  fi
  echo "[$(date '+%Y-%m-%d %H:%M:%S')] Prochaine génération dans ${SLEEP_MIN} min"
  sleep $(( SLEEP_MIN * 60 ))
  run_report
done
