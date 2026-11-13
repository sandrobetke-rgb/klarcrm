#!/usr/bin/env bash
# Startet KlarCRM in Codespaces und lädt beim ersten Start Demo-Daten.
set -e
cd "$(dirname "$0")/.."
[ -f .env ] || cp .env.example.codespaces .env
docker compose up -d --build
echo "Warte auf Backend…"
for i in $(seq 1 60); do
  if docker compose exec -T backend python -c "import urllib.request;urllib.request.urlopen('http://localhost:8000/api/health')" 2>/dev/null; then break; fi
  sleep 2
done
docker compose exec -T backend python -m app.seed || true
echo ""
echo "================================================================"
echo " KlarCRM läuft. Im Tab 'Ports' auf Port 8080 (KlarCRM) klicken."
echo " Admin:          admin@firma.de / admin1234"
echo " Vertrieb:       anna.berg@firma.de / demo1234"
echo " Gesellschafter: gesellschafter@firma.de / demo1234"
echo "================================================================"
