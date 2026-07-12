"""Add normalized job fields.

Revision ID: 0005_normalized_job_fields
Revises: 0004_analysis_idempotency
Create Date: 2026-07-12
"""

from alembic import op
import sqlalchemy as sa

revision = "0005_normalized_job_fields"
down_revision = "0004_analysis_idempotency"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column("job_posts", sa.Column("source_type", sa.String(length=32), nullable=False, server_default="internal"))
    op.add_column("job_posts", sa.Column("source_provider", sa.String(length=80), nullable=False, server_default="fairhire"))
    op.add_column("job_posts", sa.Column("external_id", sa.String(length=180), nullable=False, server_default=""))
    op.add_column("job_posts", sa.Column("canonical_title", sa.String(length=180), nullable=False, server_default=""))
    op.add_column("job_posts", sa.Column("canonical_company", sa.String(length=180), nullable=False, server_default=""))
    op.add_column("job_posts", sa.Column("canonical_location", sa.String(length=180), nullable=False, server_default=""))
    op.add_column("job_posts", sa.Column("canonical_remote", sa.Integer(), nullable=False, server_default="1"))
    op.add_column("job_posts", sa.Column("canonical_salary_min", sa.Integer(), nullable=False, server_default="0"))
    op.add_column("job_posts", sa.Column("canonical_salary_max", sa.Integer(), nullable=False, server_default="0"))
    op.add_column("job_posts", sa.Column("canonical_currency", sa.String(length=16), nullable=False, server_default="USD"))
    op.add_column("job_posts", sa.Column("canonical_skills", sa.Text(), nullable=False, server_default="[]"))
    op.create_index("ix_job_posts_source_provider", "job_posts", ["source_provider"])
    op.create_index("ix_job_posts_external_id", "job_posts", ["external_id"])
    op.execute("UPDATE job_posts SET canonical_title = lower(title), canonical_company = lower(company), canonical_location = lower(location)")
    op.execute("UPDATE job_posts SET canonical_remote = CASE WHEN work_mode = 'remote' THEN 1 ELSE 0 END")


def downgrade() -> None:
    op.drop_index("ix_job_posts_external_id", table_name="job_posts")
    op.drop_index("ix_job_posts_source_provider", table_name="job_posts")
    op.drop_column("job_posts", "canonical_skills")
    op.drop_column("job_posts", "canonical_currency")
    op.drop_column("job_posts", "canonical_salary_max")
    op.drop_column("job_posts", "canonical_salary_min")
    op.drop_column("job_posts", "canonical_remote")
    op.drop_column("job_posts", "canonical_location")
    op.drop_column("job_posts", "canonical_company")
    op.drop_column("job_posts", "canonical_title")
    op.drop_column("job_posts", "external_id")
    op.drop_column("job_posts", "source_provider")
    op.drop_column("job_posts", "source_type")
