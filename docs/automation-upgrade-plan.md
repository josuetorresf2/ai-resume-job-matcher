# FairHire AI Automation Upgrade Plan

This plan upgrades the existing FairHire AI application incrementally for an Automation Software Engineer portfolio. It preserves the current Next.js + FastAPI + SQLAlchemy architecture unless a later task documents a stronger reason to add or change technology.

## Guiding Rules

- Do not rebuild or rename FairHire.
- Preserve working candidate, recruiter, matching, trust, and deployment flows.
- Add one independently reviewable vertical slice at a time.
- Prefer documented public APIs over browser automation.
- Use Puppeteer only for controlled QA of FairHire flows, not unauthorized scraping or CAPTCHA/security-control evasion.
- Treat MongoDB and Temporal as optional additions behind clear boundaries, not replacements for the current SQL source of truth.

## Recommended Implementation Order

1. Harden authentication/session boundaries.
2. Add request correlation IDs and structured logging.
3. Add idempotency support for write operations.
4. Expand recruiter job data model/UI completeness.
5. Add normalized external-job connector interface.
6. Add one public API integration with throttling and retries.
7. Add Temporal workflow integration for imports/analysis.
8. Add Puppeteer end-to-end QA.
9. Add Docker Compose verification and deployment hardening.
10. Add AWS-ready architecture docs/infrastructure.

The first task is auth/session hardening because external connectors, job imports, automation workflows, and recruiter/candidate data exposure all depend on a trustworthy security boundary.

## 1. Strong Candidate and Recruiter Role Isolation

### Why it matters

Role isolation is already partially implemented and tested, but production hardening is needed before adding external automation. `X-User-Id` fallback and weak password hashing are the largest current risks.

### Existing files likely to change

- `backend/app/security.py`
- `backend/app/main.py`
- `backend/app/config.py`
- `backend/app/schemas.py`
- `backend/tests/test_api.py`
- `frontend/lib/api.ts`

### New files likely required

- Possibly `backend/app/auth.py`
- Possibly Alembic migration for password hash metadata if changing hash format.

### Main risks

- Breaking existing tests that use `X-User-Id`.
- Locking users out if password hash migration is not backward compatible.
- Frontend session handling may need migration.

### Dependencies

- Existing bearer token generation and role checks.
- Test strategy for local/test auth fallback.

### Acceptance criteria

- Production mode rejects `X-User-Id` without bearer token.
- Tests can still use a clearly marked test auth mode.
- Password hashing uses a slow salted algorithm or documented transitional compatibility.
- Candidate/recruiter/admin authorization tests still pass.

## 2. Recruiter Company Profiles

### Why it matters

Company profiles already exist in the backend and partial recruiter UI. Completing the UI fields improves trust and supports safer job publishing.

### Existing files likely to change

- `frontend/app/page.tsx`
- `frontend/lib/api.ts`
- `backend/app/schemas.py`
- `backend/tests/test_api.py`

### New files likely required

- Optional frontend component files if the large page is split in a scoped way.

### Main risks

- Unrelated frontend refactor creep.
- Validation mismatch between frontend and backend.

### Dependencies

- Existing `Recruiter` model and `/recruiter/profile` endpoint.

### Acceptance criteria

- Recruiter can edit all company profile fields visible in backend model.
- Frontend displays company status and trust score.
- Backend validation errors are visible in the UI.
- Tests cover invalid website/contact email.

## 3. Company Verification Workflow

### Why it matters

Verified companies are required before publishing jobs. Current admin backend exists, but no admin UI exists.

### Existing files likely to change

- `frontend/app/page.tsx`
- `frontend/lib/api.ts`
- `backend/tests/test_api.py`

### New files likely required

- Optional `frontend/components/AdminDashboard.tsx` if component extraction is kept small.

### Main risks

- Admin role may become too powerful without audit logs.
- UI could expose admin actions to non-admins if backend checks are not relied on.

### Dependencies

- Existing `/admin/companies` and `/admin/companies/{recruiter_user_id}/review`.

### Acceptance criteria

- Admin can list pending/rejected/verified companies.
- Admin can approve/reject company verification.
- Non-admin users cannot access admin actions.
- Tests prove backend enforcement remains intact.

## 4. Job-Posting Verification Workflow

### Why it matters

Job quality and spam scoring exist but recruiter feedback is limited. A clear pre-publish workflow demonstrates automation safety and trust.

