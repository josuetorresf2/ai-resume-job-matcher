from dataclasses import dataclass
import html
import re
import time
from typing import Callable, Optional, Protocol

import httpx


@dataclass(frozen=True)
class RetryPolicy:
    max_attempts: int = 3
    backoff_seconds: float = 0.5
    throttle_seconds: float = 1.0


class ConnectorHttpClient:
    def __init__(
        self,
        retry_policy: RetryPolicy,
        get: Callable[..., httpx.Response] = httpx.get,
        sleep: Callable[[float], None] = time.sleep,
        monotonic: Callable[[], float] = time.monotonic,
    ) -> None:
        self.retry_policy = retry_policy
        self.get = get
        self.sleep = sleep
        self.monotonic = monotonic
        self._last_request_at = 0.0

    def request_json(self, url: str, params: dict[str, str], timeout: float) -> dict:
        last_error: Optional[Exception] = None
        for attempt in range(1, self.retry_policy.max_attempts + 1):
            self._throttle()
            try:
                response = self.get(url, params=params, timeout=timeout)
                if response.status_code == 429:
                    self._sleep_for_retry_after(response, attempt)
                    last_error = httpx.HTTPStatusError("Rate limited", request=httpx.Request("GET", url), response=response)
                    continue
                if 500 <= response.status_code < 600:
                    last_error = httpx.HTTPStatusError("Retryable provider error", request=httpx.Request("GET", url), response=response)
                    self._sleep_for_attempt(attempt)
                    continue
                if 400 <= response.status_code < 500:
                    raise httpx.HTTPStatusError("Non-retryable provider error", request=httpx.Request("GET", url), response=response)
                data = response.json()
                if not isinstance(data, dict):
                    raise ValueError("Provider response must be a JSON object.")
                return data
            except (httpx.TimeoutException, httpx.TransportError) as exc:
                last_error = exc
                self._sleep_for_attempt(attempt)
        if last_error is not None:
            raise last_error
        raise RuntimeError("Connector request failed without an error.")

    def _throttle(self) -> None:
        elapsed = self.monotonic() - self._last_request_at
        wait_for = self.retry_policy.throttle_seconds - elapsed
        if self._last_request_at and wait_for > 0:
            self.sleep(wait_for)
        self._last_request_at = self.monotonic()

    def _sleep_for_attempt(self, attempt: int) -> None:
        if attempt < self.retry_policy.max_attempts:
            self.sleep(self.retry_policy.backoff_seconds * attempt)

    def _sleep_for_retry_after(self, response: httpx.Response, attempt: int) -> None:
        retry_after = response.headers.get("Retry-After")
        if retry_after:
            try:
                self.sleep(min(float(retry_after), 60.0))
                return
            except ValueError:
                pass
        self._sleep_for_attempt(attempt)


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

    def __init__(
        self,
        query: str = "python",
        limit: int = 5,
        timeout_seconds: float = 10.0,
        http_client: Optional[ConnectorHttpClient] = None,
    ) -> None:
        self.query = query
        self.limit = limit
        self.timeout_seconds = timeout_seconds
        self.http_client = http_client or ConnectorHttpClient(RetryPolicy())

    def fetch_jobs(self) -> list[NormalizedJobInput]:
        payload = self.http_client.request_json(self.endpoint, params={"search": self.query}, timeout=self.timeout_seconds)
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
