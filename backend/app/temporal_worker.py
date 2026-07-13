from __future__ import annotations

import asyncio
import logging

from temporalio.client import Client
from temporalio.worker import Worker

from .config import get_settings
from .temporal_job_import_activities import run_job_import_activity
from .temporal_job_import_workflows import JobImportWorkflow


async def main() -> None:
    settings = get_settings()
    logging.basicConfig(level=logging.INFO)
    client = await Client.connect(settings.temporal_address, namespace=settings.temporal_namespace)
    worker = Worker(
        client,
        task_queue=settings.temporal_task_queue,
        workflows=[JobImportWorkflow],
        activities=[run_job_import_activity],
    )
    await worker.run()


if __name__ == "__main__":
    asyncio.run(main())