### Existing files likely to change

- `frontend/app/page.tsx`
- `frontend/lib/api.ts`
- `backend/app/trust.py`
- `backend/tests/test_api.py`

### New files likely required

- Optional `backend/app/job_quality.py` if trust logic grows.

### Main risks

- Overblocking legitimate jobs.
- Presenting heuristic scores as definitive fraud detection.

### Dependencies

- Existing spam score, quality score, publish block.

### Acceptance criteria

- Recruiter sees spam reasons and quality tips before publishing.
- High spam score blocks publishing with actionable fixes.
- Draft save still works for unverified recruiters/companies.
- Tests cover publish allowed/blocked paths.

## 5. Common Normalized Job Data Model

### Why it matters

External job imports and internal recruiter-created jobs need a common shape for deduplication, search, matching, and trust scoring.

### Existing files likely to change

- `backend/app/models.py`
- `backend/app/schemas.py`
- `backend/app/main.py`
- `backend/alembic/versions/*`
- `frontend/lib/api.ts`

### New files likely required

- `backend/app/job_normalization.py`

### Main risks

- Migration complexity.
- Breaking existing job-post UI and tests.

### Dependencies

- Current `JobPost` model.

### Acceptance criteria

- Existing job posts still work.
- Normalized fields exist for provider/source, external id, canonical title, canonical company, location, remote flag, salary min/max/currency, and source URL.
- Tests verify normalization from recruiter-created jobs.

## 6. External Job-Provider Connector Interface

### Why it matters

Connector boundaries demonstrate REST/API integration while preventing ad hoc scraping.

### Existing files likely to change

- `backend/app/config.py`
- `backend/app/main.py`
- `backend/tests/test_api.py`

### New files likely required

- `backend/app/connectors/base.py`
- `backend/app/connectors/public_jobs.py`
- `backend/app/services/job_imports.py`

### Main risks

- Accidentally implementing scraping against sites that disallow it.
- Connector contract too broad before one provider is understood.

### Dependencies

- Normalized job model.

### Acceptance criteria

- Connector interface returns normalized job DTOs.
- No browser automation is used for imports.
- Provider errors are surfaced without crashing the API.
- Tests use mocked HTTP responses.

## 7. One Initial Public API Integration

### Why it matters

A real API integration demonstrates HTTP fundamentals, normalization, error handling, and product value.

### Existing files likely to change

- `backend/app/connectors/*`
- `backend/app/services/job_imports.py`
- `backend/tests/test_api.py`
- `README.md`

### New files likely required

- Provider-specific connector module.

### Main risks

- Public API availability/rate limits.
- Terms-of-service issues.
- Data quality mismatch.

### Dependencies

- Connector interface.
- Normalized job model.

### Acceptance criteria

- One documented public API can import jobs in test mode with mocked responses.
- Imported jobs store provider/source metadata.
- Failures are retried or reported according to policy.

## 8. Idempotent Job Imports

### Why it matters

Automation jobs can rerun due to retries or scheduling. Idempotency prevents duplicate job posts and duplicated side effects.

### Existing files likely to change

- `backend/app/models.py`
- `backend/app/main.py`
- `backend/alembic/versions/*`
- `backend/tests/test_api.py`

### New files likely required

- `backend/app/idempotency.py`

### Main risks

- Incorrect unique constraints causing false deduplication.
- Race conditions without transaction coverage.

### Dependencies

- Normalized job fields including source/provider/external id.

### Acceptance criteria

- Reimporting the same provider job updates or no-ops instead of duplicating.
- Tests prove repeated import calls produce one stored job.
- Idempotency key handling is documented.

## 9. Temporal Workflow Integration

### Why it matters

Temporal demonstrates durable automation workflows, retries, scheduling, and observability.

### Existing files likely to change

- `docker-compose.yml`
- `backend/requirements.txt`
- `README.md`
- `.github/workflows/ci.yml`

### New files likely required

- `backend/app/workflows/job_import_workflow.py`
- `backend/app/workers/temporal_worker.py`
- `backend/app/activities/job_import_activities.py`

### Main risks

- Large operational dependency.
- Hard to run in CI if introduced too early.

### Dependencies

- Idempotent import service.
- Connector interface.

### Acceptance criteria

- Local Docker Compose starts Temporal services.
- Worker runs an import workflow against mocked provider data.
- Workflow retries transient failures.
- Tests cover activity logic without requiring live Temporal where possible.

