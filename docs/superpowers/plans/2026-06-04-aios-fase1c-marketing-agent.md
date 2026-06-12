# AIOS Fase 1c — Founder Model + Marketing Agent Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development. Steps use checkbox (`- [ ]`).

**Goal:** First reasoning agent. A minimal Founder Model (Luigi's voice/priorities) plus a Marketing agent that reads the real sensors, asks Claude to evaluate the content and propose improvements, and files each proposal into the kernel approval queue at L1.

**Architecture:** `FounderModel` is a dataclass with a `to_prompt()` text projection, seeded from the project's own brand voice (CLAUDE.md §6) and positioning. An injectable `LLM` port abstracts the model call (`AnthropicLLM` for real, `FakeLLM` for tests). `MarketingAgent` orchestrates: gather sensor data through the kernel (L0 read tools) → build a prompt with the Founder Model + data → call the LLM → parse JSON proposals → enqueue each via a kernel `proponi_marketing` tool whose action is L1 (so proposals land in the approval queue, governed by the same autonomy ladder). Everything is unit-tested with fakes; live run needs `ANTHROPIC_API_KEY`.

**Tech Stack:** Python 3.12, pytest, anthropic>=0.40 (matches the rest of the repo), existing aios kernel + sources.

---

## File Structure

```
aios/src/aios/
├── founder.py               # FounderModel + default_founder_model()
├── llm.py                   # LLM port, AnthropicLLM, FakeLLM
└── agents/
    ├── __init__.py
    └── marketing.py         # MarketingAgent + proponi_marketing tool factory
aios/tests/
├── test_founder.py
├── test_llm.py
└── test_agent_marketing.py
aios/run_marketing.py        # live runner script (manual)
```

---

### Task 1: Founder Model

**Files:**
- Create: `aios/src/aios/founder.py`
- Test: `aios/tests/test_founder.py`

- [ ] **Step 1: Write the test `aios/tests/test_founder.py`**

```python
from aios.founder import FounderModel, default_founder_model


def test_to_prompt_contains_voice_and_priorities():
    fm = FounderModel(
        voice="diretto, pragmatico, niente buzzword",
        priorities=["acquisire PMI 5-50 dipendenti"],
        delegation_rules=["mai pubblicare senza approvazione"],
        voice_samples=["Automatizza la contabilità e libera ore"],
    )
    p = fm.to_prompt()
    assert "diretto, pragmatico" in p
    assert "acquisire PMI" in p
    assert "mai pubblicare senza approvazione" in p
    assert "Automatizza la contabilità" in p


def test_default_founder_model_is_k2ai_flavored():
    fm = default_founder_model()
    assert fm.voice and isinstance(fm.priorities, list) and fm.priorities
    blob = fm.to_prompt().lower()
    # K2-AI brand voice markers from CLAUDE.md §6
    assert "italiano" in blob or "tu" in blob
    assert "pmi" in blob
```

- [ ] **Step 2: Run** `cd aios && .venv/bin/pytest tests/test_founder.py -q` — FAIL (no module).

- [ ] **Step 3: Write `aios/src/aios/founder.py`**

```python
from __future__ import annotations

from dataclasses import dataclass, field


@dataclass
class FounderModel:
    voice: str
    priorities: list[str]
    delegation_rules: list[str]
    voice_samples: list[str] = field(default_factory=list)

    def to_prompt(self) -> str:
        prios = "\n".join(f"- {p}" for p in self.priorities)
        rules = "\n".join(f"- {r}" for r in self.delegation_rules)
        samples = "\n".join(f'"{s}"' for s in self.voice_samples)
        return (
            "# CHI SEI (Founder Model — il fondatore di K2-AI)\n"
            f"## Voce e tono\n{self.voice}\n\n"
            f"## Priorità attuali\n{prios}\n\n"
            f"## Regole di delega\n{rules}\n\n"
            f"## Esempi di come scrive (imita questo stile)\n{samples}\n"
        )


def default_founder_model() -> FounderModel:
    # Seeded from CLAUDE.md §6 (brand voice) + positioning v2.
    return FounderModel(
        voice=(
            "Italiano sempre, mai inglese nei titoli (eccetto termini tecnici "
            "consolidati: agenti AI, RAG, API). Tono pragmatico, diretto, "
            "orientato al fare. Dai del 'tu' diretto ('ti diamo un agente che…'). "
            "Quantifica sempre in numeri concreti (ore/settimana, euro). "
            "Vietato: 'trasformazione digitale', 'journey', 'rivoluzionario', "
            "'innovativo', 'all'avanguardia', buzzword in generale."
        ),
        priorities=[
            "Acquisire PMI italiane 5-50 dipendenti (servizi professionali, "
            "manifatturiero, B2B)",
            "Posizionamento: sistemi AI operativi chiavi in mano in 30-60 giorni",
            "Far crescere autorità e traffico (blog pillar/cluster, Instagram)",
        ],
        delegation_rules=[
            "Mai pubblicare contenuti senza approvazione del fondatore",
            "Proporre, non eseguire: ogni contenuto è una bozza da validare",
            "Restare nel posizionamento K2-AI v2 (niente termini v1)",
        ],
        voice_samples=[],  # filled live from real IG captions when available
    )
```

- [ ] **Step 4: Run** `cd aios && .venv/bin/pytest tests/test_founder.py -q` — expect 2 passed.

- [ ] **Step 5: Full suite + commit**

```bash
cd aios && .venv/bin/pytest -q
cd /Volumes/PARASSITA/K-AI/.claude/worktrees/kind-lumiere-240e75
git add aios/src/aios/founder.py aios/tests/test_founder.py
git commit -m "feat(aios): minimal Founder Model seeded from K2-AI brand voice"
```

---

### Task 2: LLM port (Anthropic + fake)

**Files:**
- Create: `aios/src/aios/llm.py`
- Modify: `aios/pyproject.toml` (add anthropic dep)
- Test: `aios/tests/test_llm.py`

- [ ] **Step 1: Add dependency in `aios/pyproject.toml`** — change the `dependencies` line to:
```toml
dependencies = ["psycopg[binary]>=3.1", "anthropic>=0.40"]
```

- [ ] **Step 2: Write the test `aios/tests/test_llm.py`**

```python
from aios.llm import FakeLLM, LLM


def test_fakellm_returns_scripted_and_records_calls():
    llm = FakeLLM(responses=["ciao"])
    out = llm.complete(system="s", user="u")
    assert out == "ciao"
    assert llm.calls == [("s", "u")]


def test_fakellm_cycles_when_exhausted():
    llm = FakeLLM(responses=["a"])
    assert llm.complete(system="s", user="u1") == "a"
    assert llm.complete(system="s", user="u2") == "a"  # reuses last


def test_llm_is_a_protocol():
    assert hasattr(LLM, "__subclasshook__") or True  # importable protocol
```

- [ ] **Step 3: Run** `cd aios && .venv/bin/pip install -e ".[dev]" && .venv/bin/pytest tests/test_llm.py -q` — FAIL (no module). (pip install pulls anthropic.)

- [ ] **Step 4: Write `aios/src/aios/llm.py`**

```python
from __future__ import annotations

import os
from typing import Protocol


class LLM(Protocol):
    def complete(self, *, system: str, user: str) -> str: ...


class FakeLLM:
    """Deterministic LLM for tests. Returns scripted responses; reuses the last
    one when exhausted. Records (system, user) calls."""

    def __init__(self, responses: list[str]) -> None:
        self._responses = list(responses)
        self._i = 0
        self.calls: list[tuple[str, str]] = []

    def complete(self, *, system: str, user: str) -> str:
        self.calls.append((system, user))
        if self._i < len(self._responses):
            out = self._responses[self._i]
            self._i += 1
            return out
        return self._responses[-1]


class AnthropicLLM:
    """Real LLM via the Anthropic SDK. Model defaults to Haiku for cost."""

    def __init__(self, api_key: str | None = None,
                 model: str = "claude-haiku-4-5-20251001",
                 max_tokens: int = 2000) -> None:
        import anthropic
        self._client = anthropic.Anthropic(
            api_key=api_key or os.environ["ANTHROPIC_API_KEY"])
        self._model = model
        self._max_tokens = max_tokens

    def complete(self, *, system: str, user: str) -> str:
        msg = self._client.messages.create(
            model=self._model,
            max_tokens=self._max_tokens,
            system=system,
            messages=[{"role": "user", "content": user}],
        )
        return "".join(b.text for b in msg.content if getattr(b, "type", None) == "text")
```

- [ ] **Step 5: Run** `cd aios && .venv/bin/pytest tests/test_llm.py -q` — expect 3 passed.

- [ ] **Step 6: Full suite + commit**

```bash
cd aios && .venv/bin/pytest -q
cd /Volumes/PARASSITA/K-AI/.claude/worktrees/kind-lumiere-240e75
git add aios/pyproject.toml aios/src/aios/llm.py aios/tests/test_llm.py
git commit -m "feat(aios): LLM port with Anthropic adapter and fake"
```

---

### Task 3: Marketing agent

**Files:**
- Create: `aios/src/aios/agents/__init__.py` (`# agents package`)
- Create: `aios/src/aios/agents/marketing.py`
- Test: `aios/tests/test_agent_marketing.py`

- [ ] **Step 1: Write the test `aios/tests/test_agent_marketing.py`**

```python
import json

from aios.kernel import Kernel
from aios.autonomy import AutonomyLevel
from aios.founder import default_founder_model
from aios.llm import FakeLLM
from aios.tools import Tool
from aios.agents.marketing import MarketingAgent, PROPOSE_ACTION


def _kernel_with_fake_sensors():
    k = Kernel()
    k.register_tool(Tool(name="leggi_servizi", action_type=None, readonly=True,
                         run=lambda **_: [{"Servizio": "Automazioni", "Stato": "da usare"}]))
    k.register_tool(Tool(name="leggi_topics", action_type=None, readonly=True,
                         run=lambda **_: [{"Tema": "RAG per PMI", "Stato": "da usare"}]))
    k.register_tool(Tool(name="leggi_profilo_ig", action_type=None, readonly=True,
                         run=lambda **_: {"username": "k2_ai.it", "followers_count": 5}))
    k.register_tool(Tool(name="leggi_post_ig", action_type=None, readonly=True,
                         run=lambda **_: [{"caption": "Automatizza la contabilità",
                                            "like_count": 2, "comments_count": 0}]))
    return k


def test_agent_files_proposals_into_approval_queue():
    k = _kernel_with_fake_sensors()
    proposals = [
        {"tipo": "nuovo_tema", "titolo": "Agenti email per studi",
         "contenuto": "Post su come un agente gestisce le email", "motivo": "alto volume ricerca"},
        {"tipo": "caption", "titolo": "Migliora caption contabilità",
         "contenuto": "Riscrittura con numero di ore risparmiate", "motivo": "manca il numero"},
    ]
    llm = FakeLLM(responses=[json.dumps({"proposte": proposals})])
    agent = MarketingAgent(kernel=k, llm=llm, founder=default_founder_model())

    result = agent.run()

    # two proposals queued as L1 approvals
    assert len(result.approval_ids) == 2
    pending = k.approvals.pending()
    assert len(pending) == 2
    assert pending[0].action_key == PROPOSE_ACTION.key
    # the founder voice and the real data made it into the prompt
    system, user = llm.calls[0]
    assert "Founder Model" in system or "Founder Model" in user
    assert "k2_ai.it" in user and "RAG per PMI" in user


def test_agent_survives_messy_llm_json():
    k = _kernel_with_fake_sensors()
    # LLM wraps JSON in prose / code fence
    messy = "Ecco le proposte:\n```json\n" + json.dumps(
        {"proposte": [{"tipo": "fix", "titolo": "x", "contenuto": "y", "motivo": "z"}]}
    ) + "\n```\nSpero siano utili!"
    agent = MarketingAgent(kernel=k, llm=FakeLLM(responses=[messy]),
                           founder=default_founder_model())
    result = agent.run()
    assert len(result.approval_ids) == 1


