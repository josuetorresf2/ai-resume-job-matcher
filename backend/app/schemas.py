from datetime import datetime
from typing import Optional
from pydantic import BaseModel, Field


class HealthResponse(BaseModel):
    status: str


class LoginRequest(BaseModel):
    name: str = Field(..., min_length=2)
    email: str = Field(..., min_length=5)
    role: str = Field(..., pattern="^(candidate|recruiter)$")


class UserResponse(BaseModel):
    id: int
    name: str
    email: str
    role: str

    model_config = {"from_attributes": True}


class CandidateProfileUpdate(BaseModel):
    headline: str = ""
    skills: str = ""
    bio: str = ""


class CandidateProfileResponse(CandidateProfileUpdate):
    id: int
    user_id: int

    model_config = {"from_attributes": True}


class RecruiterProfileUpdate(BaseModel):
    company: str = ""
    title: str = ""


class RecruiterProfileResponse(RecruiterProfileUpdate):
    id: int
    user_id: int

    model_config = {"from_attributes": True}


class ResumeCreate(BaseModel):
    title: str = "Primary resume"
    resume_text: str = Field(..., min_length=20)


class ResumeUpdate(BaseModel):
    title: Optional[str] = None
    resume_text: Optional[str] = Field(default=None, min_length=20)


class ResumeResponse(BaseModel):
    id: int
    candidate_user_id: int
    title: str
    resume_text: str
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class JobPostCreate(BaseModel):
    title: str = Field(..., min_length=2)
    company: str = ""
    description: str = Field(..., min_length=20)


class JobPostUpdate(BaseModel):
    title: Optional[str] = Field(default=None, min_length=2)
    company: Optional[str] = None
    description: Optional[str] = Field(default=None, min_length=20)


class JobPostResponse(BaseModel):
    id: int
    recruiter_user_id: int
    title: str
    company: str
    description: str
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class MatchCreate(BaseModel):
    resume_id: int
    job_post_id: int


class AnalysisCreate(BaseModel):
    resume_text: str = Field(..., min_length=20)
    job_description: str = Field(..., min_length=20)


class AnalysisResult(BaseModel):
    id: int
    resume_id: Optional[int] = None
    job_post_id: Optional[int] = None
    candidate_user_id: Optional[int] = None
    recruiter_user_id: Optional[int] = None
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
