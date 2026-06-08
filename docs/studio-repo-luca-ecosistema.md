# Studio ecosistema GitHub di Luca (inglucarossi73) — 22 repo

**Accesso**: GigiK2A invitato a tutte le repo, studiate read-only 2026-06-08 (clonate in `/tmp/k2a-study/`).
**Scopo**: capire l'intero ecosistema dietro il motore 8e / K-BOT e cosa è build-time vs runtime.

---

## TL;DR — la mappa mentale

Esistono **DUE ecosistemi K2A distinti** che condividono la sigla:

1. **Portale commerciale PMI** (quello che costruiamo noi: 8e + K-BOT). Repo: `k2a-ai-masterplan`, `k2a-skills`, `k2a-mcp-agevolazioni` (=`k2a-catalogo`), `normattiva-mcp`, `k2a-mcp-deliverable`, `k2a-mcp-quant`, `k2-marketplace`, `k2a-giurisprudenza`, `k2a-skill-evolution`, `k2a-k2bot`.
2. **Ingegneria interna TLC/strutturale** (FUORI portale, D-035). Repo: `k2a-masterplan`, `k2a-mcp-strutturale`, `k2a-mcp-elettrico`, `k2a-mcp-elettrico-validator`, `k2a-mcp-norme-tecniche`, `relsta-k2a`. Strumenti da-tavolo per il consulente ingegnere (iliad/Cellnex/INWIT), non vendibili dal sito.

I 6 `k-bot-*-skills` sono **copie/packaging** della libreria skill per verticale.

**Architettura a 3 livelli** (portale): **L1** K-BOT (agente chat) → **L2** orchestratori/plugin (`k2-marketplace`, skill `flusso-*boost`) → **L3** motori MCP deterministici (calcolo+prezzi+norme).

---

## Conferme che validano la nostra architettura 8e

1. **MCP = build-time, non runtime** (D-043). Il motore 8e NON chiama MCP a runtime: consuma `grounding-snapshot.json` + `catalog.json` + libreria `k2a_validation` (L1/L2 in-process). Esattamente quello che abbiamo costruito. Verificato: `grep` su `kai-website/k2a-8e/app/` = 0 chiamate MCP.
2. **`resolver_stub.py` = reference impl** del pipeline (LegalBoost): la nostra `pipeline.py` ne è la versione di produzione. Allineata.
3. **Determinismo legale** (D-028/029/030/031): testo normativo verbatim da MCP `normattiva`/override → snapshot; numeri commerciali da `k2a-catalogo`; route-or-refuse a 3 famiglie (UE→EUR-Lex, CCNL→rinvio, attuativi→disclaimer). Il nostro engine rispetta questo (citazioni con fonte+vigenza, refuse esplicito).
4. **Prezzo sempre da catalogo, mai hardcoded** (D-038/040/045): il nostro `catalog.py` + `build_catalog.py` rispettano la fonte unica. Check Express = **19€** (non 49€).

---

## GAP-1 RISOLTO con questo accesso

