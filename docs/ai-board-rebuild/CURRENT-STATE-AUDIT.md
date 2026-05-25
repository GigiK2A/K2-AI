# AI-Board Current State Audit
Date: 2026-05-15
Owner: Luigi Rossi (K2-AI)
Auditor: Claude (Opus 4.7)
Codebase: `/Volumes/PARASSITA/K-AI/ai-board/` — ~16.400 LOC Python + Jinja2

---

## TL;DR

1. **Agent system è teatro**. Dichiari 17 nomi di agenti (`db/models.py:24-41`), il registry ne carica solo 9 (`core/orchestrator.py:17-27`) e ne aliasa 8 verso 4 "hub" (`AGENT_ALIAS_MAP`). Risultato: 8 file in `agents/` (brand_strategy, marketing_strategy, lead_generation, offer_positioning, outreach, project_operations, risk_review, knowledge) sono **completamente dead code**: nessun `import` in tutto il repo (verificato). Sono identità senza implementazione attiva.
2. **Database split senza principio**. Tutto scrive sia su Supabase che su Notion (mutuamente esclusivi via `notion_enabled()`), e per giunta **le chat di Giuseppina vengono salvate come righe nella tabella `approvals`** con `content_type="telegram_agent_chat"` (`agents/orchestrator.py:243-260`). La tabella `approvals` è inquinata da migliaia di turni conversazionali che non sono approvazioni.
3. **L'orchestrator non orchestra**. La funzione `run_objective` in `core/orchestrator.py:103-113` istanzia `OrchestratorAgent()` ma quel simbolo **non è importato** (è definito solo come alias in `agents/orchestrator.py:266`) — bug latente: la funzione probabilmente fallisce ogni volta. Nessuno fa fanout multi-agente reale; tutti i workflow girano un singolo agente alla volta.
4. **Dashboard è un visore Notion travestito**. 14 route, 1300+ righe di template, ma quasi tutto è "leggi da Notion → mostra". Le poche azioni reali (approva/rifiuta, edit lavori, edit workshop) duplicano funzionalità che Notion offre nativamente meglio. Tailwind via CDN (`templates/base.html:8`) carica ~3MB al primo hit.
5. **Telegram è il vero prodotto**, ma è un monolite da 1140 righe (`handlers.py`) con state machine fragile, locking globale ad-hoc (`_CHAT_LOCKS`), e logica business mescolata con presentation. Funziona, ma è il pezzo più rischioso da estendere.

**Sintesi opinionata**: il sistema fa una cosa utile (chat con Giuseppina su Telegram, write su Notion) sepolta sotto 3 layer di astrazione (boardroom multi-agente, dashboard web, scheduler) che producono prevalentemente rumore. Da ricostruire come **un singolo assistente Claude con tool calling su Postgres + interfaccia web PWA mobile-first**, eliminando 60-70% del codice.

---

## 1. Architecture Map

```
ai-board/
├── main.py                       # entry — uvicorn + APScheduler + Telegram polling/webhook
├── core/                         # ~5.000 LOC — utility + dominio misti
│   ├── orchestrator.py           # 119 — registry agenti + run/chat
│   ├── notion_board.py           # 1.304 — client Notion completo (GOD MODULE)
│   ├── notion_tools.py           # 680 — wrap tool agno per i 9 agenti
│   ├── scheduler.py              # 995 — APScheduler + 8 job (GOD MODULE)
│   ├── memory.py                 # 206 — "shared memory" k/v su Supabase+seed (positioning vecchio)
│   ├── conversation.py           # 172 — caricamento storia chat (legge da approvals!)
│   ├── approval.py               # 196 — CRUD approvals (Supabase+Notion)
│   ├── board_auth.py             # 216 — sessioni dashboard
│   ├── action_guard.py           # 243 — conferme pending Telegram
│   ├── undo.py                   # 293 — sistema undo Telegram (poco usato)
│   ├── business_audit.py         # 146 — audit log azioni
│   ├── csrf.py / rate_limit.py / email.py / session_state.py / text.py / logger.py / config.py
│   └── (12 file totali)
├── agents/                       # 17 file, ma solo 9 effettivamente registrati
│   ├── base.py                   # 739 — BoardAgent ABC (system prompt monstre)
│   ├── orchestrator.py           # 266 — Giuseppina (CEO, unica chat point)
│   ├── content_engine.py         # 284 — Genoveffa
│   ├── sales_enablement.py       # 172 — Peppe Pipeline
│   ├── geo_seo.py                # 244
│   ├── legal.py                  # 112
│   ├── chief_of_staff.py         # 38, finance_kpi.py 37, solution_architect.py 34
│   ├── brand_strategy.py         # 28  ─┐
│   ├── marketing_strategy.py     # 28   │
│   ├── lead_generation.py        # 34   │
│   ├── offer_positioning.py      # 28   │ ◀── 8 file DEAD CODE
│   ├── outreach.py               # 29   │     (definiti, aliasati a hub agents,
│   ├── project_operations.py     # 29   │      mai importati né istanziati)
│   ├── risk_review.py            # 28   │
│   ├── knowledge.py              # 29   │
│   ├── market_intelligence.py    # 29  ─┘
│   └── scheduler_tasks/posthog_sync.py
├── controllers/                  # MVC layer "moderno": 2 file (home, agents)
├── services/                     # use-case: home, agents, posthog_ingest, reports
├── repositories/                 # 4 repo (agent_logs, approvals, pipeline, tasks)
├── db/                           # client Supabase + 6 migrazioni SQL + Pydantic models
├── interfaces/
│   ├── dashboard/                # FastAPI + Jinja2 + HTMX + Tailwind CDN
│   │   ├── app.py                # 268 — middleware (auth, CSP, CSRF, rate-limit)
│   │   ├── routes/               # 14 file route, 2.700+ LOC
│   │   │   ├── public_intake.py  # 863 — endpoint K-BOT chat + form contatti
│   │   │   ├── workshop.py       # 639 — CRUD pacchetti workshop (admin)
│   │   │   ├── pipeline.py       # 277, lavori.py 213, approvals.py 213, admin.py 230
│   │   │   └── ...
│   │   └── templates/            # ~30 file Jinja, partials/ per HTMX swap
│   └── telegram/
│       ├── handlers.py           # 1.140 — GOD FILE
│       ├── assistant.py          # 966 — LLM intent routing + heuristics
│       ├── bot.py                # 140 — application setup
│       ├── notifier.py           # 263, presentation.py 119, keyboards.py 55
├── skills/                       # 16 cartelle SKILL.md (markdown statico, agno LocalSkills)
├── stitch/                       # ❌ DEAD — mockup HTML Stitch (Google)
├── stitch_step4b/                # ❌ DEAD — altra rev mockup, mai linkati
├── tools/                        # 1 script one-off (fix_notion_intake.py)
├── tests/                        # 4 file test minimi
└── uploads/                      # storage locale (Railway → ephemeral!)
```

