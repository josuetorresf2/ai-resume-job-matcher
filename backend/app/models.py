from datetime import datetime
from sqlalchemy import DateTime, ForeignKey, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from .database import Base


class User(Base):
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    name: Mapped[str] = mapped_column(String(120))
    email: Mapped[str] = mapped_column(String(255), unique=True, index=True)
    phone_number: Mapped[str] = mapped_column(String(32), default="")
    password_hash: Mapped[str] = mapped_column(String(128), default="")
    role: Mapped[str] = mapped_column(String(32), index=True)
    language: Mapped[str] = mapped_column(String(8), default="en")
    verification_status: Mapped[str] = mapped_column(String(32), default="unverified")
    verification_channel: Mapped[str] = mapped_column(String(32), default="email")
    low_bandwidth: Mapped[int] = mapped_column(Integer, default=0)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

    candidate: Mapped["Candidate | None"] = relationship(back_populates="user", uselist=False)
    recruiter: Mapped["Recruiter | None"] = relationship(back_populates="user", uselist=False)
    resumes: Mapped[list["Resume"]] = relationship(back_populates="candidate_user")
    job_posts: Mapped[list["JobPost"]] = relationship(back_populates="recruiter_user")


class Candidate(Base):
    __tablename__ = "candidates"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"), unique=True, index=True)
    headline: Mapped[str] = mapped_column(String(180), default="")
    skills: Mapped[str] = mapped_column(Text, default="")
    experience: Mapped[str] = mapped_column(Text, default="")
    education: Mapped[str] = mapped_column(Text, default="")
    portfolio_url: Mapped[str] = mapped_column(String(255), default="")
    github_url: Mapped[str] = mapped_column(String(255), default="")
    linkedin_url: Mapped[str] = mapped_column(String(255), default="")
    project_demo_urls: Mapped[str] = mapped_column(Text, default="")
    visibility: Mapped[str] = mapped_column(String(64), default="private")
    completeness_score: Mapped[int] = mapped_column(Integer, default=0)
    bio: Mapped[str] = mapped_column(Text, default="")

    user: Mapped[User] = relationship(back_populates="candidate")


class Recruiter(Base):
    __tablename__ = "recruiters"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"), unique=True, index=True)
    company: Mapped[str] = mapped_column(String(180), default="")
    title: Mapped[str] = mapped_column(String(120), default="")
    website: Mapped[str] = mapped_column(String(255), default="")
    country: Mapped[str] = mapped_column(String(120), default="")
    city: Mapped[str] = mapped_column(String(120), default="")
    industry: Mapped[str] = mapped_column(String(120), default="")
    company_size: Mapped[str] = mapped_column(String(80), default="")
    description: Mapped[str] = mapped_column(Text, default="")
    contact_email: Mapped[str] = mapped_column(String(255), default="")
    company_status: Mapped[str] = mapped_column(String(32), default="pending_review")
    trust_score: Mapped[int] = mapped_column(Integer, default=0)

    user: Mapped[User] = relationship(back_populates="recruiter")


class Resume(Base):
    __tablename__ = "resumes"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    candidate_user_id: Mapped[int] = mapped_column(ForeignKey("users.id"), index=True)
    title: Mapped[str] = mapped_column(String(180), default="Primary resume")
    resume_text: Mapped[str] = mapped_column(Text)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    candidate_user: Mapped[User] = relationship(back_populates="resumes")
    analyses: Mapped[list["Analysis"]] = relationship(back_populates="resume")


class JobPost(Base):
    __tablename__ = "job_posts"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    recruiter_user_id: Mapped[int] = mapped_column(ForeignKey("users.id"), index=True)
    title: Mapped[str] = mapped_column(String(180))
    company: Mapped[str] = mapped_column(String(180), default="")
    location: Mapped[str] = mapped_column(String(180), default="")
    work_mode: Mapped[str] = mapped_column(String(32), default="remote")
    salary_range: Mapped[str] = mapped_column(String(120), default="")
    experience_level: Mapped[str] = mapped_column(String(120), default="")
    required_skills: Mapped[str] = mapped_column(Text, default="")
    nice_to_have_skills: Mapped[str] = mapped_column(Text, default="")
    description: Mapped[str] = mapped_column(Text)
    status: Mapped[str] = mapped_column(String(32), default="draft")
    spam_score: Mapped[int] = mapped_column(Integer, default=0)
    spam_reasons: Mapped[str] = mapped_column(Text, default="[]")
    quality_score: Mapped[int] = mapped_column(Integer, default=0)
    quality_tips: Mapped[str] = mapped_column(Text, default="[]")
    reports_count: Mapped[int] = mapped_column(Integer, default=0)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    recruiter_user: Mapped[User] = relationship(back_populates="job_posts")
    analyses: Mapped[list["Analysis"]] = relationship(back_populates="job_post")


class Analysis(Base):
    __tablename__ = "analyses"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    resume_id: Mapped[int] = mapped_column(ForeignKey("resumes.id"), index=True)
    job_post_id: Mapped[int] = mapped_column(ForeignKey("job_posts.id"), index=True)
    candidate_user_id: Mapped[int] = mapped_column(ForeignKey("users.id"), index=True)
    recruiter_user_id: Mapped[int] = mapped_column(ForeignKey("users.id"), index=True)
    match_score: Mapped[int] = mapped_column(Integer)
    missing_skills: Mapped[str] = mapped_column(Text, default="[]")
    strongest_skills: Mapped[str] = mapped_column(Text, default="[]")
    improvements: Mapped[str] = mapped_column(Text, default="[]")
    summary: Mapped[str] = mapped_column(Text, default="")
    resume_summary: Mapped[str] = mapped_column(Text, default="")
    fit_summary: Mapped[str] = mapped_column(Text, default="")
    concerns: Mapped[str] = mapped_column(Text, default="[]")
    interview_questions: Mapped[str] = mapped_column(Text, default="[]")
    recommendation: Mapped[str] = mapped_column(String(32), default="Possible fit")
    recruiter_status: Mapped[str] = mapped_column(String(32), default="Maybe")
    recruiter_notes: Mapped[str] = mapped_column(Text, default="")
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, index=True)
    source: Mapped[str] = mapped_column(String(32), default="heuristic")
    idempotency_key: Mapped[str] = mapped_column(String(128), default="")
    idempotency_user_id: Mapped[int] = mapped_column(Integer, default=0, index=True)

    resume: Mapped[Resume] = relationship(back_populates="analyses")
    job_post: Mapped[JobPost] = relationship(back_populates="analyses")


class JobReport(Base):
    __tablename__ = "job_reports"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    job_post_id: Mapped[int] = mapped_column(ForeignKey("job_posts.id"), index=True)
    candidate_user_id: Mapped[int] = mapped_column(ForeignKey("users.id"), index=True)
    reason: Mapped[str] = mapped_column(Text)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
