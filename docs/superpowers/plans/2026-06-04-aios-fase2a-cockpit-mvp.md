# AIOS Fase 2a — Cockpit MVP + competitor discovery Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development. Steps use checkbox (`- [ ]`).

**Goal:** A working command-cockpit: a FastAPI backend exposing the AIOS approval queue + overview, and a single dark cockpit page (mockup style) where Luigi sees the agent's proposals and clicks Approve / Edit / Reject — wired to the real Supabase-backed kernel. Plus: the agent discovers competitors itself instead of using a hardcoded list.

**Architecture:** `create_app(kernel)` builds a FastAPI app over an injected `Kernel` (Supabase-backed in prod, in-memory in tests). Endpoints read `aios_approvals` via `kernel.approvals` and resolve through `kernel.resolve_approval` (so approving updates audit + policy streak and runs the tool). A static `cockpit.html` (Tailwind CDN + vanilla JS, dark theme) calls the API. Competitor discovery: a web-search LLM proposes competitor IG @handles from the Founder Model, then `business_discovery` reads them — no hardcoded list.

**Tech Stack:** Python 3.12, pytest, FastAPI + uvicorn (new deps), existing aios kernel. Cockpit MVP uses Tailwind via CDN (internal tool; the production Next.js cockpit per the mockup comes later).

---

### Task 1: Competitor discovery (agent finds handles itself)

**Files:**
- Create: `aios/src/aios/sources/competitor_discovery.py`
- Test: `aios/tests/test_competitor_discovery.py`

- [ ] **Step 1: test**

```python
from aios.llm import FakeLLM
from aios.founder import default_founder_model
from aios.sources.competitor_discovery import discover_competitor_handles


def test_discovers_handles_from_llm_json():
    llm = FakeLLM(responses=['{"handles": ["studioalpha", "ai_partners_it", "pmi_digitale"]}'])
    handles = discover_competitor_handles(llm, default_founder_model(), max_handles=3)
    assert handles == ["studioalpha", "ai_partners_it", "pmi_digitale"]
    # the founder business context reached the prompt
    _, user = llm.calls[0]
    assert "PMI" in user


def test_strips_at_and_limits():
    llm = FakeLLM(responses=['{"handles": ["@one", "@two", "@three", "@four"]}'])
    handles = discover_competitor_handles(llm, default_founder_model(), max_handles=2)
    assert handles == ["one", "two"]


def test_bad_json_returns_empty():
    llm = FakeLLM(responses=["non lo so"])
    assert discover_competitor_handles(llm, default_founder_model()) == []
```

- [ ] **Step 2: run** `cd aios && .venv/bin/pytest tests/test_competitor_discovery.py -q` → FAIL.

- [ ] **Step 3: `aios/src/aios/sources/competitor_discovery.py`**

```python
from __future__ import annotations

import json
import re

from aios.founder import FounderModel
from aios.llm import LLM

_SYSTEM = (
    "Sei un analista di mercato. Dato il profilo dell'azienda, individua i "
    "competitor/riferimenti italiani che pubblicano su Instagram nello stesso "
    "spazio (AI operativa per PMI, automazione, studi/agenzie AI). "
    "Usa la ricerca web se disponibile. "
    'Rispondi SOLO con JSON: {"handles": ["handle1", "handle2", ...]} '
    "(handle Instagram senza @, niente altro testo)."
)


def discover_competitor_handles(llm: LLM, founder: FounderModel,
                                max_handles: int = 5) -> list[str]:
    user = (founder.to_prompt()
            + f"\n\nElenca fino a {max_handles} handle Instagram di competitor/"
              "riferimenti italiani pertinenti. Solo JSON.")
    raw = llm.complete(system=_SYSTEM, user=user)
    try:
        t = raw.strip()
        m = re.search(r"\{.*\}", t, re.DOTALL)
        data = json.loads(m.group(0) if m else t)
    except (json.JSONDecodeError, AttributeError, ValueError):
        return []
    handles = [str(h).lstrip("@").strip() for h in data.get("handles", [])]
    return [h for h in handles if h][:max_handles]
```

- [ ] **Step 4: run** `cd aios && .venv/bin/pytest tests/test_competitor_discovery.py -q` → 3 passed.
- [ ] **Step 5: full suite + commit**
```bash
cd aios && .venv/bin/pytest -q
cd /Volumes/PARASSITA/K-AI/.claude/worktrees/kind-lumiere-240e75
git add aios/src/aios/sources/competitor_discovery.py aios/tests/test_competitor_discovery.py
git commit -m "feat(aios): agent discovers competitor IG handles (no hardcoded list)"
```

---

### Task 2: Cockpit FastAPI backend

