"""Retain source PDF filename and page on RVCE course records."""

from alembic import op
import sqlalchemy as sa


revision = "0008_rvce_source_page"
down_revision = "0007_rvce_syllabus_courses"
branch_labels = None
depends_on = None


def upgrade() -> None:
    """Add source filename and page columns when they are not already present."""
    inspector = sa.inspect(op.get_bind())
    columns = {column["name"] for column in inspector.get_columns("rvce_syllabus_courses")}
    if "source_filename" not in columns:
        op.add_column("rvce_syllabus_courses", sa.Column("source_filename", sa.String(length=500), nullable=False, server_default=""))
    if "source_page" not in columns:
        op.add_column("rvce_syllabus_courses", sa.Column("source_page", sa.Integer(), nullable=True))


def downgrade() -> None:
    """Remove the RVCE source-location columns introduced by this revision."""
    op.drop_column("rvce_syllabus_courses", "source_page")
    op.drop_column("rvce_syllabus_courses", "source_filename")