## 10. Request Throttling and Retries

### Why it matters

External APIs need respectful rate limits and resilient retry behavior.

### Existing files likely to change

- `backend/app/connectors/*`
- `backend/app/config.py`
- `backend/tests/test_api.py`

### New files likely required

- `backend/app/http_client.py`
- `backend/app/rate_limit.py`

### Main risks

- Global throttling that blocks normal user actions.
- Tests becoming slow due to real sleeps.

### Dependencies

- Connector interface.

### Acceptance criteria

- HTTP client has timeout, retry, and backoff policy.
- Provider rate-limit response is handled.
- Tests use fake clocks or mocked clients.

## 11. Puppeteer End-to-End QA Tests

### Why it matters

Puppeteer demonstrates QA automation skills without using browser automation for unauthorized scraping.

### Existing files likely to change

- `frontend/package.json`
- `.github/workflows/ci.yml`
- `README.md`

### New files likely required

- `frontend/tests/e2e/*.test.mjs`
- `frontend/tests/e2e/helpers/*`

### Main risks

- Flaky tests if backend/dev server setup is not controlled.
- Large screenshots or generated artifacts accidentally committed.

### Dependencies

- Stable local backend/frontend startup commands.
- Test data setup API helpers.

### Acceptance criteria

- Puppeteer test covers role selection, candidate login, resume save, and AI tool display.
- Puppeteer test covers recruiter login and draft job save.
- CI can run E2E or a documented local command can run it reliably.

## 12. Structured Logging and Correlation IDs

### Why it matters

Automation systems need traceability across frontend requests, backend logs, external API calls, and workflows.

### Existing files likely to change

- `backend/app/main.py`
- `frontend/lib/api.ts`
- `backend/tests/test_api.py`

### New files likely required

- `backend/app/logging.py`
- `backend/app/middleware.py`

### Main risks

- Logging sensitive personal data.
- Inconsistent correlation ID propagation.

### Dependencies

- None; can be done early.

### Acceptance criteria

- Every API response includes or echoes `X-Correlation-ID`.
- Backend logs structured request metadata without PII-heavy payloads.
- Frontend sends a correlation ID for API requests.
- Tests verify header propagation.

## 13. Docker-Based Local Environment

### Why it matters

Docker demonstrates repeatable local setup and is required before Temporal/Postgres/worker workflows become practical.

### Existing files likely to change

- `docker-compose.yml`
- `frontend/Dockerfile`
- `backend/Dockerfile`
- `README.md`

### New files likely required

- `.dockerignore`
- `scripts/wait-for-services.sh`

### Main risks

- Breaking current manual local setup.
- Slow rebuilds.

### Dependencies

- Current Docker Compose.

### Acceptance criteria

- `docker compose up --build` starts frontend, backend, and Postgres.
- Frontend Docker image runs a proper build before `next start`.
- Health check documents expected URLs.
- CI or local script verifies container boot.

## 14. CI/CD Verification

### Why it matters

CI already exists, but automation work requires broader checks.

### Existing files likely to change

- `.github/workflows/ci.yml`
- `README.md`

### New files likely required

- Optional `.github/workflows/e2e.yml`

### Main risks

- CI time/cost increasing too quickly.
- Secrets accidentally required for CI.

### Dependencies

- Stable install/build/test commands.
- Optional Puppeteer tests.

### Acceptance criteria

- CI includes backend tests/lint/migration and frontend lint/test/build.
- Optional E2E job is isolated and documented.
- No real external API keys are required for ordinary CI.

## 15. AWS-Ready Deployment Architecture

### Why it matters

AWS readiness demonstrates production deployment thinking without forcing immediate cloud spend.

### Existing files likely to change

- `README.md`
- `docs/architecture.md` or deployment docs.

### New files likely required

- `docs/aws-deployment.md`
- Optional infrastructure placeholders after approval, such as Terraform or CDK.

### Main risks

- Overengineering beyond portfolio needs.
- Introducing IaC without account-specific validation.

### Dependencies

- Dockerized backend/frontend.
- Database and env var documentation.

### Acceptance criteria

- Architecture diagram covers CloudFront/S3 or Amplify for frontend, ECS/App Runner/Lambda container for backend, RDS Postgres, Secrets Manager, CloudWatch, and CI/CD path.
- No AWS credentials are committed.
- Deployment doc separates verified local behavior from proposed cloud architecture.
