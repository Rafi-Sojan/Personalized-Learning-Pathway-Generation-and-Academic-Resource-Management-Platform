"""Add source-backed RVCE syllabus course records."""

from alembic import op
import sqlalchemy as sa


revision = "0007_rvce_syllabus_courses"
down_revision = "0006_processing_reliability"
branch_labels = None
depends_on = None


def upgrade() -> None:
    inspector = sa.inspect(op.get_bind())
    if "rvce_syllabus_courses" in inspector.get_table_names():
        return
    op.create_table(
        "rvce_syllabus_courses",
        sa.Column("id", sa.String(length=36), primary_key=True),
        sa.Column("program_code", sa.String(length=20), nullable=False),
        sa.Column("scheme_year", sa.Integer(), nullable=False),
        sa.Column("semester", sa.Integer(), nullable=False),
        sa.Column("course_code", sa.String(length=40), nullable=False),
        sa.Column("title", sa.String(length=240), nullable=False),
        sa.Column("credits", sa.Float(), nullable=False),
        sa.Column("category", sa.String(length=80), nullable=False, server_default=""),
        sa.Column("contact_hours", sa.Float(), nullable=True),
        sa.Column("prerequisites_json", sa.Text(), nullable=False, server_default="[]"),
        sa.Column("outcomes_json", sa.Text(), nullable=False, server_default="[]"),
        sa.Column("source_url", sa.String(length=1000), nullable=False),
        sa.Column("source_checksum", sa.String(length=64), nullable=False),
        sa.Column("verification_status", sa.String(length=24), nullable=False, server_default="pending_review"),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.UniqueConstraint("program_code", "scheme_year", "semester", "course_code", name="uq_rvce_syllabus_course_identity"),
    )
    op.create_index("ix_rvce_syllabus_courses_program_code", "rvce_syllabus_courses", ["program_code"])
    op.create_index("ix_rvce_syllabus_courses_scheme_year", "rvce_syllabus_courses", ["scheme_year"])
    op.create_index("ix_rvce_syllabus_courses_semester", "rvce_syllabus_courses", ["semester"])
    op.create_index("ix_rvce_syllabus_courses_course_code", "rvce_syllabus_courses", ["course_code"])
    op.create_index("ix_rvce_syllabus_courses_verification_status", "rvce_syllabus_courses", ["verification_status"])


def downgrade() -> None:
    op.drop_index("ix_rvce_syllabus_courses_verification_status", table_name="rvce_syllabus_courses")
    op.drop_index("ix_rvce_syllabus_courses_course_code", table_name="rvce_syllabus_courses")
    op.drop_index("ix_rvce_syllabus_courses_semester", table_name="rvce_syllabus_courses")
    op.drop_index("ix_rvce_syllabus_courses_scheme_year", table_name="rvce_syllabus_courses")
    op.drop_index("ix_rvce_syllabus_courses_program_code", table_name="rvce_syllabus_courses")
    op.drop_table("rvce_syllabus_courses")
