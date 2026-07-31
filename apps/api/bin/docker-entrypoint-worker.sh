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
# Limit prefork concurrency when CELERY_CONCURRENCY is set (small instances
# expose many host CPUs and the default can OOM the container)
CONCURRENCY_ARGS=""
if [ -n "$CELERY_CONCURRENCY" ]; then
  CONCURRENCY_ARGS="--concurrency=${CELERY_CONCURRENCY}"
fi
celery -A plane worker -l info ${CONCURRENCY_ARGS}