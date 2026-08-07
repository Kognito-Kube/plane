#!/bin/bash
set -e

# Construct REDIS_URL from host/port if not set
if [ -z "$REDIS_URL" ] && [ -n "$REDIS_HOST" ]; then
  export REDIS_URL="redis://${REDIS_HOST}:${REDIS_PORT:-6379}"
fi

python manage.py wait_for_db
# Wait for migrations
python manage.py wait_for_migrations
# Run the processes
celery -A plane beat -l info