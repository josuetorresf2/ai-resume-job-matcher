# FairHire AI Current Architecture

This document records the current implementation as verified from source code on 2026-07-11. It distinguishes verified behavior from assumptions or planned behavior.

## Repository Structure

Verified top-level structure:

```text
.
├── .github/workflows/ci.yml
├── AGENTS.md
├── README.md
├── backend/
│   ├── Dockerfile
│   ├── alembic.ini
│   ├── alembic/
│   ├── app/
│   │   ├── analysis.py
│   │   ├── config.py
│   │   ├── database.py
│   │   ├── main.py
│   │   ├── models.py
│   │   ├── resume_parser.py
│   │   ├── schemas.py
│   │   ├── security.py
│   │   ├── trust.py
│   │   └── verification.py
│   ├── requirements.txt
│   └── tests/test_api.py
├── docker-compose.yml
├── docs/images/
├── frontend/
│   ├── Dockerfile
│   ├── app/
│   │   ├── globals.css
│   │   ├── layout.tsx
│   │   └── page.tsx
│   ├── lib/
│   │   ├── api.ts
│   │   └── score.ts
│   ├── package.json
│   ├── tests/score.test.mjs
│   └── vercel.json
├── render.yaml
└── vercel.json
```

Generated/local artifacts are present in the working tree but ignored by `.gitignore`, including `frontend/.next`, `frontend/.next-vercel`, `.venv`, caches, and SQLite database files.

## Technologies Actually Found

### Frontend

Verified from `frontend/package.json`:

- Next.js `^14.2.35`
- React `18.3.1`
- React DOM `18.3.1`
- TypeScript `5.7.2`
- ESLint `8.57.1`
- `eslint-config-next` `^14.2.35`
- Node test runner via `node --test`

The frontend is a single Next.js app-router page implemented mostly in `frontend/app/page.tsx`. Styling is global CSS in `frontend/app/globals.css`.

### Backend

Verified from `backend/requirements.txt`:

- FastAPI `0.115.6`
- Uvicorn `0.34.0`
- SQLAlchemy `2.0.36`
- Alembic `1.14.0`
- psycopg `3.2.13`
- Pydantic settings `2.7.1`
- OpenAI Python SDK `1.59.7`
- pypdf `5.1.0`
- Pytest `8.3.4`
- HTTPX `0.28.1`
- Ruff `0.8.4`

### Languages

Verified source languages:

- Python for backend and tests.
- TypeScript/TSX for frontend.
- JavaScript/MJS for frontend tests.
- CSS for frontend styling.
- YAML for CI/CD and Render.
- Dockerfile syntax for containers.

## System Components

Verified components:

- Next.js frontend at `frontend/`.
- FastAPI backend at `backend/app/main.py`.
- API request tracing with `X-Correlation-ID` middleware in `backend/app/main.py`.
- SQL database through SQLAlchemy models in `backend/app/models.py`.
- Alembic migrations in `backend/alembic/versions/`.
- OpenAI integration with heuristic fallback in `backend/app/analysis.py`.
- PDF/TXT resume text extraction in `backend/app/resume_parser.py`.
- Job connector boundary with a controlled mock provider, Remotive public API provider, shared retry policy, and throttle-aware HTTP client in `backend/app/job_connectors.py`.
- Job import service in `backend/app/job_imports.py`.
- Trust/safety scoring in `backend/app/trust.py`.
- Verification messaging placeholder/Twilio sender in `backend/app/verification.py`.
- Docker Compose local stack with Postgres, backend, and frontend in `docker-compose.yml`.
- GitHub Actions workflow in `.github/workflows/ci.yml`.
- Render backend/Postgres blueprint in `render.yaml`.
- Vercel frontend configuration in `vercel.json` and `frontend/vercel.json`.

Not found in the current implementation:

- MongoDB.
- Temporal.
- Puppeteer.
- OAuth provider integration.
- Real external job-provider API connector.
- Request throttling middleware.
- Retry/backoff framework.
- Idempotency storage.
- AWS infrastructure templates.

## Database and Data Access

Verified data access:

- SQLAlchemy ORM with `DeclarativeBase`.
- Engine configured from `DATABASE_URL`, defaulting to SQLite `sqlite:///./resume_matcher.db`.
- PostgreSQL URLs are normalized to `postgresql+psycopg://`.
- Alembic migrations are configured and CI verifies upgrade against PostgreSQL.
- `initialize_database()` in `backend/app/main.py` calls `Base.metadata.create_all()` and performs ad hoc column additions for older SQLite/local schemas.

