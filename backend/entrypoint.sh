
#!/bin/sh
set -eu

cd /app

echo "Running database migrations..."
alembic -c /app/alembic.ini upgrade head

echo "Database migrations completed."

echo "Starting FastAPI server..."
exec uvicorn app.main:app \
    --host 0.0.0.0 \
    --port "${PORT:-10000}"
