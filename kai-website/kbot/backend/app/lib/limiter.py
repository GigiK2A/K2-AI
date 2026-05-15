"""Shared SlowAPI Limiter instance.

Kept in its own module to avoid circular imports between api/* and main.py.
"""
from __future__ import annotations

from slowapi import Limiter
from slowapi.util import get_remote_address

limiter = Limiter(key_func=get_remote_address)