### Duplicazioni / dead code
- `stitch/` e `stitch_step4b/`: 22 file HTML mock di design. **Nessun riferimento dal codice** (`grep -rn stitch interfaces/ controllers/ services/ core/` → zero match). Pesa pochi KB ma confonde. → buttare.
- `agents/{brand_strategy,marketing_strategy,lead_generation,offer_positioning,outreach,project_operations,risk_review,knowledge,market_intelligence}.py`: 8 file (più market_intelligence che è registrato ma effettivamente fa solo da clone di sales). Nessun `from agents.brand_strategy import` ecc. nel codebase. → buttare o consolidare.
- `interfaces/dashboard/routes/home.py`: shim legacy che importa da `controllers/` (`routes/home.py:1-19`). Doppia indirezione inutile.
- `OrchestratorAgent = GiuseppinaAgent` (`agents/orchestrator.py:266`): alias backward-compat ma `core/orchestrator.py:110` lo usa **senza importarlo** — bug, oltre che design strano.
- `core/undo.py` (293 LOC): sistema undo Telegram complesso. `tools/runner.py` non esiste come modulo eseguibile coordinato. Vale la pena verificare se viene mai chiamato in pratica.
- `repositories/_common.py`: 23 LOC, helper sottilissimo riusato in 4 file. Sopravvalutato come "repository pattern".

### Catene di chiamata reali (in produzione)
1. **Telegram message** → `handlers.message_handler` → `core.orchestrator.chat_agent(ORCHESTRATOR, ...)` → `GiuseppinaAgent.chat()` → Anthropic/OpenAI + tool calls Notion → risposta.
2. **Dashboard `/`** → `controllers/home_controller` → `services/home_service.HomeService.load_home_data()` → `repositories/*` → Supabase/Notion → render.
3. **K-BOT website** → `POST /api/intake/kbot-chat` → `public_intake.py` → OpenAI client diretto (bypassa BoardAgent!) → Notion approval + email.
4. **Scheduler** → 8 cron jobs → `run_agent_async(NAME, prompt, ctx)` → BoardAgent.run → output con `INFORMATIONAL_CONTENT_TYPES` → notifier Telegram.

---

## 2. Agent System

### Registry effettivo (`core/orchestrator.py:17-27`)
| Agente (interno) | Classe | File | Provider | Tools registrati | Davvero usato? | Valore |
|---|---|---|---|---|---|---|
| `orchestrator` | GiuseppinaAgent | `agents/orchestrator.py` | OpenAI | 10 tool Notion (lead/task/clienti/memoria) | ✅ Sì — TUTTI i msg Telegram passano da qui | ★★★★★ è il prodotto |
| `chief_of_staff` | GinoAgent | `agents/chief_of_staff.py` (38 LOC) | OpenAI | nessuno (?) | ⚠️ Solo da scheduler `daily_brief` | ★★ produce output, ma è un altro prompt di Claude |
| `content_engine` | GenoveffaAgent | `agents/content_engine.py` (284 LOC, prompt enorme) | Anthropic | search + create_task + list_tasks | ⚠️ Da scheduler `weekly_plan` o richieste dirette | ★★ |
| `market_intelligence` | MarketIntelligenceAgent | `agents/market_intelligence.py` (29 LOC) | Anthropic | search + Notion lead | ⚠️ Solo da scheduler `market_pulse` | ★ noise, vedi §6 |
| `sales_enablement` | PeppePipelineAgent | `agents/sales_enablement.py` (172 LOC) | OpenAI | Notion pipeline + task | ⚠️ Richiesta esplicita rara | ★★ |
| `solution_architect` | ArchimedeAgent | `agents/solution_architect.py` (34 LOC) | Anthropic | minimal | ⚠️ Usato da K-BOT website (`public_intake.py:25`) come **nome** dell'output ma bypassato | ★ |
| `finance_kpi` | RagionierUgoAgent | `agents/finance_kpi.py` (37 LOC) | OpenAI | Notion read | ⚠️ Solo scheduler `kpi_update` con dati spesso fittizi | ★ |
| `legal` | AvvocataPinaAgent | `agents/legal.py` (112 LOC) | Anthropic | nessuno | ⚠️ Mai chiamato in autonomia | ★ |
| `geo_seo` | GeografinoAgent | `agents/geo_seo.py` (244 LOC) | Anthropic | nessuno | ⚠️ Out of scope rispetto al business | ★ |

