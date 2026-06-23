import json
from datetime import datetime
from typing import Optional
from fastapi import Depends, FastAPI, Header, HTTPException, UploadFile, File
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy import inspect, text
from sqlalchemy.orm import Session

from .analysis import ai_analysis, build_recruiter_summary
from .config import get_settings
from .database import Base, engine, get_db
from .models import Analysis, Candidate, JobPost, Recruiter, Resume, User
from .resume_parser import extract_pdf_text, extract_text_file
from .schemas import (
    AnalysisCreate,
    AnalysisDetail,
    AnalysisResult,
    CandidateProfileResponse,
    CandidateProfileUpdate,
    HealthResponse,
    JobPostCreate,
    JobPostResponse,
    JobPostUpdate,
    JobDashboardItem,
    LoginRequest,
    MatchCreate,
    MatchReviewUpdate,
    RankedCandidateMatch,
    RecruiterDashboardResponse,
    RecruiterProfileResponse,
    RecruiterProfileUpdate,
    ResumeCreate,
    ResumeResponse,
    ResumeUpdate,
    UserResponse,
)


settings = get_settings()


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
            }
            for column_name, ddl in analysis_columns.items():
                if column_name not in columns:
                    connection.execute(text(f"ALTER TABLE analyses ADD COLUMN {column_name} {ddl}"))


initialize_database()

app = FastAPI(title=settings.app_name)
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origin_list,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


def forbidden(message: str) -> HTTPException:
    return HTTPException(status_code=403, detail=message)


def get_current_user(
    x_user_id: Optional[int] = Header(default=None, alias="X-User-Id"),
    db: Session = Depends(get_db),
) -> User:
    if x_user_id is None:
        raise HTTPException(status_code=401, detail="Missing X-User-Id session header.")

    user = db.get(User, x_user_id)
    if user is None:
        raise HTTPException(status_code=401, detail="Invalid mock session user.")
    return user


def require_role(user: User, role: str) -> None:
    if user.role != role:
        raise forbidden(f"Only {role}s can perform this action.")


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
    return RankedCandidateMatch(
        **result.model_dump(),
        candidate_name=row.resume.candidate_user.name,
        candidate_headline=profile.headline if profile else "",
        resume_title=row.resume.title,
    )


@app.get("/health", response_model=HealthResponse)
def health() -> HealthResponse:
    return HealthResponse(status="ok")


@app.post("/auth/mock-login", response_model=UserResponse)
def mock_login(payload: LoginRequest, db: Session = Depends(get_db)) -> UserResponse:
    user = db.query(User).filter(User.email == payload.email).one_or_none()
    if user is None:
        user = User(name=payload.name, email=payload.email, role=payload.role)
        db.add(user)
        db.commit()
        db.refresh(user)
    elif user.role != payload.role:
        raise HTTPException(status_code=400, detail="This email is already registered with a different role.")
    else:
        user.name = payload.name

    if user.role == "candidate" and user.candidate is None:
        db.add(Candidate(user_id=user.id))
    if user.role == "recruiter" and user.recruiter is None:
        db.add(Recruiter(user_id=user.id))
    db.commit()
    db.refresh(user)
    return user


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
    profile.bio = payload.bio
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
    db.commit()
    db.refresh(row)
    return row


@app.post("/job-posts", response_model=JobPostResponse)
def create_job_post(
    payload: JobPostCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> JobPostResponse:
    require_role(current_user, "recruiter")
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
    db.add(row)
    db.commit()
    db.refresh(row)
    return row


@app.get("/job-posts", response_model=list[JobPostResponse])
def list_job_posts(db: Session = Depends(get_db)) -> list[JobPostResponse]:
    return db.query(JobPost).order_by(JobPost.updated_at.desc()).all()


@app.get("/job-posts/mine", response_model=list[JobPostResponse])
def list_my_job_posts(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> list[JobPostResponse]:
    require_role(current_user, "recruiter")
    return db.query(JobPost).filter(JobPost.recruiter_user_id == current_user.id).order_by(JobPost.updated_at.desc()).all()


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
    db.commit()
    db.refresh(row)
    return row


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
                description=job.description,
                created_at=job.created_at,
                updated_at=job.updated_at,
                candidates_matched=len(analyses),
                average_match_score=average_score,
                shortlisted_count=shortlisted_count,
            )
        )
    return RecruiterDashboardResponse(job_posts=items, total_shortlisted=total_shortlisted)


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


@app.post("/matches", response_model=AnalysisResult)
def create_match(
    payload: MatchCreate,
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

    job_text = job_analysis_text(job_post)
    result = ai_analysis(settings, resume.resume_text, job_text)
    recruiter_summary = build_recruiter_summary(
        resume.resume_text,
        job_text,
        result["match_score"],
        result["missing_skills"],
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
