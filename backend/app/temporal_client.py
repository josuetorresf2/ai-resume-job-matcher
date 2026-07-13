from __future__ import annotations

import uuid

from .config import Settings
from .temporal_job_import_types import JobImportWorkflowInput


async def start_job_import_workflow(
    settings: Settings,
    provider: str,
    owner_user_id: int,
    publish: bool,
    query: str,
    limit: int,
) -> tuple[str, str]:
    from temporalio.client import Client

    from .temporal_job_import_workflows import JobImportWorkflow

    client = await Client.connect(settings.temporal_address, namespace=settings.temporal_namespace)
    workflow_id = f"fairhire-job-import-{provider}-{uuid.uuid4()}"
    handle = await client.start_workflow(
        JobImportWorkflow.run,
        JobImportWorkflowInput(
            provider=provider,
            owner_user_id=owner_user_id,
            publish=publish,
            query=query,
            limit=limit,
        ),
        id=workflow_id,
        task_queue=settings.temporal_task_queue,
    )
    return workflow_id, handle.result_run_id or ""
