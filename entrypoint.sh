#!/bin/sh

echo "Waiting for PostgreSQL..."
while ! nc -z $DB_HOST $DB_PORT; do
    sleep 1
done
echo "PostgreSQL is up."

echo "Waiting for Redis..."
while ! nc -z redis 6379; do
    sleep 1
done
echo "Redis is up."

# Only run migrations if this is the web container
if [ "$RUN_MIGRATIONS" = "true" ]; then
    echo "Running migrations..."
    python manage.py migrate --noinput
    echo "Collecting static files..."
    python manage.py collectstatic --noinput
fi

echo "Starting..."
exec "$@"