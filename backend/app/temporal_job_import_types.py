from __future__ import annotations

from dataclasses import dataclass


@dataclass
class JobImportWorkflowInput:
    provider: str
    owner_user_id: int
    publish: bool = False
    query: str = "python"
    limit: int = 5


@dataclass
class JobImportWorkflowResult:
    provider: str
    imported_count: int
    skipped_count: int
