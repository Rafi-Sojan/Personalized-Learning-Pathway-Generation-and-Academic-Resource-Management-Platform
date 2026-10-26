# Migrations

The application creates the development schema automatically for SQLite. Production deployments should use Alembic migrations against PostgreSQL before starting the API. The model contract is defined in `backend/app/models/__init__.py` and the initial relational contract remains documented in `database/init.sql`.