Verified tables/models:

- `users`
- `candidates`
- `recruiters`
- `resumes`
- `job_posts`
- `analyses`
- `job_reports`

Main relationships:

- One `User` may have one `Candidate`.
- One `User` may have one `Recruiter`.
- A candidate user owns many `Resume` records.
- A recruiter user owns many `JobPost` records.
- `Analysis` links one resume, one job post, one candidate user, and one recruiter user.
- `JobReport` links a candidate user to a job post.

## Authentication Flow

Verified behavior:

- Login/account creation endpoint is `POST /auth/mock-login`.
- Despite the route name, it creates/reuses a user with name, email, password, role, language, and verification channel.
- Existing users are reused by normalized lowercase email.
- The backend rejects the same email if used with a different role.
- New passwords are hashed with PBKDF2-SHA256 in `backend/app/security.py`.
- Legacy SHA-256 password hashes are still accepted on login and upgraded after a successful password check.
- A custom HMAC-signed bearer token is generated by `create_access_token()`.
- Authenticated requests can use `Authorization: Bearer <token>`.
- Authenticated requests can also use `X-User-Id` only when `AUTH_ALLOW_TEST_HEADER=true`, which is retained as a local/test fallback.
- Token payload includes `sub` and `exp`; default expiration is seven days.

Verified limitations:

- No OAuth implementation exists.
- No refresh tokens, session revocation, password reset, account lockout, or rate limiting were found.
- PBKDF2 is a safer password-hashing baseline than the previous SHA-256 hash, but Argon2id or bcrypt would still be stronger long-term options.
- `X-User-Id` fallback can bypass password/token possession if `AUTH_ALLOW_TEST_HEADER=true` is enabled in production.
- The default `AUTH_SECRET_KEY` is `"change-me-in-production"`.

## Authorization Model

Verified roles:

- `candidate`
- `recruiter`
- `admin`

Verified role enforcement:

- Candidate profile routes require candidate role.
- Recruiter profile routes require recruiter role.
- Resume create/list/update requires candidate role and ownership checks.
- Job post create/list-own/update/delete/publish requires recruiter role and ownership checks.
- Match listing is filtered by candidate or recruiter ownership.
- Match detail requires the current user to be either the candidate or recruiter linked to the analysis.
- Recruiter match review requires recruiter role and ownership.
- Admin company review and flagged job routes require admin role.
- Candidate AI career tools require candidate role.

Verified privacy behavior:

- Candidate match list hides recruiter private notes.
- Recruiter match list includes recruiter status and notes.
- Recruiter ranked candidates masks `candidate_name` as `"Private candidate"` when candidate visibility is private and the match is not shortlisted.
- Recruiter talent pool visibility is filtered by candidate visibility and recruiter verification/company status.

## Main Data Models

### User

Fields include name, unique email, phone number, password hash, role, language, verification status/channel, low-bandwidth preference, and created timestamp.

### Candidate

Fields include headline, skills, experience, education, portfolio/GitHub/LinkedIn/project demo URLs, visibility, completeness score, and bio.

### Recruiter

Fields include company, title, website, country, city, industry, company size, description, contact email, company status, and trust score.

### Resume

Stores candidate user id, title, raw resume text, created timestamp, and updated timestamp.

### JobPost

Stores recruiter user id, title, company, location, work mode, salary range, experience level, required skills, nice-to-have skills, description, status, spam score/reasons, quality score/tips, reports count, and timestamps.
It also stores normalized metadata for future imports/search: source type, source provider, external id, canonical title/company/location, remote flag, parsed salary min/max/currency, and canonical skills.

### Analysis

Stores resume/job/user links, match score, missing skills, strongest skills, improvements, summaries, concerns, interview questions, recommendation, recruiter status/notes, timestamp, and source.

### JobReport

Stores job post id, candidate user id, reason, and timestamp.

## API Structure

Verified endpoints from `backend/app/main.py`:

### Health and Auth

- `GET /health`
- `POST /auth/mock-login`
- `PUT /me/preferences`
- `GET /talent-pool`
- `POST /auth/request-verification`
- `POST /auth/verify-placeholder`
- `GET /me`

### Candidate

- `GET /candidate/profile`
- `PUT /candidate/profile`
- `POST /resumes`
- `GET /resumes`
- `PUT /resumes/{resume_id}`
- `GET /candidate/metrics`
- `POST /candidate/interview-practice`
- `POST /candidate/career-coach`
- `POST /candidate/salary-intelligence`
- `POST /candidate/github-analysis`
- `POST /resume-text`

