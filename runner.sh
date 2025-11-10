# apps/runner.sh
#!/bin/sh
set -e

echo "👉 Checking requirements..."
pip install --no-cache-dir -r requirements.txt

echo "👉 Running Black formatter..."
black .

POSTGRES_HOST=${POSTGRES_HOST:-db}
POSTGRES_PORT=${POSTGRES_PORT:-5432}


echo "⏳  Waiting for PostgreSQL at ${POSTGRES_HOST}:${POSTGRES_PORT} …"
while ! nc -z "$POSTGRES_HOST" "$POSTGRES_PORT"; do
  sleep 1
done
echo "✅  PostgreSQL is up!"

echo "🚀  Making migrations …"
python manage.py makemigrations --noinput

echo "🚀  Applying migrations …"
python manage.py migrate --noinput

echo "📦  Collecting static files …"
python manage.py collectstatic --noinput

echo "🚦  Starting server …"
python manage.py runserver 0.0.0.0:8700