### Aliasati (non istanziati mai)
`AGENT_ALIAS_MAP` (`core/orchestrator.py:29-38`) mappa 7 nomi storici a 4 hub. I file Python relativi esistono ma **non vengono mai importati né eseguiti**.

| Alias (`AgentName.*`) | File classe | Importato? |
|---|---|---|
| OFFER_POSITIONING | `agents/offer_positioning.py` | ❌ no |
| BRAND_STRATEGY | `agents/brand_strategy.py` | ❌ no |
| MARKETING_STRATEGY | `agents/marketing_strategy.py` | ❌ no |
| LEAD_GENERATION | `agents/lead_generation.py` | ❌ no |
| OUTREACH | `agents/outreach.py` | ❌ no |
| PROJECT_OPERATIONS | `agents/project_operations.py` | ❌ no |
| KNOWLEDGE | `agents/knowledge.py` | ❌ no |
| RISK_REVIEW | `agents/risk_review.py` | ❌ no |

Verifica: `grep -rn "from agents.brand_strategy\|from agents.marketing_strategy\|..." --include="*.py"` → zero risultati.

### Skills vs tools vs agents — concetti sovrapposti
- **Tools** (`core/notion_tools.py`, 680 LOC): funzioni Python esposte come tool calling agno. Reali, eseguono I/O.
- **Skills** (`skills/*/SKILL.md`): 16 cartelle con markdown statico caricato via `agno.skills.LocalSkills`. Sono **istruzioni testuali** appiccicate al system prompt. Sovrapposte con `instructions` hardcoded nei file agent.
- **Agents**: 9 BoardAgent diversi, di cui 6 hanno solo prompt diversi sullo stesso BoardAgent base.

In pratica: l'unica vera distinzione è il **system prompt** (prompt diverso → "agente diverso"). Gli altri layer (skills, tools per-agente, registry, alias map) sono **ceremonia**.

### Orchestrazione reale
- `run_agents_parallel` (`core/orchestrator.py:83-100`) esiste ma **non è mai chiamata** nel codice di produzione (solo nei test).
- `run_objective` (`core/orchestrator.py:103-113`) referenzia `OrchestratorAgent()` senza importarlo → bug nascosto. `handlers.py` lo usa via `run_objective_async` in `_dispatch_plan_tasks_background` (`handlers.py:253`).
- Giuseppina **dovrebbe** produrre un piano JSON e fare fanout. In pratica fa quasi tutto da sola con tool calling.

**Verdetto**: la metafora del "board di consiglieri" è marketing interno. È un singolo LLM con 10 tool e un prompt molto lungo. Tutto il resto è layer di indirezione.

---

## 3. Dashboard UX

### Route inventory
| URL | File | LOC | Cosa mostra | Azioni reali | Verdetto |
|---|---|---|---|---|---|
| `/` | `controllers/home_controller.py` + `services/home_service.py` | 40+344 | KPI cards, pipeline funnel, activity feed | nessuna (link a sotto-pagine) | dashboard read-only |
| `/inbox` | `routes/inbox.py` | 64 | lead da website_contact_form | nessuna (visualizza) | duplicato di pipeline |
| `/pipeline` | `routes/pipeline.py` | 277 | board pipeline kanban | edit stato lead, note | ✅ utile |
| `/lavori` | `routes/lavori.py` | 213 | lista task e progetti | edit task | duplica Notion task DB |
| `/lavori/{id}` | `routes/lavori.py` | | dettaglio progetto | upload doc, link agente | semi-utile |
| `/agents` | `routes/agents.py` + service 750 LOC | 69 | grid agenti con stato | chat con agente, run task ad hoc | ✅ utile (la chat) |
| `/agents/{slug}` | id. | | dettaglio agente, history | chat, run, vedi system prompt | mid |
| `/approvals` | `routes/approvals.py` | 213 | bozze in attesa | approva/rifiuta | ✅ utile MA polluted da telegram chat turns |
| `/logs` | `routes/logs.py` | 68 | log esecuzioni | filtri | debug, non operativo |
| `/memory` | `routes/memory.py` | 73 | shared_memory KV | edit | edita memoria seed |
| `/board-chat` | `routes/board_chat.py` | 104 | chat con Giuseppina sul web | invia messaggio | ⚠️ duplica Telegram |
| `/workshop-admin` | `routes/workshop.py` | 639 | CRUD pacchetti workshop | upload immagini, edit HTML | ❓ utile solo a Luigi, ma scoped a un caso particolare |
| `/admin` | `routes/admin.py` | 230 | user mgmt, settings | crea/disattiva utenti | ok per multi-utente, ma è single-user |
| `/admin/reports` | `routes/admin.py` | | report aggregati | export CSV? | parziale |
| `/analytics` | `routes/analytics.py` | 74 | snapshot PostHog | nessuna | gimmick |
| `/api/intake/*` | `routes/public_intake.py` | 863 | K-BOT chat + contact form site | POST pubblico (no auth, rate-limited) | ✅ critico per sito |

### Pattern problematici
- **HTMX + Jinja partials** funziona, ma ogni pagina ha layout proprio. Niente sistema di componenti coerente.
- **Tailwind via CDN** (`templates/base.html:8`): non bundled, no purge, ~3MB. La dashboard è dietro auth quindi performance importa meno, ma è comunque male.
- **`/board-chat` web + Telegram** → due UI per la stessa conversazione, con storia salvata in `approvals.content_type='telegram_agent_chat'`. Confusione.
- **`/inbox`** vs **`/pipeline`**: una mostra lead da form sito, l'altra tutta la pipeline. La separazione non aiuta — un singolo "Pipeline" con filtri canale sarebbe più semplice.
- **`/lavori`** vs Notion DB "Task": funzionalità identica, ma su Notion l'esperienza è migliore (drag-drop, filtri, viste). La pagina dashboard è inferiore.
- **`/workshop-admin`**: 639 LOC per gestire una lista di pacchetti workshop in memoria condivisa con upload immagini. Era una feature one-off per il sito, oggi è dead weight non integrato col resto.
- Conteggio sidebar (`base_context` chiama `get_pending_approvals_count` + `get_projects_count` ad ogni render → 2 query a Notion per ogni hit della dashboard).

