#!/usr/bin/env python3
"""
simulate_company.py — Simulazione REALE e READ-ONLY di K2-AI gestita dall'AI.

Esegue UNA VOLTA ciascuno dei 6 agenti di dominio (marketing, vendite, finance,
operations, legal, hr) sui dati reali in Supabase. Gli agenti LEGGONO i sensori e
PROPONGONO azioni; nulla viene approvato, eseguito o scritto su DB.

GARANZIE DI SICUREZZA (difesa in profondità):
  1. Il client Supabase viene avvolto da un guard che CONSENTE solo GET (select).
     Ogni insert/update/upsert diventa un no-op tracciato (nessuna riga scritta).
  2. Dopo build_platform() i backend di audit/approvals/policy del kernel sono
     sostituiti con backend IN-MEMORY: le proposte si accodano in RAM, non su DB.
  3. Lo snapshot dei sensori legge i tool DIRETTAMENTE (tool.run), bypassando
     persino l'audit in-memory: lettura pura.
  4. Nessun approval viene mai risolto, nessun attuatore invocato, nessun denaro.

Uso:
  cd .../aios && set -a && . ./.env && set +a && .venv/bin/python simulate_company.py
"""
from __future__ import annotations

import os
import sys
import time
import datetime as _dt
from pathlib import Path

# Rende importabile il package aios/ da src/
ROOT = Path(__file__).resolve().parent
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

DOMINI = ["marketing", "vendite", "finance", "operations", "legal", "hr"]

# Conta i tentativi di scrittura bloccati dal guard (deve restare 0 a fine run).
_WRITE_ATTEMPTS: list[str] = []


def _install_readonly_guard() -> None:
    """Patcha SupabaseREST PRIMA di build_platform: GET passa, le scritture sono
    no-op tracciate. Cosi' nemmeno gli upsert di policy fatti in __init__ degli
    agenti toccano il DB."""
    from aios import supabase_rest as _sr

    def _blocked(name):
        def _f(self, table, *a, **k):
            _WRITE_ATTEMPTS.append(f"{name}:{table}")
            return []
        return _f

    _sr.SupabaseREST.insert = _blocked("insert")   # type: ignore[assignment]
    _sr.SupabaseREST.update = _blocked("update")   # type: ignore[assignment]
    _sr.SupabaseREST.upsert = _blocked("upsert")   # type: ignore[assignment]


def _swap_kernel_to_memory(kernel, agents) -> None:
    """Sostituisce i backend persistenti del kernel con quelli in-memory: le
    proposte si accodano in RAM (come da specifica), zero righe su Supabase.

    IMPORTANTE: gli agenti, in __init__, hanno gia' impostato la propria azione a
    L1 sullo store REST (che il guard ha reso no-op). Sostituendo lo store con uno
    in-memory vuoto, quelle impostazioni andrebbero perse e tutto tornerebbe a L0
    (= il kernel NEGA invece di accodare). Quindi ri-applichiamo L1 in memoria per
    ogni azione di dominio (e la voce calendario marketing) replicando ESATTAMENTE
    cio' che fa la piattaforma reale a L1 — senza toccare il DB."""
    from aios.store.memory import (InMemoryAuditBackend, InMemoryApprovalBackend,
                                   InMemoryPolicyStateStore)
    from aios.autonomy import AutonomyLevel
    from aios.agents.marketing import PROPOSE_ACTION as MK_PROPOSE, CALENDAR_ACTION as MK_CAL
    kernel.audit._backend = InMemoryAuditBackend()
    kernel.approvals._backend = InMemoryApprovalBackend()
    kernel.policy._store = InMemoryPolicyStateStore()

    actions = []
    for name, agent in agents.items():
        cfg = getattr(agent, "cfg", None)
        if cfg is not None and getattr(cfg, "action", None) is not None:
            actions.append(cfg.action)
    # marketing non ha cfg: usa le sue azioni note
    actions.append(MK_PROPOSE)
    if "programma_contenuto" in kernel.tools.names():
        actions.append(MK_CAL)
    for act in actions:
        kernel.policy.set_level(act, AutonomyLevel.L1_PROPOSE)
        kernel.policy.set_cap(act, AutonomyLevel.L1_PROPOSE)


