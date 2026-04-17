"""Service / use-case layer.

Services hold business logic: they orchestrate repositories, apply
transformations, and return plain data structures (dicts / DTOs) ready for
controllers to render. Controllers stay thin adapters.
"""

from services.agents_service import AgentsService
from services.home_service import HomeService

__all__ = ["AgentsService", "HomeService"]