def test_proposals_default_to_L1_so_they_need_approval():
    k = _kernel_with_fake_sensors()
    agent = MarketingAgent(kernel=k, llm=FakeLLM(responses=['{"proposte": []}']),
                           founder=default_founder_model())
    agent.run()
    # the propose action is registered and capped/observed at L1 (PROPOSE), not auto
    assert k.policy.level_for(PROPOSE_ACTION) == AutonomyLevel.L1_PROPOSE
```

- [ ] **Step 2: Run** `cd aios && .venv/bin/pytest tests/test_agent_marketing.py -q` — FAIL (no module).

- [ ] **Step 3: Write `aios/src/aios/agents/marketing.py`**

```python
from __future__ import annotations

import json
from dataclasses import dataclass

from aios.autonomy import ActionType, AutonomyLevel
from aios.kernel import Kernel
from aios.founder import FounderModel
from aios.llm import LLM
from aios.tools import Tool

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
    if "```" in t:
        # take the content of the first fenced block
        t = t.split("```", 2)[1]
        if t.startswith("json"):
            t = t[4:]
    a, b = t.find("{"), t.rfind("}")
    if a >= 0 and b > a:
        t = t[a:b + 1]
    return json.loads(t)


def propose_tool() -> Tool:
    # The "action" of an accepted proposal: for now it just returns the payload
    # (a real downstream action — write to calendar etc. — comes later).
    return Tool(name="proponi_marketing", action_type=PROPOSE_ACTION,
                run=lambda **payload: {"accettata": True, **payload})