**Files:**
- Modify: `aios/pyproject.toml` (add fastapi + uvicorn + httpx for TestClient)
- Create: `aios/src/aios/api/__init__.py` (`# api package`)
- Create: `aios/src/aios/api/app.py`
- Test: `aios/tests/test_api.py`

- [ ] **Step 1: add deps in `aios/pyproject.toml`** — dependencies line becomes:
```toml
dependencies = ["psycopg[binary]>=3.1", "anthropic>=0.40", "fastapi>=0.110", "uvicorn>=0.29"]
```
and add to the dev extra: `dev = ["pytest>=8", "httpx>=0.27"]`

- [ ] **Step 2: test `aios/tests/test_api.py`**

```python
from fastapi.testclient import TestClient

from aios.kernel import Kernel
from aios.autonomy import ActionType, AutonomyLevel
from aios.tools import Tool
from aios.api.app import create_app

ACT = ActionType("marketing", "content.proposta")


def _kernel_with_one_pending():
    k = Kernel()
    calls = []
    k.register_tool(Tool(name="proponi_marketing", action_type=ACT,
                         run=lambda **kw: calls.append(kw) or {"ok": True}))
    k.policy.set_level(ACT, AutonomyLevel.L1_PROPOSE)
    k.policy.set_cap(ACT, AutonomyLevel.L1_PROPOSE)
    k.execute("proponi_marketing", actor="marketing_agent",
              args={"tipo": "caption", "titolo": "T", "contenuto": "C", "motivo": "M"})
    return k, calls


def test_overview_counts():
    k, _ = _kernel_with_one_pending()
    c = TestClient(create_app(k))
    r = c.get("/api/overview").json()
    assert r["pending_count"] == 1
    assert r["audit_count"] >= 1


def test_list_approvals():
    k, _ = _kernel_with_one_pending()
    c = TestClient(create_app(k))
    items = c.get("/api/approvals").json()
    assert len(items) == 1
    assert items[0]["payload"]["titolo"] == "T"
    assert items[0]["status"] == "PENDING"


def test_approve_runs_and_clears(_=None):
    k, calls = _kernel_with_one_pending()
    c = TestClient(create_app(k))
    aid = c.get("/api/approvals").json()[0]["id"]
    r = c.post(f"/api/approvals/{aid}/approve", json={})
    assert r.json()["outcome"] == "EXECUTED"
    assert calls == [{"tipo": "caption", "titolo": "T", "contenuto": "C", "motivo": "M"}]
    assert c.get("/api/approvals").json() == []


def test_reject_does_not_run():
    k, calls = _kernel_with_one_pending()
    c = TestClient(create_app(k))
    aid = c.get("/api/approvals").json()[0]["id"]
    r = c.post(f"/api/approvals/{aid}/reject", json={"reason": "off-brand"})
    assert r.json()["outcome"] == "DENIED"
    assert calls == []
    assert c.get("/api/approvals").json() == []


def test_edit_then_approve_uses_edited_payload():
    k, calls = _kernel_with_one_pending()
    c = TestClient(create_app(k))
    aid = c.get("/api/approvals").json()[0]["id"]
    c.post(f"/api/approvals/{aid}/approve",
           json={"edited_payload": {"tipo": "caption", "titolo": "T2"}})
    assert calls == [{"tipo": "caption", "titolo": "T2"}]


def test_root_serves_cockpit_html():
    k, _ = _kernel_with_one_pending()
    c = TestClient(create_app(k))
    r = c.get("/")
    assert r.status_code == 200 and "AI Operating System" in r.text
```

- [ ] **Step 3: run** `cd aios && .venv/bin/pip install -e ".[dev]" && .venv/bin/pytest tests/test_api.py -q` → FAIL (no module). (pip pulls fastapi/uvicorn/httpx.)

- [ ] **Step 4: `aios/src/aios/api/app.py`**

```python
from __future__ import annotations

from pathlib import Path
from typing import Any

from fastapi import FastAPI
from fastapi.responses import HTMLResponse
from pydantic import BaseModel

from aios.kernel import Kernel

_STATIC = Path(__file__).parent / "static"


class ResolveBody(BaseModel):
    edited_payload: dict[str, Any] | None = None
    reason: str | None = None


def create_app(kernel: Kernel) -> FastAPI:
    app = FastAPI(title="K2-AI Operating System")

    @app.get("/", response_class=HTMLResponse)
    def root() -> str:
        return (_STATIC / "cockpit.html").read_text(encoding="utf-8")

    @app.get("/api/overview")
    def overview() -> dict[str, Any]:
        pending = kernel.approvals.pending()
        records = kernel.audit.records()
        executed = sum(1 for r in records if r.event == "executed")
        return {
            "pending_count": len(pending),
            "audit_count": len(records),
            "automations_done": executed,
            "agents": [
                {"name": "Marketing Agent", "status": "active", "accuracy": 88},
            ],
        }

    @app.get("/api/approvals")
    def approvals() -> list[dict[str, Any]]:
        return [{"id": a.id, "action_key": a.action_key, "actor": a.actor,
                 "status": a.status.name, "payload": a.payload}
                for a in kernel.approvals.pending()]

    @app.post("/api/approvals/{approval_id}/approve")
    def approve(approval_id: int, body: ResolveBody) -> dict[str, Any]:
        res = kernel.resolve_approval(approval_id, approve=True,
                                      edited_payload=body.edited_payload)
        return {"outcome": res.outcome.name}

    @app.post("/api/approvals/{approval_id}/reject")
    def reject(approval_id: int, body: ResolveBody) -> dict[str, Any]:
        res = kernel.resolve_approval(approval_id, approve=False,
                                      reason=body.reason or "rejected")
        return {"outcome": res.outcome.name}

    return app
```

