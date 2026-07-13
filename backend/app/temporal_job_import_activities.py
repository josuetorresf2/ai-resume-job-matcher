from __future__ import annotations

import httpx
from temporalio import activity

from .database import SessionLocal
from .job_connectors import MockJobConnector, RemotiveJobConnector
from .job_imports import import_jobs_from_connector
from .temporal_job_import_types import JobImportWorkflowInput, JobImportWorkflowResult


@activity.defn
async def run_job_import_activity(payload: JobImportWorkflowInput) -> JobImportWorkflowResult:
    db = SessionLocal()
    try:
        if payload.provider == "mock":
            connector = MockJobConnector()
        elif payload.provider == "remotive":
            connector = RemotiveJobConnector(query=payload.query, limit=payload.limit)
        else:
            raise ValueError(f"Unsupported job import provider: {payload.provider}")

        try:
            imported, skipped = import_jobs_from_connector(
                db,
                connector,
                owner_user_id=payload.owner_user_id,
                publish=payload.publish,
            )
        except (ValueError, httpx.HTTPError) as exc:
            raise RuntimeError(f"{connector.provider} import failed: {exc}") from exc

        return JobImportWorkflowResult(
            provider=connector.provider,
            imported_count=len(imported),
            skipped_count=skipped,
        )
    finally:
        db.close()