---

## 4. Data Model

### Supabase (6 migrazioni)
- `001_initial.sql`: `tasks`, `agent_logs`, `approvals`, `pipeline_leads`, `shared_memory`.
- `002_projects.sql`: `projects`, `project_phases`, `project_tasks`, `project_documents`, `project_agent_links`. Aggiunge `project_id` a approvals/agent_logs.
- `003_agent_logs_archive.sql`: tabella archivio log con cleanup job.
- `004_board_accounts.sql`: `board_users` + `board_sessions` (auth dashboard).
- `005_enable_rls.sql`: RLS deny-all anon su tutte le tabelle.
- `006_analytics_snapshots.sql`: snapshot PostHog.

### Notion (database)
`core/notion_board.py:14-21` mappa 7 database Notion:
- `Task` ↔ `tasks` Supabase
- `Pipeline Lead` ↔ `pipeline_leads`
- `Clienti` ↔ ❌ no equivalente Supabase
- `Commesse` ↔ `projects`
- `Approvazioni` ↔ `approvals`
- `Log AI` ↔ `agent_logs`
- `Memoria / Decisioni` ↔ `shared_memory`
- ignorato: `Verbali / Sopralluoghi`

### Lo split: principled or accidental?
**Accidentale**. Il codice fa `if notion_board.notion_enabled(): scrivi notion; else: scrivi supabase` in 6+ posti (`agents/base.py:567-705`, `core/approval.py`, `core/memory.py`, ecc.). Sono **due implementazioni parallele** della stessa cosa, non un'architettura ibrida.