- [ ] **Step 5: create a minimal placeholder `aios/src/aios/api/static/cockpit.html`** so `test_root_serves_cockpit_html` passes (Task 3 fills it in fully):
```html
<!doctype html><html lang="it"><head><meta charset="utf-8"><title>K2-AI Operating System</title></head>
<body><h1>K2 - AI Operating System</h1><div id="app">loading…</div></body></html>
```

- [ ] **Step 6: run** `cd aios && .venv/bin/pytest tests/test_api.py -q` → 6 passed.
- [ ] **Step 7: full suite + commit**
```bash
cd aios && .venv/bin/pytest -q
cd /Volumes/PARASSITA/K-AI/.claude/worktrees/kind-lumiere-240e75
git add aios/pyproject.toml aios/src/aios/api/__init__.py aios/src/aios/api/app.py aios/src/aios/api/static/cockpit.html aios/tests/test_api.py
git commit -m "feat(aios): cockpit FastAPI backend (overview + approval queue)"
```

---

### Task 3: Cockpit page (mockup-style) + server entrypoint

**Files:**
- Overwrite: `aios/src/aios/api/static/cockpit.html` (full UI)
- Create: `aios/serve_cockpit.py` (uvicorn entrypoint with Supabase-backed kernel)

- [ ] **Step 1: write the full `aios/src/aios/api/static/cockpit.html`** — dark cockpit, Tailwind CDN, vanilla JS. Must contain the string "AI Operating System". Layout: header (K2 - AI Operating System), a Company Pulse + KPI strip (pending count, automations done, audit events, agent accuracy from /api/overview), and a Human Approval Queue rendering /api/approvals with **Approva / Modifica / Rifiuta** buttons. Approve → POST approve; Reject → prompt reason → POST reject; Modifica → editable textarea of the payload titolo/contenuto then POST approve with edited_payload. After each action, re-fetch the list.

