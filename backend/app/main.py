import json
import logging
import time
import uuid
from datetime import datetime
from typing import Optional
import httpx
from fastapi import Depends, FastAPI, Header, HTTPException, Request, UploadFile, File
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy import inspect, text
from sqlalchemy.orm import Session

from .analysis import ai_analysis, build_recruiter_summary
from .config import get_settings
from .database import Base, engine, get_db
from .models import Analysis, Candidate, JobPost, JobReport, Recruiter, Resume, User
from .job_connectors import MockJobConnector, RemotiveJobConnector
from .job_imports import import_jobs_from_connector
from .job_normalization import apply_normalized_job_fields
from .resume_parser import extract_pdf_text, extract_text_file
from .security import (
    company_email_matches_website,
    create_access_token,
    hash_password,
    is_valid_email,
    is_valid_phone_number,
    is_valid_website,
    password_hash_needs_upgrade,
    verify_access_token,
    verify_password,
)
from .schemas import (
    AdminCompanyReview,
    AnalysisCreate,
    AnalysisDetail,
    AnalysisResult,
    CandidateProfileResponse,
    CandidateProfileUpdate,
    CandidateMetricsResponse,
    CareerCoachRequest,
    CareerCoachResponse,
    GitHubAnalysisRequest,
    GitHubAnalysisResponse,
    HealthResponse,
    InterviewPracticeRequest,
    InterviewPracticeResponse,
    JobPostCreate,
    JobPublishResponse,
    JobReportCreate,
    JobPostResponse,
    JobPostUpdate,
    JobDashboardItem,
    JobImportRequest,
    JobImportResponse,
    LoginRequest,
    MatchCreate,
    MatchReviewUpdate,
    PreferenceUpdate,
    RankedCandidateMatch,
    RecruiterDashboardResponse,
    RecruiterMetricsResponse,
    RecruiterProfileResponse,
    RecruiterProfileUpdate,
    ResumeCreate,
    ResumeResponse,
    ResumeUpdate,
    SalaryIntelligenceRequest,
    SalaryIntelligenceResponse,
    SalaryRange,
    TalentPoolCandidate,
    TalentPoolResponse,
    UserResponse,
    VerificationConfirmRequest,
    VerificationRequest,
    VerificationResponse,
)
from .trust import assess_job_quality, assess_job_safety, candidate_completeness_score, recruiter_trust_score
from .analysis import extract_skills
from .verification import send_verification_message


settings = get_settings()
logger = logging.getLogger("fairhire.api")


def initialize_database() -> None:
    inspector = inspect(engine)
    if "analyses" in inspector.get_table_names():
        columns = {column["name"] for column in inspector.get_columns("analyses")}
        if "resume_id" not in columns or "job_post_id" not in columns:
            Analysis.__table__.drop(engine)
    Base.metadata.create_all(bind=engine)
    with engine.begin() as connection:
        table_names = inspect(engine).get_table_names()
        if "job_posts" in table_names:
            columns = {column["name"] for column in inspect(engine).get_columns("job_posts")}
            job_columns = {
                "location": "TEXT DEFAULT ''",
                "work_mode": "TEXT DEFAULT 'remote'",
                "salary_range": "TEXT DEFAULT ''",
                "experience_level": "TEXT DEFAULT ''",
                "required_skills": "TEXT DEFAULT ''",
                "nice_to_have_skills": "TEXT DEFAULT ''",
                "source_type": "TEXT DEFAULT 'internal'",
                "source_provider": "TEXT DEFAULT 'fairhire'",
                "external_id": "TEXT DEFAULT ''",
                "external_url": "TEXT DEFAULT ''",
                "canonical_title": "TEXT DEFAULT ''",
                "canonical_company": "TEXT DEFAULT ''",
                "canonical_location": "TEXT DEFAULT ''",
                "canonical_remote": "INTEGER DEFAULT 1",
                "canonical_salary_min": "INTEGER DEFAULT 0",
                "canonical_salary_max": "INTEGER DEFAULT 0",
                "canonical_currency": "TEXT DEFAULT 'USD'",
                "canonical_skills": "TEXT DEFAULT '[]'",
                "status": "TEXT DEFAULT 'draft'",
                "spam_score": "INTEGER DEFAULT 0",
                "spam_reasons": "TEXT DEFAULT '[]'",
                "quality_score": "INTEGER DEFAULT 0",
                "quality_tips": "TEXT DEFAULT '[]'",
                "reports_count": "INTEGER DEFAULT 0",
            }
            for column_name, ddl in job_columns.items():
                if column_name not in columns:
                    connection.execute(text(f"ALTER TABLE job_posts ADD COLUMN {column_name} {ddl}"))
        if "analyses" in table_names:
            columns = {column["name"] for column in inspect(engine).get_columns("analyses")}
            analysis_columns = {
                "strongest_skills": "TEXT DEFAULT '[]'",
                "resume_summary": "TEXT DEFAULT ''",
                "fit_summary": "TEXT DEFAULT ''",
                "concerns": "TEXT DEFAULT '[]'",
                "interview_questions": "TEXT DEFAULT '[]'",
                "recommendation": "TEXT DEFAULT 'Possible fit'",
                "recruiter_status": "TEXT DEFAULT 'Maybe'",
                "recruiter_notes": "TEXT DEFAULT ''",
                "idempotency_key": "TEXT DEFAULT ''",
                "idempotency_user_id": "INTEGER DEFAULT 0",
            }
            for column_name, ddl in analysis_columns.items():
                if column_name not in columns:
                    connection.execute(text(f"ALTER TABLE analyses ADD COLUMN {column_name} {ddl}"))
        if "users" in table_names:
            columns = {column["name"] for column in inspect(engine).get_columns("users")}
            user_columns = {
                "phone_number": "TEXT DEFAULT ''",
                "password_hash": "TEXT DEFAULT ''",
                "language": "TEXT DEFAULT 'en'",
                "verification_status": "TEXT DEFAULT 'unverified'",
                "verification_channel": "TEXT DEFAULT 'email'",
                "low_bandwidth": "INTEGER DEFAULT 0",
            }
            for column_name, ddl in user_columns.items():
                if column_name not in columns:
                    connection.execute(text(f"ALTER TABLE users ADD COLUMN {column_name} {ddl}"))
        if "candidates" in table_names:
            columns = {column["name"] for column in inspect(engine).get_columns("candidates")}
            candidate_columns = {
                "experience": "TEXT DEFAULT ''",
                "education": "TEXT DEFAULT ''",
                "portfolio_url": "TEXT DEFAULT ''",
                "github_url": "TEXT DEFAULT ''",
                "linkedin_url": "TEXT DEFAULT ''",
                "project_demo_urls": "TEXT DEFAULT ''",
                "visibility": "TEXT DEFAULT 'private'",
                "completeness_score": "INTEGER DEFAULT 0",
            }
            for column_name, ddl in candidate_columns.items():
                if column_name not in columns:
                    connection.execute(text(f"ALTER TABLE candidates ADD COLUMN {column_name} {ddl}"))
        if "recruiters" in table_names:
            columns = {column["name"] for column in inspect(engine).get_columns("recruiters")}
            recruiter_columns = {
                "website": "TEXT DEFAULT ''",
                "country": "TEXT DEFAULT ''",
                "city": "TEXT DEFAULT ''",
                "industry": "TEXT DEFAULT ''",
                "company_size": "TEXT DEFAULT ''",
                "description": "TEXT DEFAULT ''",
                "contact_email": "TEXT DEFAULT ''",
                "company_status": "TEXT DEFAULT 'pending_review'",
                "trust_score": "INTEGER DEFAULT 0",
            }
            for column_name, ddl in recruiter_columns.items():
                if column_name not in columns:
                    connection.execute(text(f"ALTER TABLE recruiters ADD COLUMN {column_name} {ddl}"))


