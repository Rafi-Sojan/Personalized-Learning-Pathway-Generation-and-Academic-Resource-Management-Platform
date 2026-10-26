"""Initial learning roadmap schema.

Revision ID: 0001_initial
"""

from alembic import op

from app.db.base import Base
from app import models  # noqa: F401

revision = "0001_initial"
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    historical_tables = [
        table for table in Base.metadata.sorted_tables
        if table.name not in {"study_plan_revisions", "resource_concept_mappings"}
    ]
    Base.metadata.create_all(bind=op.get_bind(), tables=historical_tables)


def downgrade() -> None:
    Base.metadata.drop_all(bind=op.get_bind())
