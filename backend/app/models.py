from datetime import datetime
from sqlalchemy import DateTime, ForeignKey, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from .database import Base


class User(Base):
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    name: Mapped[str] = mapped_column(String(120))
    email: Mapped[str] = mapped_column(String(255), unique=True, index=True)
    role: Mapped[str] = mapped_column(String(32), index=True)
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
    bio: Mapped[str] = mapped_column(Text, default="")

    user: Mapped[User] = relationship(back_populates="candidate")


class Recruiter(Base):
    __tablename__ = "recruiters"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"), unique=True, index=True)
    company: Mapped[str] = mapped_column(String(180), default="")
    title: Mapped[str] = mapped_column(String(120), default="")

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
    description: Mapped[str] = mapped_column(Text)
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
    improvements: Mapped[str] = mapped_column(Text, default="[]")
    summary: Mapped[str] = mapped_column(Text, default="")
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, index=True)
    source: Mapped[str] = mapped_column(String(32), default="heuristic")

    resume: Mapped[Resume] = relationship(back_populates="analyses")
    job_post: Mapped[JobPost] = relationship(back_populates="analyses")
