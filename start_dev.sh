#!/bin/bash
# Development — single worker with hot-reload

set -e

echo "▶ Applying migrations..."
alembic upgrade head

echo "▶ Starting dev server on http://localhost:8000"
uvicorn main:app --reload --host 0.0.0.0 --port 8000
