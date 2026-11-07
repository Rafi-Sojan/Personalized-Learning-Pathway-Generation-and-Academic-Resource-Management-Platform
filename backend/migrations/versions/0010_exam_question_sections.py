"""Classify imported paper prompts by part and question category."""

from alembic import op
import sqlalchemy as sa


revision = "0010_exam_question_sections"
down_revision = "0009_concept_syllabus_provenance"
branch_labels = None
depends_on = None


def upgrade() -> None:
    """Add nullable paper-part labels and default legacy rows to main questions."""
    inspector = sa.inspect(op.get_bind())
    columns = {column["name"] for column in inspector.get_columns("historical_exam_questions")}
    indexes = {index["name"] for index in inspector.get_indexes("historical_exam_questions")}
    if "paper_part" not in columns or "question_kind" not in columns or "ix_historical_exam_questions_question_kind" not in indexes:
        with op.batch_alter_table("historical_exam_questions") as batch:
            if "paper_part" not in columns:
                batch.add_column(sa.Column("paper_part", sa.String(length=20), nullable=True))
            if "question_kind" not in columns:
                batch.add_column(sa.Column("question_kind", sa.String(length=20), nullable=False, server_default="main"))
            if "ix_historical_exam_questions_question_kind" not in indexes:
                batch.create_index("ix_historical_exam_questions_question_kind", ["question_kind"])


def downgrade() -> None:
    """Remove part/category columns and their lookup index."""
    inspector = sa.inspect(op.get_bind())
    columns = {column["name"] for column in inspector.get_columns("historical_exam_questions")}
    indexes = {index["name"] for index in inspector.get_indexes("historical_exam_questions")}
    with op.batch_alter_table("historical_exam_questions") as batch:
        if "ix_historical_exam_questions_question_kind" in indexes:
            batch.drop_index("ix_historical_exam_questions_question_kind")
        if "question_kind" in columns:
            batch.drop_column("question_kind")
        if "paper_part" in columns:
            batch.drop_column("paper_part")
