"""Add analysis idempotency fields.

Revision ID: 0004_analysis_idempotency
Revises: 0003_project_demos
Create Date: 2026-07-11
"""

from alembic import op
import sqlalchemy as sa

revision = "0004_analysis_idempotency"
down_revision = "0003_project_demos"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column("analyses", sa.Column("idempotency_key", sa.String(length=128), nullable=False, server_default=""))
    op.add_column("analyses", sa.Column("idempotency_user_id", sa.Integer(), nullable=False, server_default="0"))
    op.create_index("ix_analyses_idempotency_user_id", "analyses", ["idempotency_user_id"])


def downgrade() -> None:
    op.drop_index("ix_analyses_idempotency_user_id", table_name="analyses")
    op.drop_column("analyses", "idempotency_user_id")
    op.drop_column("analyses", "idempotency_key")
