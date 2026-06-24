"""Add candidate project demo URLs.

Revision ID: 0003_project_demos
Revises: 0002_add_user_phone_number
Create Date: 2026-06-23
"""

from alembic import op
import sqlalchemy as sa

revision = "0003_project_demos"
down_revision = "0002_add_user_phone_number"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column("candidates", sa.Column("project_demo_urls", sa.Text(), nullable=False, server_default=""))


def downgrade() -> None:
    op.drop_column("candidates", "project_demo_urls")
