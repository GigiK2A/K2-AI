# Security audit — sistema K2-AI (8e + K-BOT + compute layer)

*Data: 2026-06-10. Scope: motore 8e, backend K-BOT (FastAPI), layer pagamenti, e i nuovi endpoint compute/checks + MCP vendorizzati. Metodo: revisione manuale + scansione pattern.*

---

## Sintesi esecutiva

Postura di base **solida**: SSRF, CORS, webhook, entitlement JWT e dispatch dinamico erano già ben costruiti. I problemi seri erano **introdotti dai nuovi endpoint compute** (esposizione di ~135 tool dell'ecosistema). **3 vulnerabilità fixate** in questa sessione (2 ALTE, 1 BASSA), **1 MEDIA** segnalata (componente condiviso, non modificata unilateralmente).

| # | Severità | Stato | Titolo |
|---|---|---|---|
| 1 | 🔴 ALTA | ✅ FIXATO | Endpoint compute/checks senza auth né rate-limit |
| 2 | 🟠 MEDIA | ⚠️ APERTO | Entitlement 8e fail-OPEN se segreto mancante |
| 3 | 🔴 ALTA | ✅ FIXATO | Endpoint generico /tool espone generatori che scrivono file (write arbitrario) |
| 4 | 🟡 BASSA | ✅ FIXATO | Markup injection nel renderer PDF (reportlab) |
| 5-8 | ℹ️ INFO | nota | tool non funzionali esposti, dead code, DoS-depth, SQL |

---

## Vulnerabilità — dettaglio

### 🔴 1. Endpoint compute/checks pubblici (no auth, no rate-limit) — FIXATO
**Dove:** `app/api/checks.py`, `app/api/compute.py` (`/checks`, `/check/{id}`, `/check/{id}/document`, `/tools`, `/tool/{id}`).
**Problema:** nessun `Depends(require_user)`, nessun rate-limit → (a) chiunque, non autenticato, eseguiva i servizi a pagamento e scaricava i PDF gratis; (b) **DoS**: i tool di calcolo pesante (monte_carlo, FEM strutturale) invocabili senza limite.
**Fix:** aggiunto `require_user` (JWT Supabase) + `@limiter.limit` su tutti gli endpoint. Verificato: **401 senza token**. Commit `b4f57ad`.
**Residuo (product):** un utente *autenticato* esegue ancora i check senza consumare crediti → vedi Raccomandazione R2.

### 🔴 3. Scrittura file arbitraria via tool generatori — FIXATO
**Dove:** `app/api/compute.py` `_discover()`.
**Problema:** il registry esponeva OGNI funzione `(BaseModel)->...`, inclusi i **generatori** di `k2a_elettrico`/`k2a_quant` (excel/docx/dxf/cad) che scrivono file a un path preso dall'**input utente** (`output_path`, `path_output`, `output_dir`). Un `POST /tool/elettrico/relazione_docx.*` con `output_path="/app/app/main.py"` = **sovrascrittura di codice server** → RCE/distruzione (autenticata dopo il fix #1, ma comunque grave).
**Fix:** `_writes_filesystem()` esclude i tool con campi-input filesystem. **135 → 125 tool** (10 generatori esclusi); calcolo puro intatto (dcf/monte_carlo/de_minimis presenti). Commit `f86f747`.

### 🟡 4. Markup injection nel PDF (reportlab) — FIXATO
**Dove:** `app/lib/check_renderer.py`.
**Problema:** i valori utente finivano in `reportlab.Paragraph` (mini-markup XML) senza escape → input con `<`/`&` rompeva il parser (crash 500) o iniettava markup.
**Fix:** `html.escape` su valori e chiavi. Verificato: input `<script>&"` rende un PDF valido. Commit `f86f747`.

### 🟠 2. Entitlement 8e fail-OPEN — APERTO (raccomandazione)
**Dove:** `k2a-8e/app/entitlement.py:verify()`.
**Problema:** se `K2A_ENTITLEMENT_SECRET` non è settato, `verify()` ritorna `True` ("dev-no-secret") → **in produzione, una misconfigurazione (env var mancante) bypassa il pagamento** per tutti i deliverable Boost.
**Perché non l'ho cambiato:** è un componente condiviso con Luca; il `/health` già espone la modalità (enforced/permissive) e cambiarne il default rischia di rompere i loro ambienti dev/test.
**Raccomandazione:** fail-CLOSED in produzione. Patch minima: rifiutare se il segreto manca a meno di un flag esplicito `K2A_8E_ENTITLEMENT_DEV=true`. Da concordare con Luca.

---

## Punti FORTI verificati (già sicuri)

- **SSRF** (`url_fetcher.py`): risolve `getaddrinfo` e ricontrolla **tutti** gli IP risolti (`is_private/loopback/link_local/reserved/multicast`) → **anti DNS-rebinding**; blocca schemi non-http e host interni. Robusto.
- **CORS**: guard esplicito anti-`*` con credentials, origin specifici k2-ai.it.
- **Webhook Stripe**: firma verificata (`construct_event`), **fail-closed 503** se non configurato, 400 su firma invalida.
- **Entitlement JWT**: `algorithms=["HS256"]` esplicito (**rifiuta alg=none**), `aud`/`iss`/`exp` obbligatori.
- **Deliverables (pagato)**: ownership check + mint entitlement legato a {session, servizio, tier}.
- **No eval/exec/subprocess/pickle** nel codice app. Dispatch tool = lookup per chiave in registry costruito a startup (no import arbitrario da input). Path param `{tool_id:path}` innocuo (solo chiave di dict → 404).
- **Input validation**: tutti i tool calcolo hanno modelli Pydantic con bound (es. `monte_carlo n_simulations le 1_000_000`).
- **Secrets**: nessuno hardcoded nel codice né nel vendor committato; `.env.local` non in git.
- **Supabase**: hardening pregresso (REVOKE EXECUTE su RPC, `SET search_path`, RLS).

---

## Note informative (5-8)

- **5.** I 6 tool `norme-tecniche` sono esposti ma **non funzionali** (DB `norme_tecniche.db` assente nel kbot) → 500 a runtime. Non è un buco, ma vanno esclusi o resi disponibili.
- **6.** Dead code vendorizzato: `vendor/k2a_norme_tecniche/ocr/formula_ocr.py` legge `.env` dal CWD. **Non esposto** (sottopacchetto non scoperto dal registry), ma è un odore: vedi R3.
- **7.** DoS-depth: i tool calcolo restano potenzialmente pesanti entro i bound; rate-limit+auth mitigano. Valutare un **timeout per richiesta**.
- **8.** SQL in `norme_tecniche/db.py`: verificare parametrizzazione delle query quando il DB verrà spedito (oggi non funzionante).

---

## Raccomandazioni (priorità)

| Pri | Azione | Perché |
|---|---|---|
| **R1** | Entitlement 8e **fail-closed** in prod (con Luca) | chiude il bypass pagamento da misconfig (#2) |
| **R2** | **Consumo crediti server-side** nei check (oggi il gate è solo client) | un utente autenticato non deve avere check illimitati gratis |
| **R3** | **Potare il vendor**: tenere solo i moduli calcolo usati, rimuovere ocr/cad/generatori | riduce superficie d'attacco + toglie il lettore di `.env` |
| **R4** | **Timeout per richiesta** sui tool compute | DoS-depth |
| **R5** | Allowlist esplicita dei tool esposti (oltre al filtro filesystem) | difesa in profondità: esponi solo ciò che è inteso |

---

## Cosa è stato fatto in questa sessione
- Fixati i 3 problemi (auth+rate-limit, write arbitrario, escape PDF), tutti con test verdi (9/9 kbot).
- Commit: `b4f57ad` (auth), `f86f747` (file-writer + escape).
- Aperto: #2 (entitlement, da concordare con Luca) + raccomandazioni R2-R5.
