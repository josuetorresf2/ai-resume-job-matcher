import os
from pathlib import Path

os.environ["DATABASE_URL"] = "sqlite:///./test_role_matcher.db"
os.environ.pop("OPENAI_API_KEY", None)
Path("test_role_matcher.db").unlink(missing_ok=True)

from fastapi.testclient import TestClient  # noqa: E402
from app.main import app  # noqa: E402


client = TestClient(app)


def login(email: str, role: str, name: str = "Test User", language: str = "en") -> dict:
    response = client.post(
        "/auth/mock-login",
        json={"name": name, "email": email, "password": "StrongPass123", "role": role, "language": language},
    )
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


def create_job(
    user: dict,
    description: str = (
        "We are hiring a software engineer to build reliable web products for small teams. "
        "Responsibilities include shipping FastAPI services, React interfaces, SQL-backed workflows, "
        "tests, documentation, and production support. Candidates should communicate clearly and care about maintainable systems."
    ),
) -> dict:
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


def test_login_rejects_fake_looking_email():
    response = client.post(
        "/auth/mock-login",
        json={"name": "Fake User", "email": "person@mailinator.com", "password": "StrongPass123", "role": "candidate"},
    )
    assert response.status_code == 400
    assert response.json()["detail"] == "Use a valid non-temporary email address."


def test_login_returns_bearer_token_for_authenticated_requests():
    user = login("candidate-token@example.com", "candidate", "Candidate")

    response = client.get("/me", headers={"Authorization": f"Bearer {user['access_token']}"})

    assert response.status_code == 200
    assert response.json()["email"] == "candidate-token@example.com"


def test_login_reuses_existing_user_by_normalized_email():
    first = login("duplicate@example.com", "candidate", "First Name")
    second = login("DUPLICATE@example.com", "candidate", "Updated Name")

    assert second["id"] == first["id"]
    assert second["email"] == "duplicate@example.com"
    assert second["name"] == "Updated Name"


def test_talent_pool_export_excludes_password_data():
    candidate = login("pool-candidate@example.com", "candidate", "Pool Candidate")
    admin = login("pool-admin@example.com", "admin", "Pool Admin")
    client.put(
        "/candidate/profile",
        headers=headers(candidate),
        json={
            "headline": "Backend engineer",
            "skills": "Python, FastAPI, SQL",
            "experience": "Built APIs for community projects.",
            "education": "",
            "portfolio_url": "https://portfolio.example.com",
            "github_url": "https://github.com/example",
            "linkedin_url": "",
            "project_demo_urls": "https://demo.example.com",
            "visibility": "public",
            "bio": "Programmer with proof of work.",
        },
    )

    response = client.get("/talent-pool", headers=headers(admin))
    data = response.json()
    serialized = str(data).lower()

    assert response.status_code == 200
    assert any(row["email"] == "pool-candidate@example.com" for row in data["candidates"])
    assert "password" not in serialized
    assert "hash" not in serialized


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
    assert ranked_data[0]["candidate_name"] == "Private candidate"
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


def test_recruiter_must_verify_email_and_company_before_publishing():
    recruiter = login("recruiter-publish@example.com", "recruiter", "Recruiter")
    admin = login("admin-publish@example.com", "admin", "Admin")
    job = create_job(recruiter)

    blocked_unverified_email = client.post(f"/job-posts/{job['id']}/publish", headers=headers(recruiter))
    assert blocked_unverified_email.status_code == 403
    assert blocked_unverified_email.json()["detail"] == "Verify your account before publishing jobs."

    client.post("/auth/verify-placeholder", headers=headers(recruiter))
    blocked_unverified_company = client.post(f"/job-posts/{job['id']}/publish", headers=headers(recruiter))
    assert blocked_unverified_company.status_code == 403
    assert blocked_unverified_company.json()["detail"] == "Company profile must be verified before publishing public jobs."

    client.put(
        "/recruiter/profile",
        headers=headers(recruiter),
        json={
            "company": "Acme",
            "title": "Founder",
            "website": "https://acme.com",
            "country": "Ecuador",
            "city": "Quito",
            "industry": "Software",
            "company_size": "1-10",
            "description": "Small software team hiring responsibly.",
            "contact_email": "jobs@acme.com",
        },
    )
    reviewed = client.put(f"/admin/companies/{recruiter['id']}/review", headers=headers(admin), json={"status": "verified"})
    published = client.post(f"/job-posts/{job['id']}/publish", headers=headers(recruiter))

    assert reviewed.status_code == 200
    assert reviewed.json()["company_status"] == "verified"
    assert published.status_code == 200
    assert published.json()["published"] is True
    assert published.json()["status"] == "published"


def test_unverified_company_can_save_draft_but_public_list_only_shows_published_jobs():
    recruiter = login("recruiter-draft@example.com", "recruiter", "Recruiter")
    job = create_job(recruiter)
    public_jobs = client.get("/job-posts")

    assert job["status"] == "draft"
    assert all(item["id"] != job["id"] for item in public_jobs.json())


def test_spammy_job_is_blocked_from_publishing():
    recruiter = login("recruiter-spam@example.com", "recruiter", "Recruiter")
    admin = login("admin-spam@example.com", "admin", "Admin")
    client.post("/auth/verify-placeholder", headers=headers(recruiter))
    client.put(
        "/recruiter/profile",
        headers=headers(recruiter),
        json={
            "company": "Acme",
            "title": "Recruiter",
            "website": "https://acme.com",
            "country": "Ecuador",
            "city": "Quito",
            "industry": "Software",
            "company_size": "1-10",
            "description": "Small software team hiring responsibly.",
            "contact_email": "jobs@acme.com",
        },
    )
    client.put(f"/admin/companies/{recruiter['id']}/review", headers=headers(admin), json={"status": "verified"})
    spam_job = create_job(recruiter, "WhatsApp only. Guaranteed income. Send money. http://one.test http://two.test")

    response = client.post(f"/job-posts/{spam_job['id']}/publish", headers=headers(recruiter))
    flagged = client.get("/admin/flagged-jobs", headers=headers(admin))

    assert response.status_code == 400
    assert response.json()["detail"]["message"] == "This job looks unsafe and cannot be published yet."
    assert any(item["id"] == spam_job["id"] for item in flagged.json())


