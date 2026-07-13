from __future__ import annotations

from datetime import timedelta

from temporalio import workflow
from temporalio.common import RetryPolicy

from .temporal_job_import_types import JobImportWorkflowInput, JobImportWorkflowResult


@workflow.defn
class JobImportWorkflow:
    @workflow.run
    async def run(self, payload: JobImportWorkflowInput) -> JobImportWorkflowResult:
        return await workflow.execute_activity(
            "run_job_import_activity",
            payload,
            start_to_close_timeout=timedelta(minutes=5),
            retry_policy=RetryPolicy(maximum_attempts=3),
        )
