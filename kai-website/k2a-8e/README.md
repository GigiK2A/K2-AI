# k2a-8e — Motore di esecuzione deliverable (Phase-1 skeleton)

> **STATO OWNERSHIP (2026-06-04)**: engine costruito lato Luigi come **candidato**.
> Esiste in parallelo il `PROMPT_8e_Phase1` che Code potrebbe eseguire sul Mac di
> Luca (`~/Code/k2a-8e`). **Decisione su quale engine vince: RIMANDATA** finché non
> arriva lo zip completo di Luca (MCP + skill + snapshot reali). Fino ad allora
> questo serve come riferimento/mock avanzato e per sviluppare il client K-BOT
> contro un engine fedele al contratto. NON è ancora "il" motore ufficiale.

Implementa il design `8e_Phase0_design_API.md` e il `PROMPT_8e_Phase1` (pilota
LegalBoost). Servizio FastAPI stateless, deployabile su Railway, contratto API =
`docs/interfaccia-kbot-8e.md §1`.

> **Stato**: ENGINE reale (pipeline 6 stadi, render ReportLab, gate L1/L2, API).
> Gli ASSET di dominio (blueprint, snapshot normativo) sono **FIXTURE placeholder**
> finché Luca non consegna `k2a-skills` + lo snapshot reale. Vedi §"Confine".

## Confine ENGINE (Luigi) ↔ ASSET (Luca)

L'engine è asset-agnostico. Carica blueprint/output-schema/form/snapshot tramite
`app/assets.py`:

| Asset | Reale (Luca) | Fallback (qui) |
|---|---|---|
| blueprint | `$K2A_SKILLS_DIR/blueprints/<id>.blueprint.json` | `fixtures/` |
| output-schema, form | `$K2A_SKILLS_DIR/<service>/schemas/` | `fixtures/` |
| grounding snapshot | `$K2A_8E_SNAPSHOT` (da `build_snapshot.py` via normattiva) | `grounding/legalboost.snapshot.json` (placeholder NON normativo) |
| L1/L2 | `app/validate.py` locale (semantica del gate) | — |

**Drop-in produzione**: settare `K2A_SKILLS_DIR` + `K2A_8E_SNAPSHOT` agli asset
reali → zero modifiche al codice. Il `meta.blueprint_source`/`snapshot_source`
nell'output dichiara se gira su REALE o FIXTURE.

⚠️ **I testi nello snapshot fixture NON sono legge reale.** Il deliverable
prodotto ora è strutturalmente valido ma NON vendibile finché lo snapshot non è
generato da normattiva (gate pre-vendita).

## Pipeline (6 stadi, `app/pipeline.py`)

`routing` (catalogo chiuso, refuse fuori-catalogo) → `resolve` (fatti
deterministici dallo snapshot; manca → `unresolvable_placeholder`) → `filiera`
(Sonnet scrive la prosa attorno ai fatti; offline se no key) → `validate` (L1+L2;
fail → non consegna) → `render` (HTML+PDF ReportLab) → `output` (path locali in
Phase-1; prod = upload K-BOT).

## Run locale

```bash
cd kai-website/k2a-8e
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt

# coverage-report snapshot (fail-closed)
python grounding/build_snapshot.py

# smoke test (offline, no rete) — genera un PDF reale in _out/
python tests/smoke_test.py

# server
uvicorn app.main:app --port 8800
curl localhost:8800/health
```

## Env

| Var | Default | Note |
|---|---|---|
| `K2A_8E_API_KEY` | `dev-key` | Bearer backend-to-backend |
| `K2A_8E_API_KEY_NEXT` | — | seconda chiave per rotazione (G6) |
| `ANTHROPIC_API_KEY` | — | se assente → filiera offline (template) |
| `K2A_8E_MODEL` | `claude-sonnet-4-5` | modello filiera |
| `K2A_SKILLS_DIR` | — | repo asset reali di Luca (drop-in) |
| `K2A_8E_SNAPSHOT` | `grounding/legalboost.snapshot.json` | snapshot grounding |
| `K2A_8E_OUT_DIR` | `_out/` | output locale (Phase-1) |
| `PORT` | `8800` | iniettato da Railway |

## Deploy Railway

```bash
railway up --detach   # da kai-website/k2a-8e/
# poi: setta K2A_8E_API_KEY + ANTHROPIC_API_KEY nelle env Railway
```

Il K-BOT punta qui via `K2A_8E_BASE_URL` (vedi `kbot/backend/app/settings.py`).
In dev il K-BOT usa il MOCK (`kbot/mock-8e`); per il flow reale → questo servizio.

## Cosa manca per "LegalBoost vendibile" (gate, da Luca)

1. `k2a-skills` accessibile (blueprint reale) → `K2A_SKILLS_DIR`
2. snapshot reale via `normattiva get_articolo` (override Cod.Civ. 1341/1342)
3. coverage-report PASS senza `da confermare`/`INCOMPLETO`
4. membrana §9 chiusa (entitlement JWT G1, storage cross-service G2)

Phase-2: peer-review subagent, L1/L2 via MCP reale, bundle artefatti, multi-servizio.