def test_candidate_can_report_suspicious_published_job():
    candidate = login("candidate-report@example.com", "candidate", "Candidate")
    recruiter = login("recruiter-report@example.com", "recruiter", "Recruiter")
    admin = login("admin-report@example.com", "admin", "Admin")
    client.post("/auth/verify-placeholder", headers=headers(recruiter))
    client.put(
        "/recruiter/profile",
        headers=headers(recruiter),
        json={
            "company": "Acme",
            "title": "Recruiter",
            "website": "https://acme.com",
            "country": "Ecuador",
            "city": "Quito",
            "industry": "Software",
            "company_size": "1-10",
            "description": "Small software team hiring responsibly.",
            "contact_email": "jobs@acme.com",
        },
    )
    client.put(f"/admin/companies/{recruiter['id']}/review", headers=headers(admin), json={"status": "verified"})
    job = create_job(recruiter)
    client.post(f"/job-posts/{job['id']}/publish", headers=headers(recruiter))

    report = client.post(
        f"/job-posts/{job['id']}/report",
        headers=headers(candidate),
        json={"reason": "The recruiter asked for payment outside the platform."},
    )
    flagged = client.get("/admin/flagged-jobs", headers=headers(admin))

    assert report.status_code == 200
    assert report.json() == {"status": "reported"}
    assert any(item["id"] == job["id"] and item["reports_count"] == 1 for item in flagged.json())


def test_admin_routes_are_protected():
    candidate = login("candidate-admin-denied@example.com", "candidate", "Candidate")
    response = client.get("/admin/companies", headers=headers(candidate))
    assert response.status_code == 403
    assert response.json()["detail"] == "Only admins can perform this action."


def test_spanish_matching_returns_spanish_fallback_text():
    candidate = login("candidate-spanish@example.com", "candidate", "Candidate", language="es")
    recruiter = login("recruiter-spanish@example.com", "recruiter", "Recruiter")
    resume = create_resume(candidate)
    job = create_job(recruiter)

    response = client.post("/matches", headers=headers(candidate), json={"resume_id": resume["id"], "job_post_id": job["id"]})

    assert response.status_code == 200
    assert "Analisis local" in response.json()["summary"]


def test_candidate_ai_interview_simulator():
    candidate = login("candidate-interview@example.com", "candidate", "Candidate")
    resume = create_resume(candidate, "Python FastAPI SQL Docker backend engineer resume with APIs.")

    response = client.post("/candidate/interview-practice", headers=headers(candidate), json={"resume_id": resume["id"]})

    assert response.status_code == 200
    data = response.json()
    assert data["interview_score"] == 84
    assert "Communication" in data["strengths"]
    assert "API security concepts" in data["needs_improvement"]
    assert len(data["questions"]) >= 5


def test_candidate_career_coach_generates_roadmap():
    candidate = login("candidate-coach@example.com", "candidate", "Candidate")
    recruiter = login("recruiter-coach@example.com", "recruiter", "Recruiter")
    resume = create_resume(candidate, "Python FastAPI SQL backend resume.")
    job = create_job(
        recruiter,
        "Backend role requiring Python, FastAPI, Docker, PostgreSQL, CI/CD, testing, and API security for production services.",
    )

    response = client.post(
        "/candidate/career-coach",
        headers=headers(candidate),
        json={"resume_id": resume["id"], "job_post_id": job["id"], "target_score": 85},
    )

    assert response.status_code == 200
    data = response.json()
    assert data["target_score"] == 85
    assert "Docker" in data["learn"]
    assert data["estimated_effort"] == "4 weeks"
    assert len(data["roadmap"]) == 4


def test_candidate_salary_intelligence():
    candidate = login("candidate-salary@example.com", "candidate", "Candidate")
    resume = create_resume(candidate, "Python FastAPI SQL backend engineer resume.")

    response = client.post("/candidate/salary-intelligence", headers=headers(candidate), json={"resume_id": resume["id"]})

    assert response.status_code == 200
    data = response.json()
    assert data["ranges"][0] == {"market": "Ecuador", "range": "$1200-$1800"}
    assert data["ranges"][1] == {"market": "Remote LATAM", "range": "$1800-$3000"}
    assert data["ranges"][2] == {"market": "US Contractor", "range": "$3000-$5000"}


def test_candidate_github_analysis_generates_portfolio_score():
    candidate = login("candidate-github@example.com", "candidate", "Candidate")

    response = client.post(
        "/candidate/github-analysis",
        headers=headers(candidate),
        json={"github_url": "https://github.com/example/backend-portfolio"},
    )

    assert response.status_code == 200
    data = response.json()
    assert data["portfolio_score"] == 88
    assert "Python" in data["languages"]
    assert data["recommendations"]


def test_recruiter_cannot_use_candidate_ai_tools():
    recruiter = login("recruiter-ai-denied@example.com", "recruiter", "Recruiter")

    response = client.post(
        "/candidate/github-analysis",
        headers=headers(recruiter),
        json={"github_url": "https://github.com/example/backend-portfolio"},
    )

    assert response.status_code == 403
    assert response.json()["detail"] == "Only candidates can perform this action."


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
