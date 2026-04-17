# AI Board

Fondamenta del sistema multi-agente per la gestione business.

## Setup

1. Installa le dipendenze con `uv sync`
2. Attiva l'ambiente con `source .venv/bin/activate`
3. Copia `.env.example` in `.env`
4. Compila le variabili reali
5. Esegui `db/migrations/001_initial.sql` su Supabase
6. Avvia con `python main.py`

## Step 1 incluso

- bootstrap applicativo
- connessione Supabase
- seed e cache della memoria condivisa
- classe base `BoardAgent`

## Non incluso in questo step

- agenti specifici
- bot Telegram
- dashboard FastAPI
- scheduler

## MVC layering

La dashboard FastAPI è organizzata in quattro strati, con dipendenze
direzionate sempre da "fuori" verso "dentro":

```
HTTP ─▶ controllers/ ─▶ services/ ─▶ repositories/ ─▶ Supabase / Notion
                           │
                           └─▶ core/ (dominio, orchestrator, notion_board…)
Template Jinja  ◀── View  (interfaces/dashboard/templates/)
Modelli Pydantic / Enum   (db/models.py)
```

### Responsabilità

- **Model** — `db/models.py` (Pydantic + Enum), schema Supabase in
  `db/migrations/`. Nessun cambiamento in questo refactor.
- **View** — template Jinja2 in `interfaces/dashboard/templates/`.
  Contratto invariato: nomi, partial e variabili di contesto identici.
- **Controller** — `controllers/` (`home_controller.py`,
  `agents_controller.py`). FastAPI router "sottili": parsano la request,
  chiamano un service, renderizzano template o restituiscono JSON. Nessuna
  query diretta, nessuna business logic.
- **Service** — `services/` (`home_service.py`, `agents_service.py`,
  `dto.py`). Orchestrano repository, aggregano/filtrano/ordinano, applicano
  regole di dominio (es. stato agente, feed attività, status meta). I
  payload restituiti sono `TypedDict` tipizzati (`services/dto.py`).
- **Repository** — `repositories/` (`approvals.py`, `agent_logs.py`,
  `pipeline.py`, `tasks.py`). Uniche porte verso i dati (Supabase /
  Notion). Incapsulano la scelta tra i due backend via
  `notion_board.notion_enabled()`, così il service non conosce il
  provider.

### Mappa "prima → dopo"

| Area | Prima | Dopo |
|------|-------|------|
| Home KPI / feed | `interfaces/dashboard/routes/home.py::_load_home_data` | `services.home_service.HomeService.load_home_data` |
| Home routes | `routes/home.py` (logica + render) | `controllers/home_controller.py` (render) + service |
| Lista agenti | `routes/agents.py::_load_agents_data` | `AgentsService.list_agents` |
| Metadati agente | `routes/agents.py::_agent_meta` | `AgentsService.agent_meta` |
| Stato agente | `routes/agents.py::_agent_status` | `AgentsService.agent_status` |
| Storico run | `routes/agents.py::_load_agent_runs` / `_load_agent_history_page` | `AgentsService.load_agent_runs` / `load_history_page` |
| Content Engine generate | inline in route | `AgentsService.run_content_engine` |
| Chat agente | inline in route | `AgentsService.send_agent_chat` + `chat_panel_payload` |
| Letture Supabase/Notion | dict literal sparsi nei route | `repositories.ApprovalsRepository` / `AgentLogsRepository` / `PipelineRepository` / `TasksRepository` |

### Compatibilità legacy

`interfaces/dashboard/routes/home.py` e
`interfaces/dashboard/routes/agents.py` restano come shim: ri-esportano
`router`, `RUN_REGISTRY` e gli helper privati storici
(`_agent_meta`, `_load_agents_data`, `_load_agent_history_page`, …) così
i moduli che già li importavano (`routes/board_chat.py`,
`routes/approvals.py`) continuano a funzionare senza modifiche.

### Tradeoff

- `RUN_REGISTRY` resta un dict di processo nel service: semplice, ma
  non scala oltre un worker. Da migrare a Redis quando si passa a più
  istanze.
- Il flag Notion vs Supabase è controllato dal singolo repository.
  Duplica un po' di condizionali ma evita una gerarchia di classi
  prematura; si può estrarre con `Protocol` se/quando i backend
  divergono ulteriormente.
- I payload service→controller sono `TypedDict`, non dataclass: nessuna
  conversione necessaria lato Jinja, però meno ergonomia IDE rispetto a
  `dataclass`/`BaseModel`.

### Test di parity

`tests/test_mvc_layering.py` copre: shape KPI home, helper agenti
(`build_task_from_form`, `agent_summary`, `system_prompt_sections`),
re-export degli shim legacy, inventario delle rotte esposte dai router.
Eseguibile con:

```bash
uv run python -m unittest tests.test_mvc_layering -v
```
