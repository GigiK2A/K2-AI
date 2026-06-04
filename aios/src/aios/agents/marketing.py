from __future__ import annotations

import json
import re
from dataclasses import dataclass

from aios.autonomy import ActionType, AutonomyLevel
from aios.kernel import Kernel
from aios.founder import FounderModel
from aios.llm import LLM
from aios.tools import Tool
from aios.skills import SkillLibrary

PROPOSE_ACTION = ActionType("marketing", "content.proposta")

_SYSTEM = (
    "Sei il responsabile marketing di K2-AI. Lavori SEMPRE rispettando il "
    "Founder Model qui sotto (voce, priorità, regole). Non pubblichi nulla: "
    "PROPONI soltanto, ogni proposta è una bozza da far approvare.\n\n"
    "Rispondi ESCLUSIVAMENTE con JSON valido nella forma:\n"
    '{"proposte": [{"tipo": "nuovo_tema|caption|calendario|fix", '
    '"titolo": "...", "contenuto": "...", "motivo": "..."}]}\n'
    "Niente testo fuori dal JSON."
)


@dataclass
class MarketingResult:
    approval_ids: list[int]
    proposals: list[dict]


def _extract_json(text: str) -> dict:
    t = text.strip()
    # 1) try the whole thing as-is (covers values that contain backticks)
    try:
        return json.loads(t)
    except json.JSONDecodeError:
        pass
    # 2) fenced ```json ... ``` or ``` ... ```
    m = re.search(r"```(?:json)?\s*(.*?)```", t, re.DOTALL)
    if m:
        try:
            return json.loads(m.group(1).strip())
        except json.JSONDecodeError:
            t = m.group(1).strip()
    # 3) outermost braces slice
    a, b = t.find("{"), t.rfind("}")
    if a >= 0 and b > a:
        return json.loads(t[a:b + 1])
    raise ValueError("nessun oggetto JSON trovato nella risposta")


def propose_tool() -> Tool:
    return Tool(name="proponi_marketing", action_type=PROPOSE_ACTION,
                run=lambda **payload: {"accettata": True, **payload})


class MarketingAgent:
    def __init__(self, *, kernel: Kernel, llm: LLM, founder: FounderModel,
                 skills: SkillLibrary | None = None,
                 actor: str = "marketing_agent") -> None:
        self.k = kernel
        self.llm = llm
        self.founder = founder
        self.skills = skills
        self.actor = actor
        if "proponi_marketing" not in self.k.tools.names():
            self.k.register_tool(propose_tool())
        self.k.policy.set_level(PROPOSE_ACTION, AutonomyLevel.L1_PROPOSE)
        self.k.policy.set_cap(PROPOSE_ACTION, AutonomyLevel.L1_PROPOSE)

    def _gather(self) -> dict:
        def read(name, **a):
            return self.k.execute(name, actor=self.actor, args=a).result
        return {
            "servizi": read("leggi_servizi"),
            "topics": read("leggi_topics"),
            "profilo_ig": read("leggi_profilo_ig"),
            "post_ig": read("leggi_post_ig", limit=10),
        }

    def run(self) -> MarketingResult:
        data = self._gather()
        user = (
            self.founder.to_prompt()
            + "\n\n# DATI REALI ATTUALI\n"
            + "## Servizi (tabella contenuti)\n" + json.dumps(data["servizi"], ensure_ascii=False)
            + "\n## Temi blog\n" + json.dumps(data["topics"], ensure_ascii=False)
            + "\n## Profilo Instagram\n" + json.dumps(data["profilo_ig"], ensure_ascii=False)
            + "\n## Ultimi post Instagram\n" + json.dumps(data["post_ig"], ensure_ascii=False)
            + "\n\nValuta cosa funziona e cosa no, poi proponi miglioramenti "
              "concreti (nuovi temi ad alto potenziale, caption migliori con numeri, "
              "calendario, fix). Massimo 5 proposte."
        )
        if self.skills is not None:
            user += (
                "\n\n# FRAMEWORK MARKETING DISPONIBILI\n"
                "Quando valuti e proponi, applica i framework più pertinenti tra questi "
                "(sono competenze di marketing che possiedi):\n"
                + self.skills.menu()
            )
        raw = self.llm.complete(system=_SYSTEM, user=user)
        try:
            parsed = _extract_json(raw)
        except (json.JSONDecodeError, ValueError) as exc:
            raise ValueError(
                f"LLM ha risposto con JSON non valido: {raw[:200]!r}") from exc
        proposals = parsed.get("proposte", [])
        ids: list[int] = []
        for p in proposals:
            res = self.k.execute("proponi_marketing", actor=self.actor, args=p)
            if res.approval_id is not None:
                ids.append(res.approval_id)
        return MarketingResult(approval_ids=ids, proposals=proposals)
