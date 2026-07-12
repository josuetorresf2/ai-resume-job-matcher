# FairHire

A free AI-powered recruiting platform for candidates and small companies in underserved markets.

Hiring tools are expensive. This project aims to make AI-powered recruiting accessible to candidates, small businesses, and communities that cannot afford enterprise recruiting software.

> Live Demo: add your Vercel URL after deployment  
> API Demo: add your Render URL after deployment

## Overview

FairHire is a full-stack recruiting SaaS project built around trust, accessibility, and practical AI workflows for underserved hiring markets. The first screen lets users preview real job categories by target market before sharing personal information, then choose Candidate or Recruiter and create an account. Candidates can upload resumes, match against jobs, practice interviews, analyze salary ranges, and review GitHub portfolio strength. Recruiters can create verified company profiles, publish safer job posts, review ranked candidates, and track recruiting metrics.

The project is production-oriented: PostgreSQL-ready persistence, SQLAlchemy migrations, role-based permissions, CI/CD, deployment configuration for Vercel and Render, multilingual UI, OpenAI integration with local fallback logic, and tests for security rules.

## Screenshots

### Home

![FairHire home page](docs/images/home.png)

### Resume Upload

![FairHire resume upload page](docs/images/upload.png)

### AI Results

![FairHire results page](docs/images/results.png)

### Recruiter Dashboard

![FairHire dashboard page](docs/images/dashboard.png)

## Features

- Candidate, recruiter, and admin roles
- Market-first onboarding with role selection before personal data entry
- Job discovery preview for Latin America, Africa, and global remote work
- English, Spanish, Portuguese, French, and Swahili UI support
- Candidate proof-of-work links for live demos, GitHub repos, portfolio, LinkedIn, case studies, and docs
- User language preference stored in the backend
- AI/fallback responses generated in the selected language
- PDF and TXT resume upload
- Resume-to-job match score from 0-100
- Missing skills and resume improvement suggestions
- AI Interview Simulator for backend engineering practice
- AI Career Coach with target score, learning gaps, effort estimate, and roadmap
- Salary Intelligence for Ecuador, Remote LATAM, and US contractor markets
- GitHub Portfolio Analysis with portfolio score, languages, projects, tests, documentation, and recommendations
- Recruiter dashboard with job posts, candidates applied, average match score, and interviews scheduled
- Candidate metrics for applications, average match score, and profile strength
- Company verification workflow
- Email validation, Bearer token sessions, and verification flow for email, SMS, or WhatsApp
- E.164 phone validation for SMS/WhatsApp verification
- Job spam scoring and quality scoring
- Candidate privacy controls
- Suspicious job reporting
- Admin routes for company review and flagged job moderation
- Job import connector boundary with mock imports and Remotive public API integration
- Low-bandwidth preference
- PostgreSQL deployment path with Alembic migrations
- CI/CD checks for backend tests, linting, migrations, frontend tests, and build verification

## Tech Stack

| Layer | Technology |
| --- | --- |
| Frontend | Next.js, React, TypeScript |
| Backend | FastAPI, Python |
| Database | PostgreSQL for production, SQLite fallback for local tests |
| ORM/Migrations | SQLAlchemy, Alembic |
| AI | OpenAI API integration with local heuristic fallback |
| Testing | Pytest, Node test runner |
| CI/CD | GitHub Actions |
| Deployment | Vercel frontend, Render backend, Render PostgreSQL |
| Resume parsing | PDF and UTF-8 TXT extraction |

## Architecture

```mermaid
flowchart LR
    Candidate[Candidate Browser] --> Frontend[Next.js Frontend on Vercel]
    Recruiter[Recruiter Browser] --> Frontend
    Admin[Admin Browser] --> Frontend
    Frontend --> API[FastAPI Backend on Render]
    API --> Auth[Role-Based Auth Layer]
    API --> DB[(PostgreSQL)]
    API --> AI[OpenAI API]
    API --> LocalAI[Local Heuristic Fallback]
    API --> Parser[PDF/TXT Resume Parser]
```

```mermaid
flowchart TD
    User[User Login] --> Role{Role}
    Role --> Candidate[Candidate Routes]
    Role --> Recruiter[Recruiter Routes]
    Role --> Admin[Admin Routes]
    Candidate --> Resume[Own Resumes Only]
    Candidate --> Matches[Own Match History]
    Recruiter --> Jobs[Own Job Posts Only]
    Recruiter --> Rankings[Ranked Candidates]
    Admin --> Reviews[Company and Flagged Job Review]
```

```mermaid
flowchart LR
    Push[Git Push or Pull Request] --> BackendCI[Backend CI]
    Push --> FrontendCI[Frontend CI]
    BackendCI --> Pytest[Pytest]
    BackendCI --> Ruff[Ruff Lint]
    BackendCI --> Alembic[Alembic Postgres Migration Check]
    FrontendCI --> NodeTests[Node Tests]
    FrontendCI --> Lint[Next Lint]
    FrontendCI --> Build[Next Build]
```

Core backend tables:

- `users`
- `candidates`
- `recruiters`
- `resumes`
- `job_posts`
- `analyses`
- `job_reports`

## Security Model

- Candidates can edit only their own profile and resumes.
- Recruiters can edit only their own company profile and job posts.
- Recruiters cannot edit candidate profiles, resumes, or personal data.
- Candidates cannot edit recruiter job posts or company profiles.
- Recruiters cannot publish jobs without verified account and verified company status.
- Admin-only review routes are protected.

Current auth supports password-based account creation and signed Bearer tokens, while keeping `X-User-Id` as a local fallback for tests. Production OAuth should add Google, GitHub, and email login through a provider such as Auth.js, Clerk, Supabase Auth, or Auth0.