### Recruiter and Jobs

- `GET /recruiter/profile`
- `PUT /recruiter/profile`
- `POST /job-posts`
- `GET /job-posts`
- `GET /job-posts/mine`
- `PUT /job-posts/{job_post_id}`
- `POST /job-posts/{job_post_id}/publish`
- `DELETE /job-posts/{job_post_id}`
- `GET /recruiter/dashboard`
- `GET /recruiter/metrics`
- `GET /job-posts/{job_post_id}/ranked-candidates`

### Reports and Admin

- `POST /job-posts/{job_post_id}/report`
- `GET /admin/companies`
- `PUT /admin/companies/{recruiter_user_id}/review`
- `GET /admin/flagged-jobs`
- `DELETE /admin/jobs/{job_post_id}`

### Matching

- `POST /matches`
- `GET /matches`
- `GET /matches/{analysis_id}`
- `PUT /matches/{analysis_id}/review`
- `POST /analyses` legacy unauthenticated analysis endpoint

## Frontend-to-Backend Communication

Verified from `frontend/lib/api.ts`:

- The frontend reads `NEXT_PUBLIC_API_URL`, defaulting to `http://localhost:8000`.
- JSON requests include `Content-Type: application/json`.
- JSON requests include `X-Correlation-ID`.
- Authenticated requests include both `X-User-Id` and, when available, `Authorization: Bearer <token>`.
- File upload to `/resume-text` uses `FormData` without JSON headers.
- Errors from FastAPI `detail` payloads are converted into readable frontend messages.

## Frontend Functionality

Verified from `frontend/app/page.tsx`:

- First screen supports role selection and job-market preview.
- User can choose Candidate or Recruiter, then enter name, email, phone, password, language, and verification channel.
- Language selector supports English, Spanish, Portuguese, French, and Swahili in the UI copy object.
- Theme toggle and low-bandwidth toggle exist.
- Candidate dashboard supports:
  - Candidate profile fields.
  - Proof-of-work links.
  - Visibility setting.
  - Resume text/PDF/TXT upload.
  - Match against published jobs.
  - Suspicious job reporting.
  - AI interview, career coach, salary, and GitHub portfolio tool buttons.
  - Match history.
- Recruiter dashboard supports:
  - Company/recruiter profile fields.
  - Account verification placeholder button.
  - Job post create/update/publish with title, company, location, work mode, salary range, experience level, required skills, nice-to-have skills, and description.
  - Job quality/spam/status display.
  - Recruiter metrics and match history.
- Admin dashboard supports:
  - Listing companies for review.
  - Approving/rejecting company verification.
  - Listing flagged jobs.
  - Removing flagged jobs.

Verified limitations:

- Recruiter UI does not expose ranked candidates or recruiter match review controls, although backend endpoints exist.
- Candidate GitHub analysis is simulated; it does not call the GitHub API.
- Career/salary/interview tools are heuristic/simulated and not full conversational AI workflows.

## Validation

Verified backend validation:

- Pydantic validates role, language, verification channel, visibility, work mode, admin review status, match review status, target score, and minimum text lengths.
- Email format and fake-looking domains are checked in `security.py`.
- SMS/WhatsApp verification requires E.164 phone format.
- Company website must be HTTP/HTTPS with a dotted host.
- Company contact email must be valid.
- Website/email domain mismatch leaves company pending review.
- Job publish requires verified user, verified company, and spam score below 70.
- Resume upload supports readable PDFs and UTF-8 text files.

Verified frontend validation:

- Login checks non-empty name, an email containing `@`, and password length at least 8 before calling backend.
- Candidate save resume button disables for short resume text.
- Candidate run match button disables when resume/job is not selected.
- Salary tool requires saved resume or sufficiently long pasted resume text.

Limitations:

- URL fields on candidate profile are not strongly validated.
- Password strength is only minimum length at schema/UI level.
- Legacy `/analyses` is unauthenticated.
- No request size limits were found for uploaded files or long text payloads.

## AI and External Integrations

Verified:

- OpenAI is used only by `ai_analysis()` when `OPENAI_API_KEY` is configured.
- When no OpenAI key is present or parsing fails, heuristic analysis is used.
- WhatsApp can send through Meta WhatsApp Cloud API when Meta env vars are configured. Twilio SMS/WhatsApp can still send through HTTPX only if Twilio env vars are configured.
- Email verification is placeholder-only.

Not found:

