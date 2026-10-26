"""Add roadmap revision history.

Revision ID: 0002_lifecycle_controls
"""

from alembic import op
import sqlalchemy as sa

revision = "0002_lifecycle_controls"
down_revision = "0001_initial"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "study_plan_revisions",
        sa.Column("id", sa.String(length=36), primary_key=True),
        sa.Column("plan_id", sa.String(length=36), sa.ForeignKey("study_plans.id"), nullable=False),
        sa.Column("revision_number", sa.Integer(), nullable=False),
        sa.Column("event", sa.String(length=32), nullable=False, server_default="generated"),
        sa.Column("snapshot", sa.Text(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
    )
    op.create_index("ix_study_plan_revisions_plan_id", "study_plan_revisions", ["plan_id"])


def downgrade() -> None:
    op.drop_index("ix_study_plan_revisions_plan_id", table_name="study_plan_revisions")
    op.drop_table("study_plan_revisions")
