#!/bin/bash
# Production start — (2 * CPU cores) + 1 workers
# Adjust --workers to your server's CPU count

set -e

echo "▶ Applying database migrations..."
alembic upgrade head

echo "▶ Starting server..."
exec gunicorn main:app \
  --workers "${WORKERS:-4}" \
  --worker-class uvicorn.workers.UvicornWorker \
  --bind "0.0.0.0:${PORT:-8000}" \
  --timeout 30 \
  --keepalive 5 \
  --max-requests 1000 \
  --max-requests-jitter 100 \
  --log-level info \
  --access-logfile -
