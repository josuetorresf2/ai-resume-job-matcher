from dataclasses import dataclass
from typing import Protocol


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
            ),
        ]
