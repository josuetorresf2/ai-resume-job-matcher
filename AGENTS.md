# FairHire AI Agent Rules

These rules apply to future coding agents working in this repository.

## Start Here

- Read `docs/current-architecture.md` before modifying code.
- Read `docs/automation-upgrade-plan.md` and `TASKS.md` before selecting implementation work.
- Preserve current working behavior unless the task explicitly changes it.
- Work on one vertical slice at a time.
- Avoid unrelated refactors.

## Engineering Standards

- Use TypeScript for frontend code.
- Use Python type hints for backend code.
- Prefer existing patterns, scripts, tests, and conventions before adding abstractions.
- Add comments only when they clarify non-obvious behavior.
- Validate all external input at the backend boundary.
- Enforce authorization in the backend, not only in the UI.
- Add tests for new functionality and bug fixes.
- Never edit, weaken, skip, or delete tests to make work pass.

## Verification

- Run available lint, type-check, test, and build commands relevant to the files changed.
- Never claim a command passed unless terminal output confirms it.
- If a command fails, record the exact command, relevant error, likely cause, and recommended fix.
- For deployment, auth, migrations, and user-data access changes, widen verification beyond the happy path.

## Security and Automation Boundaries

- Keep secrets out of Git. Use `.env` locally and deployment/GitHub secrets for CI or production.
- Do not invent secrets, endpoints, schemas, product decisions, or external account state.
- Do not implement CAPTCHA bypassing, credential attacks, unauthorized scraping, or security-control evasion.
- Prefer documented public APIs over browser automation.
- Use Puppeteer only for FairHire QA and controlled local testing unless the user explicitly authorizes a compliant external test target.
- Record limitations honestly, especially around mock auth, verification placeholders, AI fallbacks, and deployment state.
