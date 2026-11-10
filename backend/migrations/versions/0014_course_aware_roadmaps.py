"""Add reviewed course profiles and activity-aware semester roadmaps."""

from alembic import op
import sqlalchemy as sa


revision = "0014_course_aware_roadmaps"
down_revision = "0013_matcher_evidence"
branch_labels = None
depends_on = None


def _columns(table_name: str) -> set[str]:
    """Return current column names so recovery from development create-all state stays safe."""
    return {item["name"] for item in sa.inspect(op.get_bind()).get_columns(table_name)}


def _indexes(table_name: str) -> set[str]:
    """Return current named indexes before creating or removing migration-owned indexes."""
    return {item["name"] for item in sa.inspect(op.get_bind()).get_indexes(table_name)}


def _foreign_keys(table_name: str) -> set[str]:
    """Return named foreign keys so bootstrap-created schemas can downgrade safely."""
    return {
        str(item["name"])
        for item in sa.inspect(op.get_bind()).get_foreign_keys(table_name)
        if item.get("name")
    }


def upgrade() -> None:
    """Persist course workload review, unit ordering, typed sessions, and semester-plan scope."""
    version_columns = _columns("syllabus_versions")
    with op.batch_alter_table("syllabus_versions") as batch:
        if "roadmap_profile_json" not in version_columns:
            batch.add_column(sa.Column("roadmap_profile_json", sa.Text(), nullable=False, server_default="{}"))
        if "roadmap_profile_status" not in version_columns:
            batch.add_column(sa.Column("roadmap_profile_status", sa.String(length=24), nullable=False, server_default="pending_review"))
        if "roadmap_profile_review_notes" not in version_columns:
            batch.add_column(sa.Column("roadmap_profile_review_notes", sa.Text(), nullable=False, server_default=""))
    if "ix_syllabus_versions_roadmap_profile_status" not in _indexes("syllabus_versions"):
        op.create_index("ix_syllabus_versions_roadmap_profile_status", "syllabus_versions", ["roadmap_profile_status"])

    concept_columns = _columns("concepts")
    if "unit_sequence" not in concept_columns:
        with op.batch_alter_table("concepts") as batch:
            batch.add_column(sa.Column("unit_sequence", sa.Integer(), nullable=True))

    plan_columns = _columns("study_plans")
    with op.batch_alter_table("study_plans") as batch:
        if "scope_type" not in plan_columns:
            batch.add_column(sa.Column("scope_type", sa.String(length=24), nullable=False, server_default="course"))
        if "mode" not in plan_columns:
            batch.add_column(sa.Column("mode", sa.String(length=24), nullable=False, server_default="full_term"))
        if "start_date" not in plan_columns:
            batch.add_column(sa.Column("start_date", sa.Date(), nullable=True))
        if "revision_minutes" not in plan_columns:
            batch.add_column(sa.Column("revision_minutes", sa.Integer(), nullable=False, server_default="30"))
        if "unavailable_weekdays_json" not in plan_columns:
            batch.add_column(sa.Column("unavailable_weekdays_json", sa.Text(), nullable=False, server_default="[]"))
        if "program_code" not in plan_columns:
            batch.add_column(sa.Column("program_code", sa.String(length=20), nullable=True))
        if "scheme_year" not in plan_columns:
            batch.add_column(sa.Column("scheme_year", sa.Integer(), nullable=True))
        if "semester" not in plan_columns:
            batch.add_column(sa.Column("semester", sa.Integer(), nullable=True))
        batch.alter_column("course_id", existing_type=sa.String(length=36), nullable=True)
    op.execute(sa.text("UPDATE study_plans SET start_date = target_date WHERE start_date IS NULL"))
    with op.batch_alter_table("study_plans") as batch:
        batch.alter_column("start_date", existing_type=sa.Date(), nullable=False)
    if "ix_study_plans_scope_type" not in _indexes("study_plans"):
        op.create_index("ix_study_plans_scope_type", "study_plans", ["scope_type"])

    item_columns = _columns("study_plan_items")
    with op.batch_alter_table("study_plan_items") as batch:
        if "course_id" not in item_columns:
            batch.add_column(sa.Column("course_id", sa.String(length=36), nullable=True))
            batch.create_foreign_key("fk_study_plan_items_course_id_courses", "courses", ["course_id"], ["id"])
        if "syllabus_version_id" not in item_columns:
            batch.add_column(sa.Column("syllabus_version_id", sa.String(length=36), nullable=True))
            batch.create_foreign_key("fk_study_plan_items_syllabus_version_id_syllabus_versions", "syllabus_versions", ["syllabus_version_id"], ["id"])
        if "activity_type" not in item_columns:
            batch.add_column(sa.Column("activity_type", sa.String(length=32), nullable=False, server_default="learn"))
        if "modality" not in item_columns:
            batch.add_column(sa.Column("modality", sa.String(length=32), nullable=False, server_default="self_study"))
        if "unit_label" not in item_columns:
            batch.add_column(sa.Column("unit_label", sa.String(length=120), nullable=True))
        if "source_page" not in item_columns:
            batch.add_column(sa.Column("source_page", sa.Integer(), nullable=True))
        if "assessment_scope" not in item_columns:
            batch.add_column(sa.Column("assessment_scope", sa.String(length=24), nullable=False, server_default="both"))
        if "evidence_question_ids_json" not in item_columns:
            batch.add_column(sa.Column("evidence_question_ids_json", sa.Text(), nullable=False, server_default="[]"))
    op.execute(sa.text(
        "UPDATE study_plan_items SET course_id = "
        "(SELECT concepts.course_id FROM concepts WHERE concepts.id = study_plan_items.concept_id) "
        "WHERE course_id IS NULL"
    ))
    with op.batch_alter_table("study_plan_items") as batch:
        batch.alter_column("course_id", existing_type=sa.String(length=36), nullable=False)
    if "ix_study_plan_items_course_id" not in _indexes("study_plan_items"):
        op.create_index("ix_study_plan_items_course_id", "study_plan_items", ["course_id"])


