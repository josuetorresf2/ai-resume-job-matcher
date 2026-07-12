# FairHire AI Automation Upgrade Tasks

Each task is a small vertical slice. Do not combine unrelated tasks in one pull request or commit unless explicitly approved.

## Task 1: Harden Authentication and Session Boundaries

Status: completed in `Harden auth session boundaries`.

### Goal

Make authentication safer for production while preserving local/test developer workflows.

### User-visible or operational result

Production deployments reject unsafe mock identity headers and rely on signed bearer tokens. Developers still have a documented test/local path.

### Scope

- Add explicit environment setting for auth mode, for example `AUTH_ALLOW_TEST_HEADER=false`.
- Disable `X-User-Id` fallback unless test/local mode is enabled.
- Add stronger password hashing or a backward-compatible migration path.
- Keep existing login/account creation behavior working.

### Tests

- Backend test: bearer token still authenticates.
- Backend test: `X-User-Id` works only when test header mode is enabled.
- Backend test: candidate/recruiter/admin authorization behavior remains unchanged.
- Backend test: wrong password still fails.

### Acceptance Criteria

- Existing API tests pass.
- New auth-mode tests pass.
- Production default does not accept `X-User-Id`.
- Documentation explains local/test auth behavior.

### Verification Commands

```bash
cd backend
pip install -r requirements.txt
ruff check app tests
pytest
DATABASE_URL=sqlite:////tmp/fairhire_auth_check.db alembic -c alembic.ini upgrade head
```

Completed verification:

- `cd backend && .venv/bin/ruff check app tests && .venv/bin/pytest && rm -f /tmp/fairhire_auth_check.db && DATABASE_URL=sqlite:////tmp/fairhire_auth_check.db .venv/bin/alembic -c alembic.ini upgrade head`
- `cd frontend && npm run lint && npm test && npx tsc --noEmit && npm run build:vercel`

## Task 2: Add Correlation IDs and Structured Request Logging

Status: completed in `Add correlation IDs to API requests`.

### Goal

Add traceability for API calls before adding external automations.

### User-visible or operational result

Each API response includes `X-Correlation-ID`, and logs can connect frontend actions to backend processing.

### Scope

- Add FastAPI middleware for request IDs.
- Accept incoming `X-Correlation-ID` or generate one.
- Return `X-Correlation-ID` in responses.
- Update frontend API client to send a correlation ID.
- Log method/path/status/duration/correlation ID without logging raw resumes or passwords.

### Tests

- Backend test for generated correlation ID.
- Backend test for echoing incoming correlation ID.
- Frontend unit/helper test if request helper is extracted.

### Acceptance Criteria

- Correlation ID appears in all API responses.
- Logs avoid sensitive request payloads.
- Existing frontend/backend behavior is unchanged.

### Verification Commands

```bash
cd backend
ruff check app tests
pytest
cd ../frontend
npm run lint
npm test
npm run build:vercel
```

Completed verification:

- `cd backend && .venv/bin/ruff check app tests && .venv/bin/pytest`
- `cd frontend && npm run lint && npm test && npx tsc --noEmit && npm run build:vercel`

## Task 3: Complete Recruiter Job Form Fields

Status: completed in `Complete recruiter job form fields`.

### Goal

Make the recruiter UI fully use the existing backend job-post model.

### User-visible or operational result

Recruiters can enter location, work mode, salary range, experience level, required skills, and nice-to-have skills from the UI.

### Scope

- Update recruiter dashboard form.
- Keep create/update job APIs unchanged unless validation gaps are found.
- Display quality tips and spam reasons clearly after save.

### Tests

- Backend tests remain unchanged or add field persistence test.
- Add frontend test if form helpers are extracted.

### Acceptance Criteria

- Recruiter-created jobs preserve all job fields.
- Quality/spam feedback remains visible.
- Existing publish rules still work.

### Verification Commands

```bash
cd backend
pytest
cd ../frontend
npm run lint
npm test
npm run build:vercel
```

Completed verification:

- `cd frontend && npm run lint && npm test && npx tsc --noEmit`
- `cd frontend && npm run build:vercel`
- `cd backend && .venv/bin/ruff check app tests && .venv/bin/pytest`
- Browser smoke test: recruiter dashboard showed location, work mode, salary range, experience level, required skills, and nice-to-have skills; saving a job showed the saved notice plus quality/spam feedback.

## Task 4: Add Admin Review UI

### Goal

Expose existing admin company and flagged-job backend functionality in the frontend.

### User-visible or operational result

Admin users can review companies and remove flagged jobs from the UI.

### Scope

- Add admin dashboard path/state in the existing app.
- Add frontend API wrappers for admin endpoints.
- Do not weaken backend admin checks.

### Tests

- Backend admin protection tests already exist; add missing cases if needed.
- Add targeted frontend logic tests if components/helpers are extracted.

### Acceptance Criteria

- Admin login shows admin workspace.
- Candidate/recruiter users do not see admin actions.
- Backend still returns 403 for non-admin direct requests.

### Verification Commands

```bash
cd backend
ruff check app tests
pytest
cd ../frontend
npm run lint
npm test
npm run build:vercel
```

## Task 5: Add Idempotent Match Creation

### Goal

Prevent duplicate analyses from repeated button clicks or retried requests.

### User-visible or operational result

Submitting the same resume/job match with the same idempotency key returns the original analysis instead of creating duplicates.

### Scope

- Define idempotency key header or payload.
- Add storage for idempotency records or unique match policy.
- Apply first to `/matches`.

### Tests

- Repeating same key returns same analysis.
- Different key can create a new analysis if intended.
- Unauthorized users cannot reuse another user's idempotency key.

