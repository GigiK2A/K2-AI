from __future__ import annotations

from dataclasses import dataclass
from enum import Enum, auto

from aios.autonomy import ActionType, AutonomyLevel, DEFAULT_PROMOTION_THRESHOLD


class Decision(Enum):
    DENY = auto()
    PROPOSE = auto()
    EXECUTE = auto()


@dataclass
class PolicyState:
    level: AutonomyLevel = AutonomyLevel.L0_OBSERVE
    streak: int = 0
    capped_at: AutonomyLevel = AutonomyLevel.L3_AUTO


class PolicyEngine:
    def __init__(self, *, promotion_threshold: int = DEFAULT_PROMOTION_THRESHOLD,
                 store=None) -> None:
        if store is None:
            from aios.store.memory import InMemoryPolicyStateStore
            store = InMemoryPolicyStateStore()
        self._store = store
        self._threshold = promotion_threshold

    def _state(self, action: ActionType) -> PolicyState:
        return self._store.get(action.key)

    def level_for(self, action: ActionType) -> AutonomyLevel:
        return self._state(action).level

    def set_level(self, action: ActionType, level: AutonomyLevel) -> None:
        state = self._state(action)
        state.level = level
        state.streak = 0
        self._store.save(action.key, state)

    def decide(self, action: ActionType) -> Decision:
        level = self.level_for(action)
        if level == AutonomyLevel.L0_OBSERVE:
            return Decision.DENY
        if level == AutonomyLevel.L1_PROPOSE:
            return Decision.PROPOSE
        return Decision.EXECUTE

    def set_cap(self, action: ActionType, cap: AutonomyLevel) -> None:
        state = self._state(action)
        state.capped_at = cap
        self._store.save(action.key, state)

    def record_outcome(self, action: ActionType, *, clean: bool) -> None:
        state = self._state(action)
        if not clean:
            state.streak = 0
            self._store.save(action.key, state)
            return
        state.streak += 1
        if (state.level == AutonomyLevel.L1_PROPOSE
                and state.capped_at >= AutonomyLevel.L2_ROUTINE
                and state.streak >= self._threshold):
            state.level = AutonomyLevel.L2_ROUTINE
            state.streak = 0
        self._store.save(action.key, state)
