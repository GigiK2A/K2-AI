"""Data access layer.

Repositories encapsulate reads/writes toward persistence (Supabase/Notion).
Services depend on repositories, not on the raw clients, so business logic
stays decoupled from storage details.
"""

from repositories.agent_logs import AgentLogsRepository
from repositories.approvals import ApprovalsRepository
from repositories.pipeline import PipelineRepository
from repositories.tasks import TasksRepository

__all__ = [
    "AgentLogsRepository",
    "ApprovalsRepository",
    "PipelineRepository",
    "TasksRepository",
]