initialize_database()

app = FastAPI(title=settings.app_name)
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origin_list,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.middleware("http")
async def correlation_id_middleware(request: Request, call_next):
    correlation_id = request.headers.get("X-Correlation-ID") or str(uuid.uuid4())
    request.state.correlation_id = correlation_id
    started_at = time.perf_counter()
    response = await call_next(request)
    duration_ms = round((time.perf_counter() - started_at) * 1000, 2)
    response.headers["X-Correlation-ID"] = correlation_id
    logger.info(
        json.dumps(
            {
                "event": "http_request",
                "correlation_id": correlation_id,
                "method": request.method,
                "path": request.url.path,
                "status_code": response.status_code,
                "duration_ms": duration_ms,
            },
            separators=(",", ":"),
        )
    )
    return response


def forbidden(message: str) -> HTTPException:
    return HTTPException(status_code=403, detail=message)


def get_current_user(
    authorization: Optional[str] = Header(default=None, alias="Authorization"),
    x_user_id: Optional[int] = Header(default=None, alias="X-User-Id"),
    db: Session = Depends(get_db),
) -> User:
    token_user_id = None
    if authorization and authorization.startswith("Bearer "):
        token_user_id = verify_access_token(authorization.removeprefix("Bearer ").strip(), settings.auth_secret_key)
        if token_user_id is None:
            raise HTTPException(status_code=401, detail="Invalid or expired access token.")

    if token_user_id is not None:
        user_id = token_user_id
    elif x_user_id is not None and settings.auth_allow_test_header:
        user_id = x_user_id
    elif x_user_id is not None:
        raise HTTPException(status_code=401, detail="X-User-Id test sessions are disabled. Use a bearer token.")
    else:
        user_id = None
    if user_id is None:
        raise HTTPException(status_code=401, detail="Missing bearer token.")

    user = db.get(User, user_id)
    if user is None:
        raise HTTPException(status_code=401, detail="Invalid mock session user.")
    return user


def require_role(user: User, role: str) -> None:
    if user.role != role:
        raise forbidden(f"Only {role}s can perform this action.")


def require_admin(user: User) -> None:
    if user.role != "admin":
        raise forbidden("Only admins can perform this action.")


def read_json_list(value: str) -> list[str]:
    try:
        data = json.loads(value or "[]")
        return data if isinstance(data, list) else []
    except json.JSONDecodeError:
        return []


def job_analysis_text(job_post: JobPost) -> str:
    return "\n".join(
        [
            job_post.title,
            job_post.company,
            job_post.location,
            job_post.work_mode,
            job_post.salary_range,
            job_post.experience_level,
            "Required skills: " + job_post.required_skills,
            "Nice-to-have skills: " + job_post.nice_to_have_skills,
            job_post.description,
        ]
    )


def company_profile_complete(profile: Recruiter) -> bool:
    return all(
        [
            profile.company.strip(),
            profile.website.strip(),
            profile.country.strip(),
            profile.city.strip(),
            profile.industry.strip(),
            profile.company_size.strip(),
            profile.description.strip(),
            profile.contact_email.strip(),
        ]
    )


def update_candidate_score(db: Session, user: User) -> None:
    profile = db.query(Candidate).filter(Candidate.user_id == user.id).one()
    has_resume = db.query(Resume).filter(Resume.candidate_user_id == user.id).first() is not None
    profile.completeness_score = candidate_completeness_score(
        has_resume,
        profile.skills,
        profile.experience,
        profile.education,
        [profile.portfolio_url, profile.github_url, profile.linkedin_url, profile.project_demo_urls],
        user.language,
    )


def update_recruiter_score(db: Session, user: User) -> None:
    profile = db.query(Recruiter).filter(Recruiter.user_id == user.id).one()
    low_spam_jobs = not db.query(JobPost).filter(JobPost.recruiter_user_id == user.id, JobPost.spam_score >= 70).first()
    profile.trust_score = recruiter_trust_score(
        user.verification_status == "verified",
        profile.company_status == "verified",
        company_profile_complete(profile),
        low_spam_jobs,
    )


def assess_and_apply_job_scores(job: JobPost, recruiter: Recruiter) -> None:
    company_complete = company_profile_complete(recruiter)
    spam_score, spam_reasons = assess_job_safety(job.description, company_complete)
    quality_score, quality_tips = assess_job_quality(
        job.title,
        job.description,
        job.required_skills,
        job.salary_range,
        company_complete,
        spam_score,
    )
    job.spam_score = spam_score
    job.spam_reasons = json.dumps(spam_reasons)
    job.quality_score = quality_score
    job.quality_tips = json.dumps(quality_tips)


