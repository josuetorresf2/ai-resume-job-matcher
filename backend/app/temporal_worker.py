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
    client = await connect_with_retry(settings.temporal_address, settings.temporal_namespace)
    worker = Worker(
        client,
        task_queue=settings.temporal_task_queue,
        workflows=[JobImportWorkflow],
        activities=[run_job_import_activity],
    )
    await worker.run()


async def connect_with_retry(address: str, namespace: str) -> Client:
    last_error: Exception | None = None
    for attempt in range(1, 31):
        try:
            return await Client.connect(address, namespace=namespace)
        except Exception as exc:  # Temporal can accept TCP before frontend is healthy.
            last_error = exc
            logging.warning("Temporal is not ready yet; retrying worker connection.", extra={"attempt": attempt})
            await asyncio.sleep(min(attempt, 5))
    raise RuntimeError(f"Temporal worker could not connect to {address}") from last_error


if __name__ == "__main__":
    asyncio.run(main())
