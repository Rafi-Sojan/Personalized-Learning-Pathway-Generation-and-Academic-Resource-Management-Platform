"""Persist explainable concept-matching evidence for historical questions."""

from alembic import op
import sqlalchemy as sa


revision = "0013_matcher_evidence"
down_revision = "0012_course_academic_scope"
branch_labels = None
depends_on = None


def upgrade() -> None:
    """Add bounded JSON text metadata while preserving all existing mappings."""
    columns = {item["name"] for item in sa.inspect(op.get_bind()).get_columns("historical_exam_questions")}
    if "mapping_metadata_json" not in columns:
        op.add_column(
            "historical_exam_questions",
            sa.Column("mapping_metadata_json", sa.Text(), nullable=False, server_default="{}"),
        )


def downgrade() -> None:
    """Remove matcher evidence without changing historical question records."""
    columns = {item["name"] for item in sa.inspect(op.get_bind()).get_columns("historical_exam_questions")}
    if "mapping_metadata_json" in columns:
        with op.batch_alter_table("historical_exam_questions") as batch:
            batch.drop_column("mapping_metadata_json")
