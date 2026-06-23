"""Initial FairHire schema.

Revision ID: 0001_initial_schema
Revises:
Create Date: 2026-06-23
"""

from alembic import op
import sqlalchemy as sa

revision = "0001_initial_schema"
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "users",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("name", sa.String(length=120), nullable=False),
        sa.Column("email", sa.String(length=255), nullable=False),
        sa.Column("password_hash", sa.String(length=128), nullable=False, server_default=""),
        sa.Column("role", sa.String(length=32), nullable=False),
        sa.Column("language", sa.String(length=8), nullable=False, server_default="en"),
        sa.Column("verification_status", sa.String(length=32), nullable=False, server_default="unverified"),
        sa.Column("verification_channel", sa.String(length=32), nullable=False, server_default="email"),
        sa.Column("low_bandwidth", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.UniqueConstraint("email"),
    )
    op.create_index("ix_users_id", "users", ["id"])
    op.create_index("ix_users_email", "users", ["email"])
    op.create_index("ix_users_role", "users", ["role"])

    op.create_table(
        "candidates",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("user_id", sa.Integer(), sa.ForeignKey("users.id"), nullable=False),
        sa.Column("headline", sa.String(length=180), nullable=False, server_default=""),
        sa.Column("skills", sa.Text(), nullable=False, server_default=""),
        sa.Column("experience", sa.Text(), nullable=False, server_default=""),
        sa.Column("education", sa.Text(), nullable=False, server_default=""),
        sa.Column("portfolio_url", sa.String(length=255), nullable=False, server_default=""),
        sa.Column("github_url", sa.String(length=255), nullable=False, server_default=""),
        sa.Column("linkedin_url", sa.String(length=255), nullable=False, server_default=""),
        sa.Column("project_demo_urls", sa.Text(), nullable=False, server_default=""),
        sa.Column("visibility", sa.String(length=64), nullable=False, server_default="private"),
        sa.Column("completeness_score", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("bio", sa.Text(), nullable=False, server_default=""),
        sa.UniqueConstraint("user_id"),
    )
    op.create_index("ix_candidates_id", "candidates", ["id"])
    op.create_index("ix_candidates_user_id", "candidates", ["user_id"])

    op.create_table(
        "recruiters",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("user_id", sa.Integer(), sa.ForeignKey("users.id"), nullable=False),
        sa.Column("company", sa.String(length=180), nullable=False, server_default=""),
        sa.Column("title", sa.String(length=120), nullable=False, server_default=""),
        sa.Column("website", sa.String(length=255), nullable=False, server_default=""),
        sa.Column("country", sa.String(length=120), nullable=False, server_default=""),
        sa.Column("city", sa.String(length=120), nullable=False, server_default=""),
        sa.Column("industry", sa.String(length=120), nullable=False, server_default=""),
        sa.Column("company_size", sa.String(length=80), nullable=False, server_default=""),
        sa.Column("description", sa.Text(), nullable=False, server_default=""),
        sa.Column("contact_email", sa.String(length=255), nullable=False, server_default=""),
        sa.Column("company_status", sa.String(length=32), nullable=False, server_default="pending_review"),
        sa.Column("trust_score", sa.Integer(), nullable=False, server_default="0"),
        sa.UniqueConstraint("user_id"),
    )
    op.create_index("ix_recruiters_id", "recruiters", ["id"])
    op.create_index("ix_recruiters_user_id", "recruiters", ["user_id"])

    op.create_table(
        "resumes",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("candidate_user_id", sa.Integer(), sa.ForeignKey("users.id"), nullable=False),
        sa.Column("title", sa.String(length=180), nullable=False, server_default="Primary resume"),
        sa.Column("resume_text", sa.Text(), nullable=False),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.Column("updated_at", sa.DateTime(), nullable=False),
    )
    op.create_index("ix_resumes_id", "resumes", ["id"])
    op.create_index("ix_resumes_candidate_user_id", "resumes", ["candidate_user_id"])

    op.create_table(
        "job_posts",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("recruiter_user_id", sa.Integer(), sa.ForeignKey("users.id"), nullable=False),
        sa.Column("title", sa.String(length=180), nullable=False),
        sa.Column("company", sa.String(length=180), nullable=False, server_default=""),
        sa.Column("location", sa.String(length=180), nullable=False, server_default=""),
        sa.Column("work_mode", sa.String(length=32), nullable=False, server_default="remote"),
        sa.Column("salary_range", sa.String(length=120), nullable=False, server_default=""),
        sa.Column("experience_level", sa.String(length=120), nullable=False, server_default=""),
        sa.Column("required_skills", sa.Text(), nullable=False, server_default=""),
        sa.Column("nice_to_have_skills", sa.Text(), nullable=False, server_default=""),
        sa.Column("description", sa.Text(), nullable=False),
        sa.Column("status", sa.String(length=32), nullable=False, server_default="draft"),
        sa.Column("spam_score", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("spam_reasons", sa.Text(), nullable=False, server_default="[]"),
        sa.Column("quality_score", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("quality_tips", sa.Text(), nullable=False, server_default="[]"),
        sa.Column("reports_count", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.Column("updated_at", sa.DateTime(), nullable=False),
    )
    op.create_index("ix_job_posts_id", "job_posts", ["id"])
    op.create_index("ix_job_posts_recruiter_user_id", "job_posts", ["recruiter_user_id"])

    op.create_table(
        "analyses",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("resume_id", sa.Integer(), sa.ForeignKey("resumes.id"), nullable=False),
        sa.Column("job_post_id", sa.Integer(), sa.ForeignKey("job_posts.id"), nullable=False),
        sa.Column("candidate_user_id", sa.Integer(), sa.ForeignKey("users.id"), nullable=False),
        sa.Column("recruiter_user_id", sa.Integer(), sa.ForeignKey("users.id"), nullable=False),
        sa.Column("match_score", sa.Integer(), nullable=False),
        sa.Column("missing_skills", sa.Text(), nullable=False, server_default="[]"),
        sa.Column("strongest_skills", sa.Text(), nullable=False, server_default="[]"),
        sa.Column("improvements", sa.Text(), nullable=False, server_default="[]"),
        sa.Column("summary", sa.Text(), nullable=False, server_default=""),
        sa.Column("resume_summary", sa.Text(), nullable=False, server_default=""),
        sa.Column("fit_summary", sa.Text(), nullable=False, server_default=""),
        sa.Column("concerns", sa.Text(), nullable=False, server_default="[]"),
        sa.Column("interview_questions", sa.Text(), nullable=False, server_default="[]"),
        sa.Column("recommendation", sa.String(length=32), nullable=False, server_default="Possible fit"),
        sa.Column("recruiter_status", sa.String(length=32), nullable=False, server_default="Maybe"),
        sa.Column("recruiter_notes", sa.Text(), nullable=False, server_default=""),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.Column("source", sa.String(length=32), nullable=False, server_default="heuristic"),
    )
    op.create_index("ix_analyses_id", "analyses", ["id"])
    op.create_index("ix_analyses_resume_id", "analyses", ["resume_id"])
    op.create_index("ix_analyses_job_post_id", "analyses", ["job_post_id"])
    op.create_index("ix_analyses_candidate_user_id", "analyses", ["candidate_user_id"])
    op.create_index("ix_analyses_recruiter_user_id", "analyses", ["recruiter_user_id"])
    op.create_index("ix_analyses_created_at", "analyses", ["created_at"])

    op.create_table(
        "job_reports",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("job_post_id", sa.Integer(), sa.ForeignKey("job_posts.id"), nullable=False),
        sa.Column("candidate_user_id", sa.Integer(), sa.ForeignKey("users.id"), nullable=False),
        sa.Column("reason", sa.Text(), nullable=False),
        sa.Column("created_at", sa.DateTime(), nullable=False),
    )
    op.create_index("ix_job_reports_id", "job_reports", ["id"])
    op.create_index("ix_job_reports_job_post_id", "job_reports", ["job_post_id"])
    op.create_index("ix_job_reports_candidate_user_id", "job_reports", ["candidate_user_id"])


def downgrade() -> None:
    op.drop_table("job_reports")
    op.drop_table("analyses")
    op.drop_table("job_posts")
    op.drop_table("resumes")
    op.drop_table("recruiters")
    op.drop_table("candidates")
    op.drop_table("users")
