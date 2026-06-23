# AI Resume & Job Matcher

Full-stack portfolio project for matching candidate resumes to recruiter job posts with role-based ownership checks.

## Tech Stack

- Next.js frontend
- FastAPI backend
- SQLite database
- OpenAI API integration with local heuristic fallback
- Docker Compose
- Pytest and Node test runner
- GitHub Actions CI

## Features

- First screen lets users choose Candidate or Recruiter
- Mock session login using `X-User-Id` request headers
- Candidates can edit only their own profile and resumes
- Recruiters can edit only their own profile and job posts
- Candidates can match their own resume against public job posts
- Recruiters can view match results tied to their own job posts
- PDF and UTF-8 TXT resume extraction
- OpenAI-backed analysis with local heuristic fallback
- SQLite tables for users, candidates, recruiters, resumes, job posts, and analyses

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

## Project Rules

See `AGENTS.md` for the coding rules used by this project.

## Role-Based Model

The current app uses mock authentication so the portfolio can demonstrate authorization without a production auth provider.

- `POST /auth/mock-login` creates or returns a user with role `candidate` or `recruiter`.
- Protected requests include `X-User-Id: <id>`.
- Candidate-only routes reject recruiters with `403`.
- Recruiter-only routes reject candidates with `403`.
- Ownership checks prevent users from editing records they do not own.

Database tables:

- `users`
- `candidates`
- `recruiters`
- `resumes`
- `job_posts`
- `analyses`

The `analyses` table links `resume_id` and `job_post_id`, plus candidate and recruiter user ids for role-filtered match history.

## Local Setup

Copy the environment template:

```bash
cp .env.example .env
```

Add your OpenAI API key to `.env`:

```bash
OPENAI_API_KEY=sk-your-key
```

The backend will still work without a key by using the local heuristic analyzer.

### Run With Docker

```bash
docker compose up --build
```

Open:

- Frontend: http://localhost:3000
- Backend API docs: http://localhost:8000/docs

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

Open http://localhost:3000.

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

## GitHub Setup

Create a GitHub repo named `ai-resume-job-matcher`, then connect this local repo:

```bash
git branch -M main
git remote add origin https://github.com/YOUR_USERNAME/ai-resume-job-matcher.git
git add .
git commit -m "Initial AI resume job matcher"
git push -u origin main
```

If you want GitHub Actions or deployed services to use OpenAI, add a repository secret named `OPENAI_API_KEY`. Do not commit your real API key to the repo.
