# AI Resume & Job Matcher

A free AI-powered recruiting platform for candidates and small companies in underserved markets.

## Mission

Hiring tools are expensive. This project aims to make AI-powered recruiting accessible to candidates, small businesses, and communities that cannot afford enterprise recruiting software.

## Problem Being Solved

Many candidates and small employers do not have access to paid applicant tracking systems, resume screeners, sourcing tools, or recruiting analytics. This project demonstrates a lightweight alternative: role-based recruiting workflows, AI-assisted matching, trust and safety checks, and multilingual access in one portfolio-ready full-stack app.

## Tech Stack

- Next.js frontend with TypeScript
- FastAPI backend with Python type hints
- SQLite database
- OpenAI API integration with local heuristic fallback
- PDF and TXT resume parsing
- Pytest and Node test runner
- GitHub Actions CI
- Docker Compose files included

## Core Features

- Candidate and recruiter account creation with password-based mock auth
- Email format validation and fake-email blocking
- Email, SMS, and WhatsApp verification placeholders
- English and Spanish language preference
- AI responses generated in the selected user language
- Candidate resume upload, PDF parsing, and match history
- Recruiter company profiles, job drafts, and protected publishing
- Job spam scoring and job quality scoring before publication
- Candidate privacy controls and suspicious job reporting
- Recruiter dashboard with match counts, average scores, and shortlisted candidates
- Admin routes for company review and flagged job moderation

## Candidate Workflow

1. Create an account as a Candidate.
2. Choose English or Spanish and a verification channel.
3. Complete the candidate profile and visibility setting.
4. Upload or paste a resume.
5. Match the resume against published jobs.
6. Review match score, missing skills, strongest skills, and AI improvement suggestions.
7. Report suspicious jobs when needed.

Candidate privacy options:

- `private`
- `visible_to_verified_recruiters`
- `public`

Recruiters cannot edit candidate profiles, resumes, or private notes.

## Recruiter Workflow

1. Create an account as a Recruiter.
2. Verify the account with the placeholder verification flow.
3. Create a company profile with website, location, industry, size, description, and contact email.
4. Save job posts as drafts.
5. Review job quality score and spam warnings.
6. Publish only after account verification and admin company approval.
7. View ranked candidate matches by job post.
8. Mark each match as Shortlisted, Maybe, or Rejected and keep private recruiter notes.

Recruiters cannot edit candidate resumes, candidate profiles, or candidate personal data.

## Trust And Safety System

The backend enforces:

- Candidates cannot edit jobs or company profiles.
- Recruiters cannot edit resumes or candidate profiles.
- Recruiters cannot publish jobs without a verified account and verified company.
- Unverified companies can save draft jobs but cannot publish public jobs.
- Admin routes are protected by the `admin` role.
- Candidate contact information is not exposed in recruiter match responses.

Job spam signals include:

- Too many links
- Suspicious salary promises
- Repeated text
- Missing company information
- Very short descriptions
- Scam-like phrases

Job quality score considers:

- Clear title
- Responsibilities
- Required skills
- Salary transparency
- Complete company information
- Scam signals
- Inclusive language

Trust scores include:

- Recruiter trust score: verified email, verified company, complete profile, low spam risk
- Candidate completeness score: resume, skills, experience, education, links, language preference

## Multilingual Support

The app currently supports:

- English
- Spanish

The frontend includes a language switcher. The backend stores the user language preference and sends AI or fallback analysis text in the selected language.

## Accessibility And Low-Bandwidth Mode

The UI is responsive, mobile-friendly, and intentionally avoids heavy animations. Users can toggle a low-bandwidth preference that is stored on their account for future lightweight rendering decisions.

## Screenshots

Screenshots can be added here before publishing the final portfolio case study:

- Landing and account creation
- Candidate dashboard
- Recruiter dashboard
- Job quality and spam feedback
- Ranked candidate matches

## Project Structure

```text
ai-resume-job-matcher/
  AGENTS.md
  backend/
    app/
      analysis.py
      config.py
      database.py
      main.py
      models.py
      resume_parser.py
      schemas.py
      security.py
      trust.py
    tests/
    Dockerfile
    requirements.txt
  frontend/
    app/
    lib/
    tests/
    Dockerfile
    package.json
  .github/workflows/ci.yml
  docker-compose.yml
  .env.example
```

## Local Setup

Copy the environment template:

```bash
cp .env.example .env
```

Add your OpenAI API key to `.env`:

```bash
OPENAI_API_KEY=sk-your-key
```

The backend still works without a key by using the local heuristic analyzer.

### Run Without Docker

Backend:

```bash
cd backend
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
uvicorn app.main:app --reload
```

Frontend:

```bash
cd frontend
npm install
npm run dev
```

Open:

- Frontend: http://localhost:3000
- Backend API docs: http://localhost:8000/docs

### Run With Docker

Docker is optional. If Docker is installed:

```bash
docker compose up --build
```

## Tests

Backend:

```bash
cd backend
pytest
```

Frontend:

```bash
cd frontend
npm test
npm run build
```

## Roadmap

- Real authentication with secure password hashing and session tokens
- Real email, SMS, or WhatsApp verification provider integration
- Admin review UI
- Candidate application flow and explicit profile sharing
- Recruiter response-rate tracking
- Job report investigation workflow
- More languages for underserved markets
- Deployment guide and live demo

## GitHub Setup

Create a GitHub repo named `ai-resume-job-matcher`, then connect this local repo:

```bash
git branch -M main
git remote add origin https://github.com/YOUR_USERNAME/ai-resume-job-matcher.git
git add .
git commit -m "Initial AI resume job matcher"
git push -u origin main
```

If GitHub Actions or deployed services should use OpenAI, add a repository secret named `OPENAI_API_KEY`. Do not commit a real API key.
