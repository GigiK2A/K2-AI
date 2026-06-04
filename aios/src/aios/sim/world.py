from __future__ import annotations

import random
import re
from dataclasses import dataclass, field
from typing import Any

_BUZZ = ("rivoluzionari", "trasformazione digitale", "all'avanguardia",
         "innovativ", "cutting-edge", "journey")
_VOICE = ("pmi", "ore", "agente", "automaz", "ai ", "email", "crm", "%", "euro", "€")


def content_quality(content: dict[str, Any]) -> float:
    """Transparent heuristic: numbers + on-voice keywords good; buzzwords bad. 0..1."""
    text = (str(content.get("contenuto", "")) + " " + str(content.get("titolo", ""))).lower()
    q = 0.45
    if re.search(r"\d", text):
        q += 0.25
    q += min(0.20, 0.05 * sum(1 for k in _VOICE if k in text))
    q -= 0.30 * sum(1 for b in _BUZZ if b in text)
    return max(0.0, min(1.0, q))


@dataclass
class SimWorld:
    seed: int = 0
    followers: int = 50
    day: int = 0
    leads: int = 0
    _pending_posts: list[dict] = field(default_factory=list)
    history: list[dict] = field(default_factory=list)
    _rng: random.Random = field(default=None, repr=False)

    def __post_init__(self):
        self._rng = random.Random(self.seed)

    def publish(self, content: dict[str, Any]) -> None:
        self._pending_posts.append(content)

    def advance_day(self) -> dict[str, Any]:
        self.day += 1
        reach = 0
        gained = 0
        day_leads = 0
        for post in self._pending_posts:
            q = content_quality(post)
            noise = 0.7 + 0.6 * self._rng.random()
            r = (self.followers * (0.30 + 0.9 * q) + 25 * q) * noise
            reach += int(r)
            gained += int(r * 0.012 * (0.4 + q))
            if self._rng.random() < q * 0.25:
                day_leads += 1
        reach += int(self.followers * 0.05 * self._rng.random())
        self.followers += gained
        self.leads += day_leads
        rec = {"day": self.day, "followers": self.followers, "reach": reach,
               "gained": gained, "leads_today": day_leads, "total_leads": self.leads,
               "posts": len(self._pending_posts)}
        self.history.append(rec)
        self._pending_posts = []
        return rec

    def snapshot(self) -> dict[str, Any]:
        last = self.history[-1] if self.history else {"reach": 0}
        return {"day": self.day, "followers": self.followers,
                "reach": last.get("reach", 0), "total_leads": self.leads}
