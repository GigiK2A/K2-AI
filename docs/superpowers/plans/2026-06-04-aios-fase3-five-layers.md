# AIOS Fase 3 — 5-layer structure + Verified Deliverable Plan

> **For agentic workers:** REQUIRED SUB-SKILL: superpowers:subagent-driven-development. Steps use `- [ ]`.

**Goal:** Formalize the AIOS into the 5 layers of the K2-OS schema (Contesto, Dati, Intelligence, Automazione, Sviluppo) under the Kernel orchestrator, mapping existing code and building the missing layers, plus a **Verified Deliverable** builder (markdown/PDF, every number with its source). Tech stays cloud (Claude + Supabase); we adopt the STRUCTURE, not the literal on-premise wording.

**Architecture:** New `aios.layers` package — one module per strato, each a thin orchestration over existing primitives + the new bits. An `AIOS` facade exposes the five layers + the orchestrator (kernel). New: a knowledge store (Context), a unified data view (Dati), an insight generator (Intelligence), a skill creator (Sviluppo), and a deliverable builder with source citations.

**Tech Stack:** Python 3.12, pytest, existing aios (kernel, sensors, agent, skills, llm), Supabase REST, reportlab/markdown for PDF (reuse pattern from kbot/blog).

---

### Task 1: Layer skeleton + Context & Data layers

**Files:** Create `aios/src/aios/layers/__init__.py`, `aios/src/aios/layers/context.py`, `aios/src/aios/layers/data.py`; Test `aios/tests/test_layers_core.py`.

- [ ] **Step 1: test `aios/tests/test_layers_core.py`**
```python
from aios.kernel import Kernel
from aios.tools import Tool
from aios.founder import default_founder_model
from aios.layers.context import ContextLayer
from aios.layers.data import DataLayer


def test_context_layer_includes_founder_and_knowledge():
    ctx = ContextLayer(founder=default_founder_model(),
                       knowledge=["Caso X: vinto in 30 giorni", "Norma Y si applica"])
    blob = ctx.assemble()
    assert "PMI" in blob              # founder priorities
    assert "Caso X" in blob           # knowledge injected


def test_data_layer_unified_view_reads_registered_sensors():
    k = Kernel()
    k.register_tool(Tool(name="leggi_servizi", action_type=None, readonly=True,
                         run=lambda **_: [{"Servizio": "A"}]))
    k.register_tool(Tool(name="leggi_profilo_ig", action_type=None, readonly=True,
                         run=lambda **_: {"followers_count": 5}))
    view = DataLayer(k).vista_unica()
    assert view["servizi"] == [{"Servizio": "A"}]
    assert view["profilo_ig"]["followers_count"] == 5
    # tools not registered are simply absent, no crash
    assert "leggi_inesistente" not in view
```

- [ ] **Step 2: run** `cd aios && .venv/bin/pytest tests/test_layers_core.py -q` → FAIL.

- [ ] **Step 3: `aios/src/aios/layers/__init__.py`** = `# AIOS layers (K2-OS schema): context, data, intelligence, automation, development`

- [ ] **Step 4: `aios/src/aios/layers/context.py`**
```python
from __future__ import annotations

from aios.founder import FounderModel


class ContextLayer:
    """Strato ① Contesto: chi siamo (Founder Model) + conoscenza di dominio
    (casi, norme, precedenti)."""

    def __init__(self, founder: FounderModel, knowledge: list[str] | None = None) -> None:
        self.founder = founder
        self.knowledge = list(knowledge or [])

    def assemble(self) -> str:
        out = self.founder.to_prompt()
        if self.knowledge:
            out += "\n\n# CONTESTO / CONOSCENZA\n" + "\n".join(f"- {k}" for k in self.knowledge)
        return out
```

