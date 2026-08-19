#!/usr/bin/env bash
set -euo pipefail

mkdir -p /app/logs /app/output
touch /app/logs/cron.log /app/logs/scraper.log

# cron no hereda el entorno del contenedor, así que se persiste para el job.
printenv | grep -E '^ALSAFEX_' | sed 's/^/export /' > /app/.cron_env || true
chmod 600 /app/.cron_env

# RUN_ON_START: once (primer arranque), always (cada arranque), false (nunca).
FIRST_RUN_MARKER=/app/output/.first_run_done
run_now=false
case "${RUN_ON_START:-once}" in
    always|true)
        run_now=true
        ;;
    once)
        if [[ -f "$FIRST_RUN_MARKER" ]]; then
            echo "[entrypoint] Scrapeo inicial ya realizado ($(cat "$FIRST_RUN_MARKER")); solo cron."
        else
            run_now=true
        fi
        ;;
esac

if [[ "$run_now" == "true" ]]; then
    echo "[entrypoint] Ejecución inicial..."
    cd /app && python -m alsafex_scraper.main 2>&1 | tee -a /app/logs/scraper.log || true
    date -Is > "$FIRST_RUN_MARKER"
fi

echo "[entrypoint] cron activo (00:00 ${TZ:-UTC}); fecha actual: $(date)"
cron
exec tail -F /app/logs/cron.log /app/logs/scraper.log
