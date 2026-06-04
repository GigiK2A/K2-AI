from __future__ import annotations

import os


class MissingDSNError(RuntimeError):
    """Raised when a required database DSN env var is not set."""


def dsn_from_env(var_name: str) -> str:
    dsn = os.environ.get(var_name)
    if not dsn:
        raise MissingDSNError(f"environment variable {var_name} is not set")
    return dsn