- [ ] **Step 5: `aios/src/aios/layers/data.py`**
```python
from __future__ import annotations

from typing import Any

from aios.kernel import Kernel

# the read-only sensors that compose the unified data view, with optional args
_SENSORS = {
    "servizi": ("leggi_servizi", {}),
    "topics": ("leggi_topics", {}),
    "profilo_ig": ("leggi_profilo_ig", {}),
    "post_ig": ("leggi_post_ig", {"limit": 10}),
    "insight_ig": ("leggi_insight_ig", {}),
    "calendario": ("leggi_calendario", {}),
}


class DataLayer:
    """Strato ② Dati: vista unica sui sensori registrati nel kernel."""

    def __init__(self, kernel: Kernel) -> None:
        self.k = kernel

    def vista_unica(self) -> dict[str, Any]:
        names = set(self.k.tools.names())
        out: dict[str, Any] = {}
        for key, (tool, args) in _SENSORS.items():
            if tool in names:
                try:
                    out[key] = self.k.execute(tool, actor="data_layer", args=args).result
                except Exception as exc:
                    out[key] = {"error": str(exc)}
        return out
```

- [ ] **Step 6: run** → 2 passed. **Step 7:** full suite + commit
```bash
cd aios && .venv/bin/pytest -q
cd /Volumes/PARASSITA/K-AI/.claude/worktrees/kind-lumiere-240e75
git add aios/src/aios/layers/ aios/tests/test_layers_core.py
git commit -m "feat(aios): layer skeleton — Context (①) + Data (②) layers"
```

---

### Task 2: Intelligence layer (③) — insights

**Files:** Create `aios/src/aios/layers/intelligence.py`; Test `aios/tests/test_layer_intelligence.py`.

- [ ] **Step 1: test**
```python
from aios.llm import FakeLLM
from aios.layers.intelligence import IntelligenceLayer


def test_insights_returns_structured_points():
    llm = FakeLLM(responses=['{"insights": [{"titolo": "Engagement basso", "evidenza": "9 like su 5 post", "azione": "caption con numeri"}]}'])
    out = IntelligenceLayer(llm).insights(context="founder...", data={"insight_ig": {"reach": 182}})
    assert isinstance(out, list) and out[0]["titolo"] == "Engagement basso"
    sys, user = llm.calls[0]
    assert "182" in user   # data reached the prompt


def test_insights_robust_to_bad_json():
    out = IntelligenceLayer(FakeLLM(responses=["non json"])).insights(context="x", data={})
    assert out == []
```

- [ ] **Step 2: run** → FAIL.

- [ ] **Step 3: `aios/src/aios/layers/intelligence.py`**
```python
from __future__ import annotations

import json
from typing import Any

from aios.llm import LLM

_SYSTEM = ("Sei l'analista dell'AIOS K2. Dato il contesto e i dati reali, estrai "
           "gli insight che contano (cosa funziona, cosa no, perché) con evidenza e "
           "azione consigliata. Rispondi SOLO JSON: "
           '{"insights":[{"titolo":"...","evidenza":"...","azione":"..."}]}')


class IntelligenceLayer:
    """Strato ③ Intelligence: trasforma dati+contesto in insight con evidenza."""

    def __init__(self, llm: LLM) -> None:
        self.llm = llm

    def insights(self, *, context: str, data: dict[str, Any]) -> list[dict]:
        user = (context + "\n\n# DATI\n" + json.dumps(data, ensure_ascii=False)[:6000]
                + "\n\nEstrai 3-6 insight con evidenza dai numeri e azione.")
        try:
            parsed = self.llm.complete_json(system=_SYSTEM, user=user)
        except Exception:
            return []
        out = parsed.get("insights", [])
        return [i for i in out if isinstance(i, dict)] if isinstance(out, list) else []
```

- [ ] **Step 4: run** → 2 passed. **Step 5:** full suite + commit
```bash
cd aios && .venv/bin/pytest -q
git -C /Volumes/PARASSITA/K-AI/.claude/worktrees/kind-lumiere-240e75 add aios/src/aios/layers/intelligence.py aios/tests/test_layer_intelligence.py
git -C /Volumes/PARASSITA/K-AI/.claude/worktrees/kind-lumiere-240e75 commit -m "feat(aios): Intelligence layer (③) — insights with evidence"
```

---

### Task 3: Development layer (⑤) — skill creation

**Files:** Create `aios/src/aios/layers/development.py`; Test `aios/tests/test_layer_development.py`.

