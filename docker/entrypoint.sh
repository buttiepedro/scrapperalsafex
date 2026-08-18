#!/usr/bin/env bash
set -euo pipefail

mkdir -p /app/logs /app/output
touch /app/logs/cron.log /app/logs/scraper.log

# cron no hereda el entorno del contenedor, así que se persiste para el job.
printenv | grep -E '^ALSAFEX_' | sed 's/^/export /' > /app/.cron_env || true
chmod 600 /app/.cron_env

if [[ "${RUN_ON_START:-false}" == "true" ]]; then
    echo "[entrypoint] Ejecución inicial..."
    cd /app && python -m alsafex_scraper.main || true
fi

echo "[entrypoint] cron activo (00:00 ${TZ:-UTC}); fecha actual: $(date)"
cron
exec tail -F /app/logs/cron.log /app/logs/scraper.log
