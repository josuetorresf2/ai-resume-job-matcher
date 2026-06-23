import os

os.environ["DATABASE_URL"] = "sqlite:///./test_resume_matcher.db"
os.environ.pop("OPENAI_API_KEY", None)

from fastapi.testclient import TestClient  # noqa: E402
from app.main import app  # noqa: E402


client = TestClient(app)


def test_health():
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json() == {"status": "ok"}


def test_create_and_list_analysis():
    payload = {
        "resume_text": "Python FastAPI developer with Docker, SQL, React, and Git experience.",
        "job_description": "We need a Python engineer with FastAPI, Docker, SQL, AWS, and GitHub Actions.",
    }
    created = client.post("/analyses", json=payload)
    assert created.status_code == 200
    data = created.json()
    assert 0 <= data["match_score"] <= 100
    assert "aws" in data["missing_skills"]
    assert data["source"] == "heuristic"

    listed = client.get("/analyses")
    assert listed.status_code == 200
    assert len(listed.json()) >= 1