def _rows(x) -> int:
    if x is None:
        return 0
    if isinstance(x, list):
        return len(x)
    if isinstance(x, dict):
        return len(x)
    return 1


def _short(x, n: int) -> str:
    s = (x or "").strip().replace("\n", " ")
    return s if len(s) <= n else s[: n - 1].rstrip() + "…"


# Sensori letti dall'agente marketing (replica _gather di MarketingAgent, solo i
# tool effettivamente registrati vengono provati).
_MK_SENSORS_CORE = ["leggi_servizi", "leggi_topics", "leggi_profilo_ig", "leggi_post_ig"]
_MK_SENSORS_OPT = ["leggi_insight_ig", "leggi_calendario", "leggi_iscritti",
                   "leggi_newsletter", "leggi_analytics", "leggi_voce_clienti",
                   "leggi_ranking_seo", "leggi_funnel_web", "leggi_competitor_web",
                   "leggi_ads_meta", "leggi_ads_google", "leggi_brand_mentions",
                   "leggi_calendario_contenuti", "leggi_costi", "leggi_suite",
                   "leggi_competitor_ig"]


def _sensor_specs(domain: str, agent, kernel) -> list[tuple[str, dict]]:
    """Ritorna [(tool_name, args)] che l'agente del dominio leggera'."""
    cfg = getattr(agent, "cfg", None)
    if cfg is not None and getattr(cfg, "sensors", None):
        return list(cfg.sensors)
    # marketing: nessun cfg.sensors -> usa la lista nota di _gather
    names = set(kernel.tools.names())
    specs: list[tuple[str, dict]] = []
    for t in _MK_SENSORS_CORE:
        if t in names:
            specs.append((t, {"limit": 10} if t == "leggi_post_ig" else {}))
    for t in _MK_SENSORS_OPT:
        if t in names:
            specs.append((t, {}))
    return specs


def _snapshot_sensors(specs, kernel) -> list[dict]:
    """Legge ogni sensore DIRETTAMENTE (tool.run, nessun audit) e ne conta le
    righe. Tool non registrato -> 'non registrato'. Eccezione -> 'offline'."""
    names = set(kernel.tools.names())
    out: list[dict] = []
    for tool_name, args in specs:
        if tool_name not in names:
            out.append({"sensore": tool_name, "stato": "non registrato", "righe": 0})
            continue
        try:
            tool = kernel.tools.get(tool_name)
            res = tool.run(**(args or {}))
            out.append({"sensore": tool_name, "stato": "ok", "righe": _rows(res)})
        except Exception as exc:  # noqa: BLE001
            out.append({"sensore": tool_name, "stato": "offline",
                        "errore": _short(str(exc), 120), "righe": 0})
    return out


# Tabella/op usata dal fallback deterministico _ensure_action quando l'LLM NON
# fornisce un'azione strutturata valida (cioe' la proposta e' pura comunicazione).
_FALLBACK_TABLE = "board_tasks"
_FALLBACK_OP = "insert"


def _classifica(p: dict) -> str:
    """Distingue una proposta che porterebbe una SCRITTURA OPERATIVA mirata su DB
    (l'LLM ha indicato un'azione su una tabella/op diversa dal task di fallback)
    da una pura COMUNICAZIONE/ANALISI (che diventerebbe un task board generico)."""
    az = p.get("azione")
    if isinstance(az, dict):
        tabella = str(az.get("tabella") or az.get("table") or "").strip()
        op = str(az.get("op") or az.get("operazione") or "").strip().lower()
        if tabella and not (tabella == _FALLBACK_TABLE and op == _FALLBACK_OP):
            return "scrittura_db"
    return "comunicazione_analisi"


def _collect_proposals(kernel, domain: str) -> list[dict]:
    out: list[dict] = []
    for a in kernel.approvals.pending():
        if a.action_key.split(".", 1)[0] != domain:
            continue
        pl = a.payload or {}
        out.append({
            "id": a.id,
            "action_key": a.action_key,
            "tipo": str(pl.get("tipo") or ""),
            "titolo": str(pl.get("titolo") or ""),
            "contenuto": str(pl.get("contenuto") or ""),
            "motivo": str(pl.get("motivo") or ""),
            "azione": pl.get("azione"),
            "classe": _classifica(pl),
        })
    return out


