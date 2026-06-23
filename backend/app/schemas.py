from datetime import datetime
from pydantic import BaseModel, Field


class AnalysisCreate(BaseModel):
    resume_text: str = Field(..., min_length=20)
    job_description: str = Field(..., min_length=20)


class AnalysisResult(BaseModel):
    id: int
    match_score: int
    missing_skills: list[str]
    improvements: list[str]
    summary: str
    created_at: datetime
    source: str

    model_config = {"from_attributes": True}


class AnalysisDetail(AnalysisResult):
    resume_text: str
    job_description: str


class HealthResponse(BaseModel):
    status: str