- [ ] **Step 1: test**
```python
import tempfile, pathlib
from aios.llm import FakeLLM
from aios.skills import SkillLibrary
from aios.layers.development import DevelopmentLayer


def test_create_skill_writes_skill_md(tmp_path):
    lib = SkillLibrary(base=tmp_path)
    llm = FakeLLM(responses=['{"name": "promo-estate", "skill_md": "---\\nname: promo-estate\\ndescription: campagne estive\\n---\\nContenuto skill"}'])
    dev = DevelopmentLayer(llm=llm, skills=lib)
    name = dev.create_skill("voglio una skill per le promozioni estive")
    assert name == "promo-estate"
    assert "promo-estate" in lib.names()
    assert "campagne estive" in lib.load("promo-estate")
```

- [ ] **Step 2: run** → FAIL.

- [ ] **Step 3: `aios/src/aios/layers/development.py`**
```python
from __future__ import annotations

import re

from aios.llm import LLM
from aios.skills import SkillLibrary

_SYSTEM = ("Crei nuove skill per l'AIOS K2 in stile Anthropic SKILL.md (frontmatter "
           "name+description, poi istruzioni). Rispondi SOLO JSON: "
           '{"name":"slug-kebab","skill_md":"---\\nname: ...\\ndescription: ...\\n---\\n<corpo>"}')


class DevelopmentLayer:
    """Strato ⑤ Sviluppo: crea nuove skill su misura, salvate nella libreria."""

    def __init__(self, *, llm: LLM, skills: SkillLibrary) -> None:
        self.llm = llm
        self.skills = skills

    def create_skill(self, descrizione: str) -> str:
        parsed = self.llm.complete_json(system=_SYSTEM, user="Richiesta: " + descrizione)
        name = re.sub(r"[^a-z0-9-]", "", str(parsed.get("name", "")).lower().replace(" ", "-"))
        body = parsed.get("skill_md", "")
        if not name or not body:
            raise ValueError("skill non valida dal modello")
        d = self.skills._base / name
        d.mkdir(parents=True, exist_ok=True)
        (d / "SKILL.md").write_text(body, encoding="utf-8")
        return name
```
(Uses `SkillLibrary._base`; if that attribute name differs, read `aios/src/aios/skills.py` and adapt to the real base-path attribute.)

- [ ] **Step 4: run** → 1 passed. **Step 5:** full suite + commit
```bash
cd aios && .venv/bin/pytest -q
git -C /Volumes/PARASSITA/K-AI/.claude/worktrees/kind-lumiere-240e75 add aios/src/aios/layers/development.py aios/tests/test_layer_development.py
git -C /Volumes/PARASSITA/K-AI/.claude/worktrees/kind-lumiere-240e75 commit -m "feat(aios): Development layer (⑤) — create custom skills"
```

---

### Task 4: Verified Deliverable builder (markdown + sources) + AIOS facade

**Files:** Create `aios/src/aios/layers/deliverable.py`, `aios/src/aios/layers/automation.py` (thin wrapper exposing the marketing agent as the automation layer), `aios/src/aios/aios.py` (AIOS facade); Test `aios/tests/test_deliverable.py`.

- [ ] **Step 1: test `aios/tests/test_deliverable.py`**
```python
from aios.layers.deliverable import build_deliverable


def test_deliverable_has_sections_and_sources():
    md = build_deliverable(
        titolo="Report Marketing K2-AI",
        insights=[{"titolo": "Engagement basso", "evidenza": "9 like su 5 post", "azione": "numeri nelle caption"}],
        proposte=[{"tipo": "caption", "titolo": "Caption con numero", "contenuto": "...", "motivo": "..."}],
        fonti=[{"campo": "9 like", "fonte": "Instagram Graph API", "valore": "total_interactions=9"}])
    assert "# Report Marketing K2-AI" in md
    assert "Engagement basso" in md
    assert "## Fonti" in md
    assert "Instagram Graph API" in md     # every number traceable
```

- [ ] **Step 2: run** → FAIL.