In produzione (Railway logs nell'env: `NOTION_API_TOKEN` configurato) gira in **Notion-mode**, quindi Supabase è di fatto **fallback inutilizzato**. Le migrazioni 002–006 sono per metà morte.

### Problemi specifici
- **`approvals` come tavolo conversazionale** (`agents/orchestrator.py:243-260`): `content_type="telegram_agent_chat"` inserisce ogni turno utente↔Giuseppina nella tabella `approvals` (sia Notion che Supabase). Ogni messaggio crea una "approvazione" in stato `done`. La tabella Notion "Approvazioni" cresce all'infinito; la sidebar conta solo quelle in stato `draft/review` quindi non lo vedi, ma è inquinata.
- **`shared_memory` seed obsoleto** (`core/memory.py:10-90`): contiene `B&B, ristoranti, studi tecnici` come target (positioning v1), incompatibile con il positioning K2-AI v2 di "PMI 5-50". Se il seed gira mai (primo avvio), riscrive cose sbagliate. Giuseppina cita queste informazioni dal `get_memory_as_context` → contamina ogni risposta.
- **`Clienti`** vive solo in Notion, ma `tasks` e `pipeline_leads` linkano "Cliente" come relation. Non c'è una single source of truth.
- **Colonne unused**: `pipeline_leads.score` ha check 1-10 in SQL ma il prompt agente parla di scoring 0-100 (`agents/orchestrator.py:84`). Inconsistenza.
- **`board_users` + `board_sessions`** (mig. 004): supporto multi-utente, ma Telegram filtra su singolo `telegram_chat_id` (`handlers.py:298-300`). Non avete clienti che usano la dashboard. Tutto questo apparato non serve.

---

## 5. Telegram Bot

### Comandi
`bot.py:53-65`: `/start /help /task /agent /approvals /schedule /status /memory /log /pipeline /skip /undo /refresh_schema` + handler text + handler attachment + callback query handler. 13 comandi più message handler.

### Authorization
`handlers.py:298-300`:
```python
def is_authorized(update: Update) -> bool:
    user = update.effective_user
    return bool(user and str(user.id) == str(settings.telegram_chat_id))
```
Single-user check su env var. Per Luigi solo va bene, ma:
- **chiunque conosca il bot token può scrivere al bot** dal proprio account → fallisce auth silenziosamente. Manca un "non sei autorizzato" reply (alcuni handler lo fanno, altri no).
- Webhook secret (`X-Telegram-Bot-Api-Secret-Token`) è validato in `app.py:259` (buono).

### State management
- `_CHAT_LOCKS: dict[str, asyncio.Lock]` (`handlers.py:44`): mutex per chat_id, mai garbage-collected.
- `core/session_state.py` (119 LOC): finestra contestuale in-memory dei turni.
- `core/conversation.py`: carica storia chat **dal DB approvals** (filtrato per `content_type=telegram_agent_chat`). Si rebuilda ad ogni messaggio.
- `core/action_guard.py` (243 LOC): conferme pending in dict process-local. Se il bot riavvia, perde le conferme in volo.
- `core/undo.py` (293 LOC): sistema undo basato su snapshot azione. Fragile, e richiede che Luigi conosca le frasi giuste.

### Pattern delicati
- `handlers.py` è un **god file da 1.140 righe** con: download allegati, parsing intent, dispatch agenti, formattazione output, gestione approvals inline. Una cosa da rebuilder al netto, non da rifattorizzare.
- `interfaces/telegram/assistant.py` (966 LOC): heuristics + OpenAI per classificare l'intent del messaggio in azioni (`_heuristic_action`, `_llm_action`). Funziona ma è opaco da debuggare.
- Allegati salvati su disco locale (`uploads/chat/telegram/...`) — su Railway sono **ephemeral**: si perdono ad ogni redeploy. Non c'è S3/object storage.

### Verdetto sul valore
Il bot Telegram è **dove avviene la maggior parte del valore reale**: chat naturale con Giuseppina, crea task/lead in Notion, riceve briefing scheduler. Se domani spegnessi la dashboard nessuno se ne accorgerebbe; se spegnessi il bot perderesti il prodotto.

---

## 6. Scheduler

`core/scheduler.py:451-538` — 8 job APScheduler in fuso Europe/Rome:

| Job ID | Cron | Cosa fa | Output | Verdetto |
|---|---|---|---|---|
| `task_deadline_reminder` | configurabile | scansiona task con deadline imminente | telegram msg | ✅ utile |
| `daily_brief` | configurabile | chiama chief_of_staff con stato + pipeline | telegram msg "informativo" | ⚠️ utile se i dati Notion sono freschi |
| `weekly_plan` | configurabile | chiama content_engine per piano settimanale | telegram msg | ❓ il piano LLM-generated può essere noise se sganciato dai dati |
| `kpi_update` | configurabile | chiama finance_kpi per KPI dashboard | telegram msg | ❌ se non hai dati Stripe/revenue agganciati, è LLM che inventa |
| `approval_reminder` | mon-fri 12:00, 20:00 | conta approvals pending | telegram msg | ✅ utile, ma triggera anche su telegram chat turn fake |
| `market_pulse` | mer 9:00 | chiama market_intelligence con search web | telegram msg | ❌ rumore puro: ricerche web settimanali con valore segnale basso |
| `cleanup_logs` | lun 3:00 | archivia agent_logs vecchi | nessuno | ✅ ok |
| `schema_refresh` | ogni 6h mon-fri | re-discovery schema Notion | nessuno | ✅ ok |
| `posthog_sync` | configurabile | snapshot PostHog → supabase | DB | ✅ ok, dati per analytics page |

### Problemi
- **Generative noise**: 3 dei 9 job (`weekly_plan`, `kpi_update`, `market_pulse`) sono "fai dire qualcosa a un LLM ogni X giorni e mandalo a Luigi". Senza dati di input reali (revenue, leads convertiti, CAC), l'output è plausibile ma vuoto.
- **Weekend skip globale** (`_ROUTINE_WEEKDAY_ONLY_JOBS`): nasconde che alcuni job dovrebbero proprio non esistere il lunedì.
- **De-dup window 180s** (`_JOB_MIN_INTERVAL_SECONDS`): patch per evitare doppi run dopo crash, sintomo di state management fragile.
- **Mancano job che servirebbero davvero**:
  - Sync Stripe / Resend / Airtable (lead form sito) → DB locale ogni 15 min
  - Alert su lead nuovo che non ha avuto risposta in 24h
  - Backup automatico Notion → JSON locale (Notion sparisce o ti banna, perdi tutto)
  - Report metriche K2-AI reali (visite sito da PostHog, conversion form, K-BOT completions)

---

## 7. Code Quality Issues

### File > 500 righe (god objects)
- `core/notion_board.py` (1.304) — client + serializers + business logic Notion in un file. Va spezzato.
- `interfaces/telegram/handlers.py` (1.140) — vedi §5.
- `core/scheduler.py` (995) — definizione job + helpers + setup mescolati.
- `interfaces/telegram/assistant.py` (966) — intent routing.
- `interfaces/dashboard/routes/public_intake.py` (863) — K-BOT chat + contact form + email + Notion sync.
- `agents/base.py` (739) — BoardAgent con system prompt enorme inline (oltre 100 righe di prompt nel codice Python).
- `services/agents_service.py` (750) — ok ma sul limite.
- `core/notion_tools.py` (680) — tool wrapper, accettabile come unico file.
- `interfaces/dashboard/routes/workshop.py` (639) — feature scoped, da estrarre o eliminare.

### Bug / inconsistenze concrete
- `core/orchestrator.py:110` usa `OrchestratorAgent()` ma non lo importa. **NameError a runtime** se `run_objective` viene chiamato senza altri import (in pratica importato indirettamente via `agents/orchestrator.py:266`, fragile).
- `db/models.py:96` definisce `score: int | None = Field(ge=1, le=10)` per PipelineLead, ma `agents/orchestrator.py:85` dice "Score (0-100)" nel prompt — gli agenti potrebbero inserire 75 e fallire validation.
- `core/memory.py` seed con positioning "B&B/ristoranti" — non più valido per K2-AI v2.
- `core/scheduler.py:32-41` lista `_ROUTINE_WEEKDAY_ONLY_JOBS` hardcoded fuori dalla definizione job → drift garantito.
- `agents/base.py:25-31` `INFORMATIONAL_CONTENT_TYPES` hardcoded: aggiungere un tipo richiede modifica codice.
- Inconsistenza naming: `interfaces/telegram/handlers.py:298` usa `settings.telegram_chat_id`, ma il bot fa polling globale → nessun filtro sul chat_id in molti handler (esempio `attachment_message_handler`).
- `services/agents_service.py:36-46` ha `URL_SLUG_ALIASES` che duplica `core/orchestrator.AGENT_ALIAS_MAP`.
- `controllers/__init__.py:11` espone `agents_router, home_router` come singoli — ma altri router in `interfaces/dashboard/routes/` non passano da controllers. **MVC layering incompleto**: 12 route file ancora bypassano controllers/services.
- `tests/test_mvc_layering.py` esiste — chiaramente l'avete provato a fare. Non l'avete finito.

### Async/sync mixing
- `agents/base.py` è interamente sync. Lo si chiama da `run_agent_async` che fa `asyncio.to_thread` (`core/orchestrator.py:80`). OK, ma ogni chiamata occupa un thread pool worker.
- Dashboard FastAPI è async. Route che chiamano `notion_board.list_*` (sync, requests/httpx sync) — vedo `httpx` in `notion_board.py:8` ma probabilmente sync `Client` non `AsyncClient`. → blocca event loop.
- `core/scheduler.py:56-58` wrappa sync con `run_in_executor`, ok.

### Print / logger spam
- `tools/fix_notion_intake.py:177-186` ha 10 print, ma è uno script one-off → accettabile.
- Loguru usato ovunque, ma con livelli inconsistenti (`logger.info` per cose che dovrebbero essere `debug`, `logger.warning` per cose normali).
- Manca logging strutturato JSON (avrebbe senso su Railway).

### Hardcoded magic
- Path uploads (`UPLOADS_DIR = Path(__file__).resolve().parents[2] / "uploads"`) ripetuto in 5+ file con sintassi leggermente diversa.
- Strings tipo `"telegram_agent_chat"`, `"website_contact_form"`, `"founder"` sparpagliate. Mancano enum.
- `NotionDB` constants (`DB_TASKS = "Task"`) in italiano hardcoded — se rinomini il DB Notion, code rotto.

---

## 8. Conceptual Issues — Opinionated

Onesto, Luigi: ecco quello che secondo me è **veramente storto** nel sistema attuale.

### 8.1. Il multi-agente è cosplay
Hai 9 agenti registrati + 8 dead. Ma **tutti i messaggi reali passano da Giuseppina**, che chiama tool Notion e risponde. Gli altri agenti sono prompt diversi che girano principalmente da scheduler una volta a settimana. Non c'è collaborazione, non c'è planning multi-step orchestrato. È **un singolo Claude con 10 tool e diversi system prompt cambiati a mano**.

La metafora "board di consiglieri" funziona bene **come UI mentale** (Giuseppina, Genoveffa, Peppe...), ma non serve **come architettura tecnica**. Un'azienda da 1 persona non ha bisogno di un CdA simulato. Ha bisogno di un assistente che:
1. Capisca la richiesta
2. Scelga il tool giusto (CRM/email/calendar/docs)
3. Esegua
4. Riassuma

Quello fa già Giuseppina. Gli altri sono per la photo op.

### 8.2. Notion-as-database è una scelta che ti sta limitando
Pro:
- ✅ UI gratuita per Luigi su mobile/web (Notion app)
- ✅ Schema flessibile, modifica al volo
- ✅ Backup gestito da Notion

Contro:
- ❌ API Notion è lenta (300-800ms per query), costosa, e rate-limited (3 req/sec)
- ❌ Schema discovery a runtime ogni 6 ore (`schema_refresh`) — fragile
- ❌ Query complesse (es. "lead non contattati da 7 giorni con score > 70") richiedono fetch-all + filter client-side
- ❌ Relations Notion (Cliente → Commessa → Task) sono painful da query in modo coerente
- ❌ Lock-in: se domani Notion alza i prezzi o muore, sei nudo
- ❌ Doppia scrittura Supabase+Notion col flag `notion_enabled()` ti raddoppia la superficie bug
- ❌ Le scritture LLM-generated finiscono spesso "quasi valide" (campi che non esistono, select values inventati) → fix_notion_intake.py è la prova

**Verdetto**: Notion ti sta bene **come visualizzazione**, non come database operativo. Mossa giusta: **Postgres come source of truth, Notion sync periodico opzionale per visualizzazione mobile** (sola lettura o write-back con conferma).

### 8.3. La dashboard web non è un prodotto, è un'illusione di controllo
Hai 14 route, ~2.700 LOC di route + service, ma la maggior parte fa:
- Mostra cose che già vedi su Notion (peggio)
- Approva/rifiuta bozze che potresti fare via inline button Telegram (e infatti lo fai)
- Chat alternativa con Giuseppina (`/board-chat`) che non usi mai perché preferisci Telegram

Le UNICHE route che hanno valore unico:
- `/api/intake/*` — è critica per il sito K2-AI (K-BOT, contact form). **Questa va salvata.**
- `/agents/{slug}` chat — utile se vuoi fare conversazioni lunghe / con allegati grossi che su Telegram fa schifo. Forse.
- `/workshop-admin` — caso particolare, ma se hai un workshop in corso ha senso.
- `/approvals` — utile se ricevi tante draft contemporaneamente. Oggi probabilmente no.

**Tutto il resto è un visualizzatore di Notion costruito a mano**. Hai sprecato 2.000+ LOC.

### 8.4. Gli scheduler "generativi" sono noise
`daily_brief`, `weekly_plan`, `market_pulse`, `kpi_update` chiedono a un LLM di "produrre" qualcosa ogni giorno/settimana. Senza dati di input rigorosi (revenue, leads, CAC, contracts, calendar), l'LLM **scrive bene del nulla**. Tu lo leggi (forse), lo ignori, prosegui.

Quello che servirebbe è il contrario: **dati reali → alert specifici**. Esempio:
- "Lead Mario Rossi ha aperto la proposta 3 volte ma non ha risposto da 4 giorni → contattalo"
- "Pipeline scesa sotto 3 lead caldi → fai outreach"
- "Stripe: MRR -€200 questo mese, da chiamare X"
- "Calendar: domani 3 call, ti preparo i brief?"

Queste regole sono **deterministiche**, costano zero token, e portano valore. Quello che hai oggi è teatro.

### 8.5. La "memoria condivisa" è seed obsoleto
`core/memory.py` ha un seed con posizionamento vecchio (B&B/ristoranti). Se non hai mai cambiato `shared_memory` su Supabase post-pivot K2-AI v2, **Giuseppina sta operando con il contesto sbagliato**. Apri `get_memory_as_context()` e vedi cosa entra nel system prompt → potrebbe spiegare perché ogni tanto ti sembra "fuori asse".

### 8.6. Two interfaces, one user
Hai Telegram + dashboard web, entrambi richiamando lo stesso codice agent. Per **un solo utente**. Sembra una cosa pro ("multi-channel"), in realtà è duplicazione: ogni feature va implementata due volte.

Una scelta sola:
- **PWA mobile-first** (login, push, allegati ok, gira anche da desktop) — sostituisce sia dashboard che Telegram. Più moderno, e tutti i dati restano nel tuo dominio.
- **Solo Telegram** — semplifichi al massimo, butti la dashboard.

Mantenere entrambi ha senso solo se hanno scopi distinti (Telegram = quick capture; web = lavoro lungo). Non sembra il tuo uso reale.

### 8.7. Job-to-be-done reale
Da quello che si capisce dal codice + contesto K2-AI, il sistema **dovrebbe**:
1. **Capture rapido** (Telegram-style): "ho parlato con Mario, fissa call martedì, è interessato a workflow setup"
2. **Triage automatico**: classifica, link al cliente, calcola priorità
3. **Reminder mirati**: tira fuori al momento giusto la cosa giusta
4. **Briefing reale**: prima di una call, tira fuori storia cliente + offerte già discusse + ultimo touchpoint
5. **Generation on-demand**: quando serve, produce proposte/email/contratti partendo dai dati reali
6. **Pipeline visibile**: chi è dove, cosa devo fare oggi, cosa è bloccato

Il sistema fa #1, #2 e #5 bene (via Giuseppina+Telegram). Fallisce #3 (gli alert non sono data-driven), #4 (non c'è briefing pre-call con storia cliente), #6 (la dashboard mostra dati ma non azioni prioritizzate).

---

## 9. Missing Features

Cose che a Luigi servirebbero davvero (basato su contesto K2-AI, non generico enterprise):

### High-impact, basso-effort
- **Sync Stripe ↔ DB**: revenue reale, MRR, churn. Senza questo, ogni `kpi_update` LLM-generated è fiction.
- **Sync calendario (Google Cal o Apple Cal)**: alert pre-call con brief cliente, todo post-call, "domani hai 3 call".
- **Sync email (Gmail IMAP/Graph)**: scan automatico email → crea lead → crea task. Oggi ogni email è data persa.
- **Briefing pre-call**: "ho una call con Mario alle 15" → bot ti manda: storia, ultimi touchpoint, offerta in pipeline, link Notion, suggerimenti domande.
- **Daily action list reale**: 3-5 azioni concrete oggi, derivate da dati (lead non contattati, task scaduti, follow-up dovuti). Non un LLM-narrative.
- **Backup Notion → JSON nightly**: 1 cron job, 30 minuti di lavoro.

### Medi
- **Mobile PWA con notifiche push**: prendere appunti vocali → trascrizione → routing.
- **Pipeline con SLA**: "lead in stato Qualificato da >7gg → alert".
- **Lead form sito → push diretto al bot**: oggi va a Notion poi ti notifica via email. Lento.
- **K-BOT analytics**: quanti completion, quale % converte in lead reale, drop-off per turn.

### Bassi ma utili
- **Search globale**: cerca "Rossi" e trovi cliente + tutti i task + email + lead.
- **Export PDF proposta da template** automatico dai dati pipeline.
- **Skill marketplace interno**: i SKILL.md sono carini ma nessuno li riusa. Renderli versionati e attivabili.

### Observability
- **Sentry attivo** (`core/logger.py` ha `init_sentry()` ma se non hai DSN set, off).
- **Token & cost dashboard**: quanto spendi al giorno per provider, per agente. Oggi log warning a soglia 4k token, niente di aggregato.
- **Trace per agent invocation**: quale prompt, quale tool, quale output, quanto tempo.

---

## 10. Rebuild Proposal — KEEP / THROW / NEW

### KEEP (porta avanti)
- **Pydantic models** in `db/models.py` — buoni come base.
- **Logica K-BOT** in `routes/public_intake.py` (deve continuare a servire il sito K2-AI).
- **Logica Notion sync** in `core/notion_board.py` (utile come **sync layer**, non come primary DB).
- **System prompt di Giuseppina** in `agents/orchestrator.py` (è il prodotto reale, va mantenuto/iterato).
- **CSRF + rate limit + auth** in `app.py` (già fatto bene).
- **Telegram polling/webhook** infrastructure (`bot.py`) — è semplice, funziona.
- **Skill markdown** (`skills/*/SKILL.md`) — utili come prompt fragments.

### THROW (butta)
- `stitch/`, `stitch_step4b/` — mockup HTML morti.
- 8 file agent aliased non istanziati (`agents/{brand_strategy,marketing,lead_gen,offer_pos,outreach,project_ops,risk,knowledge}.py`).
- AGENT_ALIAS_MAP — semplifica a un agente unico con multiple "modalità" via prompt.
- `core/undo.py`, `core/action_guard.py` se non li usi quotidianamente — sono complessità per feature niche.
- `/board-chat` web — duplicato Telegram.
- `/inbox` separato — fondilo in `/pipeline`.
- `/lavori` — usa Notion direttamente.
- `/workshop-admin` — sposta in un microservice separato se serve, sennò archivia.
- `/analytics` PostHog snapshot page — di nicchia.
- Scheduler jobs `weekly_plan`, `market_pulse`, `kpi_update` — sostituisci con alert data-driven.
- Doppia path Supabase+Notion ovunque — scegli **una** source of truth.
- `board_users` + `board_sessions` migration 004 — single-user.

### NEW architecture (mia proposta)

**Stack**:
- **Backend**: Python FastAPI o Node TypeScript (entrambi vanno; se vuoi typesafe end-to-end → Next.js full-stack su Vercel/Railway).
- **DB**: **Postgres come source of truth** (Supabase EU resta perfetto, hai già RLS). Notion come **read-only view** sync nightly per uso mobile rapido.
- **LLM**: Claude come primary, OpenAI come fallback. Aggiungi **prompt caching** (`anthropic-skills:claude-api`) — i system prompt lunghi ti stanno costando 10x quel che dovrebbero.
- **Frontend**: **PWA mobile-first** (Next.js 14 + Tailwind bundled, niente CDN, shadcn/ui per componenti coerenti). Push notifications via Web Push API (sostituisce parzialmente Telegram alert).
- **Telegram**: **lo mantieni**, ma come **canale di capture rapido + alert**, non come unica UI.
- **Auth**: una sola via — Supabase Auth con magic link (single-user, ma futuro-proof se Luigi vuole far entrare un collaboratore).
- **Observability**: Sentry + Langfuse (LLM trace) + Posthog (UI usage).

**Componenti**:
1. `core-agent`: un solo agente Claude con **20-30 tool**. Niente "board". Tool: CRM (lead/cliente/task/proposta), calendar, email, stripe, knowledge base, web search, file ops. La "personalità" la metti nel prompt — basta.
2. `data-sync`: cron jobs che pullano Stripe, calendar, email (Gmail), site forms → Postgres.
3. `alert-engine`: regole deterministiche su Postgres → push/Telegram. Es. SQL view "leads_needing_followup" → notification.
4. `web-pwa`: dashboard mobile-first con 5 viste: Today, Pipeline, Clienti, Inbox, Settings.
5. `telegram-bot`: capture rapido + comandi power-user.
6. `public-intake`: K-BOT chat + form sito (resta separato, già funziona).

### Trade-off recap

| Decisione | Opzione A | Opzione B | Raccomandazione |
|---|---|---|---|
| Linguaggio | Python/FastAPI (status quo) | Next.js TypeScript full-stack | **Python se vuoi velocità ricostruzione**; TS se vuoi PWA tight con BE. Io sceglierei **TS Next.js + tRPC** per nuovo, con servizio Python separato per agent LLM (Claude SDK è ottimo in Python). |
| Agent | Multi-agente (status quo) | Single agent + tools | **Single agent + tools**. La metafora "board" la mantieni nell'UI/prompt, non nel codice. |
| DB | Notion-primary | Postgres-primary + Notion view | **Postgres-primary**. Notion come display layer opzionale. |
| UI | Jinja+HTMX (status quo) | PWA Next.js + shadcn | **PWA**. È il 2026, Tailwind CDN non è una soluzione. |
| Channel | Telegram + dashboard | PWA + push + Telegram (capture) | **PWA + Telegram come capture**. Niente dashboard web tradizionale. |

---

## Priority Matrix

### High value, low effort (fai subito, anche senza rebuild)
1. **Rimuovi seed memory obsoleto** in `core/memory.py:10-90` — sostituiscilo con positioning K2-AI v2.
2. **Disattiva o sostituisci** `weekly_plan`, `kpi_update`, `market_pulse` scheduler jobs — produce noise.
3. **Stop salvare chat turn in `approvals`** (`agents/orchestrator.py:243-260`) — crea tabella `conversation_turns` separata.
4. **Fix `OrchestratorAgent` import** in `core/orchestrator.py:110`.
5. **Rimuovi `stitch/` e `stitch_step4b/`** dal repo.
6. **Cancella i 8 agent file dead** (brand_strategy, marketing_strategy, lead_generation, offer_positioning, outreach, project_operations, risk_review, knowledge).
7. **Bundle Tailwind** invece di CDN se mantieni la dashboard.

### High value, medium effort (fase 1 rebuild)
8. **Postgres primary, Notion sync read-only**: migra le scritture su Supabase, scheduler 1/giorno pubblica view su Notion.
9. **Sync Stripe + Calendar + Email**: 3 cron job, dati reali in DB.
10. **Alert data-driven**: 5-10 regole SQL che generano notifications.
11. **Briefing pre-call**: bot manda brief automatico 30 minuti prima call calendario.
12. **Compatta i 9 agenti in 1**: stesso BoardAgent base, 1 system prompt con sezioni, tool calling completo.

### High value, high effort (fase 2 rebuild)
13. **PWA mobile-first** sostitutiva di dashboard.
14. **Knowledge base RAG**: clienti / proposte / chat passate → embedding → semantic search via tool.
15. **Voice capture** Telegram: nota vocale → Whisper → triage automatico.

### Low value (skip)
- Multi-utente board_users/sessions.
- /board-chat web alternativo a Telegram.
- /workshop-admin se non lo usi più.
- 8 mock Stitch HTML files.

---

## Appendix: numeri di riferimento

- Totale LOC Python: ~16.400
- File Python: 60+
- Template Jinja: ~30
- Migrazioni SQL: 6
- Route FastAPI: 14
- Comandi Telegram: 13
- Agenti registrati: 9 (di cui 1 davvero in uso)
- Agenti dead code: 8
- Scheduler jobs: 9
- Skill markdown: 16
- Tabelle Supabase: 12
- Database Notion mappati: 7

**Stima rebuild** (assumendo TS Next.js + Python agent service):
- Setup base + DB + auth: 1 settimana
- Migration data Notion → Postgres: 3-5 giorni
- Agent core con 20 tool: 1 settimana
- PWA Today / Pipeline / Clienti: 1.5 settimane
- Telegram bot snello: 3-4 giorni
- Integrations Stripe/Calendar/Email: 1 settimana
- Alert engine: 3-4 giorni
- Polish + deploy: 1 settimana

Totale: **6-8 settimane** part-time, con 60-70% di codice in meno del sistema attuale.