def candidate_resume_for_user(db: Session, current_user: User, resume_id: Optional[int]) -> Optional[Resume]:
    query = db.query(Resume).filter(Resume.candidate_user_id == current_user.id)
    if resume_id is not None:
        row = query.filter(Resume.id == resume_id).one_or_none()
        if row is None:
            raise HTTPException(status_code=404, detail="Resume not found.")
        return row
    return query.order_by(Resume.updated_at.desc()).first()


def candidate_resume_text_for_tools(db: Session, current_user: User, resume_id: Optional[int], resume_text: str = "") -> str:
    if resume_text.strip():
        return resume_text.strip()
    resume = candidate_resume_for_user(db, current_user, resume_id)
    return resume.resume_text if resume else ""


def localized(language: str, english: str, spanish: str) -> str:
    return spanish if language == "es" else english


def career_skills_to_learn(resume_text: str, job_text: str = "") -> list[str]:
    resume_skills = set(extract_skills(resume_text))
    target_skills = set(extract_skills(job_text)) if job_text else {"docker", "postgresql", "ci/cd", "aws", "github actions"}
    missing = sorted(target_skills - resume_skills)
    priority = ["Docker", "PostgreSQL", "CI/CD", "AWS", "GitHub Actions", "System design", "API security"]
    found = [skill for skill in priority if skill.lower() in {item.lower() for item in missing}]
    return found or ["Docker", "PostgreSQL", "CI/CD"]


def serialize_analysis(row: Analysis, include_private: bool = False) -> AnalysisResult:
    return AnalysisResult(
        id=row.id,
        resume_id=row.resume_id,
        job_post_id=row.job_post_id,
        candidate_user_id=row.candidate_user_id,
        recruiter_user_id=row.recruiter_user_id,
        match_score=row.match_score,
        missing_skills=read_json_list(row.missing_skills),
        strongest_skills=read_json_list(row.strongest_skills),
        improvements=read_json_list(row.improvements),
        summary=row.summary,
        resume_summary=row.resume_summary,
        fit_summary=row.fit_summary,
        concerns=read_json_list(row.concerns),
        interview_questions=read_json_list(row.interview_questions),
        recommendation=row.recommendation,
        recruiter_status=row.recruiter_status if include_private else None,
        recruiter_notes=row.recruiter_notes if include_private else None,
        created_at=row.created_at,
        source=row.source,
    )


def serialize_job(job: JobPost) -> JobPostResponse:
    return JobPostResponse(
        id=job.id,
        recruiter_user_id=job.recruiter_user_id,
        title=job.title,
        company=job.company,
        location=job.location,
        work_mode=job.work_mode,
        salary_range=job.salary_range,
        experience_level=job.experience_level,
        required_skills=job.required_skills,
        nice_to_have_skills=job.nice_to_have_skills,
        source_type=job.source_type,
        source_provider=job.source_provider,
        external_id=job.external_id,
        external_url=job.external_url,
        canonical_title=job.canonical_title,
        canonical_company=job.canonical_company,
        canonical_location=job.canonical_location,
        canonical_remote=job.canonical_remote,
        canonical_salary_min=job.canonical_salary_min,
        canonical_salary_max=job.canonical_salary_max,
        canonical_currency=job.canonical_currency,
        canonical_skills=read_json_list(job.canonical_skills),
        description=job.description,
        status=job.status,
        spam_score=job.spam_score,
        spam_reasons=read_json_list(job.spam_reasons),
        quality_score=job.quality_score,
        quality_tips=read_json_list(job.quality_tips),
        reports_count=job.reports_count,
        created_at=job.created_at,
        updated_at=job.updated_at,
    )


def serialize_analysis_detail(row: Analysis, include_private: bool = False) -> AnalysisDetail:
    result = serialize_analysis(row, include_private=include_private)
    return AnalysisDetail(
        **result.model_dump(),
        resume_text=row.resume.resume_text,
        job_description=row.job_post.description,
    )


def serialize_ranked_match(row: Analysis) -> RankedCandidateMatch:
    result = serialize_analysis(row, include_private=True)
    profile = row.resume.candidate_user.candidate
    candidate_name = row.resume.candidate_user.name
    if profile and profile.visibility == "private" and row.recruiter_status != "Shortlisted":
        candidate_name = "Private candidate"
    return RankedCandidateMatch(
        **result.model_dump(),
        candidate_name=candidate_name,
        candidate_headline=profile.headline if profile else "",
        resume_title=row.resume.title,
    )


@app.get("/health", response_model=HealthResponse)
def health() -> HealthResponse:
    return HealthResponse(status="ok")


@app.post("/auth/mock-login", response_model=UserResponse)
def mock_login(payload: LoginRequest, db: Session = Depends(get_db)) -> UserResponse:
    normalized_email = payload.email.strip().lower()
    if not is_valid_email(normalized_email):
        raise HTTPException(status_code=400, detail="Use a valid non-temporary email address.")
    if payload.verification_channel in {"sms", "whatsapp"} and not is_valid_phone_number(payload.phone_number):
        raise HTTPException(status_code=400, detail="SMS and WhatsApp verification require a real E.164 phone number, for example +593987654321.")
    user = db.query(User).filter(User.email == normalized_email).one_or_none()
    if user is None:
        user = User(
            name=payload.name.strip(),
            email=normalized_email,
            phone_number=payload.phone_number.strip(),
            password_hash=hash_password(payload.password),
            role=payload.role,
            language=payload.language,
            verification_channel=payload.verification_channel,
        )
        db.add(user)
        db.commit()
        db.refresh(user)
    elif user.role != payload.role:
        raise HTTPException(status_code=400, detail="This email is already registered with a different role.")
    elif user.password_hash and not verify_password(payload.password, user.password_hash):
        raise HTTPException(status_code=401, detail="Incorrect password.")
    else:
        if user.password_hash and password_hash_needs_upgrade(user.password_hash):
            user.password_hash = hash_password(payload.password)
        if payload.name.strip():
            user.name = payload.name.strip()
        if payload.phone_number.strip():
            user.phone_number = payload.phone_number.strip()
        user.language = payload.language
        user.verification_channel = payload.verification_channel

    if user.role == "candidate" and user.candidate is None:
        db.add(Candidate(user_id=user.id))
    if user.role == "recruiter" and user.recruiter is None:
        db.add(Recruiter(user_id=user.id))
    db.commit()
    db.refresh(user)
    response = UserResponse.model_validate(user)
    response.access_token = create_access_token(user.id, settings.auth_secret_key)
    return response