- [ ] **Step 3: `aios/src/aios/layers/deliverable.py`**
```python
from __future__ import annotations

from typing import Any


def build_deliverable(*, titolo: str, insights: list[dict] | None = None,
                      proposte: list[dict] | None = None,
                      fonti: list[dict] | None = None) -> str:
    """Strato output: Deliverable Verificato in markdown — ogni numero con la sua fonte."""
    parts = [f"# {titolo}\n"]
    if insights:
        parts.append("## Insight\n")
        for i in insights:
            parts.append(f"- **{i.get('titolo','')}** — {i.get('evidenza','')} "
                         f"→ _{i.get('azione','')}_")
        parts.append("")
    if proposte:
        parts.append("## Proposte\n")
        for p in proposte:
            parts.append(f"- **[{p.get('tipo','')}] {p.get('titolo','')}** — "
                         f"{p.get('contenuto','')}  \n  perché: {p.get('motivo','')}")
        parts.append("")
    parts.append("## Fonti\n")
    if fonti:
        for f in fonti:
            parts.append(f"- `{f.get('campo','')}` = {f.get('valore','')} "
                         f"(fonte: {f.get('fonte','')})")
    else:
        parts.append("- (nessuna fonte numerica dichiarata)")
    return "\n".join(parts) + "\n"
```

- [ ] **Step 4: `aios/src/aios/layers/automation.py`**
```python
from __future__ import annotations

from aios.agents.marketing import MarketingAgent


class AutomationLayer:
    """Strato ④ Automazione: esegue agenti/skill che producono deliverable."""

    def __init__(self, agent: MarketingAgent) -> None:
        self.agent = agent

    def run(self):
        return self.agent.run()
```

- [ ] **Step 5: `aios/src/aios/aios.py`** (the facade tying the 5 layers to the orchestrator)
```python
from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from aios.kernel import Kernel
from aios.layers.context import ContextLayer
from aios.layers.data import DataLayer
from aios.layers.intelligence import IntelligenceLayer


@dataclass
class AIOS:
    """K2-OS: orchestratore (Kernel) + i 5 strati."""
    kernel: Kernel
    context: ContextLayer
    data: DataLayer
    intelligence: IntelligenceLayer
    automation: Any = None      # AutomationLayer (optional)
    development: Any = None      # DevelopmentLayer (optional)

    def situazione(self) -> dict[str, Any]:
        """Vista d'insieme: dati unici + insight dal contesto."""
        d = self.data.vista_unica()
        ins = self.intelligence.insights(context=self.context.assemble(), data=d)
        return {"dati": d, "insight": ins}
```

- [ ] **Step 6: run** `cd aios && .venv/bin/pytest tests/test_deliverable.py -q` → 1 passed. Full suite + commit
```bash
cd aios && .venv/bin/pytest -q
git -C /Volumes/PARASSITA/K-AI/.claude/worktrees/kind-lumiere-240e75 add aios/src/aios/layers/deliverable.py aios/src/aios/layers/automation.py aios/src/aios/aios.py aios/tests/test_deliverable.py
git -C /Volumes/PARASSITA/K-AI/.claude/worktrees/kind-lumiere-240e75 commit -m "feat(aios): Verified Deliverable builder + Automation layer + AIOS facade (5 strati)"
```

---

## Self-Review
- The 5 strati of the schema are now explicit modules under `aios.layers`, orchestrated by the Kernel via the `AIOS` facade: ① context, ② data, ③ intelligence, ④ automation, ⑤ development, + Verified Deliverable output.
- Maps existing code (founder, sensors, marketing agent, skills) into the structure; adds the genuinely missing layers (knowledge-in-context, unified data view, insights, skill creation, deliverable-with-sources).
- "Ogni numero con la sua fonte": deliverable has a Fonti section keyed by field→value→source.
- Types: layers depend only on existing primitives; `complete_json` reused; FakeLLM works in tests.
- Deferred (next): PDF render of the deliverable (reportlab), persist knowledge base to Supabase (aios_knowledge), wire the AIOS facade into the cockpit + runner, source-grounding automation (auto-fill `fonti` from the data layer).