def downgrade() -> None:
    """Remove course-aware planning fields while retaining one representative course per old plan."""
    op.execute(sa.text(
        "UPDATE study_plans SET course_id = "
        "(SELECT study_plan_items.course_id FROM study_plan_items "
        "WHERE study_plan_items.plan_id = study_plans.id AND study_plan_items.course_id IS NOT NULL "
        "ORDER BY study_plan_items.sequence LIMIT 1) WHERE course_id IS NULL"
    ))
    if "ix_study_plan_items_course_id" in _indexes("study_plan_items"):
        op.drop_index("ix_study_plan_items_course_id", table_name="study_plan_items")
    item_columns = _columns("study_plan_items")
    item_foreign_keys = _foreign_keys("study_plan_items")
    with op.batch_alter_table("study_plan_items") as batch:
        if "syllabus_version_id" in item_columns and "fk_study_plan_items_syllabus_version_id_syllabus_versions" in item_foreign_keys:
            batch.drop_constraint("fk_study_plan_items_syllabus_version_id_syllabus_versions", type_="foreignkey")
        if "course_id" in item_columns and "fk_study_plan_items_course_id_courses" in item_foreign_keys:
            batch.drop_constraint("fk_study_plan_items_course_id_courses", type_="foreignkey")
        for name in (
            "evidence_question_ids_json", "assessment_scope", "source_page", "unit_label",
            "modality", "activity_type", "syllabus_version_id", "course_id",
        ):
            if name in item_columns:
                batch.drop_column(name)

    if "ix_study_plans_scope_type" in _indexes("study_plans"):
        op.drop_index("ix_study_plans_scope_type", table_name="study_plans")
    plan_columns = _columns("study_plans")
    with op.batch_alter_table("study_plans") as batch:
        for name in ("semester", "scheme_year", "program_code", "unavailable_weekdays_json", "revision_minutes", "start_date", "mode", "scope_type"):
            if name in plan_columns:
                batch.drop_column(name)
        batch.alter_column("course_id", existing_type=sa.String(length=36), nullable=False)

    concept_columns = _columns("concepts")
    if "unit_sequence" in concept_columns:
        with op.batch_alter_table("concepts") as batch:
            batch.drop_column("unit_sequence")

    if "ix_syllabus_versions_roadmap_profile_status" in _indexes("syllabus_versions"):
        op.drop_index("ix_syllabus_versions_roadmap_profile_status", table_name="syllabus_versions")
    version_columns = _columns("syllabus_versions")
    with op.batch_alter_table("syllabus_versions") as batch:
        for name in ("roadmap_profile_review_notes", "roadmap_profile_status", "roadmap_profile_json"):
            if name in version_columns:
                batch.drop_column(name)