def run_simulation() -> dict:
    _install_readonly_guard()
    from aios.platform import build_platform

    print("[sim] build_platform() …", flush=True)
    platform = build_platform()
    kernel = platform.kernel
    _swap_kernel_to_memory(kernel, platform.agents)
    print(f"[sim] kernel pronto · tool registrati: {len(kernel.tools.names())} · "
          f"backend audit/approvals/policy = IN-MEMORY (read-only)", flush=True)

    # Deliverable esistenti (1 lettura Supabase consentita).
    try:
        deliverables = platform.deliverables()
        n_deliverables = _rows(deliverables)
    except Exception as exc:  # noqa: BLE001
        deliverables = []
        n_deliverables = 0
        print(f"[sim] WARN deliverables non leggibili: {_short(str(exc), 120)}", flush=True)
    print(f"[sim] deliverable gia' presenti su Supabase: {n_deliverables}", flush=True)

    risultati: list[dict] = []
    total_secs = 0.0
    seen_ids: set[int] = set()

    for domain in DOMINI:
        print(f"\n[sim] ===== {domain.upper()} =====", flush=True)
        agent = platform.agents[domain]

        specs = _sensor_specs(domain, agent, kernel)
        print(f"[sim] {domain}: snapshot {len(specs)} sensori …", flush=True)
        sensori = _snapshot_sensors(specs, kernel)
        for s in sensori:
            tag = s["stato"] if s["stato"] != "ok" else f"{s['righe']} righe"
            print(f"      - {s['sensore']}: {tag}", flush=True)

        err = None
        t0 = time.perf_counter()
        try:
            print(f"[sim] {domain}: run agente (LLM Haiku) …", flush=True)
            platform.run(domain)
        except Exception as exc:  # noqa: BLE001
            err = _short(str(exc), 200)
            print(f"[sim] {domain}: ERRORE → {err}", flush=True)
        dt = time.perf_counter() - t0
        total_secs += dt

        proposte = _collect_proposals(kernel, domain)
        # difesa: considera solo le proposte NUOVE di questo ciclo
        proposte = [p for p in proposte if p["id"] not in seen_ids]
        for p in proposte:
            seen_ids.add(p["id"])

        n_scrittura = sum(1 for p in proposte if p["classe"] == "scrittura_db")
        n_comm = len(proposte) - n_scrittura
        print(f"[sim] {domain}: {len(proposte)} proposte in coda "
              f"({n_scrittura} scrittura DB · {n_comm} comunicazione/analisi) · "
              f"{dt:.1f}s", flush=True)

        risultati.append({
            "dominio": domain,
            "sensori": sensori,
            "righe_lette": sum(s["righe"] for s in sensori),
            "secondi": dt,
            "errore": err,
            "proposte": proposte,
            "n_proposte": len(proposte),
            "n_scrittura_db": n_scrittura,
            "n_comunicazione": n_comm,
        })

    # Aggregati reali
    tot_prop = sum(r["n_proposte"] for r in risultati)
    per_tipo: dict[str, int] = {}
    for r in risultati:
        for p in r["proposte"]:
            t = p["tipo"] or "(non indicato)"
            per_tipo[t] = per_tipo.get(t, 0) + 1
    tot_scrittura = sum(r["n_scrittura_db"] for r in risultati)
    tot_comm = sum(r["n_comunicazione"] for r in risultati)

    return {
        "risultati": risultati,
        "tot_prop": tot_prop,
        "per_tipo": per_tipo,
        "tot_scrittura": tot_scrittura,
        "tot_comm": tot_comm,
        "n_deliverables": n_deliverables,
        "total_secs": total_secs,
        "write_attempts": list(_WRITE_ATTEMPTS),
    }


# ---------------------------------------------------------------------------
# REPORT (italiano, brand voice K2-AI: pragmatico, concreto, niente buzzword)
# ---------------------------------------------------------------------------

