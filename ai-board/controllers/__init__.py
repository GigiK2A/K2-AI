"""HTTP controllers (FastAPI adapters).

Controllers parse HTTP requests, delegate to the service layer, and render
templates / JSON responses. They MUST NOT contain business logic or direct
database queries.
"""

from controllers.agents_controller import router as agents_router
from controllers.home_controller import router as home_router

__all__ = ["agents_router", "home_router"]