### Acceptance Criteria

- Duplicate click/retry is safe for `/matches`.
- Behavior is documented.
- Existing match tests pass.

### Verification Commands

```bash
cd backend
ruff check app tests
pytest
DATABASE_URL=sqlite:////tmp/fairhire_idempotency.db alembic -c alembic.ini upgrade head
```

## Task 6: Define Normalized Job Data Model

### Goal

Prepare internal and imported jobs to share a common representation.

### User-visible or operational result

Recruiter-created jobs gain normalized metadata needed for search, matching, and future imports.

### Scope

- Add source/provider fields and canonical fields.
- Add Alembic migration.
- Backfill current recruiter-created jobs as internal source.

### Tests

- Migration upgrade test.
- Job create/list tests verify normalized defaults.

### Acceptance Criteria

- Existing jobs remain compatible.
- New fields are present and documented.
- PostgreSQL Alembic migration passes.

### Verification Commands

```bash
cd backend
ruff check app tests
pytest
DATABASE_URL=sqlite:////tmp/fairhire_normalized_jobs.db alembic -c alembic.ini upgrade head
```

## Task 7: Add External Job Connector Interface With Mock Provider

### Goal

Create the boundary for public API integrations without scraping.

### User-visible or operational result

Operators can run a safe mocked import path that normalizes jobs and reports import results.

### Scope

- Add connector protocol/interface.
- Add mock connector implementation.
- Add import service that accepts normalized jobs.

### Tests

- Mock connector returns normalized data.
- Import service validates and stores internal records.
- Error response is handled.

### Acceptance Criteria

- No browser automation is used.
- No real external API is required for tests.
- Imported jobs can be listed like existing jobs when published.

### Verification Commands

```bash
cd backend
ruff check app tests
pytest
```

## Task 8: Add One Public Job API Integration

### Goal

Demonstrate real REST API integration using the connector boundary.

### User-visible or operational result

FairHire can import jobs from one documented public API into draft or review status.

### Scope

- Choose a provider with documented terms and no scraping.
- Add connector implementation with timeout handling.
- Add mocked tests; do not require live network in CI.

### Tests

- Successful provider response import.
- Provider timeout/retryable failure.
- Invalid provider payload normalization failure.

### Acceptance Criteria

- CI uses mocked provider responses.
- Imported jobs include provider/source metadata.
- Documentation names the provider and limitations.

### Verification Commands

```bash
cd backend
ruff check app tests
pytest
```

## Task 9: Add Request Throttling and Retry Policy for Connectors

### Goal

Make external API usage respectful and resilient.

### User-visible or operational result

External imports retry transient errors and stop on rate-limit policies without hammering providers.

### Scope

- Add shared HTTP client wrapper.
- Add retry/backoff policy.
- Add per-provider throttle config.

### Tests

- Retries on 5xx.
- Does not retry non-retryable 4xx.
- Handles 429/rate-limit headers.

### Acceptance Criteria

- No real sleeps in tests.
- Connector code uses shared policy.
- Failures are logged with correlation ID after Task 2.

### Verification Commands

```bash
cd backend
ruff check app tests
pytest
```

## Task 10: Add Temporal Workflow for Job Imports

### Goal

Move long-running imports to a durable workflow.

### User-visible or operational result

An import workflow can be started and tracked locally.

### Scope

- Add Temporal dependency after documenting reason.
- Add worker, workflow, and activities for job import.
- Extend Docker Compose with Temporal services.

### Tests

- Unit tests for activities.
- Workflow test if Temporal test environment is practical.

### Acceptance Criteria

- Docker Compose can start Temporal stack.
- Worker runs without blocking API startup.
- Import activity is idempotent.

### Verification Commands

```bash
docker compose up --build
cd backend
pytest
```

## Task 11: Add Puppeteer E2E QA Tests

### Goal

Demonstrate browser automation for controlled QA.

### User-visible or operational result

One command validates core candidate and recruiter flows in a browser.

### Scope

- Add Puppeteer as a dev dependency.
- Add E2E scripts for local app.
- Use seeded test accounts/data.

### Tests

- Candidate flow: login, save resume, run AI tool.
- Recruiter flow: login, save draft job.

### Acceptance Criteria

- Tests do not scrape third-party sites.
- Tests do not bypass CAPTCHA or security controls.
- Screenshots/videos are ignored unless intentionally committed.

### Verification Commands

```bash
cd frontend
npm run e2e
```

## Task 12: Fix Frontend Docker Image

### Goal

Make the frontend container production-runnable.

### User-visible or operational result

`docker compose up --build` starts frontend/backend/Postgres from a clean clone.

### Scope

- Update frontend Dockerfile to run `npm ci` and `npm run build`.
- Use `npm run start` only after build.
- Add `.dockerignore` files.

### Tests

- Local Docker Compose smoke test.
- Optional CI Docker build job.

### Acceptance Criteria

- Frontend container starts without pre-existing `.next`.
- Backend health and frontend page respond.

### Verification Commands

```bash
docker compose up --build
curl http://localhost:8000/health
curl -I http://localhost:3000
```

## Task 13: Add AWS-Ready Deployment Documentation

### Goal

Document production deployment architecture without requiring AWS credentials.

### User-visible or operational result

Recruiters/hiring managers can see how FairHire would run on AWS.

### Scope

- Add architecture diagram.
- Document services, secrets, networking, logs, and deployment flow.
- Do not add account-specific secrets.

### Tests

- Documentation review only.

### Acceptance Criteria

- Diagram includes frontend, API, database, worker, secrets, logs, and CI/CD.
- Risks and cost controls are documented.

### Verification Commands

```bash
sed -n '1,240p' docs/aws-deployment.md
```