# Etichetta qualitativa dell'impatto per tipo di proposta (NESSUN numero inventato).
_IMPATTO = {
    "brand": "coerenza brand e posizionamento",
    "content": "pipeline contenuti alimentata",
    "social": "presenza social piu' curata",
    "seo": "visibilita' organica sui termini target",
    "email": "lifecycle e nurturing iscritti",
    "product_mkt": "messaggi prodotto piu' chiari",
    "analytics": "decisioni basate su dati, non a sensazione",
    "research": "voce del cliente raccolta",
    "competitor": "lettura del posizionamento competitivo",
    "paid": "ipotesi su canali a pagamento (da validare)",
    "demand_gen": "generazione domanda dalla pipeline",
    "automation": "igiene dati e workflow, meno lavoro manuale",
    "pr": "monitoraggio reputazione/menzioni",
    "influencer": "scouting profili di nicchia",
    "events": "ipotesi eventi/webinar",
    "cro": "ottimizzazione funnel sito",
    "creative": "brief/asset creativi pronti",
    "budget": "controllo spesa marketing",
    "strategy": "piano che lega le iniziative",
    "fix": "correzione operativa puntuale",
    "lead_gen": "lead caldi intercettati",
    "qualification": "fit ICP e priorita' lead",
    "pipeline_mgmt": "igiene pipeline, lead fermi sbloccati",
    "forecasting": "previsione vendite pesata",
    "proposal": "offerta pronta da inviare",
    "negotiation": "obiezioni anticipate",
    "retention": "segnali churn presidiati",
    "upsell": "cross/upsell su clienti attivi",
    "general_ledger": "libro giornale quadrato",
    "accounts_receivable": "incassi sollecitati",
    "accounts_payable": "scadenze fornitori coperte",
    "treasury": "cassa e runway sotto controllo",
    "tax_compliance_IT": "scadenza fiscale coperta",
    "cost_control": "spesa SaaS sotto la soglia",
    "pricing": "marginalita' verificata",
    "commessa_tracking": "avanzamento commesse monitorato",
    "risk_blockers": "blocchi di progetto identificati",
    "capacity": "carico del team bilanciato",
    "milestone_SAL": "milestone/SAL presidiati",
    "gdpr": "adempimento privacy presidiato",
    "contratti": "scadenze contrattuali coperte",
    "compliance": "rischio normativo ridotto",
    "recruiting": "pipeline assunzioni avviata",
    "onboarding": "inserimento nuove persone strutturato",
    "performance": "ciclo performance presidiato",
    "hr_compliance": "sicurezza sul lavoro presidiata",
}


def _impatto(tipo: str) -> str:
    t = (tipo or "").lower().strip()
    if not t:
        return "azione operativa concreta da valutare"
    if t in _IMPATTO:
        return _IMPATTO[t]
    # match prudente: la chiave (>=4 char) deve comparire come token dentro il tipo
    # — evita falsi positivi di chiavi corte (pr, cro) su tipi generici (AZIONE…).
    toks = set(t.replace("/", "_").replace("-", "_").split("_"))
    for k, v in _IMPATTO.items():
        if len(k) >= 4 and (k in toks or k in t):
            return v
    return "azione operativa concreta da valutare"


_DOMINIO_LABEL = {
    "marketing": "Marketing (CMO)",
    "vendite": "Vendite / CRM (CRO)",
    "finance": "Finance (CFO)",
    "operations": "Operations (COO)",
    "legal": "Legal & Compliance",
    "hr": "HR / People (CHRO)",
}


