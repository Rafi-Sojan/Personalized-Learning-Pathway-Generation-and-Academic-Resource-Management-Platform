"""Attach learner courses to an RVCE branch, scheme, semester, and catalog origin."""

from alembic import op
import sqlalchemy as sa


revision = "0012_course_academic_scope"
down_revision = "0011_ingestion_provenance_review"
branch_labels = None
depends_on = None


def upgrade() -> None:
    """Add optional academic scope and catalog provenance to learner-owned courses."""
    columns = {item["name"] for item in sa.inspect(op.get_bind()).get_columns("courses")}
    # Add columns outside batch mode so SQLite does not infer contradictory
    # relative positions while rebuilding a table with several new constraints.
    additions = (
        sa.Column("program_code", sa.String(length=20), nullable=True),
        sa.Column("scheme_year", sa.Integer(), nullable=True),
        sa.Column("semester", sa.Integer(), nullable=True),
        sa.Column("origin", sa.String(length=24), nullable=False, server_default="personal"),
        sa.Column("catalog_course_id", sa.String(length=36), nullable=True),
    )
    for column in additions:
        if column.name not in columns:
            op.add_column("courses", column)

    inspector = sa.inspect(op.get_bind())
    foreign_keys = inspector.get_foreign_keys("courses")
    unique_constraints = inspector.get_unique_constraints("courses")
    has_catalog_foreign_key = any(item["constrained_columns"] == ["catalog_course_id"] and item["referred_table"] == "rvce_syllabus_courses" for item in foreign_keys)
    unique_columns = {tuple(item["column_names"]) for item in unique_constraints}
    academic_scope_columns = ("owner_id", "program_code", "scheme_year", "semester", "code")
    catalog_scope_columns = ("owner_id", "catalog_course_id")
    if not has_catalog_foreign_key or academic_scope_columns not in unique_columns or catalog_scope_columns not in unique_columns:
        with op.batch_alter_table("courses") as batch:
            if not has_catalog_foreign_key:
                batch.create_foreign_key("fk_courses_catalog_course_id_rvce_syllabus_courses", "rvce_syllabus_courses", ["catalog_course_id"], ["id"])
            if academic_scope_columns not in unique_columns:
                batch.create_unique_constraint("uq_course_owner_academic_scope", list(academic_scope_columns))
            if catalog_scope_columns not in unique_columns:
                batch.create_unique_constraint("uq_course_owner_catalog_record", list(catalog_scope_columns))

    indexes = {item["name"] for item in sa.inspect(op.get_bind()).get_indexes("courses")}
    for index_name, column_name in (
        ("ix_courses_program_code", "program_code"),
        ("ix_courses_origin", "origin"),
        ("ix_courses_catalog_course_id", "catalog_course_id"),
    ):
        if index_name not in indexes:
            op.create_index(index_name, "courses", [column_name])


def downgrade() -> None:
    """Remove learner-course scope fields and their indexes and constraints."""
    inspector = sa.inspect(op.get_bind())
    indexes = {item["name"] for item in inspector.get_indexes("courses")}
    for index_name in ("ix_courses_catalog_course_id", "ix_courses_origin", "ix_courses_program_code"):
        if index_name in indexes:
            op.drop_index(index_name, table_name="courses")
    unique_constraints = {item["name"] for item in inspector.get_unique_constraints("courses")}
    foreign_keys = {item["name"] for item in inspector.get_foreign_keys("courses")}
    columns = {item["name"] for item in inspector.get_columns("courses")}
    with op.batch_alter_table("courses") as batch:
        if "uq_course_owner_catalog_record" in unique_constraints:
            batch.drop_constraint("uq_course_owner_catalog_record", type_="unique")
        if "uq_course_owner_academic_scope" in unique_constraints:
            batch.drop_constraint("uq_course_owner_academic_scope", type_="unique")
        if "fk_courses_catalog_course_id_rvce_syllabus_courses" in foreign_keys:
            batch.drop_constraint("fk_courses_catalog_course_id_rvce_syllabus_courses", type_="foreignkey")
        for column_name in ("catalog_course_id", "origin", "semester", "scheme_year", "program_code"):
            if column_name in columns:
                batch.drop_column(column_name)
