"""Add user phone number.

Revision ID: 0002_add_user_phone_number
Revises: 0001_initial_schema
Create Date: 2026-06-23
"""

from alembic import op
import sqlalchemy as sa

revision = "0002_add_user_phone_number"
down_revision = "0001_initial_schema"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column("users", sa.Column("phone_number", sa.String(length=32), nullable=False, server_default=""))


def downgrade() -> None:
    op.drop_column("users", "phone_number")