## Installation

```bash
git clone https://github.com/josuetorresf2/ai-resume-job-matcher.git
cd ai-resume-job-matcher
cp .env.example .env
```

Example `.env`:

```bash
OPENAI_API_KEY=sk-your-key
OPENAI_MODEL=gpt-4o-mini
DATABASE_URL=postgresql+psycopg://fairhire:fairhire@localhost:5432/fairhire
CORS_ORIGINS=http://localhost:3000,http://127.0.0.1:3000
NEXT_PUBLIC_API_URL=http://localhost:8000
AUTH_SECRET_KEY=change-this-before-deploy
AUTH_ALLOW_TEST_HEADER=false
TWILIO_ACCOUNT_SID=
TWILIO_AUTH_TOKEN=
TWILIO_SMS_FROM=
TWILIO_WHATSAPP_FROM=whatsapp:+14155238886
```

The backend still works without an OpenAI key by using local heuristic analysis.

`AUTH_ALLOW_TEST_HEADER=false` is the production-safe default. Set it to `true` only in local automated tests if you need the legacy `X-User-Id` test session header. Normal browser/API clients should use the bearer token returned by `/auth/mock-login`.

## Running Locally

### Option 1: Docker Compose with PostgreSQL

```bash
docker compose up --build
```

Open:

- Frontend: http://localhost:3000
- Backend API docs: http://localhost:8000/docs

### Option 2: Manual Backend and Frontend

Start PostgreSQL locally, then run migrations:

```bash
cd backend
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
alembic -c alembic.ini upgrade head
uvicorn app.main:app --reload
```

Frontend:

```bash
cd frontend
npm install
npm run dev
```

## Deployment

Recommended free-first path:

- Frontend: Vercel Hobby or Cloudflare Pages.
- Backend: Render free web service, Fly.io free allowance, or another low-cost container host for FastAPI.
- Database: Supabase Postgres free tier or Render Postgres if available in the account.

This repo keeps the frontend and backend deployable separately. The frontend can go live first, but the AI/job workflows need `NEXT_PUBLIC_API_URL` set to the deployed backend URL.

### Backend: Render

This repo includes `render.yaml`.

1. Create a Render account.
2. Create a new Blueprint from this GitHub repo.
3. Render will create:
   - `fairhire-api`
   - `fairhire-postgres`
4. Set backend environment variables:
   - `OPENAI_API_KEY`
   - `OPENAI_MODEL=gpt-4o-mini`
   - `AUTH_SECRET_KEY`
   - `TWILIO_ACCOUNT_SID`
   - `TWILIO_AUTH_TOKEN`
   - `TWILIO_SMS_FROM`
   - `TWILIO_WHATSAPP_FROM`
   - `CORS_ORIGINS=https://your-vercel-app.vercel.app`
5. Deploy.
6. Copy the Render backend URL.

The backend Dockerfile runs:

```bash
alembic -c alembic.ini upgrade head
uvicorn app.main:app --host 0.0.0.0 --port $PORT
```

### Frontend: Vercel

This repo includes `vercel.json`.

1. Import the GitHub repo into Vercel.
2. Set the project root to the repository root or `frontend`. The root `vercel.json` builds with `npm --prefix frontend` so monorepo builds install the correct package.
3. Add environment variable:
   - `NEXT_PUBLIC_API_URL=https://your-render-backend.onrender.com`
4. Deploy.
5. Add the Vercel URL to Render `CORS_ORIGINS`.

## Usage Examples

Candidate workflow:

1. Create a candidate account.
2. Add a real E.164 phone number, for example `+593987654321`, if using SMS or WhatsApp verification.
3. Upload or paste a resume.
4. Match against published jobs.
5. Practice an AI interview.
6. Generate a career roadmap to reach a target match score.
7. Estimate salary ranges.
8. Analyze GitHub portfolio strength.

Recruiter workflow:

1. Create a recruiter account.
2. Complete company profile.
3. Verify account and company.
4. Create job drafts.
5. Review quality and spam scores.
6. Publish jobs.
7. Review ranked candidates and shortlist matches.

## API Highlights

```http
POST /auth/mock-login
GET  /candidate/metrics
POST /candidate/interview-practice
POST /candidate/career-coach
POST /candidate/salary-intelligence
POST /candidate/github-analysis
POST /matches
GET  /recruiter/metrics
GET  /recruiter/dashboard
POST /job-posts/{job_post_id}/publish
PUT  /admin/companies/{recruiter_user_id}/review
POST /admin/job-imports/mock
POST /admin/job-imports/remotive
```

Remotive imports use the documented public Remotive remote jobs API and store provider metadata plus source URLs for attribution.

## CI/CD

GitHub Actions runs on every push and pull request:

- Backend dependency install
- Ruff linting
- Pytest test suite
- Alembic migration check against PostgreSQL
- Frontend dependency install
- Next lint
- Node tests
- Next production build

## Roadmap

- Real authentication with Google, GitHub, and email login
- Production email, SMS, or WhatsApp verification provider
- Admin review UI
- Fraud detection for fake companies, fake candidates, AI-generated nonsense resumes, and copy-paste job descriptions
- Recruiter Copilot for job descriptions, responsibilities, salary recommendations, and interview questions
- One-click resume builder with ATS-friendly PDF export and LinkedIn summary
- AI job search agent that finds, ranks, and explains job opportunities
- Video introduction analysis for clarity, confidence, and speaking pace
- Referral network for community-supported referrals
- University mode for students without experience or portfolio
- Opportunity Score for salary transparency, company reputation, growth, and remote flexibility
- Live production demo link

## License

MIT License. See [LICENSE](LICENSE).
