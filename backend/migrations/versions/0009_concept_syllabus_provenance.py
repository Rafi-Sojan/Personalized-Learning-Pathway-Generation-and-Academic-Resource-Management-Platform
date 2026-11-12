"""Record syllabus version, unit, and page provenance on mapped concepts."""

from alembic import op
import sqlalchemy as sa


revision = "0009_concept_syllabus_provenance"
down_revision = "0008_rvce_source_page"
branch_labels = None
depends_on = None


def upgrade() -> None:
    """Add provenance fields only when an earlier metadata-created schema lacks them."""
    inspector = sa.inspect(op.get_bind())
    columns = {column["name"] for column in inspector.get_columns("concepts")}
    indexes = {index["name"] for index in inspector.get_indexes("concepts")}
    foreign_keys = inspector.get_foreign_keys("concepts")
    has_version_foreign_key = any("syllabus_version_id" in key.get("constrained_columns", []) for key in foreign_keys)
    needs_change = bool({"unit_label", "source_page", "syllabus_version_id"} - columns) or not has_version_foreign_key or "ix_concepts_syllabus_version_id" not in indexes
    if not needs_change:
        return
    with op.batch_alter_table("concepts") as batch:
        if "unit_label" not in columns:
            batch.add_column(sa.Column("unit_label", sa.String(length=120), nullable=True))
        if "source_page" not in columns:
            batch.add_column(sa.Column("source_page", sa.Integer(), nullable=True))
        if "syllabus_version_id" not in columns:
            batch.add_column(sa.Column("syllabus_version_id", sa.String(length=36), nullable=True))
        if not has_version_foreign_key:
            batch.create_foreign_key(
                "fk_concepts_syllabus_version_id_syllabus_versions",
                "syllabus_versions",
                ["syllabus_version_id"],
                ["id"],
            )
        if "ix_concepts_syllabus_version_id" not in indexes:
            batch.create_index("ix_concepts_syllabus_version_id", ["syllabus_version_id"])


def downgrade() -> None:
    """Remove concept provenance fields introduced by this revision."""
    inspector = sa.inspect(op.get_bind())
    columns = {column["name"] for column in inspector.get_columns("concepts")}
    indexes = {index["name"] for index in inspector.get_indexes("concepts")}
    foreign_keys = inspector.get_foreign_keys("concepts")
    has_version_foreign_key = any("syllabus_version_id" in key.get("constrained_columns", []) for key in foreign_keys)
    with op.batch_alter_table("concepts") as batch:
        if "ix_concepts_syllabus_version_id" in indexes:
            batch.drop_index("ix_concepts_syllabus_version_id")
        if has_version_foreign_key:
            constraint = next(
                (
                    key.get("name")
                    for key in foreign_keys
                    if "syllabus_version_id" in key.get("constrained_columns", [])
                ),
                None,
            )
            if not isinstance(constraint, str):
                raise RuntimeError(
                    "Cannot downgrade: syllabus version "
                    "foreign key has no usable constraint name"
                )
            batch.drop_constraint(
                constraint,
                type_="foreignkey",
            )
        for column in ("syllabus_version_id", "source_page", "unit_label"):
            if column in columns:
                batch.drop_column(column)
