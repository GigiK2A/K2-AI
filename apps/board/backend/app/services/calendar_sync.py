"""Google Calendar sync — stub.

Sprint 7+8 ships the placeholder only. The real OAuth flow + incremental sync
arrives with Sprint 9 (Giuseppina agent). Keeping the symbol present means the
rest of the codebase can already import it behind a feature flag.

See `GOOGLE-CALENDAR-SETUP.md` for what's required to flip this on.
"""
from __future__ import annotations

from typing import Any, Dict, List


def sync_meetings_from_google() -> List[Dict[str, Any]]:
    """Pull upcoming events from Google Calendar and upsert into `board_meetings`.

    Not implemented — requires OAuth client + refresh token (see settings stubs
    GOOGLE_CLIENT_ID / GOOGLE_CLIENT_SECRET / GOOGLE_REFRESH_TOKEN) and a
    `google-api-python-client` dependency we deliberately have NOT added yet to
    keep the image lean.
    """
    raise NotImplementedError(
        "Google Calendar sync is not implemented yet — see GOOGLE-CALENDAR-SETUP.md"
    )
