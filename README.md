# AI Resume & Job Matcher

Full-stack portfolio project that compares a resume against a job description and returns a match score, missing skills, and targeted resume improvements.

## Tech Stack

- Next.js frontend
- FastAPI backend
- SQLite database
- OpenAI API integration with local heuristic fallback
- Docker Compose
- Pytest and Node test runner
- GitHub Actions CI

## Features

- Paste resume text or upload a UTF-8 `.txt` resume
- Paste a job description
- Generate a 0-100 match score
- Show missing skills
- Suggest resume improvements
- Store previous analyses in SQLite
- Dashboard with latest score, saved analyses, average score, and history

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
