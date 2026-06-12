# Interfaccia K-BOT ↔ 8e — contratto vivente (membrana)

*Unico punto di contatto tra il lato frontend/produzione (Luigi + Claude operativo, `kai-website/kbot`) e il lato backend/ecosistema (Luca + Claude backend, 8e + skill + grounding). Si aggiorna SOLO quando cambia l'interfaccia, non a ogni iterazione. Owner condiviso. Riferimenti: `8e_Phase0_design_API.md`, `ARCHITETTURA_PRODOTTO_FINALE_K2-AI.md`, `risposta-contesto-operativo.md`.*

---

## 0. Principio
Due piattaforme proprietarie + Claude come motore. **Il K-BOT non genera il deliverable**: capisce il cliente, instrada, incassa, e lo richiede all'8e. **L'8e genera in modo deterministico** (i fatti dallo snapshot, non dal modello). Tra i due lati c'e' **una sola interfaccia**: l'API dell'8e + lo schema `catalog.json`. Stabili questi due, i due lati deployano indipendenti.

---

## 1. Contratto API (l'8e espone, il K-BOT consuma)
Servizio FastAPI su Railway · **stateless** · auth **Bearer key** (`K2A_8E_API_KEY`, solo backend-to-backend) · modello **job asincrono** · timeout richiesta 180s.

**`GET /v1/catalog`** → elenco servizi vendibili (specchio di `catalog.json`).

**`POST /v1/deliverables`** (Bearer)
```json
{ "service_id": "flusso-legalboost-pmi", "tier": "boost",
  "inputs": { /* campi da <skill>/schemas/form.json */ },
  "entitlement_token": "<rilasciato dal billing del K-BOT>" }
```
→ `202 { "job_id", "status":"routed", "confidence" }`
→ `402 { "status":"payment_required" }` · `422 { "status":"refused", "reason", "message" }`

**`GET /v1/deliverables/{job_id}`**
```json
{ "status":"routed|running|validating|rendered|refused|error",
  "outputs": { "html_url", "pdf_url", "bundle":[{"type","url"}] },
  "validation": { "L1":"PASS", "L2":"PASS" },
  "citazioni": [ {"campo","fonte","coordinate","vigenza"} ],
  "refusal_reason": null }
```

**Contratto di rifiuto** (esplicito, mai inventare): `reason ∈ { out_of_catalog, low_confidence, unresolvable_placeholder, validation_failed, payment_required }`.

**Entitlement**: il billing del K-BOT rilascia il token al pagamento; l'8e lo **verifica**, non lo gestisce. Storage output: **Supabase Storage del K-BOT** (l'8e ritorna i file/URL).

---

## 2. `catalog.json` — schema e direzione
**Direzione**: fonte di verita' = **k2a-catalogo** (prezzi, 73 tipi vendibili, parametri prodotto). `catalog.json` e' un **artefatto generato** da k2a-catalogo e committato nel monorepo (interim: comando sul Mac; target: CI). Non si edita a mano in due posti.

Campi (schema §1.1 del piano + 3 aggiunte backend):
```json
{
  "id": "flusso-legalboost-pmi",
  "tipo": "servizio",                 // consumo | tappa | servizio | retainer
  "label": "LegalBoost",
  "prezzo_eur": 1499,                  // da k2a-catalogo
  "tag_pillar_sito": ["P03"],
  "genera_via": "8e",                  // 8e | manuale | external
  "blueprint_id": "flusso-legalboost-pmi.boost",
  "output_schema_ref": "flusso-legalboost-pmi/schemas/output-schema.json"
}
```
`genera_via=8e` → il K-BOT chiama `POST /v1/deliverables`. `manuale|external` → high-touch, nessuna chiamata 8e.

---

## 3. Mapping service_id → blueprint (cosa esegue l'8e)
| service_id (catalog) | blueprint | stato |
|---|---|---|
| flusso-legalboost-pmi | flusso-legalboost-pmi.boost | pronto (grounded) |
| flusso-fiscoboost-pmi | flusso-fiscoboost-pmi.boost | pronto |
| flusso-advisorboost-pmi | flusso-advisorboost-pmi.boost | pronto |
| flusso-financeboost-pmi | flusso-financeboost-pmi.boost | pronto |
| flusso-strategyboost-pmi | flusso-strategyboost-pmi.boost | pronto |
| flusso-agevolazioni-pmi | flusso-agevolazioni-pmi.boost | pronto |
| flusso-safetyboost-studio | safetyboost-studio.boost | pronto |
| (build/mep/host/web) | *.boost | pronti |
| check-* express | check | pronti |
| Boost P01-P20 "AI operativa" (CRM/RAG/…) | — | da decidere (tassonomia) |