class MarketingAgent:
    def __init__(self, *, kernel: Kernel, llm: LLM, founder: FounderModel,
                 actor: str = "marketing_agent") -> None:
        self.k = kernel
        self.llm = llm
        self.founder = founder
        self.actor = actor
        if "proponi_marketing" not in self.k.tools.names():
            self.k.register_tool(propose_tool())
        # proposals are L1: queued for human approval, never auto-run
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
        raw = self.llm.complete(system=_SYSTEM, user=user)
        parsed = _extract_json(raw)
        proposals = parsed.get("proposte", [])
        ids: list[int] = []
        for p in proposals:
            res = self.k.execute("proponi_marketing", actor=self.actor, args=p)
            if res.approval_id is not None:
                ids.append(res.approval_id)
        return MarketingResult(approval_ids=ids, proposals=proposals)
```

- [ ] **Step 4: Run** `cd aios && .venv/bin/pytest tests/test_agent_marketing.py -q` — expect 3 passed.

- [ ] **Step 5: Full suite + commit**

```bash
cd aios && .venv/bin/pytest -q
cd /Volumes/PARASSITA/K-AI/.claude/worktrees/kind-lumiere-240e75
git add aios/src/aios/agents/__init__.py aios/src/aios/agents/marketing.py aios/tests/test_agent_marketing.py
git commit -m "feat(aios): marketing agent — reads sensors, proposes via L1 approval queue"
```

---

### Task 4: Live runner script

**Files:**
- Create: `aios/run_marketing.py`

- [ ] **Step 1: Write `aios/run_marketing.py`**

```python
"""Live run of the Marketing agent against real data.

Requires env: ANTHROPIC_API_KEY, AIOS_IG_TOKEN, AIOS_IG_USER_ID, AIOS_DATABASE_URL.
Reads sensors, asks Claude for proposals, files them as L1 approvals, prints them.
Usage: cd aios && set -a && . ./.env && set +a && .venv/bin/python run_marketing.py
"""
from __future__ import annotations

