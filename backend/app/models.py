from datetime import datetime
from sqlalchemy import DateTime, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from .database import Base


class Analysis(Base):
    __tablename__ = "analyses"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    resume_text: Mapped[str] = mapped_column(Text)
    job_description: Mapped[str] = mapped_column(Text)
    match_score: Mapped[int] = mapped_column(Integer)
    missing_skills: Mapped[str] = mapped_column(Text, default="[]")
    improvements: Mapped[str] = mapped_column(Text, default="[]")
    summary: Mapped[str] = mapped_column(Text, default="")
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, index=True)
    source: Mapped[str] = mapped_column(String(32), default="heuristic")
