from datetime import datetime
from typing import Optional
from pydantic import BaseModel, Field


class HealthResponse(BaseModel):
    status: str


class LoginRequest(BaseModel):
    name: str = Field(..., min_length=2)
    email: str = Field(..., min_length=5)
    phone_number: str = ""
    password: str = Field(..., min_length=8)
    role: str = Field(..., pattern="^(candidate|recruiter|admin)$")
    language: str = Field(default="en", pattern="^(en|es)$")
    verification_channel: str = Field(default="email", pattern="^(email|sms|whatsapp)$")


class UserResponse(BaseModel):
    id: int
    name: str
    email: str
    phone_number: str
    role: str
    language: str
    verification_status: str
    verification_channel: str
    low_bandwidth: int
    access_token: Optional[str] = None

    model_config = {"from_attributes": True}


class PreferenceUpdate(BaseModel):
    language: str = Field(..., pattern="^(en|es)$")
    low_bandwidth: int = 0


class VerificationRequest(BaseModel):
    channel: str = Field(..., pattern="^(email|sms|whatsapp)$")


class VerificationResponse(BaseModel):
    status: str
    message: str


class CandidateProfileUpdate(BaseModel):
    headline: str = ""
    skills: str = ""
    experience: str = ""
    education: str = ""
    portfolio_url: str = ""
    github_url: str = ""
    linkedin_url: str = ""
    visibility: str = Field(default="private", pattern="^(private|visible_to_verified_recruiters|public)$")
    bio: str = ""


class CandidateProfileResponse(CandidateProfileUpdate):
    id: int
    user_id: int

    model_config = {"from_attributes": True}


class RecruiterProfileUpdate(BaseModel):
    company: str = ""
    title: str = ""
    website: str = ""
    country: str = ""
    city: str = ""
    industry: str = ""
    company_size: str = ""
    description: str = ""
    contact_email: str = ""


class RecruiterProfileResponse(RecruiterProfileUpdate):
    id: int
    user_id: int
    company_status: str
    trust_score: int

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
    status: str
    spam_score: int
    spam_reasons: list[str] = []
    quality_score: int
    quality_tips: list[str] = []
    reports_count: int
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class JobPublishResponse(JobPostResponse):
    published: bool


class JobReportCreate(BaseModel):
    reason: str = Field(..., min_length=10)


class AdminCompanyReview(BaseModel):
    status: str = Field(..., pattern="^(verified|rejected)$")


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


class InterviewPracticeRequest(BaseModel):
    role: str = "Backend Engineer"
    resume_id: Optional[int] = None


class InterviewPracticeResponse(BaseModel):
    interview_score: int
    questions: list[str]
    strengths: list[str]
    needs_improvement: list[str]
    feedback: str


class CareerCoachRequest(BaseModel):
    resume_id: Optional[int] = None
    job_post_id: Optional[int] = None
    target_score: int = Field(default=85, ge=0, le=100)


class CareerCoachResponse(BaseModel):
    current_score: int
    target_score: int
    learn: list[str]
    estimated_effort: str
    roadmap: list[str]


class SalaryIntelligenceRequest(BaseModel):
    resume_id: int


class SalaryRange(BaseModel):
    market: str
    range: str


class SalaryIntelligenceResponse(BaseModel):
    ranges: list[SalaryRange]
    rationale: str


class GitHubAnalysisRequest(BaseModel):
    github_url: str = Field(..., min_length=5)


class GitHubAnalysisResponse(BaseModel):
    portfolio_score: int
    commit_frequency: str
    languages: list[str]
    projects: list[str]
    tests: str
    documentation: str
    recommendations: list[str]


class CandidateMetricsResponse(BaseModel):
    applications: int
    average_match_score: int
    profile_strength: int


class RecruiterMetricsResponse(BaseModel):
    candidates_applied: int
    average_match_score: int
    interviews_scheduled: int
