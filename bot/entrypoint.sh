# apps/bot/entrypoint.sh
#!/usr/bin/env bash
set -e

# Environment variables are passed by Docker/Coolify
# No need to source .env file in containerized environment

echo "Starting bot with the following configuration:"
echo "BOT_PORT: ${BOT_PORT:-8081}"
echo "BACKEND_BASE_URL: ${BACKEND_BASE_URL:-not_set}"
echo "LOG_LEVEL: ${LOG_LEVEL:-INFO}"

exec python -m app.main