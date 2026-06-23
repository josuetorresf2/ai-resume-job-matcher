import json
from fastapi import Depends, FastAPI, HTTPException, UploadFile, File
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session

from .analysis import ai_analysis
from .config import get_settings
from .database import Base, engine, get_db
from .models import Analysis
from .resume_parser import extract_pdf_text, extract_text_file
from .schemas import AnalysisCreate, AnalysisDetail, AnalysisResult, HealthResponse


settings = get_settings()
Base.metadata.create_all(bind=engine)

app = FastAPI(title=settings.app_name)
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origin_list,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


def serialize_analysis(row: Analysis) -> AnalysisDetail:
    return AnalysisDetail(
        id=row.id,
        resume_text=row.resume_text,
        job_description=row.job_description,
        match_score=row.match_score,
        missing_skills=json.loads(row.missing_skills),
        improvements=json.loads(row.improvements),
        summary=row.summary,
        created_at=row.created_at,
        source=row.source,
    )


@app.get("/health", response_model=HealthResponse)
def health() -> HealthResponse:
    return HealthResponse(status="ok")


@app.post("/analyses", response_model=AnalysisResult)
def create_analysis(payload: AnalysisCreate, db: Session = Depends(get_db)) -> AnalysisResult:
    result = ai_analysis(settings, payload.resume_text, payload.job_description)
    row = Analysis(
        resume_text=payload.resume_text,
        job_description=payload.job_description,
        match_score=result["match_score"],
        missing_skills=json.dumps(result["missing_skills"]),
        improvements=json.dumps(result["improvements"]),
        summary=result["summary"],
        source=result["source"],
    )
    db.add(row)
    db.commit()
    db.refresh(row)
    return serialize_analysis(row)


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


@app.get("/analyses", response_model=list[AnalysisResult])
def list_analyses(db: Session = Depends(get_db)) -> list[AnalysisResult]:
    rows = db.query(Analysis).order_by(Analysis.created_at.desc()).limit(25).all()
    return [serialize_analysis(row) for row in rows]


@app.get("/analyses/{analysis_id}", response_model=AnalysisDetail)
def get_analysis(analysis_id: int, db: Session = Depends(get_db)) -> AnalysisDetail:
    row = db.get(Analysis, analysis_id)
    if row is None:
        raise HTTPException(status_code=404, detail="Analysis not found")
    return serialize_analysis(row)
