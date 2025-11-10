# apps/bot/entrypoint.sh
#!/usr/bin/env bash
set -e

# .env bo'lsa sourced
if [ -f ".env" ]; then
  set -o allexport
  source .env
  set +o allexport
fi

exec python -m app.main