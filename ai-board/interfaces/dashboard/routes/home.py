"""Legacy shim — home logic moved to `controllers.home_controller`.

Preserved so external imports (`from interfaces.dashboard.routes import home`)
keep working. New code should import from `controllers` / `services` directly.
"""

from controllers.home_controller import router  # noqa: F401
from services import HomeService

_service = HomeService()


def _load_home_data() -> dict:
    """Legacy helper — delegates to `HomeService.load_home_data`."""
    return _service.load_home_data()


__all__ = ["router", "_load_home_data"]
