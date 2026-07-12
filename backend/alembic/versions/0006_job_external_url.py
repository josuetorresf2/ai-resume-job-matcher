"""Add job external URL.

Revision ID: 0006_job_external_url
Revises: 0005_normalized_job_fields
Create Date: 2026-07-12
"""

from alembic import op
import sqlalchemy as sa

revision = "0006_job_external_url"
down_revision = "0005_normalized_job_fields"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column("job_posts", sa.Column("external_url", sa.String(length=500), nullable=False, server_default=""))


def downgrade() -> None:
    op.drop_column("job_posts", "external_url")