def build_report(agg: dict) -> str:
    risultati = agg["risultati"]
    oggi = _dt.date.today().isoformat()
    L: list[str] = []
    A = L.append

    A("# Se lasciassi K2-AI gestita dall'AI — simulazione reale, read-only")
    A("")
    A(f"_Generato il {oggi} · 1 ciclo operativo (\"una giornata\") · autonomia L1 (solo proposte)._")
    A("")
    A("## In breve")
    A("")
    A("Questo non e' uno scenario inventato: e' una **esecuzione reale** dei 6 agenti "
      "di dominio di K2-AI (marketing, vendite, finance, operations, legal, hr) sui "
      "**dati veri** presenti nel sistema. Ogni agente ha letto i propri sensori e ha "
      "prodotto proposte tramite LLM (Claude Haiku). Tutto in **sola lettura**: nessuna "
      "scrittura su database, nessun pagamento, nessuna azione eseguita.")
    A("")
    A(f"In **un solo ciclo** l'AI ha messo in coda **{agg['tot_prop']} decisioni** che "
      f"aspettano l'ok umano. Nessuna e' stata approvata: con l'autonomia attuale (L1) "
      f"l'AI **propone, non agisce**. Tempo macchina totale: **{agg['total_secs']:.0f} secondi**.")
    A("")
    n_falliti = [r["dominio"] for r in risultati if r["errore"]]
    n_zero = [r["dominio"] for r in risultati if not r["errore"] and r["n_proposte"] == 0]
    A(f"- Reparti che hanno prodotto proposte: "
      f"**{sum(1 for r in risultati if r['n_proposte'] > 0)}/6**")
    A(f"- Proposte che diventerebbero una **scrittura operativa mirata** su una "
      f"tabella interna: **{agg['tot_scrittura']}**")
    A(f"- Proposte che restano **comunicazione/analisi** (diventano un task da "
      f"validare): **{agg['tot_comm']}**")
    A(f"- Deliverable gia' archiviati nel sistema prima di oggi: **{agg['n_deliverables']}**")
    if n_falliti:
        A(f"- Reparti in errore in questo ciclo: **{', '.join(n_falliti)}**")
    if n_zero:
        A(f"- Reparti con 0 proposte in questo ciclo: **{', '.join(n_zero)}**")
    A("")

    # Distribuzione per tipo (reale)
    A("### Proposte per tipo (reali)")
    A("")
    if agg["per_tipo"]:
        for t, n in sorted(agg["per_tipo"].items(), key=lambda kv: (-kv[1], kv[0])):
            A(f"- `{t}`: {n}")
    else:
        A("- (nessuna proposta)")
    A("")

    # Tabella riepilogo per reparto
    A("### Riepilogo per reparto")
    A("")
    A("| Reparto | Sensori ok/tot | Righe lette | Proposte | di cui scrittura DB | Tempo |")
    A("|---|---|---|---|---|---|")
    for r in risultati:
        ok = sum(1 for s in r["sensori"] if s["stato"] == "ok")
        tot = len(r["sensori"])
        nota = " ⚠ errore" if r["errore"] else ""
        A(f"| {_DOMINIO_LABEL.get(r['dominio'], r['dominio'])} | {ok}/{tot} | "
          f"{r['righe_lette']} | {r['n_proposte']}{nota} | {r['n_scrittura_db']} | "
          f"{r['secondi']:.1f}s |")
    A("")

    # Dettaglio per reparto
    A("---")
    A("")
    A("## Cosa farebbe ogni reparto, nel dettaglio")
    A("")
    for r in risultati:
        A(f"### {_DOMINIO_LABEL.get(r['dominio'], r['dominio'])}")
        A("")
        # cosa ha letto
        letti = [s for s in r["sensori"] if s["stato"] == "ok"]
        vuoti = [s for s in r["sensori"] if s["stato"] == "ok" and s["righe"] == 0]
        offline = [s for s in r["sensori"] if s["stato"] == "offline"]
        nonreg = [s for s in r["sensori"] if s["stato"] == "non registrato"]
        with_data = [s for s in letti if s["righe"] > 0]
        if with_data:
            letti_str = ", ".join(f"`{s['sensore']}` ({s['righe']})" for s in with_data)
            A(f"**Cosa ha letto (dati reali):** {letti_str}.")
        else:
            A("**Cosa ha letto (dati reali):** nessun sensore con righe popolate.")
        if vuoti:
            A(f"**Sensori vuoti (0 righe):** {', '.join('`'+s['sensore']+'`' for s in vuoti)}.")
        if offline:
            A(f"**Sensori offline:** {', '.join('`'+s['sensore']+'`' for s in offline)}.")
        if nonreg:
            A(f"**Sensori non registrati:** {', '.join('`'+s['sensore']+'`' for s in nonreg)}.")
        A("")

        if r["errore"]:
            A(f"> ⚠ L'agente e' andato in errore in questo ciclo: {r['errore']}")
            A("")
            continue
        if r["n_proposte"] == 0:
            A("> L'agente non ha prodotto proposte in questo ciclo (output vuoto). "
              "Va verificato: prompt troppo denso per Haiku o dati insufficienti.")
            A("")
            continue

        A(f"**Cosa PROPONE ({r['n_proposte']} azioni, tutte da approvare):**")
        A("")
        for p in r["proposte"]:
            titolo = _short(p["titolo"] or p["tipo"] or "Proposta", 90)
            frase = _short(p["contenuto"], 160)
            A(f"- **{titolo}** — {frase}")
        A("")
        # impatto qualitativo
        impatti = []
        seen = set()
        for p in r["proposte"]:
            imp = _impatto(p["tipo"])
            if imp not in seen:
                seen.add(imp)
                impatti.append(imp)
        A(f"**Impatto atteso (qualitativo):** {', '.join(impatti)}.")
        scr = r["n_scrittura_db"]
        if scr:
            A(f"_{scr} di queste, se approvate, scriverebbero direttamente su una "
              f"tabella operativa interna (es. pipeline lead, fatture, task di commessa); "
              f"le altre diventerebbero task da lavorare._")
        else:
            A("_Nessuna di queste tocca direttamente una tabella operativa: sono analisi "
              "e comunicazioni che diventerebbero task da validare._")
        A("> Stato: **da approvare**. Niente e' stato eseguito.")
        A("")

    # Autonomia L2/L3
    A("---")
    A("")
    A("## Cosa farebbe oggi l'AI in autonomia (se le dessi L2/L3)")
    A("")
    A("Con l'autonomia attuale **L1** ogni proposta passa dall'approvazione umana. "
      "Salendo di livello, una parte di queste azioni potrebbe partire da sola. "
      "La linea di sicurezza la traccia gia' l'attuatore del kernel.")
    A("")
    A("**Candidabili ad automazione (L2, basso rischio, reversibili):**")
    A("")
    A("- Creazione di **task operativi** interni (board/commessa) a partire da segnali "
      "letti dai sensori: e' il caso piu' frequente in questo ciclo.")
    A("- **Igiene dati**: aggiornare lo stato di un lead fermo in pipeline, riconciliare "
      "una voce di costo, programmare una bozza in calendario contenuti.")
    A("- **Promemoria e alert** su scadenze (SAL di commessa, scadenze fiscali, rinnovi "
      "contratti): l'AI li accoda gia' come task, automatizzarli toglie lavoro manuale.")
    A("")
    A("**Devono restare con approvazione umana (L1, sempre):**")
    A("")
    A("- **Denaro**: qualsiasi movimento su ricavi, conversioni, Stripe. L'attuatore "
      "ha gia' queste tabelle in blocklist e non puo' scriverci.")
    A("- **Contratti e firme**: offerte ai clienti, NDA, atti societari, deposito bilancio.")
    A("- **Dati personali**: consensi, registro trattamenti, dati degli utenti del K-BOT.")
    A("- **Persone**: assunzioni, licenziamenti, offboarding.")
    A("- **Comunicazioni verso l'esterno**: nessun contatto a clienti/lead parte senza ok.")
    A("")

    # Rischi/limiti osservati
    A("## Rischi e limiti osservati (reali, in questo ciclo)")
    A("")
    osserv = []
    if n_falliti:
        osserv.append(f"**Agenti in errore**: {', '.join(n_falliti)} non hanno completato "
                      f"il ciclo. Un reparto puo' fallire senza bloccare gli altri, ma la "
                      f"copertura del giorno ne risente.")
    if n_zero:
        osserv.append(f"**Output vuoto**: {', '.join(n_zero)} non ha prodotto proposte. "
                      f"Con Haiku capita su prompt molto densi; va monitorato.")
    # sensori vuoti / offline aggregati
    vuoti_glob = {}
    offline_glob = {}
    nonreg_glob = {}
    for r in risultati:
        for s in r["sensori"]:
            if s["stato"] == "ok" and s["righe"] == 0:
                vuoti_glob[s["sensore"]] = vuoti_glob.get(s["sensore"], 0) + 1
            elif s["stato"] == "offline":
                offline_glob[s["sensore"]] = offline_glob.get(s["sensore"], 0) + 1
            elif s["stato"] == "non registrato":
                nonreg_glob[s["sensore"]] = nonreg_glob.get(s["sensore"], 0) + 1
    if vuoti_glob:
        osserv.append(f"**Sensori vuoti**: {len(vuoti_glob)} sensori restituiscono 0 righe "
                      f"(es. {', '.join(list(vuoti_glob)[:6])}). L'AI lavora in modalita' "
                      f"strategia su quelle aree: utile, ma non e' lettura di dati reali.")
    if offline_glob:
        osserv.append(f"**Connettori offline**: {', '.join(list(offline_glob)[:6])} non "
                      f"rispondono (probabile env non configurato). Restituiscono lista vuota, "
                      f"quindi nessun crash, ma manca il dato.")
    if nonreg_glob:
        osserv.append(f"**Sensori non registrati**: {', '.join(list(nonreg_glob)[:6])}.")
    osserv.append("**Dipendenza da un LLM**: le proposte sono buone quanto il modello e i "
                  "dati che legge. Su dati scarsi puo' restare sul generico: serve sempre "
                  "il filtro umano prima di alzare l'autonomia.")
    for o in osserv:
        A(f"- {o}")
    A("")

    # Chiusura
    A("## In conclusione")
    A("")
    A(f"In **una giornata simulata**, lasciata a se' stessa, l'AI di K2-AI metterebbe in "
      f"coda **{agg['tot_prop']} decisioni** su tutti e sei i reparti — coperti in "
      f"**{agg['total_secs']:.0f} secondi** di calcolo. Oggi sono tutte proposte: niente "
      f"e' partito, niente e' stato scritto, nessun euro si e' mosso.")
    A("")
    A("Per **alzare l'autonomia in sicurezza** servono, nell'ordine:")
    A("")
    A("1. **Collegare i sensori ancora vuoti** (CRM, Stripe, analytics): senza dati reali "
      "l'AI ragiona in astratto.")
    A("2. **Partire da L2 solo sulle azioni reversibili e a basso rischio** (task, igiene "
      "dati, promemoria), tenendo denaro/contratti/persone/dati personali sempre a L1.")
    A("3. **Far maturare il track record**: il kernel promuove a L2 solo dopo una serie di "
      "esiti puliti approvati. La fiducia si guadagna sui numeri, non si concede a priori.")
    A("")
    # Garanzia di sicurezza
    wa = agg["write_attempts"]
    A("---")
    A("")
    A("### Nota di sicurezza")
    A("")
    A("Simulazione **read-only** verificata: backend audit/approvals/policy del kernel "
      "spostati in memoria, client Supabase in sola lettura (GET).")
    if wa:
        A(f"- Tentativi di scrittura intercettati e neutralizzati dal guard: **{len(wa)}** "
          f"(tutti resi no-op, nessuna riga scritta).")
    else:
        A("- Tentativi di scrittura verso Supabase durante il run: **0**.")
    A("- Approval risolti / azioni eseguite / movimenti di denaro: **0**.")
    A("")
    return "\n".join(L)


def main() -> int:
    if not os.environ.get("ANTHROPIC_API_KEY"):
        print("ERRORE: ANTHROPIC_API_KEY non in ambiente. Esegui con:\n"
              "  set -a && . ./.env && set +a && .venv/bin/python simulate_company.py",
              file=sys.stderr)
        return 2
    agg = run_simulation()
    report = build_report(agg)

    out_path = ROOT / "docs" / "SIMULAZIONE_AZIENDA.md"
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(report, encoding="utf-8")

    print("\n" + "=" * 78)
    print(report)
    print("=" * 78)
    print(f"\n[sim] report scritto in: {out_path}", flush=True)
    print(f"[sim] proposte totali in coda: {agg['tot_prop']} · "
          f"tempo totale: {agg['total_secs']:.1f}s · "
          f"tentativi scrittura DB bloccati: {len(agg['write_attempts'])}", flush=True)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
