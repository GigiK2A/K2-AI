from __future__ import annotations

from dataclasses import dataclass
from enum import IntEnum

DEFAULT_PROMOTION_THRESHOLD = 10


class AutonomyLevel(IntEnum):
    L0_OBSERVE = 0
    L1_PROPOSE = 1
    L2_ROUTINE = 2
    L3_AUTO = 3


@dataclass(frozen=True)
class ActionType:
    domain: str
    capability: str

    @property
    def key(self) -> str:
        return f"{self.domain}.{self.capability}"
