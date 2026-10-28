FROM python:3.12-slim

ENV PYTHONDONTWRITEBYTECODE=1 PYTHONUNBUFFERED=1 PYTHONPATH=/app
WORKDIR /app
COPY backend/requirements.txt ./requirements.txt
COPY backend/requirements-storage.txt ./requirements-storage.txt
RUN pip install --no-cache-dir -r requirements.txt -r requirements-storage.txt
COPY backend/app ./app
COPY backend/alembic.ini ./alembic.ini
COPY backend/migrations ./migrations
COPY database/rvce_catalog.json ./database/rvce_catalog.json
COPY ml ./ml
COPY scripts ./scripts
RUN useradd --create-home --uid 10001 appuser && mkdir -p /app/storage/uploads /app/storage/processed && chown -R appuser:appuser /app
USER appuser
EXPOSE 8000
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