Le skill/blueprint vivono in `k2a-skills` e sono **interne all'8e** (bundlate al build). **Il K-BOT non accede a `k2a-skills`** — consuma solo l'API.

---

## 4. Versioning end-to-end (riproducibilita')
Al momento dell'acquisto il K-BOT logga in `kbot_purchases` la terna + motore:
`{ catalog.version, blueprint.version, grounding_snapshot.version, "8e".version }`.
Per riprodurre un report (reclamo): si fissano le 4 versioni. La prosa Sonnet non e' byte-identica; i **fatti e la struttura** si' (sono da fonte+versione).

---

## 5. Confini di responsabilita'
**Backend (Luca + Claude backend)**: blueprint, grounding (snapshot), 8e, MCP (fabbrica), pricing/params in k2a-catalogo, contenuto del deliverable. **Frontend (Luigi + Claude operativo)**: chat/UI/login/sessione, Stripe/billing/entitlement, routing via catalogo+tag, chiamata API 8e, consegna (Supabase+Resend), monitoring/on-call Railway, SEO/sito/blog, deploy materiale di tutti i container (incluso 8e).

---

## 6. Cosa NON e' nella membrana (anti scope-creep)
Le skill interne, i blueprint, il grounding-snapshot, la prosa del modello, gli MCP. Sono dettagli interni all'8e: cambiano senza toccare l'interfaccia, **purche'** API e `catalog.json` restino stabili.

---

## 7. Regole di modifica
- Si aggiorna solo se cambia l'API o lo schema `catalog.json`.
- CODEOWNERS su `catalog.json`: prezzo/label/tassonomia → Luca; campi tecnici (`genera_via`, `blueprint_id`, `output_schema_ref`) → backend.
- Ogni cambio d'interfaccia = nota in coda con data + versione.

---

## 8. Stato decisioni
**Chiuse**: 8e su Railway · snapshot **interim** per il lancio · `catalog.json` generato da k2a-catalogo · MCP = fabbrica (build-time), non in catena calda · auth Bearer · job async · storage = Supabase del K-BOT · il K-BOT non accede al repo skill.
**Aperte (Luca)**: tassonomia P01-P20 ↔ blueprint · accesso read repo a Luigi (trasparenza, non blocco) · on-call 8e (runbook dal backend) · snapshot interim → CI/remote scale-to-zero (evoluzione, non blocco).
**Gate pre-vendita**: un Boost non si vende finche' i suoi articoli sono `da confermare`/`INCOMPLETO` (coverage-report al build).

---

## 9. Gap tecnici da chiudere prima di scrivere il client 8e definitivo
*Aggiunti dal lato operativo (Luigi) il 2026-06-04. Non bloccano lo sviluppo contro il MOCK (vedi `kbot/mock-8e/`), ma vanno risolti prima del cutover su 8e reale. Ogni gap ha una proposta operativa: Luca conferma o controproppone.*

