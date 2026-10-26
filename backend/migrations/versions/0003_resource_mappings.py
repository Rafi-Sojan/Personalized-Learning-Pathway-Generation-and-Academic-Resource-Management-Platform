"""Add resource to concept mapping review records.

Revision ID: 0003_resource_mappings
"""

from alembic import op
import sqlalchemy as sa

revision = "0003_resource_mappings"
down_revision = "0002_lifecycle_controls"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "resource_concept_mappings",
        sa.Column("id", sa.String(length=36), primary_key=True),
        sa.Column("resource_id", sa.String(length=36), sa.ForeignKey("academic_resources.id"), nullable=False),
        sa.Column("concept_id", sa.String(length=36), sa.ForeignKey("concepts.id"), nullable=False),
        sa.Column("confidence", sa.Float(), nullable=True),
        sa.Column("status", sa.String(length=24), nullable=False, server_default="proposed"),
        sa.Column("source", sa.String(length=32), nullable=False, server_default="manual"),
        sa.Column("reviewed_by", sa.String(length=36), sa.ForeignKey("users.id"), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.UniqueConstraint("resource_id", "concept_id", name="uq_resource_concept_mapping"),
    )
    op.create_index("ix_resource_concept_mappings_resource_id", "resource_concept_mappings", ["resource_id"])
    op.create_index("ix_resource_concept_mappings_concept_id", "resource_concept_mappings", ["concept_id"])


def downgrade() -> None:
    op.drop_index("ix_resource_concept_mappings_concept_id", table_name="resource_concept_mappings")
    op.drop_index("ix_resource_concept_mappings_resource_id", table_name="resource_concept_mappings")
    op.drop_table("resource_concept_mappings")
