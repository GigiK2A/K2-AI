from __future__ import annotations

import random
from typing import Any

from aios.kernel import Kernel
from aios.founder import default_founder_model
from aios.tools import Tool
from aios.agents.marketing import MarketingAgent, PROPOSE_ACTION
from aios.sim.world import SimWorld

_POOL = [
    {"tipo": "caption", "titolo": "Caption con numero", "contenuto": "Caso reale PMI: 70% email gestite, 5 ore/sett recuperate. Prenota call.", "motivo": "numeri concreti"},
    {"tipo": "nuovo_tema", "titolo": "Quando delegare all'AI", "contenuto": "3 segnali per delegare un task all'AI, con esempi per settore.", "motivo": "riduce obiezioni"},
    {"tipo": "fix", "titolo": "Togli buzzword", "contenuto": "Rimuovere #DigitalTransformation, aggiungere hashtag di settore e 1 numero.", "motivo": "brand voice"},
    {"tipo": "caption", "titolo": "Case study amministrazione", "contenuto": "Studio commercialista: 8 ore/sett su fatture, ridotte del 60% con la pipeline AI.", "motivo": "social proof"},
    {"tipo": "nuovo_tema", "titolo": "Agenti vs automazione", "contenuto": "Differenza pratica con ROI a 6 mesi, tabella comparativa.", "motivo": "posizionamento"},
    {"tipo": "caption", "titolo": "Reel formazione", "contenuto": "5 prompt copia-incolla per l'email aziendale, salva il post.", "motivo": "save-oriented"},
]


class SimLLM:
    """Deterministic stand-in LLM for the simulation: returns 1-3 varied proposte."""
    def __init__(self, seed: int = 0) -> None:
        self._rng = random.Random(seed)

    def complete(self, *, system: str, user: str) -> str:
        import json
        return json.dumps(self.complete_json(system=system, user=user))

    def complete_json(self, *, system: str, user: str, schema=None) -> dict:
        n = self._rng.randint(1, 3)
        picks = self._rng.sample(_POOL, n)
        return {"proposte": [dict(p) for p in picks], "voci_calendario": []}


def _sim_sensors(world: SimWorld) -> list[Tool]:
    return [
        Tool(name="leggi_servizi", action_type=None, readonly=True, run=lambda **_: []),
        Tool(name="leggi_topics", action_type=None, readonly=True, run=lambda **_: []),
        Tool(name="leggi_profilo_ig", action_type=None, readonly=True,
             run=lambda **_: {"username": "sim", "followers_count": world.followers,
                              "media_count": world.day}),
        Tool(name="leggi_post_ig", action_type=None, readonly=True, run=lambda **_: []),
        Tool(name="leggi_insight_ig", action_type=None, readonly=True,
             run=lambda **_: world.snapshot()),
    ]


def run_simulation(days: int = 21, seed: int = 0, approve_rate: float = 0.8) -> dict[str, Any]:
    rng = random.Random(seed)
    world = SimWorld(seed=seed, followers=50)
    k = Kernel()
    for t in _sim_sensors(world):
        k.register_tool(t)
    agent = MarketingAgent(kernel=k, llm=SimLLM(seed=seed),
                           founder=default_founder_model(), discover_competitors=False)
    timeline = []
    for _ in range(days):
        agent.run()
        for appr in list(k.approvals.pending()):
            if rng.random() < approve_rate:
                k.resolve_approval(appr.id, approve=True)
                world.publish(appr.payload)
            else:
                k.resolve_approval(appr.id, approve=False, reason="off")
        row = world.advance_day()
        row["autonomy"] = int(k.policy.level_for(PROPOSE_ACTION))
        timeline.append(row)
    return {"timeline": timeline, "seed": seed,
            "final_followers": world.followers, "final_leads": world.leads,
            "final_autonomy_level": int(k.policy.level_for(PROPOSE_ACTION))}


def _multiverse(days: int = 21, seeds=(1, 2, 3), approve_rate: float = 0.8):
    return [run_simulation(days=days, seed=s, approve_rate=approve_rate) for s in seeds]


run_simulation.multiverse = _multiverse
