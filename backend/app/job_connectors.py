from dataclasses import dataclass
import html
import re
from typing import Protocol

import httpx


@dataclass(frozen=True)
class NormalizedJobInput:
    title: str
    company: str
    location: str
    work_mode: str
    salary_range: str
    experience_level: str
    required_skills: str
    nice_to_have_skills: str
    description: str
    source_provider: str
    external_id: str
    external_url: str = ""


class JobConnector(Protocol):
    provider: str

    def fetch_jobs(self) -> list[NormalizedJobInput]:
        """Return normalized jobs from a documented provider or controlled test source."""


class MockJobConnector:
    provider = "mock_public_jobs"

    def fetch_jobs(self) -> list[NormalizedJobInput]:
        return [
            NormalizedJobInput(
                title="Remote Python Automation Engineer",
                company="Community Tech Collective",
                location="Remote LATAM",
                work_mode="remote",
                salary_range="$1800-$2800",
                experience_level="Mid-level",
                required_skills="Python, REST APIs, SQL, Automation",
                nice_to_have_skills="FastAPI, Docker, GitHub Actions",
                description=(
                    "Build reliable API integrations and workflow automations for small companies. "
                    "The role focuses on documented public APIs, testing, retries, and clean operational handoffs."
                ),
                source_provider=self.provider,
                external_id="mock-python-automation-001",
                external_url="https://example.com/jobs/mock-python-automation-001",
            ),
            NormalizedJobInput(
                title="React Frontend Engineer",
                company="Open Market Studio",
                location="Remote Africa",
                work_mode="remote",
                salary_range="$1600-$2400",
                experience_level="Junior to Mid-level",
                required_skills="React, TypeScript, HTML, CSS",
                nice_to_have_skills="Accessibility, Testing, API Integration",
                description=(
                    "Create lightweight recruiting and marketplace interfaces for low-bandwidth environments. "
                    "Candidates should show portfolio projects, clear UI thinking, and practical frontend testing."
                ),
                source_provider=self.provider,
                external_id="mock-react-frontend-002",
                external_url="https://example.com/jobs/mock-react-frontend-002",
            ),
        ]


class RemotiveJobConnector:
    provider = "remotive"
    endpoint = "https://remotive.com/api/remote-jobs"

    def __init__(self, query: str = "python", limit: int = 5, timeout_seconds: float = 10.0) -> None:
        self.query = query
        self.limit = limit
        self.timeout_seconds = timeout_seconds

    def fetch_jobs(self) -> list[NormalizedJobInput]:
        response = httpx.get(self.endpoint, params={"search": self.query}, timeout=self.timeout_seconds)
        response.raise_for_status()
        payload = response.json()
        return self.from_payload(payload, limit=self.limit)

    def from_payload(self, payload: dict, limit: int = 5) -> list[NormalizedJobInput]:
        jobs = payload.get("jobs", [])
        if not isinstance(jobs, list):
            raise ValueError("Remotive payload must include a jobs list.")
        return [self.normalize_job(job) for job in jobs[:limit] if isinstance(job, dict)]

    def normalize_job(self, job: dict) -> NormalizedJobInput:
        required = ["id", "title", "company_name", "url", "description"]
        missing = [field for field in required if not job.get(field)]
        if missing:
            raise ValueError(f"Remotive job is missing required fields: {', '.join(missing)}")
        description = re.sub(r"\s+", " ", html.unescape(re.sub(r"<[^>]+>", " ", str(job["description"])))).strip()
        tags = job.get("tags") if isinstance(job.get("tags"), list) else []
        return NormalizedJobInput(
            title=str(job["title"]),
            company=str(job["company_name"]),
            location=str(job.get("candidate_required_location") or "Remote"),
            work_mode="remote",
            salary_range=str(job.get("salary") or ""),
            experience_level=str(job.get("job_type") or ""),
            required_skills=", ".join(str(tag) for tag in tags[:8]),
            nice_to_have_skills="",
            description=f"{description}\n\nSource: Remotive {job['url']}",
            source_provider=self.provider,
            external_id=str(job["id"]),
            external_url=str(job["url"]),
        )