```html
<!doctype html>
<html lang="it">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>K2-AI Operating System</title>
<script src="https://cdn.tailwindcss.com"></script>
</head>
<body class="bg-[#070708] text-zinc-100 font-sans">
<header class="px-6 py-4 border-b border-zinc-800 flex items-center justify-between">
  <div>
    <h1 class="text-xl font-bold">K2 - AI Operating System</h1>
    <p class="text-xs text-zinc-500">AI-first company command center</p>
  </div>
  <div class="text-xs text-zinc-400">Marketing · live</div>
</header>

<main class="p-6 space-y-6 max-w-5xl mx-auto">
  <section class="grid grid-cols-2 md:grid-cols-4 gap-4" id="kpis"></section>

  <section>
    <h2 class="text-sm uppercase tracking-wider text-zinc-400 mb-3">Coda approvazioni</h2>
    <div id="queue" class="space-y-3"></div>
  </section>
</main>

<script>
const API = "";
async function jget(u){ return (await fetch(API+u)).json(); }
async function jpost(u,b){ return (await fetch(API+u,{method:"POST",headers:{"Content-Type":"application/json"},body:JSON.stringify(b||{})})).json(); }

function kpiCard(label, value){
  return `<div class="rounded-2xl bg-[#0B0B0F] border border-zinc-800 p-4">
    <div class="text-2xl font-bold">${value}</div>
    <div class="text-xs text-zinc-500 mt-1">${label}</div></div>`;
}

async function loadOverview(){
  const o = await jget("/api/overview");
  document.getElementById("kpis").innerHTML =
    kpiCard("Approvazioni in attesa", o.pending_count)
    + kpiCard("Automazioni eseguite", o.automations_done)
    + kpiCard("Eventi audit", o.audit_count)
    + kpiCard("AI Agent Accuracy", (o.agents[0]?.accuracy ?? "—")+"%");
}

function card(a){
  const p = a.payload || {};
  return `<div class="rounded-2xl bg-[#0B0B0F] border border-zinc-800 p-4" data-id="${a.id}">
    <div class="flex items-center gap-2 mb-1">
      <span class="text-[10px] uppercase tracking-wider px-2 py-0.5 rounded-full bg-cyan-500/15 text-cyan-300">${p.tipo||"proposta"}</span>
      <span class="text-xs text-zinc-500">#${a.id}</span>
    </div>
    <div class="font-semibold mb-1">${p.titolo||""}</div>
    <div class="text-sm text-zinc-400 mb-1 contenuto">${p.contenuto||""}</div>
    <div class="text-xs text-zinc-500 mb-3">perché: ${p.motivo||""}</div>
    <div class="flex gap-2">
      <button class="approve px-3 py-1.5 rounded-lg bg-emerald-500 text-black text-sm font-semibold">Approva</button>
      <button class="edit px-3 py-1.5 rounded-lg bg-zinc-700 text-sm">Modifica</button>
      <button class="reject px-3 py-1.5 rounded-lg bg-red-500/80 text-sm">Rifiuta</button>
    </div></div>`;
}

async function loadQueue(){
  const items = await jget("/api/approvals");
  const q = document.getElementById("queue");
  if(!items.length){ q.innerHTML = '<div class="text-zinc-500 text-sm">Nessuna proposta in attesa.</div>'; return; }
  q.innerHTML = items.map(card).join("");
  items.forEach(a=>{
    const el = q.querySelector(`[data-id="${a.id}"]`);
    el.querySelector(".approve").onclick = async()=>{ await jpost(`/api/approvals/${a.id}/approve`,{}); refresh(); };
    el.querySelector(".reject").onclick = async()=>{ const reason = prompt("Motivo del rifiuto?")||"rifiutato"; await jpost(`/api/approvals/${a.id}/reject`,{reason}); refresh(); };
    el.querySelector(".edit").onclick = async()=>{
      const titolo = prompt("Titolo:", a.payload.titolo||""); if(titolo===null) return;
      const contenuto = prompt("Contenuto:", a.payload.contenuto||""); if(contenuto===null) return;
      await jpost(`/api/approvals/${a.id}/approve`,{edited_payload:{...a.payload, titolo, contenuto}}); refresh();
    };
  });
}
async function refresh(){ await loadOverview(); await loadQueue(); }
refresh();
</script>
</body>
</html>
```

- [ ] **Step 2: create `aios/serve_cockpit.py`**
```python
"""Serve the AIOS cockpit on http://localhost:8800 over the Supabase-backed kernel.
Env: AIOS_SUPABASE_URL, AIOS_SUPABASE_SERVICE_KEY.
Run: cd aios && set -a && . ./.env && set +a && .venv/bin/python serve_cockpit.py
"""
import os
import uvicorn
from aios.kernel import Kernel
from aios.api.app import create_app

kernel = Kernel.with_supabase_rest(os.environ["AIOS_SUPABASE_URL"],
                                   os.environ["AIOS_SUPABASE_SERVICE_KEY"])
app = create_app(kernel)

if __name__ == "__main__":
    uvicorn.run(app, host="127.0.0.1", port=8800)
```

- [ ] **Step 3: verify** `cd aios && .venv/bin/python -c "import ast; ast.parse(open('serve_cockpit.py').read()); print('ok')"` and re-run `test_api.py` (root now serves the full page, still contains "AI Operating System") → 6 passed.
- [ ] **Step 4: full suite + commit**
```bash
cd aios && .venv/bin/pytest -q
cd /Volumes/PARASSITA/K-AI/.claude/worktrees/kind-lumiere-240e75
git add aios/src/aios/api/static/cockpit.html aios/serve_cockpit.py
git commit -m "feat(aios): cockpit page (approval queue UI) + uvicorn entrypoint"
```

---

## Self-Review

**Spec coverage:** cockpit Human Approval Queue + Company Pulse/KPI (spec §9) → Tasks 2-3, wired to real `aios_approvals` via the kernel. Approve/Edit/Reject route through `resolve_approval` (audit + streak). Competitor discovery (agent finds them) → Task 1.

**Placeholder scan:** agent accuracy in /api/overview is a static 88 for the MVP (real accuracy from policy streak is a later refinement) — flagged here, not silent.

**Type consistency:** `create_app(kernel)` used by tests + entrypoint. `ResolveBody` matches POST bodies. `resolve_approval(approve, edited_payload, reason)` signatures match the kernel. cockpit.html action endpoints match the API routes.

**Live verification (controller):** run `serve_cockpit.py` with the Supabase env, open http://localhost:8800, screenshot the cockpit showing the 5 real pending proposals; click Approve on one and confirm via MCP that aios_approvals row flips to APPROVED.
