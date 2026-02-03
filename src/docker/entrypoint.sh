#!/bin/sh
set -e

cd /app

if [ "${RUN_MIGRATIONS:-1}" = "1" ]; then
  python manage.py migrate --noinput
fi

if [ "${RUN_COLLECTSTATIC:-1}" = "1" ]; then
  python manage.py collectstatic --noinput
fi

exec daphne -b 0.0.0.0 -p "${PORT:-8000}" effi_time.asgi:application
