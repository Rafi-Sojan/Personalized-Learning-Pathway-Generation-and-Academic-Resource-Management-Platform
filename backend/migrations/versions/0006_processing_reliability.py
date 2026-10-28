"""Add durable document-processing retry and failure state."""

from alembic import op
import sqlalchemy as sa


revision = "0006_processing_reliability"
down_revision = "0005_token_revocation"
branch_labels = None
depends_on = None


def upgrade() -> None:
    inspector = sa.inspect(op.get_bind())
    columns = {column["name"] for column in inspector.get_columns("academic_resources")}
    additions = (
        ("processing_attempts", sa.Column("processing_attempts", sa.Integer(), nullable=False, server_default="0")),
        ("processing_error", sa.Column("processing_error", sa.Text(), nullable=True)),
        ("processing_started_at", sa.Column("processing_started_at", sa.DateTime(timezone=True), nullable=True)),
        ("processing_next_attempt_at", sa.Column("processing_next_attempt_at", sa.DateTime(timezone=True), nullable=True)),
        ("processed_at", sa.Column("processed_at", sa.DateTime(timezone=True), nullable=True)),
    )
    for name, column in additions:
        if name not in columns:
            op.add_column("academic_resources", column)


def downgrade() -> None:
    for name in ("processed_at", "processing_next_attempt_at", "processing_started_at", "processing_error", "processing_attempts"):
        op.drop_column("academic_resources", name)