- GitHub API integration.
- Public jobs API integration.
- OAuth integration.
- MongoDB integration.
- Temporal workflows.
- Puppeteer tests.

## Deployment Structure

Verified:

- `docker-compose.yml` runs PostgreSQL, backend, and frontend locally.
- Backend Dockerfile runs Alembic migrations before Uvicorn.
- Frontend Dockerfile runs `npm ci`, copies source, builds Next.js with `npm run build`, and starts with `npm run start`.
- `render.yaml` deploys backend as Docker web service plus Render Postgres.
- `frontend/vercel.json` builds frontend with `npm run build:vercel` and outputs `.next-vercel`.
- Root `vercel.json` supports repository-root builds with `npm --prefix frontend run build:vercel`.

Verified risk:

- Vercel config currently contains placeholder `NEXT_PUBLIC_API_URL=https://your-render-backend.onrender.com`; the real backend URL must be set in Vercel project settings for live functionality.

## CI/CD

Verified `.github/workflows/ci.yml`:

- Backend job:
  - Python 3.12.
  - Postgres 16 service.
  - `pip install -r requirements.txt`.
  - `ruff check app tests`.
  - `pytest`.
  - `alembic -c alembic.ini upgrade head` against PostgreSQL.
- Frontend job:
  - Node 22.
  - `npm install`.
  - `npm run lint`.
  - `npm test`.
  - `npm run build`.

Limitations:

- CI does not run Docker Compose.
- CI does not run end-to-end browser tests.
- CI does not publish artifacts or validate deployment environment variables.
- Frontend test coverage is minimal.

## Environment Variables

Verified from code and deployment files:

- `DATABASE_URL`
- `OPENAI_API_KEY`
- `OPENAI_MODEL`
- `CORS_ORIGINS`
- `AUTH_SECRET_KEY`
- `AUTH_ALLOW_TEST_HEADER`
- `TWILIO_ACCOUNT_SID`
- `TWILIO_AUTH_TOKEN`
- `TWILIO_SMS_FROM`
- `TWILIO_WHATSAPP_FROM`
- `WHATSAPP_CLOUD_ACCESS_TOKEN`
- `WHATSAPP_CLOUD_PHONE_NUMBER_ID`
- `WHATSAPP_CLOUD_API_VERSION`
- `NEXT_PUBLIC_API_URL`

The local `.env` file exists but was not copied into this document. Only variable names were inspected.

## Features Confirmed Complete

Based on source and tests:

- Candidate/recruiter/admin role creation through `/auth/mock-login`.
- Bearer token authentication for `/me`.
- Candidate profile update.
- Recruiter profile update.
- Candidate resume create/list/update.
- PDF/TXT resume text extraction.
- Recruiter job create/update/delete.
- Job draft/public publish flow.
- Verified email/company requirement before job publish.
- Spammy job publish block.
- Candidate suspicious-job reporting.
- Admin company review.
- Admin flagged job listing.
- Admin job removal.
- Candidate/recruiter match creation and listing.
- Recruiter private review notes hidden from candidates.
- Recruiter dashboard metrics.
- Candidate AI interview/career/salary/GitHub endpoints as deterministic/heuristic features.
- Multilingual UI copy and Spanish backend fallback text for some flows.
- PostgreSQL migration verification in CI.

## Features Incomplete or UI/Placeholder Only

Verified gaps:

- Product is not using MongoDB.
- No Temporal worker/client/workflows.
- No Puppeteer QA tests.
- No OAuth login.
- Email verification is a placeholder.
- WhatsApp verification can send through Meta WhatsApp Cloud API when `WHATSAPP_CLOUD_ACCESS_TOKEN` and `WHATSAPP_CLOUD_PHONE_NUMBER_ID` are configured, with Twilio as a fallback. Without provider credentials, the local demo still uses hard-coded code `"123456"`; there is no persisted verification-code validation flow.
- GitHub analysis is simulated and only validates that the URL contains `github.com`.
- Salary intelligence uses static ranges.
- AI interview simulator is deterministic heuristic logic, not a chat/interview state machine.
- Career coach is heuristic and does not persist plans.
- Ranked candidates backend exists, but recruiter UI does not expose a ranked-candidate page.
- Mock job-provider imports are available through admin endpoint `POST /admin/job-imports/mock`.
- Remotive public API imports are available through admin endpoint `POST /admin/job-imports/remotive`.
- Remotive imports store source provider, external id, and external URL for attribution/link-back.
- Match creation supports an optional `Idempotency-Key` header scoped to the current user, resume, and job post.
- No idempotency for job imports or external requests.
- AWS-ready deployment architecture is documented in `docs/aws-deployment.md`, but no Terraform/CDK/CloudFormation files exist yet.

