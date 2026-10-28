"""Add per-user token revocation versions."""

from alembic import op
import sqlalchemy as sa

revision = "0005_token_revocation"
down_revision = "0004_exam_storage_audit"
branch_labels = None
depends_on = None


def upgrade() -> None:
    inspector = sa.inspect(op.get_bind())
    if "token_version" not in {column["name"] for column in inspector.get_columns("users")}:
        op.add_column("users", sa.Column("token_version", sa.Integer(), nullable=False, server_default="0"))


def downgrade() -> None:
    op.drop_column("users", "token_version")
