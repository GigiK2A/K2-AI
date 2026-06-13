from __future__ import annotations


class KillSwitch:
    def __init__(self) -> None:
        self._engaged = False
        self._reason: str | None = None

    @property
    def engaged(self) -> bool:
        return self._engaged

    @property
    def reason(self) -> str | None:
        return self._reason

    def engage(self, *, reason: str) -> None:
        self._engaged = True
        self._reason = reason

    def release(self) -> None:
        self._engaged = False
        self._reason = None
