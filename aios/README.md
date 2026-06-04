# AIOS — K2-AI internal platform (K2-OS)

AI Operating System che fa girare K2-AI: kernel orchestratore + 5 strati + agenti di dominio + cockpit.

## Struttura (schema K2-OS)
- **Orchestratore** = `kernel` (scaletta autonomia L0–L3, tool registry, audit, kill-switch, coda approvazioni).
- **① Contesto** = `layers/context.py` + Founder Model + **knowledge base** (`layers/knowledge.py`, tabella `aios_knowledge`, 113 chunk reali da CLAUDE.md/docs/servizi/topics).
- **② Dati** = `layers/data.py` (vista unica sui sensori) + sensori reali (Instagram, contenuti Supabase, lead).
- **③ Intelligence** = `layers/intelligence.py` (insight con evidenza).
- **④ Automazione** = agenti (`agents/marketing.py`, `agents/domain.py`) + skill (38) + deliverable.
- **⑤ Sviluppo** = `layers/development.py` (crea nuove skill su misura).
- **Deliverable verificato** = `layers/deliverable.py` (markdown con sezione Fonti).
- **Facade** = `aios/aios.py` (`AIOS.situazione()`), **Platform** = `platform.py` (multi-dominio).

## Agenti (6 domini, ognuno con reparto ricercato + sotto-funzioni)
Per ogni dominio è stata fatta ricerca su come le aziende compongono quel reparto
(8 sotto-funzioni ciascuno), poi implementato come agente su dati reali. Tutti a **cap L1** (propongono, il founder approva).
- **Marketing** (ricco): insight IG + competitor auto-scoperti + calendario + skill complete + analisi post-per-post → proposte + voci calendario.
- **Vendite** (`sales_config.py`): 8 sotto-funzioni (qualificazione, pipeline, outreach, account research, meeting prep, proposta/ROI, obiezioni, forecast) su `pipeline_leads` + `board_memos`.
- **Finance** (`finance_config.py`): ricavi/MRR, forecast pipeline, cash-flow, controllo costi, budget vs actual, FP&A, KPI, scadenze fiscali — su `kbot_conversions`, `board_revenue_events`, `projects`, `shared_memory`.
- **Operations** (`operations_config.py`): tracking commessa, SAL, capacity, rischi/blocchi, onboarding, documenti, SLA, report — su `projects`, `project_phases`, `project_tasks`, `project_documents`, `tasks`.
- **Legal & Compliance** (`legal_config.py`): review contratti/NDA, GDPR, tracciamento consensi, 231, regulatory watch, DPA, risk, IP — su `newsletter_subscribers`, `kbot_profiles`. (Verificato live: ha trovato anomalie GDPR reali.)
- **HR** (`hr_config.py`): recruiting, interview, onboarding, people ops, performance, training, retention, org planning — **modalità consulenza** (nessuna anagrafica dipendenti/candidati ancora connessa: lo dichiara in ogni output).
- Framework `DomainAgent` config-driven: nuovo ambito = nuova `DomainConfig` + i suoi sensori. Sensori non-marketing in `sources/domains.py`.

## Run
```bash
cd aios
python3 -m venv .venv && .venv/bin/pip install -e ".[dev]"
set -a && . ./.env && set +a            # AIOS_SUPABASE_URL/SERVICE_KEY, AIOS_IG_TOKEN, ANTHROPIC_API_KEY, (AIOS_API_TOKEN in prod)
.venv/bin/pytest -q                      # test
.venv/bin/python serve_cockpit.py        # cockpit http://127.0.0.1:8800
.venv/bin/python scheduler.py            # fai girare tutti gli agenti (cron-friendly)
.venv/bin/python run_simulation.py       # "multiverso": simulazione a tempo compresso
```

## API (FastAPI)
- `GET /` cockpit · `GET /api/overview` · `GET /api/insights` · `GET /api/approvals` · `GET /api/deliverables` · `GET /api/domini`
- `POST /api/agents/{domain}/run` · `POST /api/approvals/{id}/approve|reject` (auth bearer se `AIOS_API_TOKEN` impostato)

Sicurezza: vedi `SECURITY.md`. Deploy: imposta `AIOS_API_TOKEN`, HTTPS, ruota i segreti.