### G1 — Formato `entitlement_token` (CRITICO, sicurezza)
L'8e deve verificarlo **stateless**, senza richiamare il K-BOT (altrimenti i due lati non sono disaccoppiati).
**Proposta Luigi**: JWT firmato HS256/EdDSA. Il K-BOT firma con chiave privata, l'8e verifica con chiave pubblica/shared-secret (`K2A_ENTITLEMENT_PUBKEY` in env 8e). Claim minimi: `{ sub: user_id, service_id, tier, jti, iat, exp (15 min), kbot_session_id }`. L'8e verifica firma + `exp` + `service_id == body.service_id`. `jti` per anti-replay (opzionale, l'8e può ignorarlo se single-use non serve).
**Da Luca**: ok JWT? Quale algoritmo? Chi genera la coppia di chiavi?

### G2 — Storage cross-service (CRITICO, sicurezza)
§1 dice "storage output = Supabase Storage del K-BOT, l'8e ritorna i file/URL". Ma se l'8e scrive direttamente, ha la `service_role` key di Luigi → accesso a TUTTO il DB di Luigi. Buco.
**Proposta Luigi** (preferita): l'8e ritorna i **bytes** (o un URL temporaneo firmato del proprio storage effimero); il **K-BOT uploada** su Supabase Storage e genera il signed URL al cliente. L'8e non tocca mai il DB/Storage di Luigi.
**Alternativa**: il K-BOT pre-crea un **signed upload URL** (scoped a un singolo path) e lo passa nell'`inputs`; l'8e ci fa solo PUT. Nessuna credenziale persistente all'8e.
**Da Luca**: quale delle due? L'8e ritorna bytes o fa upload con URL pre-firmato?

### G3 — `grounding_snapshot.version` al checkout
Il K-BOT deve loggare la versione snapshot in `kbot_purchases` (§4) ma "non accede a k2a-skills" (§3). Da dove la legge?
**Proposta Luigi**: `GET /v1/catalog` espone in testa `{ engine_version, grounding_snapshot_version, catalog_version }`; il K-BOT li legge al checkout e li logga. In più ogni `GET /v1/deliverables/{job_id}` rieccheggia le versioni effettive usate per QUEL job (potrebbero differire se nel frattempo l'8e è stato ridepleyato).
**Da Luca**: ok esporre le versioni in `/v1/catalog` header/body + nel job response?

### G4 — `catalog.json` (committato) vs `GET /v1/catalog` = due fonti
Stesso dato in due posti → rischio drift.
**Proposta Luigi**: `catalog.json` committato nel monorepo = **fonte di verità per il routing/pricing del K-BOT** (deve funzionare anche con 8e a scale-to-zero/freddo). `GET /v1/catalog` = **self-check dell'8e** (cosa SA generare davvero). Al deploy, una CI confronta i due e fallisce se divergono su `id`/`blueprint_id`. Il cliente non vede mai prezzi da `/v1/catalog`.
**Da Luca**: ok come regola? L'8e accetta di essere allineato a `catalog.json`, non viceversa?

### G5 — Cold start scale-to-zero
Primo `POST` dopo idle = boot container Railway (~10-30s). Il job async lo assorbe, ma la UX deve coprirlo.
**Proposta Luigi**: il K-BOT mostra "sto preparando il motore…" sul primo job; polling con backoff. Accettiamo cold start a basso volume. Opzionale: un warm-ping `GET /health` quando il cliente apre il checkout, così l'8e è caldo al pagamento.
**Da Luca**: `GET /health` esiste/è leggero? Possiamo warm-pingarlo senza costo?

### G6 — Auth: Bearer key singola
Leak = generazione gratis illimitata.
**Proposta Luigi**: chiave in env Railway (mai in repo/frontend), rotazione supportata (l'8e accetta 2 chiavi valide durante la rotazione: `K2A_8E_API_KEY` + `K2A_8E_API_KEY_NEXT`). Rate-limit lato 8e per chiave. La chiamata è solo backend→backend (FastAPI K-BOT → 8e), mai dal browser.
**Da Luca**: l'8e supporta 2 chiavi simultanee per rotazione zero-downtime? Rate-limit per-key previsto?

### G7 — Polling, timeout, retry
**Proposta Luigi**: K-BOT polla `GET /{job_id}` ogni 2s con backoff fino a 5 min max; oltre → stato `error`, refund automatico, alert. Job idempotente su retry con stesso `entitlement_token.jti` (l'8e ritorna lo stesso `job_id` se ricevuto due volte lo stesso token). Timeout hard job lato 8e: proposta 240s, oltre → `error`.
**Da Luca**: l'8e supporta idempotency-key (`jti` o header `Idempotency-Key`)? Qual è il timeout hard reale di un Boost completo (5 sezioni + peer-review)?

### G8 — Reclamo/riproduzione
§4 logga 4 versioni. Ma per riprodurre serve anche **rieseguire** quella versione dell'8e.
**Proposta Luigi**: l'8e tagga ogni release immutabile (`8e:vX.Y.Z`) e tiene gli snapshot versionati raggiungibili; dato il log a 4 versioni, si può re-deployare la combinazione. Non serve runtime perenne, basta che le immagini/snapshot siano archiviati.
**Da Luca**: gli snapshot storici restano archiviati (object storage) e le immagini 8e taggate sono ripristinabili?

---
*Contratto vivente. Da committare in `docs/interfaccia-kbot-8e.md` nel monorepo. Modifiche solo per cambi d'interfaccia. I gap §9 sono lo stato aperto lato operativo: rispondere inline o in `docs/risposta-gap-membrana.md`.*