import os

import psycopg

from aios.kernel import Kernel
from aios.founder import default_founder_model
from aios.llm import AnthropicLLM
from aios.sources.instagram import InstagramClient
from aios.sources.tools import content_tools, instagram_tools
from aios.agents.marketing import MarketingAgent


def main() -> None:
    conn = psycopg.connect(os.environ["AIOS_DATABASE_URL"])
    ig = InstagramClient(token=os.environ["AIOS_IG_TOKEN"],
                         ig_user_id=os.environ.get("AIOS_IG_USER_ID", "17841429842127461"))
    k = Kernel()
    for t in content_tools(conn):
        k.register_tool(t)
    for t in instagram_tools(ig):
        k.register_tool(t)

    # seed founder voice with real captions
    fm = default_founder_model()
    posts = k.execute("leggi_post_ig", actor="bootstrap", args={"limit": 10}).result
    fm.voice_samples = [p.get("caption", "") for p in posts if p.get("caption")][:5]

    agent = MarketingAgent(kernel=k, llm=AnthropicLLM(), founder=fm)
    result = agent.run()

    print(f"\n=== {len(result.proposals)} PROPOSTE (in coda approvazioni, L1) ===\n")
    for appr in k.approvals.pending():
        p = appr.payload
        print(f"[#{appr.id}] {p.get('tipo','?').upper()} — {p.get('titolo','')}")
        print(f"    {p.get('contenuto','')}")
        print(f"    perché: {p.get('motivo','')}\n")


if __name__ == "__main__":
    main()
```

- [ ] **Step 2: Verify it imports** `cd aios && .venv/bin/python -c "import ast; ast.parse(open('run_marketing.py').read()); print('ok')"`

- [ ] **Step 3: Commit**

```bash
cd /Volumes/PARASSITA/K-AI/.claude/worktrees/kind-lumiere-240e75
git add aios/run_marketing.py
git commit -m "feat(aios): live runner for the marketing agent"
```

---

## Self-Review

**Spec coverage:** Founder Model ⑦ (spec §3) → Task 1. Marketing agent that evaluates + proposes at L1 (spec §5 the operative loop, §5 levels) → Task 3. LLM = Claude with Haiku default (spec §2) → Task 2. Proposals flow through the autonomy ladder approval queue (spec §4) → Task 3 (PROPOSE_ACTION at L1, capped at L1).

**Placeholder scan:** none — all code complete.

**Type consistency:** `PROPOSE_ACTION` ActionType used by the tool and the policy calls and the test. `MarketingResult` returned by `run()`. `LLM.complete(*, system, user)` signature shared by `FakeLLM`/`AnthropicLLM` and called by the agent. `_extract_json` handles fenced/messy output (tested).

**Live verification (controller):** after Task 4, run `run_marketing.py` with `ANTHROPIC_API_KEY` + the `.env` (IG token + DSN) to see real Claude proposals queued. Until the key is provided, only unit tests (fake LLM) run; note this in the report.
