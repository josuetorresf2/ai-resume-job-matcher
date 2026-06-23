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
    location: str = ""
    work_mode: str = Field(default="remote", pattern="^(remote|hybrid|onsite)$")
    salary_range: str = ""
    experience_level: str = ""
    required_skills: str = ""
    nice_to_have_skills: str = ""
    description: str = Field(..., min_length=20)


class JobPostUpdate(BaseModel):
    title: Optional[str] = Field(default=None, min_length=2)
    company: Optional[str] = None
    location: Optional[str] = None
    work_mode: Optional[str] = Field(default=None, pattern="^(remote|hybrid|onsite)$")
    salary_range: Optional[str] = None
    experience_level: Optional[str] = None
    required_skills: Optional[str] = None
    nice_to_have_skills: Optional[str] = None
    description: Optional[str] = Field(default=None, min_length=20)


class JobPostResponse(BaseModel):
    id: int
    recruiter_user_id: int
    title: str
    company: str
    location: str
    work_mode: str
    salary_range: str
    experience_level: str
    required_skills: str
    nice_to_have_skills: str
    description: str
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class MatchCreate(BaseModel):
    resume_id: int
    job_post_id: int


class MatchReviewUpdate(BaseModel):
    recruiter_status: str = Field(..., pattern="^(Shortlisted|Maybe|Rejected)$")
    recruiter_notes: str = ""


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
    strongest_skills: list[str] = []
    improvements: list[str]
    summary: str
    resume_summary: str = ""
    fit_summary: str = ""
    concerns: list[str] = []
    interview_questions: list[str] = []
    recommendation: str = "Possible fit"
    recruiter_status: Optional[str] = None
    recruiter_notes: Optional[str] = None
    created_at: datetime
    source: str

    model_config = {"from_attributes": True}


class AnalysisDetail(AnalysisResult):
    resume_text: str
    job_description: str


class RankedCandidateMatch(AnalysisResult):
    candidate_name: str
    candidate_headline: str = ""
    resume_title: str = ""


class JobDashboardItem(JobPostResponse):
    candidates_matched: int
    average_match_score: int
    shortlisted_count: int


class RecruiterDashboardResponse(BaseModel):
    job_posts: list[JobDashboardItem]
    total_shortlisted: int
