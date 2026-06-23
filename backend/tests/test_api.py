import os
from pathlib import Path

os.environ["DATABASE_URL"] = "sqlite:///./test_role_matcher.db"
os.environ.pop("OPENAI_API_KEY", None)
Path("test_role_matcher.db").unlink(missing_ok=True)

from fastapi.testclient import TestClient  # noqa: E402
from app.main import app  # noqa: E402


client = TestClient(app)


def login(email: str, role: str, name: str = "Test User") -> dict:
    response = client.post("/auth/mock-login", json={"name": name, "email": email, "role": role})
    assert response.status_code == 200
    return response.json()


def headers(user: dict) -> dict[str, str]:
    return {"X-User-Id": str(user["id"])}


def create_resume(user: dict, text: str = "Python FastAPI React Docker SQL resume with measurable outcomes.") -> dict:
    response = client.post(
        "/resumes",
        headers=headers(user),
        json={"title": "Primary resume", "resume_text": text},
    )
    assert response.status_code == 200
    return response.json()


def create_job(user: dict, description: str = "Hiring Python FastAPI React Docker SQL AWS engineer.") -> dict:
    response = client.post(
        "/job-posts",
        headers=headers(user),
        json={
            "title": "Software Engineer",
            "company": "Acme",
            "location": "New York, NY",
            "work_mode": "hybrid",
            "salary_range": "$120k-$150k",
            "experience_level": "Mid-level",
            "required_skills": "Python, FastAPI, React, Docker, SQL",
            "nice_to_have_skills": "AWS, GitHub Actions",
            "description": description,
        },
    )
    assert response.status_code == 200
    return response.json()


def test_health():
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json() == {"status": "ok"}


def test_candidate_cannot_edit_recruiter_job_post():
    candidate = login("candidate-job-edit@example.com", "candidate", "Candidate")
    recruiter = login("recruiter-job-edit@example.com", "recruiter", "Recruiter")
    job = create_job(recruiter)

    response = client.put(
        f"/job-posts/{job['id']}",
        headers=headers(candidate),
        json={"title": "Changed", "description": "Changed job description with enough words."},
    )

    assert response.status_code == 403
    assert response.json()["detail"] == "Only recruiters can perform this action."


def test_recruiter_cannot_edit_candidate_resume():
    candidate = login("candidate-resume-edit@example.com", "candidate", "Candidate")
    recruiter = login("recruiter-resume-edit@example.com", "recruiter", "Recruiter")
    resume = create_resume(candidate)

    response = client.put(
        f"/resumes/{resume['id']}",
        headers=headers(recruiter),
        json={"resume_text": "Recruiter tries to change candidate owned resume text."},
    )

    assert response.status_code == 403
    assert response.json()["detail"] == "Only candidates can perform this action."


def test_users_can_only_modify_their_own_data():
    candidate_one = login("candidate-one@example.com", "candidate", "Candidate One")
    candidate_two = login("candidate-two@example.com", "candidate", "Candidate Two")
    recruiter_one = login("recruiter-one@example.com", "recruiter", "Recruiter One")
    recruiter_two = login("recruiter-two@example.com", "recruiter", "Recruiter Two")
    resume = create_resume(candidate_one)
    job = create_job(recruiter_one)

    resume_response = client.put(
        f"/resumes/{resume['id']}",
        headers=headers(candidate_two),
        json={"resume_text": "Another candidate tries to edit this resume with enough words."},
    )
    job_response = client.put(
        f"/job-posts/{job['id']}",
        headers=headers(recruiter_two),
        json={"description": "Another recruiter tries to edit this job post with enough words."},
    )

    assert resume_response.status_code == 403
    assert resume_response.json()["detail"] == "Candidates can only edit their own resumes."
    assert job_response.status_code == 403
    assert job_response.json()["detail"] == "Recruiters can only edit their own job posts."


def test_matching_still_works_for_role_based_flow():
    candidate = login("candidate-match@example.com", "candidate", "Candidate")
    recruiter = login("recruiter-match@example.com", "recruiter", "Recruiter")
    resume = create_resume(candidate)
    job = create_job(recruiter)

    response = client.post(
        "/matches",
        headers=headers(candidate),
        json={"resume_id": resume["id"], "job_post_id": job["id"]},
    )
    data = response.json()

    assert response.status_code == 200
    assert data["resume_id"] == resume["id"]
    assert data["job_post_id"] == job["id"]
    assert data["candidate_user_id"] == candidate["id"]
    assert data["recruiter_user_id"] == recruiter["id"]
    assert 0 <= data["match_score"] <= 100
    assert data["source"] == "heuristic"
    assert data["recommendation"] in {"Strong fit", "Possible fit", "Weak fit"}
    assert data["resume_summary"]
    assert data["interview_questions"]

    candidate_matches = client.get("/matches", headers=headers(candidate))
    recruiter_matches = client.get("/matches", headers=headers(recruiter))
    assert len(candidate_matches.json()) >= 1
    assert len(recruiter_matches.json()) >= 1


