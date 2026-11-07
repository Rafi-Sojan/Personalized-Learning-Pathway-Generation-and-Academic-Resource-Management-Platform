"""Persist syllabus extraction and question-paper provenance and review state."""

from alembic import op
import sqlalchemy as sa


revision = "0011_ingestion_provenance_review"
down_revision = "0010_exam_question_sections"
branch_labels = None
depends_on = None


def upgrade() -> None:
    """Add durable parsed syllabus records and reviewable question metadata."""
    if "syllabus_records" not in sa.inspect(op.get_bind()).get_table_names():
        op.create_table(
            "syllabus_records",
            sa.Column("id", sa.String(36), primary_key=True),
            sa.Column("syllabus_version_id", sa.String(36), sa.ForeignKey("syllabus_versions.id"), nullable=False),
            sa.Column("source_resource_id", sa.String(36), sa.ForeignKey("academic_resources.id"), nullable=False),
            sa.Column("course_id", sa.String(36), sa.ForeignKey("courses.id"), nullable=False),
            sa.Column("record_type", sa.String(24), nullable=False, server_default="topic"),
            sa.Column("source_page", sa.Integer(), nullable=True),
            sa.Column("source_text", sa.Text(), nullable=False),
            sa.Column("normalized_text", sa.String(500), nullable=False),
            sa.Column("unit_label", sa.String(120), nullable=True),
            sa.Column("parent_label", sa.String(200), nullable=True),
            sa.Column("hours", sa.Float(), nullable=True),
            sa.Column("confidence", sa.Float(), nullable=False, server_default="0.5"),
            sa.Column("review_status", sa.String(24), nullable=False, server_default="pending_review"),
            sa.Column("mapped_concept_id", sa.String(36), sa.ForeignKey("concepts.id"), nullable=True),
        )
    edge_columns = {column["name"] for column in sa.inspect(op.get_bind()).get_columns("concept_prerequisites")}
    with op.batch_alter_table("concept_prerequisites") as batch:
        if "status" not in edge_columns:
            batch.add_column(sa.Column("status", sa.String(length=24), nullable=False, server_default="accepted"))
            batch.create_index("ix_concept_prerequisites_status", ["status"])
        if "source_page" not in edge_columns:
            batch.add_column(sa.Column("source_page", sa.Integer(), nullable=True))
        if "confidence" not in edge_columns:
            batch.add_column(sa.Column("confidence", sa.Float(), nullable=True))
        if "rationale" not in edge_columns:
            batch.add_column(sa.Column("rationale", sa.Text(), nullable=False, server_default=""))
    for column in ("syllabus_version_id", "source_resource_id", "course_id", "record_type", "review_status", "mapped_concept_id"):
        index_name = f"ix_syllabus_records_{column}"
        existing_indexes = {index["name"] for index in sa.inspect(op.get_bind()).get_indexes("syllabus_records")}
        if index_name not in existing_indexes:
            op.create_index(index_name, "syllabus_records", [column])
    concept_columns = {column["name"] for column in sa.inspect(op.get_bind()).get_columns("concepts")}
    if "parent_concept_id" not in concept_columns:
        with op.batch_alter_table("concepts") as batch:
            batch.add_column(sa.Column("parent_concept_id", sa.String(36), nullable=True))
            batch.create_foreign_key("fk_concepts_parent_concept_id_concepts", "concepts", ["parent_concept_id"], ["id"])
            batch.create_index("ix_concepts_parent_concept_id", ["parent_concept_id"])
    if "estimated_minutes" not in concept_columns:
        with op.batch_alter_table("concepts") as batch:
            batch.add_column(sa.Column("estimated_minutes", sa.Integer(), nullable=True))
    columns = [
        sa.Column("source_resource_id", sa.String(36), nullable=True),
        sa.Column("source_document", sa.String(length=500), nullable=False, server_default=""),
        sa.Column("question_number", sa.String(32), nullable=True),
        sa.Column("subpart", sa.String(32), nullable=True),
        sa.Column("marks", sa.Float(), nullable=True),
        sa.Column("source_page", sa.Integer(), nullable=True),
        sa.Column("assessment_type", sa.String(24), nullable=False, server_default="unknown"),
        sa.Column("question_format", sa.String(24), nullable=False, server_default="unknown"),
        sa.Column("mapping_confidence", sa.Float(), nullable=True),
        sa.Column("review_status", sa.String(24), nullable=False, server_default="pending_review"),
    ]
    with op.batch_alter_table("historical_exam_questions") as batch:
        batch.alter_column("difficulty", existing_type=sa.Integer(), nullable=True)
        for column in columns:
            batch.add_column(column)
        batch.create_foreign_key("fk_historical_exam_questions_source_resource_id", "academic_resources", ["source_resource_id"], ["id"])
        batch.create_index("ix_historical_exam_questions_source_resource_id", ["source_resource_id"])
        batch.create_index("ix_historical_exam_questions_assessment_type", ["assessment_type"])
        batch.create_index("ix_historical_exam_questions_review_status", ["review_status"])
    # Legacy difficulty was defaulted to 1 during import and was not reliable evidence.
    op.execute("UPDATE historical_exam_questions SET difficulty = NULL")


def downgrade() -> None:
    """Remove ingestion additions while retaining the preceding question model."""
    op.execute("UPDATE historical_exam_questions SET difficulty = 1 WHERE difficulty IS NULL")
    with op.batch_alter_table("historical_exam_questions") as batch:
        batch.drop_constraint("fk_historical_exam_questions_source_resource_id", type_="foreignkey")
        batch.drop_index("ix_historical_exam_questions_source_resource_id")
        batch.drop_index("ix_historical_exam_questions_review_status")
        batch.drop_index("ix_historical_exam_questions_assessment_type")
        for name in ("review_status", "mapping_confidence", "question_format", "assessment_type", "source_page", "marks", "subpart", "question_number", "source_document", "source_resource_id"):
            batch.drop_column(name)
        batch.alter_column("difficulty", existing_type=sa.Integer(), nullable=False)
    with op.batch_alter_table("concept_prerequisites") as batch:
        batch.drop_index("ix_concept_prerequisites_status")
        for name in ("rationale", "confidence", "source_page", "status"):
            batch.drop_column(name)
    for column in ("syllabus_version_id", "source_resource_id", "course_id", "record_type", "review_status", "mapped_concept_id"):
        op.drop_index(f"ix_syllabus_records_{column}", table_name="syllabus_records")
    op.drop_table("syllabus_records")
    with op.batch_alter_table("concepts") as batch:
        batch.drop_index("ix_concepts_parent_concept_id")
        batch.drop_column("estimated_minutes")
        batch.drop_constraint("fk_concepts_parent_concept_id_concepts", type_="foreignkey")
        batch.drop_column("parent_concept_id")