## Security Weaknesses

Verified or directly inferred from implementation:

- Legacy users may still have old SHA-256 password hashes until they successfully log in and are upgraded.
- `X-User-Id` fallback can authenticate requests without possession of a password or bearer token if `AUTH_ALLOW_TEST_HEADER=true` is accidentally enabled outside local/test environments.
- Default `AUTH_SECRET_KEY` is unsafe for production if not overridden.
- No OAuth provider or standard auth framework.
- No rate limiting for login, verification, AI, upload, or job-publish endpoints.
- No CSRF strategy is needed for bearer-token APIs, but no broader browser security policy is documented.
- CORS allows configured origins but production correctness depends on env setup.
- Uploaded file size limits are not enforced.
- Verification codes are not persisted or checked.
- Legacy `/analyses` endpoint is unauthenticated.
- Talent pool endpoint can expose candidate email/phone to admins and to verified recruiters for visible candidates; this is intended by current code but needs stricter consent/audit before production.
- `Base.metadata.create_all()` and ad hoc schema mutation run at app import time, which can mask migration drift and is risky in production.

## Architectural Risks

- Backend startup performs schema creation/mutation outside Alembic, creating two schema-management paths.
- The frontend is a single large page component, making future role dashboards and E2E tests harder to isolate.
- JSON arrays are stored as text fields instead of native JSON columns.
- Match creation is idempotent when the client sends `Idempotency-Key`; ordinary requests without that header can still create new analyses.
- No background worker exists for slow AI/API jobs.
- External integration boundaries are not defined.
- API logs include method, path, status, duration, and correlation ID, but broader application/event logging is still limited.
- Current CI verifies unit/API/build but not full local Docker boot or browser flows.
- Vercel currently deploys the frontend only; live workflows depend on a deployed backend URL and correct CORS.

## Assumptions and Unknowns

- It is assumed that production should keep FastAPI/PostgreSQL unless a documented reason is accepted; the current repo does not contain MongoDB.
- It is unknown whether the deployed Vercel preview is publicly accessible without deployment protection; previous manual checks saw a Vercel login on at least one preview URL.
- It is unknown whether Render backend is deployed and configured with real `CORS_ORIGINS`, `AUTH_SECRET_KEY`, and `NEXT_PUBLIC_API_URL`.

## Verification Results

Commands run during this audit:

| Area | Command | Result | Notes |
| --- | --- | --- | --- |
| Backend dependency install | `cd backend && .venv/bin/pip install -r requirements.txt` | Passed | Existing virtual environment uses Python 3.9.6. Pip warned that pip itself is old. |
| Backend lint | `cd backend && .venv/bin/ruff check app tests` | Passed | Output: `All checks passed!` |
| Backend tests | `cd backend && .venv/bin/pytest` | Passed | 25 tests passed. |
| Backend migration smoke test | `cd backend && DATABASE_URL=sqlite:////tmp/fairhire_audit_alembic.db .venv/bin/alembic -c alembic.ini upgrade head` | Passed | Verified SQLite migration path. GitHub CI also verifies PostgreSQL migrations. |
| Frontend dependency install | `cd frontend && npm ci --include=dev` | Passed with warnings | Local Node is `v19.7.0`; several packages warn that they expect Node 18/20/22/24 ranges. Install completed. |
| Frontend lint | `cd frontend && npm run lint` | Passed | Next lint completed with no warnings/errors. |
| Frontend tests | `cd frontend && npm test` | Passed | 1 Node test passed. |
| Frontend type check | `cd frontend && npx tsc --noEmit` | Passed | `tsc` produced no output and exited successfully as part of the verification chain. |
| Frontend Vercel build | `cd frontend && npm run build:vercel` | Passed | Built Next.js output into `.next-vercel`. |
| Frontend production build | `cd frontend && npm run build` | Passed | Built standard `.next` output. |
| Docker availability | `docker --version` | Failed before modifications | `zsh:1: command not found: docker`. Docker is not installed or not on PATH on this machine. |

Existing command failure recorded:

- `docker --version`
  - Relevant error: `zsh:1: command not found: docker`
  - Whether failure existed before audit modifications: yes, this was checked before documentation edits.
  - Likely cause: Docker Desktop or Docker CLI is not installed on the Mac, or not available on PATH.
  - Recommended fix: install Docker Desktop for macOS, start it, then rerun `docker --version` and `docker compose up --build`.