@app.put("/me/preferences", response_model=UserResponse)
def update_preferences(
    payload: PreferenceUpdate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> UserResponse:
    current_user.language = payload.language
    current_user.low_bandwidth = payload.low_bandwidth
    db.commit()
    db.refresh(current_user)
    return current_user


@app.get("/talent-pool", response_model=TalentPoolResponse)
def list_talent_pool(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> TalentPoolResponse:
    if current_user.role not in {"recruiter", "admin"}:
        raise forbidden("Only recruiters and admins can view the talent pool.")
    rows = db.query(Candidate).join(User, Candidate.user_id == User.id).all()
    candidates: list[TalentPoolCandidate] = []
    for profile in rows:
        user = profile.user
        if current_user.role == "recruiter":
            recruiter = db.query(Recruiter).filter(Recruiter.user_id == current_user.id).one_or_none()
            recruiter_verified = current_user.verification_status == "verified" and recruiter is not None and recruiter.company_status == "verified"
            if profile.visibility == "private":
                continue
            if profile.visibility == "visible_to_verified_recruiters" and not recruiter_verified:
                continue
        candidates.append(
            TalentPoolCandidate(
                user_id=user.id,
                name=user.name,
                email=user.email,
                phone_number=user.phone_number,
                language=user.language,
                verification_status=user.verification_status,
                headline=profile.headline,
                skills=profile.skills,
                experience=profile.experience,
                education=profile.education,
                portfolio_url=profile.portfolio_url,
                github_url=profile.github_url,
                linkedin_url=profile.linkedin_url,
                project_demo_urls=profile.project_demo_urls,
                visibility=profile.visibility,
                completeness_score=profile.completeness_score,
                bio=profile.bio,
            )
        )
    return TalentPoolResponse(candidates=candidates)


@app.post("/auth/request-verification", response_model=VerificationResponse)
def request_verification(
    payload: VerificationRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> VerificationResponse:
    if payload.channel in {"sms", "whatsapp"} and not is_valid_phone_number(current_user.phone_number):
        raise HTTPException(status_code=400, detail="Add a real E.164 phone number before requesting SMS or WhatsApp verification.")
    current_user.verification_channel = payload.channel
    db.commit()
    status = send_verification_message(settings, payload.channel, current_user.phone_number, "123456")
    message = (
        f"Verification sent by {payload.channel}."
        if status == "sent"
        else f"Demo verification prepared for {payload.channel}. Use code 123456. Configure Twilio env vars to send real messages."
    )
    return VerificationResponse(status=status, message=message, demo_code=None if status == "sent" else "123456")


@app.post("/auth/verify-code", response_model=UserResponse)
def verify_code(
    payload: VerificationConfirmRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> UserResponse:
    if payload.code.strip() != "123456":
        raise HTTPException(status_code=400, detail="Invalid verification code.")
    current_user.verification_status = "verified"
    if current_user.role == "recruiter":
        update_recruiter_score(db, current_user)
    db.commit()
    db.refresh(current_user)
    response = UserResponse.model_validate(current_user)
    response.access_token = create_access_token(current_user.id, settings.auth_secret_key)
    return response


@app.post("/auth/verify-placeholder", response_model=UserResponse)
def verify_placeholder(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> UserResponse:
    current_user.verification_status = "verified"
    if current_user.role == "recruiter":
        update_recruiter_score(db, current_user)
    db.commit()
    db.refresh(current_user)
    return current_user


@app.get("/me", response_model=UserResponse)
def get_me(current_user: User = Depends(get_current_user)) -> UserResponse:
    return current_user


@app.get("/candidate/profile", response_model=CandidateProfileResponse)
def get_candidate_profile(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> CandidateProfileResponse:
    require_role(current_user, "candidate")
    profile = db.query(Candidate).filter(Candidate.user_id == current_user.id).one()
    return profile


@app.put("/candidate/profile", response_model=CandidateProfileResponse)
def update_candidate_profile(
    payload: CandidateProfileUpdate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> CandidateProfileResponse:
    require_role(current_user, "candidate")
    profile = db.query(Candidate).filter(Candidate.user_id == current_user.id).one()
    profile.headline = payload.headline
    profile.skills = payload.skills
    profile.experience = payload.experience
    profile.education = payload.education
    profile.portfolio_url = payload.portfolio_url
    profile.github_url = payload.github_url
    profile.linkedin_url = payload.linkedin_url
    profile.project_demo_urls = payload.project_demo_urls
    profile.visibility = payload.visibility
    profile.bio = payload.bio
    update_candidate_score(db, current_user)
    db.commit()
    db.refresh(profile)
    return profile


@app.get("/recruiter/profile", response_model=RecruiterProfileResponse)
def get_recruiter_profile(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> RecruiterProfileResponse:
    require_role(current_user, "recruiter")
    profile = db.query(Recruiter).filter(Recruiter.user_id == current_user.id).one()
    return profile


@app.put("/recruiter/profile", response_model=RecruiterProfileResponse)
def update_recruiter_profile(
    payload: RecruiterProfileUpdate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> RecruiterProfileResponse:
    require_role(current_user, "recruiter")
    profile = db.query(Recruiter).filter(Recruiter.user_id == current_user.id).one()
    profile.company = payload.company
    profile.title = payload.title
    profile.website = payload.website
    profile.country = payload.country
    profile.city = payload.city
    profile.industry = payload.industry
    profile.company_size = payload.company_size
    profile.description = payload.description
    profile.contact_email = payload.contact_email
    if profile.website and not is_valid_website(profile.website):
        raise HTTPException(status_code=400, detail="Company website must be a valid http(s) URL.")
    if profile.contact_email and not is_valid_email(profile.contact_email):
        raise HTTPException(status_code=400, detail="Company contact email must be valid.")
    if profile.website and profile.contact_email and not company_email_matches_website(profile.contact_email, profile.website):
        profile.company_status = "pending_review"
    update_recruiter_score(db, current_user)
    db.commit()
    db.refresh(profile)
    return profile


@app.post("/resumes", response_model=ResumeResponse)
def create_resume(
    payload: ResumeCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> ResumeResponse:
    require_role(current_user, "candidate")
    row = Resume(candidate_user_id=current_user.id, title=payload.title, resume_text=payload.resume_text)
    db.add(row)
    update_candidate_score(db, current_user)
    db.commit()
    db.refresh(row)
    return row


@app.get("/resumes", response_model=list[ResumeResponse])
def list_my_resumes(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> list[ResumeResponse]:
    require_role(current_user, "candidate")
    return db.query(Resume).filter(Resume.candidate_user_id == current_user.id).order_by(Resume.updated_at.desc()).all()


@app.put("/resumes/{resume_id}", response_model=ResumeResponse)
def update_resume(
    resume_id: int,
    payload: ResumeUpdate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> ResumeResponse:
    require_role(current_user, "candidate")
    row = db.get(Resume, resume_id)
    if row is None:
        raise HTTPException(status_code=404, detail="Resume not found.")
    if row.candidate_user_id != current_user.id:
        raise forbidden("Candidates can only edit their own resumes.")
    if payload.title is not None:
        row.title = payload.title
    if payload.resume_text is not None:
        row.resume_text = payload.resume_text
    update_candidate_score(db, current_user)
    db.commit()
    db.refresh(row)
    return row


@app.get("/candidate/metrics", response_model=CandidateMetricsResponse)
def get_candidate_metrics(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> CandidateMetricsResponse:
    require_role(current_user, "candidate")
    profile = db.query(Candidate).filter(Candidate.user_id == current_user.id).one()
    rows = db.query(Analysis).filter(Analysis.candidate_user_id == current_user.id).all()
    average = round(sum(row.match_score for row in rows) / len(rows)) if rows else 0
    return CandidateMetricsResponse(
        applications=len(rows),
        average_match_score=average,
        profile_strength=profile.completeness_score,
    )


@app.post("/candidate/interview-practice", response_model=InterviewPracticeResponse)
def create_interview_practice(
    payload: InterviewPracticeRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> InterviewPracticeResponse:
    require_role(current_user, "candidate")
    resume_text = candidate_resume_text_for_tools(db, current_user, payload.resume_id, payload.resume_text)
    skills = set(extract_skills(resume_text))
    score = 84 if {"python", "fastapi", "sql"} & skills else 72
    if current_user.language == "es":
        return InterviewPracticeResponse(
            interview_score=score,
            questions=[
                "Explica como disenarias una API REST segura para un servicio de pagos.",
                "Que diferencias practicas hay entre una cola, un cache y una base de datos?",
                "Describe un proyecto donde tuviste que comunicar un tradeoff tecnico.",
                "Como depurarias una API de Python lenta en produccion?",
                "Que controles agregarias para autenticacion, autorizacion y rate limiting?",
            ],
            strengths=["Comunicacion", "Profundidad tecnica"],
            needs_improvement=["Respuestas concisas", "Conceptos de seguridad de APIs"],
            feedback="Practica respuestas de 60 a 90 segundos con ejemplos medibles y una estructura problema, accion, resultado.",
        )
    return InterviewPracticeResponse(
        interview_score=score,
        questions=[
            "Explain how you would design a secure REST API for a payments service.",
            "What are the practical differences between a queue, a cache, and a database?",
            "Describe a project where you had to communicate a technical tradeoff.",
            "How would you debug a slow Python API in production?",
            "What controls would you add for authentication, authorization, and rate limiting?",
        ],
        strengths=["Communication", "Technical depth"],
        needs_improvement=["Concise answers", "API security concepts"],
        feedback="Practice 60 to 90 second answers with measurable examples and a problem, action, result structure.",
    )


@app.post("/candidate/career-coach", response_model=CareerCoachResponse)
def create_career_coach_plan(
    payload: CareerCoachRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> CareerCoachResponse:
    require_role(current_user, "candidate")
    resume_text = candidate_resume_text_for_tools(db, current_user, payload.resume_id, payload.resume_text)
    if not resume_text:
        raise HTTPException(status_code=404, detail="Create or upload a resume first.")
    job_text = ""
    current_score = 62
    if payload.job_post_id is not None:
        job = db.get(JobPost, payload.job_post_id)
        if job is None:
            raise HTTPException(status_code=404, detail="Job post not found.")
        job_text = job_analysis_text(job)
        current_score = ai_analysis(settings, resume_text, job_text, language=current_user.language)["match_score"]
    learn = career_skills_to_learn(resume_text, job_text)
    estimated_effort = localized(current_user.language, "4 weeks", "4 semanas")
    if current_user.language == "es":
        roadmap = [
            f"Semana 1: crea un proyecto pequeno usando {learn[0]}.",
            f"Semana 2: agrega {learn[1] if len(learn) > 1 else 'pruebas'} con ejemplos en tu README.",
            f"Semana 3: practica {learn[2] if len(learn) > 2 else 'CI/CD'} y despliegue.",
            "Semana 4: actualiza tu resume con resultados medibles y vuelve a correr el matcher.",
        ]
    else:
        roadmap = [
            f"Week 1: build a small project using {learn[0]}.",
            f"Week 2: add {learn[1] if len(learn) > 1 else 'tests'} with examples in your README.",
            f"Week 3: practice {learn[2] if len(learn) > 2 else 'CI/CD'} and deployment.",
            "Week 4: update your resume with measurable outcomes and run the matcher again.",
        ]
    return CareerCoachResponse(
        current_score=current_score,
        target_score=payload.target_score,
        learn=learn,
        estimated_effort=estimated_effort,
        roadmap=roadmap,
    )


@app.post("/candidate/salary-intelligence", response_model=SalaryIntelligenceResponse)
def create_salary_intelligence(
    payload: SalaryIntelligenceRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> SalaryIntelligenceResponse:
    require_role(current_user, "candidate")
    resume_text = candidate_resume_text_for_tools(db, current_user, payload.resume_id, payload.resume_text)
    if not resume_text:
        raise HTTPException(status_code=404, detail="Resume not found.")
    skills = set(extract_skills(resume_text))
    senior_signal = len(skills & {"aws", "docker", "kubernetes", "terraform", "postgresql", "ci/cd"}) >= 3
    ranges = [
        SalaryRange(market="Ecuador", range="$1200-$1800" if not senior_signal else "$1800-$2600"),
        SalaryRange(market="Remote LATAM", range="$1800-$3000" if not senior_signal else "$3000-$4500"),
        SalaryRange(market="US Contractor", range="$3000-$5000" if not senior_signal else "$5000-$7500"),
    ]
    rationale = localized(
        current_user.language,
        "Estimate based on resume skills, backend scope, and market type. Validate with live market data before negotiation.",
        "Estimacion basada en habilidades del resume, alcance backend y tipo de mercado. Valida con datos actuales antes de negociar.",
    )
    return SalaryIntelligenceResponse(ranges=ranges, rationale=rationale)


@app.post("/candidate/github-analysis", response_model=GitHubAnalysisResponse)
def create_github_analysis(
    payload: GitHubAnalysisRequest,
    current_user: User = Depends(get_current_user),
) -> GitHubAnalysisResponse:
    require_role(current_user, "candidate")
    if "github.com" not in payload.github_url.lower():
        raise HTTPException(status_code=400, detail="Use a valid GitHub profile or repository URL.")
    if current_user.language == "es":
        return GitHubAnalysisResponse(
            portfolio_score=88,
            commit_frequency="Actividad constante simulada a partir del perfil conectado.",
            languages=["Python", "TypeScript", "SQL"],
            projects=["API backend", "Dashboard full-stack", "Automatizacion"],
            tests="Buenas senales: incluye pruebas o estructura preparada para pruebas.",
            documentation="README visible, pero puede mejorar con capturas, arquitectura y decisiones tecnicas.",
            recommendations=[
                "Agrega badges de CI y cobertura.",
                "Incluye capturas o GIFs cortos en los proyectos principales.",
                "Documenta decisiones de arquitectura y tradeoffs.",
            ],
        )
    return GitHubAnalysisResponse(
        portfolio_score=88,
        commit_frequency="Consistent simulated activity from the connected profile.",
        languages=["Python", "TypeScript", "SQL"],
        projects=["Backend API", "Full-stack dashboard", "Automation"],
        tests="Strong signal: includes tests or test-ready structure.",
        documentation="README is visible, but can improve with screenshots, architecture, and technical decisions.",
        recommendations=[
            "Add CI and coverage badges.",
            "Include screenshots or short GIFs for flagship projects.",
            "Document architecture decisions and tradeoffs.",
        ],
    )


@app.post("/job-posts", response_model=JobPostResponse)
def create_job_post(
    payload: JobPostCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> JobPostResponse:
    require_role(current_user, "recruiter")
    recruiter = db.query(Recruiter).filter(Recruiter.user_id == current_user.id).one()
    row = JobPost(
        recruiter_user_id=current_user.id,
        title=payload.title,
        company=payload.company,
        location=payload.location,
        work_mode=payload.work_mode,
        salary_range=payload.salary_range,
        experience_level=payload.experience_level,
        required_skills=payload.required_skills,
        nice_to_have_skills=payload.nice_to_have_skills,
        description=payload.description,
    )
    apply_normalized_job_fields(row)
    assess_and_apply_job_scores(row, recruiter)
    db.add(row)
    update_recruiter_score(db, current_user)
    db.commit()
    db.refresh(row)
    return serialize_job(row)


@app.get("/job-posts", response_model=list[JobPostResponse])
def list_job_posts(db: Session = Depends(get_db)) -> list[JobPostResponse]:
    rows = db.query(JobPost).filter(JobPost.status == "published").order_by(JobPost.updated_at.desc()).all()
    return [serialize_job(row) for row in rows]


@app.get("/job-posts/mine", response_model=list[JobPostResponse])
def list_my_job_posts(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> list[JobPostResponse]:
    require_role(current_user, "recruiter")
    rows = db.query(JobPost).filter(JobPost.recruiter_user_id == current_user.id).order_by(JobPost.updated_at.desc()).all()
    return [serialize_job(row) for row in rows]


@app.put("/job-posts/{job_post_id}", response_model=JobPostResponse)
def update_job_post(
    job_post_id: int,
    payload: JobPostUpdate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> JobPostResponse:
    require_role(current_user, "recruiter")
    row = db.get(JobPost, job_post_id)
    if row is None:
        raise HTTPException(status_code=404, detail="Job post not found.")
    if row.recruiter_user_id != current_user.id:
        raise forbidden("Recruiters can only edit their own job posts.")
    if payload.title is not None:
        row.title = payload.title
    if payload.company is not None:
        row.company = payload.company
    if payload.location is not None:
        row.location = payload.location
    if payload.work_mode is not None:
        row.work_mode = payload.work_mode
    if payload.salary_range is not None:
        row.salary_range = payload.salary_range
    if payload.experience_level is not None:
        row.experience_level = payload.experience_level
    if payload.required_skills is not None:
        row.required_skills = payload.required_skills
    if payload.nice_to_have_skills is not None:
        row.nice_to_have_skills = payload.nice_to_have_skills
    if payload.description is not None:
        row.description = payload.description
    apply_normalized_job_fields(row)
    recruiter = db.query(Recruiter).filter(Recruiter.user_id == current_user.id).one()
    assess_and_apply_job_scores(row, recruiter)
    update_recruiter_score(db, current_user)
    db.commit()
    db.refresh(row)
    return serialize_job(row)


@app.post("/job-posts/{job_post_id}/publish", response_model=JobPublishResponse)
def publish_job_post(
    job_post_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> JobPublishResponse:
    require_role(current_user, "recruiter")
    row = db.get(JobPost, job_post_id)
    if row is None:
        raise HTTPException(status_code=404, detail="Job post not found.")
    if row.recruiter_user_id != current_user.id:
        raise forbidden("Recruiters can only publish their own job posts.")
    recruiter = db.query(Recruiter).filter(Recruiter.user_id == current_user.id).one()
    assess_and_apply_job_scores(row, recruiter)
    if current_user.verification_status != "verified":
        raise forbidden("Verify your account before publishing jobs.")
    if recruiter.company_status != "verified":
        raise forbidden("Company profile must be verified before publishing public jobs.")
    if row.spam_score >= 70:
        raise HTTPException(
            status_code=400,
            detail={"message": "This job looks unsafe and cannot be published yet.", "fixes": read_json_list(row.spam_reasons)},
        )
    row.status = "published"
    update_recruiter_score(db, current_user)
    db.commit()
    db.refresh(row)
    return JobPublishResponse(**serialize_job(row).model_dump(), published=True)


@app.delete("/job-posts/{job_post_id}")
def delete_job_post(
    job_post_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> dict[str, str]:
    require_role(current_user, "recruiter")
    row = db.get(JobPost, job_post_id)
    if row is None:
        raise HTTPException(status_code=404, detail="Job post not found.")
    if row.recruiter_user_id != current_user.id:
        raise forbidden("Recruiters can only delete their own job posts.")
    db.query(Analysis).filter(Analysis.job_post_id == row.id).delete()
    db.delete(row)
    db.commit()
    return {"status": "deleted"}


@app.get("/recruiter/dashboard", response_model=RecruiterDashboardResponse)
def get_recruiter_dashboard(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> RecruiterDashboardResponse:
    require_role(current_user, "recruiter")
    jobs = db.query(JobPost).filter(JobPost.recruiter_user_id == current_user.id).order_by(JobPost.updated_at.desc()).all()
    items = []
    total_shortlisted = 0
    for job in jobs:
        analyses = db.query(Analysis).filter(Analysis.job_post_id == job.id).all()
        shortlisted_count = len([analysis for analysis in analyses if analysis.recruiter_status == "Shortlisted"])
        total_shortlisted += shortlisted_count
        average_score = round(sum(analysis.match_score for analysis in analyses) / len(analyses)) if analyses else 0
        items.append(
            JobDashboardItem(
                **serialize_job(job).model_dump(),
                candidates_matched=len(analyses),
                average_match_score=average_score,
                shortlisted_count=shortlisted_count,
            )
        )
    return RecruiterDashboardResponse(job_posts=items, total_shortlisted=total_shortlisted)


@app.get("/recruiter/metrics", response_model=RecruiterMetricsResponse)
def get_recruiter_metrics(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> RecruiterMetricsResponse:
    require_role(current_user, "recruiter")
    rows = db.query(Analysis).filter(Analysis.recruiter_user_id == current_user.id).all()
    average = round(sum(row.match_score for row in rows) / len(rows)) if rows else 0
    interviews = len([row for row in rows if row.recruiter_status == "Shortlisted"])
    return RecruiterMetricsResponse(
        candidates_applied=len({row.candidate_user_id for row in rows}),
        average_match_score=average,
        interviews_scheduled=interviews,
    )


@app.get("/job-posts/{job_post_id}/ranked-candidates", response_model=list[RankedCandidateMatch])
def list_ranked_candidates(
    job_post_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> list[RankedCandidateMatch]:
    require_role(current_user, "recruiter")
    job = db.get(JobPost, job_post_id)
    if job is None:
        raise HTTPException(status_code=404, detail="Job post not found.")
    if job.recruiter_user_id != current_user.id:
        raise forbidden("Recruiters can only view candidates for their own job posts.")
    rows = (
        db.query(Analysis)
        .filter(Analysis.job_post_id == job_post_id)
        .order_by(Analysis.match_score.desc(), Analysis.created_at.desc())
        .all()
    )
    return [serialize_ranked_match(row) for row in rows]


@app.post("/job-posts/{job_post_id}/report")
def report_job_post(
    job_post_id: int,
    payload: JobReportCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> dict[str, str]:
    require_role(current_user, "candidate")
    job = db.get(JobPost, job_post_id)
    if job is None:
        raise HTTPException(status_code=404, detail="Job post not found.")
    db.add(JobReport(job_post_id=job.id, candidate_user_id=current_user.id, reason=payload.reason))
    job.reports_count += 1
    db.commit()
    return {"status": "reported"}


@app.get("/admin/companies", response_model=list[RecruiterProfileResponse])
def list_companies_for_review(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> list[RecruiterProfileResponse]:
    require_admin(current_user)
    return db.query(Recruiter).order_by(Recruiter.id.desc()).all()


@app.put("/admin/companies/{recruiter_user_id}/review", response_model=RecruiterProfileResponse)
def review_company(
    recruiter_user_id: int,
    payload: AdminCompanyReview,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> RecruiterProfileResponse:
    require_admin(current_user)
    recruiter_user = db.get(User, recruiter_user_id)
    if recruiter_user is None or recruiter_user.role != "recruiter" or recruiter_user.recruiter is None:
        raise HTTPException(status_code=404, detail="Recruiter company profile not found.")
    recruiter_user.recruiter.company_status = payload.status
    update_recruiter_score(db, recruiter_user)
    db.commit()
    db.refresh(recruiter_user.recruiter)
    return recruiter_user.recruiter


@app.get("/admin/flagged-jobs", response_model=list[JobPostResponse])
def list_flagged_jobs(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> list[JobPostResponse]:
    require_admin(current_user)
    rows = (
        db.query(JobPost)
        .filter((JobPost.spam_score >= 70) | (JobPost.reports_count > 0))
        .order_by(JobPost.updated_at.desc())
        .all()
    )
    return [serialize_job(row) for row in rows]


@app.delete("/admin/jobs/{job_post_id}")
def admin_remove_job(
    job_post_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> dict[str, str]:
    require_admin(current_user)
    row = db.get(JobPost, job_post_id)
    if row is None:
        raise HTTPException(status_code=404, detail="Job post not found.")
    db.query(Analysis).filter(Analysis.job_post_id == row.id).delete()
    db.query(JobReport).filter(JobReport.job_post_id == row.id).delete()
    db.delete(row)
    db.commit()
    return {"status": "removed"}


@app.post("/admin/job-imports/mock", response_model=JobImportResponse)
def import_mock_jobs(
    payload: JobImportRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> JobImportResponse:
    require_admin(current_user)
    connector = MockJobConnector()
    imported, skipped = import_jobs_from_connector(db, connector, owner_user_id=current_user.id, publish=payload.publish)
    return JobImportResponse(
        provider=connector.provider,
        imported_count=len(imported),
        skipped_count=skipped,
        jobs=[serialize_job(job) for job in imported],
    )


@app.post("/admin/job-imports/remotive", response_model=JobImportResponse)
def import_remotive_jobs(
    payload: JobImportRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> JobImportResponse:
    require_admin(current_user)
    connector = RemotiveJobConnector(query=payload.query, limit=payload.limit)
    try:
        imported, skipped = import_jobs_from_connector(db, connector, owner_user_id=current_user.id, publish=payload.publish)
    except (ValueError, httpx.HTTPError) as exc:
        raise HTTPException(status_code=502, detail=f"Remotive import failed: {exc}") from exc
    return JobImportResponse(
        provider=connector.provider,
        imported_count=len(imported),
        skipped_count=skipped,
        jobs=[serialize_job(job) for job in imported],
    )


@app.post("/matches", response_model=AnalysisResult)
def create_match(
    payload: MatchCreate,
    idempotency_key: Optional[str] = Header(default=None, alias="Idempotency-Key"),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> AnalysisResult:
    resume = db.get(Resume, payload.resume_id)
    job_post = db.get(JobPost, payload.job_post_id)
    if resume is None:
        raise HTTPException(status_code=404, detail="Resume not found.")
    if job_post is None:
        raise HTTPException(status_code=404, detail="Job post not found.")

    if current_user.role == "candidate" and resume.candidate_user_id != current_user.id:
        raise forbidden("Candidates can only match their own resumes.")
    if current_user.role == "recruiter" and job_post.recruiter_user_id != current_user.id:
        raise forbidden("Recruiters can only run matches for their own job posts.")
    if current_user.role not in {"candidate", "recruiter"}:
        raise forbidden("Unsupported user role.")

    normalized_idempotency_key = (idempotency_key or "").strip()[:128]
    if normalized_idempotency_key:
        existing = (
            db.query(Analysis)
            .filter(
                Analysis.idempotency_user_id == current_user.id,
                Analysis.idempotency_key == normalized_idempotency_key,
                Analysis.resume_id == resume.id,
                Analysis.job_post_id == job_post.id,
            )
            .one_or_none()
        )
        if existing is not None:
            return serialize_analysis(existing, include_private=current_user.role == "recruiter")

    job_text = job_analysis_text(job_post)
    result = ai_analysis(settings, resume.resume_text, job_text, language=current_user.language)
    recruiter_summary = build_recruiter_summary(
        resume.resume_text,
        job_text,
        result["match_score"],
        result["missing_skills"],
        language=current_user.language,
    )
    row = Analysis(
        resume_id=resume.id,
        job_post_id=job_post.id,
        candidate_user_id=resume.candidate_user_id,
        recruiter_user_id=job_post.recruiter_user_id,
        match_score=result["match_score"],
        missing_skills=json.dumps(result["missing_skills"]),
        strongest_skills=json.dumps(result.get("strongest_skills", recruiter_summary["strongest_skills"])),
        improvements=json.dumps(result["improvements"]),
        summary=result["summary"],
        resume_summary=recruiter_summary["resume_summary"],
        fit_summary=recruiter_summary["fit_summary"],
        concerns=json.dumps(recruiter_summary["concerns"]),
        interview_questions=json.dumps(recruiter_summary["interview_questions"]),
        recommendation=recruiter_summary["recommendation"],
        source=result["source"],
        idempotency_key=normalized_idempotency_key,
        idempotency_user_id=current_user.id if normalized_idempotency_key else 0,
    )
    db.add(row)
    db.commit()
    db.refresh(row)
    return serialize_analysis(row, include_private=current_user.role == "recruiter")


@app.get("/matches", response_model=list[AnalysisResult])
def list_matches(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> list[AnalysisResult]:
    query = db.query(Analysis).order_by(Analysis.created_at.desc())
    if current_user.role == "candidate":
        rows = query.filter(Analysis.candidate_user_id == current_user.id).all()
        return [serialize_analysis(row, include_private=False) for row in rows]
    elif current_user.role == "recruiter":
        rows = query.filter(Analysis.recruiter_user_id == current_user.id).all()
        return [serialize_analysis(row, include_private=True) for row in rows]
    else:
        raise forbidden("Unsupported user role.")


@app.get("/matches/{analysis_id}", response_model=AnalysisDetail)
def get_match(
    analysis_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> AnalysisDetail:
    row = db.get(Analysis, analysis_id)
    if row is None:
        raise HTTPException(status_code=404, detail="Analysis not found.")
    if current_user.id not in {row.candidate_user_id, row.recruiter_user_id}:
        raise forbidden("You can only view match results connected to your own resume or job post.")
    return serialize_analysis_detail(row, include_private=current_user.role == "recruiter")


@app.put("/matches/{analysis_id}/review", response_model=AnalysisResult)
def update_match_review(
    analysis_id: int,
    payload: MatchReviewUpdate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> AnalysisResult:
    require_role(current_user, "recruiter")
    row = db.get(Analysis, analysis_id)
    if row is None:
        raise HTTPException(status_code=404, detail="Analysis not found.")
    if row.recruiter_user_id != current_user.id:
        raise forbidden("Recruiters can only review matches for their own job posts.")
    row.recruiter_status = payload.recruiter_status
    row.recruiter_notes = payload.recruiter_notes
    db.commit()
    db.refresh(row)
    return serialize_analysis(row, include_private=True)


@app.post("/resume-text")
async def extract_resume_text(file: UploadFile = File(...)) -> dict[str, str]:
    content = await file.read()
    filename = (file.filename or "").lower()
    content_type = (file.content_type or "").lower()

    if content_type == "application/pdf" or filename.endswith(".pdf"):
        text = extract_pdf_text(content)
    elif content_type.startswith("text/") or filename.endswith(".txt"):
        text = extract_text_file(content)
    else:
        raise HTTPException(status_code=400, detail="Upload a UTF-8 .txt file or readable PDF.")

    return {"text": text}


@app.post("/analyses", response_model=AnalysisResult)
def create_legacy_analysis(payload: AnalysisCreate) -> AnalysisResult:
    result = ai_analysis(settings, payload.resume_text, payload.job_description)
    return AnalysisResult(
        id=0,
        match_score=result["match_score"],
        missing_skills=result["missing_skills"],
        improvements=result["improvements"],
        summary=result["summary"],
        created_at=datetime.utcnow(),
        source=result["source"],
    )