`k2a-skills/snapshot/build_snapshot.py` (il file mancante dall'handoff zip) contiene `manifest()` = **mappa completa placeholder→boost**. Estratta: **57 chiavi / 11 boost**. Sostituito il nostro `boost_placeholders.json` interim → **gli 11 boost sono ora sbloccati** nel motore (non più solo LegalBoost).

| boost | n chiavi |
|---|---|
| flusso-financeboost-pmi | 12 |
| flusso-fiscoboost-pmi | 9 |
| cruscotto-direzionale | 6 |
| flusso-hostboost-ricettive | 6 |
| flusso-buildboost-studio | 5 |
| flusso-mepboost-studio | 5 |
| flusso-safetyboost-studio | 5 |
| flusso-advisorboost-pmi | 3 |
| flusso-legalboost-pmi | 3 |
| flusso-webboost-pmi | 2 |
| flusso-strategyboost-pmi | 1 |

## Asset aggiornati dal repo (più nuovi del zip handoff v2.27)

⚠️ **Smell di versioning**: stesso `snapshot_version=1.0.0` / `catalog_version=1.0.0` ma contenuto diverso. Da segnalare a Luca (bump versione quando cambia il contenuto).
- **snapshot**: zip handoff = 53/57 risolti; repo = **55/57** (benchmark_settore + multipli_ev ora risolti). Restano 2 gap `da_strutturare`: `revpar_zona` (HostBoost), `keyword_dataset` (WebBoost).
- **catalog**: zip = 76 servizi; repo = **81 servizi** (15 generabili 8e invariati).
- Vendorizzati i nuovi snapshot+catalog+blueprints+k2a_validation; rigenerato `kbot catalog.json` (81 servizi). Smoke engine PASS.

---

## Repo per repo (sintesi)

### Portale commerciale (rilevanti per noi)

- **k2a-ai-masterplan** — MASTERPLAN autoritativo **v2.29**, ~47 decisioni D-xxx. Governa prodotto/prezzo/architettura. Trappola: version-drift (fidarsi della testata, non delle righe vive); prezzi nel prosa a volte vecchi (verità = catalogo).
- **k2a-skills** — **fonte di verità**: ~234-266 cartelle skill (SKILL.md + schemas/form.json + output-schema.json + references/grounding-*.md), 12 boost `flusso-*`, 12 check-express, 25 blueprint, `snapshot/` (fabbrica: build_snapshot.py + grounding-snapshot.json + build_catalog.py + catalog.json), `handoff-8e/` (k2a_validation L1/L2 + resolver_stub). **È la membrana.**
- **k2a-mcp-agevolazioni** (server name `k2a-catalogo`) — Mega-MCP servizi PMI, 25 tool, **listino single-source** (`scheda_listino`, `classifica_prodotto`). Produce numeri PMI (crediti d'imposta, bancabilità, KPI settoriali) + prezzi. 149 test.
- **normattiva-mcp** — KB Normattiva (62k articoli + override locali curati). `get_articolo` cascata: override_locale → bulk-XML AKN → fallback. Fonte del grounding legale verbatim. Path hardcoded `/Users/lucarossi/normattiva_ai/`.
- **k2a-mcp-deliverable** — validatore **L1** (`validate_blueprint`) + **L2** (`lint_deliverable`/`lint_file`). FastMCP+jsonschema. Parità 12/12 con la libreria `k2a_validation` portata nell'handoff (quella che usiamo).
- **k2a-mcp-quant** — finanza quantitativa, 27 tool (DCF/WACC/VaR/LBO/multipli Damodaran). Per FinanceBoost/AdvisorBoost. Snapshot dati statici (invecchiano).
- **k2-marketplace** — 18 plugin commerciali `k2ai-*` (L2 orchestratori) + 3 `k2-knowledge-*`. Regola: prezzi/KPI mai hardcoded, sempre da MCP `k2a-catalogo`. Gold standard: `k2ai-hospitality`.
- **k2a-giurisprudenza** — **Legal Evidence Stack**: scraper+indexer+CLI di giurisprudenza IT/UE (CCost, CGUE, CEDU, CdS/TAR, Merito, Cassazione live). Anti-allucinazione legale, backing di LegalBoost (esposto via normattiva-mcp). Dati gitignored.
- **k2a-skill-evolution** — loop apprendimento K2-OS: osserva diff git dei deliverable, classifica (10 categorie), propone CREATE_SKILL/ADD_CHECK/ADD_RULE. Human-in-the-loop. Alimenta k2a-skills.
- **k2a-k2bot** — ingestione **Telegram→K2-OS** (Fase A): canale intake interno per il consulente (manda PDF, riceve sintesi+deliverable). 5 verticali. NON è il portale cliente; stesso layer skill, canale parallelo.

### Ingegneria interna (fuori portale, D-035)

- **k2a-masterplan** — masterplan ecosistema strutturale **v3.0** (≠ ai-masterplan). NON confondere: numerazioni decisioni diverse (DN-xx).
- **k2a-mcp-strutturale** — 52 tool verifica statica pali TLC NTC 2018. CI completa, caso reale validato. Per StructBoost/TLCBoost interni.
- **k2a-mcp-elettrico** (+ **-validator**) — impianti elettrici BT/MT CEI/IEC, ~45 tool + doppia-implementazione safety-critical (1/30 tool cross-validato finora).
- **k2a-mcp-norme-tecniche** — RAG norme tecniche (NTC/CEI), FTS5+embeddings. L'unico concettualmente affine al grounding boost edilizi, ma il portale usa snapshot statico.
- **relsta-k2a** — skill orchestratore RELSTA strutturali TLC (DOCX). Business ingegneria di Luca, binario separato.

### Librerie verticali (packaging)

- **k-bot-{legale,commercialista,ingegneria,hospitality,artigiano,pmi}-skills** — bundle skill per verticale (30/35/43/29/26/55 skill). **Copie byte-identiche** (md5) di k2a-skills + orchestratori dal marketplace + (legale) blocco `LEGAL-EVIDENCE-BLOCK`. Stack dichiarato Railway+Clerk (vecchio). Non sono divergenze: packaging.

---

## Implicazioni operative per noi (Luigi)

1. **GAP-1 chiuso** → posso abilitare gli 11 boost nel motore (non solo Legal). Prossimo: test pipeline su un boost numerico (es. FiscoBoost — chiavi TUIR/IVA) per validare il path `formula`/`input`.
2. **Sync asset**: invece di copiare dallo zip, ora ho accesso a `k2a-skills` → posso sincronizzare snapshot/catalog/blueprints/k2a_validation via git (sub-module o fetch CI). Da decidere con Luca il meccanismo (membrana §2).
3. **Versioning da chiarire con Luca**: snapshot/catalog cambiano contenuto senza bump versione → serve disciplina semver, altrimenti non so se il mio vendor è aggiornato.
4. **2 gap benchmark** (`revpar_zona`, `keyword_dataset`) restano `da_strutturare` → HostBoost e WebBoost generano ma senza quel confronto (non bloccante, il resolve li tratta non-bloccanti).
5. **Build-time resta sul Mac di Luca** (`build_snapshot.py` dipende da `~/normattiva_ai/`): per la produzione serve o lo snapshot committato (come ora) o produttizzare la fabbrica. Coerente con la membrana.

---

*Studio read-only. Repo non modificati. Asset aggiornati nel motore: `kai-website/k2a-8e/{grounding,catalog,blueprints,k2a_validation}` + `kbot/backend/app/data/catalog.json`.*
