import json
import re

from .models import JobPost


def normalize_skill_list(value: str) -> list[str]:
    return sorted({item.strip().lower() for item in value.split(",") if item.strip()})


def parse_salary_range(value: str) -> tuple[int, int, str]:
    amounts = [int(part.replace(",", "")) for part in re.findall(r"\d[\d,]*", value or "")]
    currency = "USD" if "$" in (value or "") else "USD"
    if not amounts:
        return 0, 0, currency
    if len(amounts) == 1:
        return amounts[0], amounts[0], currency
    return min(amounts[0], amounts[1]), max(amounts[0], amounts[1]), currency


def apply_normalized_job_fields(job: JobPost) -> None:
    salary_min, salary_max, currency = parse_salary_range(job.salary_range)
    job.source_type = job.source_type or "internal"
    job.source_provider = job.source_provider or "fairhire"
    job.external_id = job.external_id or ""
    job.canonical_title = job.title.strip().lower()
    job.canonical_company = job.company.strip().lower()
    job.canonical_location = job.location.strip().lower()
    job.canonical_remote = 1 if job.work_mode == "remote" else 0
    job.canonical_salary_min = salary_min
    job.canonical_salary_max = salary_max
    job.canonical_currency = currency
    job.canonical_skills = json.dumps(normalize_skill_list(", ".join([job.required_skills, job.nice_to_have_skills])))
