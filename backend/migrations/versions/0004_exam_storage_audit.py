"""Add historical exam, storage metadata, and audit retention records."""

from alembic import op
import sqlalchemy as sa

revision = "0004_exam_storage_audit"
down_revision = "0003_resource_mappings"
branch_labels = None
depends_on = None


def upgrade() -> None:
    inspector = sa.inspect(op.get_bind())
    if "processed_key" not in {column["name"] for column in inspector.get_columns("academic_resources")}:
        op.add_column("academic_resources", sa.Column("processed_key", sa.String(length=500), nullable=True))
    if "historical_exam_questions" not in inspector.get_table_names():
        op.create_table(
        "historical_exam_questions",
        sa.Column("id", sa.String(length=36), primary_key=True),
        sa.Column("course_id", sa.String(length=36), sa.ForeignKey("courses.id"), nullable=False),
        sa.Column("source", sa.String(length=240), nullable=False),
        sa.Column("exam_year", sa.Integer(), nullable=False),
        sa.Column("prompt", sa.Text(), nullable=False),
        sa.Column("concept_id", sa.String(length=36), sa.ForeignKey("concepts.id"), nullable=True),
        sa.Column("topic_label", sa.String(length=120), nullable=False, server_default="general"),
        sa.Column("difficulty", sa.Integer(), nullable=False, server_default="1"),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        )
        op.create_index("ix_historical_exam_questions_course_id", "historical_exam_questions", ["course_id"])
        op.create_index("ix_historical_exam_questions_exam_year", "historical_exam_questions", ["exam_year"])
        op.create_index("ix_historical_exam_questions_concept_id", "historical_exam_questions", ["concept_id"])
    if "audit_events" not in inspector.get_table_names():
        op.create_table(
        "audit_events",
        sa.Column("id", sa.String(length=36), primary_key=True),
        sa.Column("actor_id", sa.String(length=36), sa.ForeignKey("users.id"), nullable=True),
        sa.Column("event_type", sa.String(length=80), nullable=False),
        sa.Column("request_id", sa.String(length=64), nullable=True),
        sa.Column("metadata_json", sa.Text(), nullable=False, server_default="{}"),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        )
        op.create_index("ix_audit_events_actor_id", "audit_events", ["actor_id"])
        op.create_index("ix_audit_events_event_type", "audit_events", ["event_type"])
        op.create_index("ix_audit_events_created_at", "audit_events", ["created_at"])


def downgrade() -> None:
    op.drop_index("ix_audit_events_created_at", table_name="audit_events")
    op.drop_index("ix_audit_events_event_type", table_name="audit_events")
    op.drop_index("ix_audit_events_actor_id", table_name="audit_events")
    op.drop_table("audit_events")
    op.drop_index("ix_historical_exam_questions_concept_id", table_name="historical_exam_questions")
    op.drop_index("ix_historical_exam_questions_exam_year", table_name="historical_exam_questions")
    op.drop_index("ix_historical_exam_questions_course_id", table_name="historical_exam_questions")
    op.drop_table("historical_exam_questions")
    op.drop_column("academic_resources", "processed_key")