def test_recruiter_dashboard_and_ranked_candidates():
    candidate_one = login("candidate-rank-one@example.com", "candidate", "Candidate One")
    candidate_two = login("candidate-rank-two@example.com", "candidate", "Candidate Two")
    recruiter = login("recruiter-rank@example.com", "recruiter", "Recruiter")
    resume_one = create_resume(candidate_one, "Python FastAPI React Docker SQL AWS GitHub Actions resume.")
    resume_two = create_resume(candidate_two, "Customer support resume with light SQL exposure and documentation.")
    job = create_job(recruiter)

    client.post("/matches", headers=headers(candidate_one), json={"resume_id": resume_one["id"], "job_post_id": job["id"]})
    client.post("/matches", headers=headers(candidate_two), json={"resume_id": resume_two["id"], "job_post_id": job["id"]})

    dashboard = client.get("/recruiter/dashboard", headers=headers(recruiter))
    ranked = client.get(f"/job-posts/{job['id']}/ranked-candidates", headers=headers(recruiter))

    assert dashboard.status_code == 200
    assert dashboard.json()["job_posts"][0]["candidates_matched"] == 2
    assert dashboard.json()["job_posts"][0]["average_match_score"] >= 0
    assert ranked.status_code == 200
    ranked_data = ranked.json()
    assert len(ranked_data) == 2
    assert ranked_data[0]["match_score"] >= ranked_data[1]["match_score"]
    assert ranked_data[0]["candidate_name"]
    assert "strongest_skills" in ranked_data[0]


def test_recruiter_review_notes_are_private_to_recruiter():
    candidate = login("candidate-private-notes@example.com", "candidate", "Candidate")
    recruiter = login("recruiter-private-notes@example.com", "recruiter", "Recruiter")
    resume = create_resume(candidate)
    job = create_job(recruiter)
    created = client.post("/matches", headers=headers(candidate), json={"resume_id": resume["id"], "job_post_id": job["id"]}).json()

    review = client.put(
        f"/matches/{created['id']}/review",
        headers=headers(recruiter),
        json={"recruiter_status": "Shortlisted", "recruiter_notes": "Strong backend screen candidate."},
    )
    candidate_view = client.get(f"/matches/{created['id']}", headers=headers(candidate))
    recruiter_view = client.get(f"/matches/{created['id']}", headers=headers(recruiter))

    assert review.status_code == 200
    assert review.json()["recruiter_status"] == "Shortlisted"
    assert review.json()["recruiter_notes"] == "Strong backend screen candidate."
    assert candidate_view.json()["recruiter_status"] is None
    assert candidate_view.json()["recruiter_notes"] is None
    assert recruiter_view.json()["recruiter_notes"] == "Strong backend screen candidate."


def test_recruiter_can_delete_only_own_job_posts():
    owner = login("recruiter-delete-owner@example.com", "recruiter", "Owner")
    other = login("recruiter-delete-other@example.com", "recruiter", "Other")
    job = create_job(owner)

    denied = client.delete(f"/job-posts/{job['id']}", headers=headers(other))
    deleted = client.delete(f"/job-posts/{job['id']}", headers=headers(owner))

    assert denied.status_code == 403
    assert denied.json()["detail"] == "Recruiters can only delete their own job posts."
    assert deleted.status_code == 200
    assert deleted.json() == {"status": "deleted"}


def test_extract_text_resume_upload():
    response = client.post(
        "/resume-text",
        files={"file": ("resume.txt", b"Python FastAPI resume", "text/plain")},
    )
    assert response.status_code == 200
    assert response.json() == {"text": "Python FastAPI resume"}


def test_extract_pdf_resume_upload(monkeypatch):
    monkeypatch.setattr("app.main.extract_pdf_text", lambda content: "PDF resume text")
    response = client.post(
        "/resume-text",
        files={"file": ("resume.pdf", b"%PDF fake", "application/pdf")},
    )
    assert response.status_code == 200
    assert response.json() == {"text": "PDF resume text"}
