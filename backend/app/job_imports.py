import json
from typing import Optional

from sqlalchemy.orm import Session

from .job_connectors import JobConnector
from .job_normalization import apply_normalized_job_fields
from .models import JobPost, Recruiter
from .trust import assess_job_quality, assess_job_safety


def company_profile_complete(profile: Optional[Recruiter]) -> bool:
    if profile is None:
        return False
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


def import_jobs_from_connector(
    db: Session,
    connector: JobConnector,
    owner_user_id: int,
    publish: bool = False,
) -> tuple[list[JobPost], int]:
    imported: list[JobPost] = []
    skipped = 0
    owner_profile = db.query(Recruiter).filter(Recruiter.user_id == owner_user_id).one_or_none()

    for job in connector.fetch_jobs():
        existing = (
            db.query(JobPost)
            .filter(JobPost.source_provider == job.source_provider, JobPost.external_id == job.external_id)
            .one_or_none()
        )
        if existing is not None:
            skipped += 1
            continue

        row = JobPost(
            recruiter_user_id=owner_user_id,
            title=job.title,
            company=job.company,
            location=job.location,
            work_mode=job.work_mode,
            salary_range=job.salary_range,
            experience_level=job.experience_level,
            required_skills=job.required_skills,
            nice_to_have_skills=job.nice_to_have_skills,
            description=job.description,
                source_type="external",
                source_provider=job.source_provider,
                external_id=job.external_id,
                external_url=job.external_url,
                status="published" if publish else "draft",
        )
        apply_normalized_job_fields(row)
        company_complete = company_profile_complete(owner_profile)
        spam_score, spam_reasons = assess_job_safety(row.description, company_complete)
        quality_score, quality_tips = assess_job_quality(
            row.title,
            row.description,
            row.required_skills,
            row.salary_range,
            company_complete,
            spam_score,
        )
        row.quality_score = quality_score
        row.quality_tips = json.dumps(quality_tips)
        row.spam_score = spam_score
        row.spam_reasons = json.dumps(spam_reasons)
        imported.append(row)
        db.add(row)

    db.commit()
    for row in imported:
        db.refresh(row)
    return imported, skipped
