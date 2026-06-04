# KBot v2 — Follow-up alle decisioni di allineamento

**Companion di**: `docs/analisi-architettura-kbot-v2.md` + `risposta-analisi-kbot-allineamento.md` (allineamento ricevuto).

**Scopo**: chiudere le 4 decisioni che bloccano l'esecuzione + piano operativo dei
prossimi 30 giorni con gate quantitativi.

**Stato**: la direzione strategica è ratificata (modello unico Check → Boost →
percorsi, ritiro dei 20 P01-P20). Restano nodi che vanno chiusi PRIMA di scrivere
codice nuovo, perché toccano repo che oggi vivono di P01-P20.

---

## 1. Quattro decisioni che bloccano l'esecuzione

### 1.1 Cosa fare del modello 20 P01-P20 fuori dal KBot

Il "ritiro" del modello 20 servizi vale solo per `services.py` del backend KBot,
o anche per:

- **Sito vetrina Vite** (`kai-website/src/`): pillar hub `/suite-ai/[slug].html` (10 in pianificazione, alcuni già pubblicati)
- **Blog-bot** (`tools/blog-bot/`): genera automaticamente articoli SEO per i 20 pillar. Commit recenti che ne stanno pubblicando (es. `66f6ef1` per P01).
- **Skill library** (`skills sito k2-ai 2/P01-P20/`): 20 directory con SKILL.md per ogni pillar
- **Mirror frontend** (`kai-website/src/data/suiteAiServices.ts`): mirror di `services.py`
- **Keyword map** (`docs/piano-strategico/K2-AI_Keyword_Map.xlsx`): 80 keyword su 10 pillar
- **Posizionamento v2** (`CLAUDE.md §1`): claim "Sistemi AI operativi per PMI italiane" è ombrello dei 20 pillar

**Scenari possibili** (da scegliere):

| Scenario | Cosa succede | Costo | Rischio |
|---|---|---|---|
| **A — Ritiro totale** | Stop blog-bot. Redirect 301 articoli pubblicati. Rifare sito su Check/Boost/percorsi. Riscrivere keyword map. | Alto (settimane lavoro sito) | SEO: perdita backlink/ranking guadagnati |
| **B — Convivenza** | Sito vetrina mostra 20 P01-P20 (SEO entry). KBot vende solo Check/Boost/percorsi. Mapping tra i due. | Medio | Confusione visitatore (entra cercando P01, KBot gli vende AdvisorBoost) |
| **C — Mappatura** | 20 P01-P20 restano come "tag tematici" lato SEO. Ogni P punta a 1 Boost destinazione del nuovo modello. Sito = entry point, KBot = vendita. | Basso (mapping 20→N) | Più gestibile, richiede tabella di mapping |

**Raccomandazione**: scenario C. Mantiene il lavoro SEO esistente, allinea il
funnel di vendita al nuovo modello, costa poco. Decisione formale necessaria
prima di toccare codice.

### 1.2 Allineamento owner repo

Il "decisore" della risposta non è esplicitamente nominato. CLAUDE.md §12 dice
**Owner = rluigiluca@gmail.com (Luca)**.

Domanda esplicita: Luca approva il ritiro/mappatura dei 20 P01-P20 e la
trasformazione del K-BOT da macchina-report a agente di vendita Check+Boost?

Risposta scritta richiesta nel repo (commit o PR description), non implicita.
Senza, qualsiasi merge nel `main` rischia di essere rifatto al primo conflitto
di roadmap.

### 1.3 Gate quantitativi accettati o no

La risposta accetta "incrementale a gate" in §3. Va formalizzato:

| Fase | Gate per passare alla successiva |
|---|---|
| 0 — Misurazione baseline | 30 giorni dati: sessioni/mese, conv 19€, retention, costo LLM |
| 1 — Catalog.json + upsell statico | ≥2 Boost venduti/mese tramite upsell post-Check |
| 2 — Percorso pilota | ≥5 percorsi completi venduti |
| 3 — Estensione catalogo | ≥3 utenti ricorrenti acquistano >1 servizio in 6 mesi |
| 4 — Wallet + abbonamenti | ≥20 abbonati Pro/Business attivi |
| 5 — MCP server | ≥1 partner esterno formalmente interessato |

Se il decisore RIFIUTA i gate ("si fa perché lo dice il piano"), si torna al
rischio big-bang travestito da incrementale, e bisogna saperlo prima.

Se ACCETTA: ottimo, l'incrementalità è reale e proteggiamo l'investimento.

### 1.4 Forma del catalogo e ownership

Quattro opzioni proposte in §4 della risposta. Scelta consigliata:

**`catalog.json` in `kai-website/kbot/data/catalog.json`** (committed nel repo
KBot). Motivazioni:

- Zero dipendenze runtime esterne
- Zero coordinamento inter-team (PR review come ogni altra modifica)
- Modificabile via PR con review umana → traccia decisionale
- Banale fare versioning (git history) e rollback
- JSON Schema validation in CI per evitare regressioni
- Quando in futuro serve UI admin → migrazione a tabella Supabase (1 giorno di
  lavoro, schema identico)

**Schema minimo proposto**:

```json
{
  "version": "1.0.0",
  "updated_at": "2026-06-04",
  "tipi_listino": {
    "consumo": {"label": "Check Express", "ruolo": "entry"},
    "tappa": {"label": "Tappa percorso", "ruolo": "intermedio"},
    "servizio": {"label": "Boost", "ruolo": "destinazione"},
    "retainer": {"label": "Abbonamento continuativo", "ruolo": "post-boost"}
  },
  "servizi": [
    {
      "id": "check-express",
      "tipo": "consumo",
      "label": "Check Express PMI",
      "prezzo_eur": 19,
      "skill_orchestratore": "diagnosi-ai-operativa-pmi",
      "tag_pillar_sito": ["P01", "P02", "P12"]
    },
    {
      "id": "advisorboost",
      "tipo": "servizio",
      "label": "AdvisorBoost",
      "prezzo_eur": 2499,
      "tappe_ordinate": ["ab-tappa-1", "ab-tappa-2", "ab-tappa-3", "ab-tappa-4", "ab-tappa-5"],
      "sconto_completamento_pct": 24,
      "skill_orchestratore": "flusso-advisorboost-pmi",
      "tag_pillar_sito": ["P12", "P09"]
    },
    {
      "id": "ab-tappa-1",
      "tipo": "tappa",
      "label": "Diagnosi rapida",
      "prezzo_eur": 299,
      "percorso_padre": "advisorboost",
      "ordine": 1,
      "skill_orchestratore": "check-pmi-express",
      "include_check_express": true
    }
  ],
  "percorsi": [
    {
      "id": "advisorboost",
      "destinazione_id": "advisorboost",
      "tappe_id_ordinate": ["ab-tappa-1", "ab-tappa-2", "ab-tappa-3", "ab-tappa-4", "ab-tappa-5"]
    }
  ],
  "abbonamenti": [
    {"id": "pro", "prezzo_mensile_eur": 49, "crediti_mensili": 49, "sconto_tappa_pct": 10},
    {"id": "business", "prezzo_mensile_eur": 149, "crediti_mensili": 149, "sconto_tappa_pct": 20}
  ]
}
```

Il campo `tag_pillar_sito` è la mappatura per lo scenario C di §1.1 — collega
ogni servizio del nuovo modello ai pillar SEO esistenti del sito. Risolve il
funnel: visitatore arriva su `/suite-ai/agenti-email-crm.html` (P01) → CTA al
KBot → KBot riconosce contesto P01 → propone Check Express + AdvisorBoost
(perché P01 è taggato sotto entrambi).

Layer di accesso lato backend KBot:

```python
# kbot/backend/app/lib/catalog.py
from pathlib import Path
import json
from functools import lru_cache

CATALOG_PATH = Path(__file__).parent.parent / "data" / "catalog.json"

@lru_cache(maxsize=1)
def load_catalog() -> dict:
    return json.loads(CATALOG_PATH.read_text())

def get_servizio(servizio_id: str) -> dict | None:
    return next((s for s in load_catalog()["servizi"] if s["id"] == servizio_id), None)

def get_percorso(percorso_id: str) -> dict | None:
    return next((p for p in load_catalog()["percorsi"] if p["id"] == percorso_id), None)

def prezzo_per_piano(servizio_id: str, piano: str | None) -> int:
    s = get_servizio(servizio_id)
    if not s: return 0
    base = s["prezzo_eur"]
    if piano == "pro": return int(base * 0.9)
    if piano == "business": return int(base * 0.8)
    return base
```

Identica interfaccia di `services.py` attuale, dato esterno. Quando catalog.json
cambia, il loader rilegge al prossimo restart (o invalida cache con webhook).

---

## 2. Piano operativo dei prossimi 30 giorni (zero-rischio)

Tutto quello che SI PUÒ fare ORA senza ambiguità decisionale:

### Settimana 1 — Misurazione baseline (zero codice nuovo)

- Query analytics K-BOT esistente:
  - Sessioni/mese ultimi 90 giorni
  - Conversion rate sessione → checkout → pagamento
  - Distribuzione per `service_id` selezionato (quali P01-P20 attivano davvero)
  - Costo LLM mensile (Haiku chat + Sonnet PDF)
  - Tempo medio sessione, messaggi medi per sessione
- Output: 1 report di 1 pagina con i numeri. Necessario per dimensionare il
  resto.

### Settimana 2 — Stop pubblicazioni in conflitto + schema catalogo

- **Stop blog-bot** finché non si decide scenario A/B/C su §1.1
  - Implementazione: env var `BLOG_BOT_ENABLED=0` o feature flag in
    `tools/blog-bot/config.json`
  - Articoli già pubblicati: NON toccare (decisione separata su redirect)
- **Definire schema `catalog.json`** finale insieme al decisore
  - JSON Schema in `kbot/backend/app/data/catalog.schema.json`
  - Validazione CI: PR che modifica catalog.json fallisce se schema non valida
- **Mock catalog.json**: versione iniziale con 5 servizi (Check + 1 Boost
  diretto + 3 tappe di 1 percorso). Permette dev backend di partire senza
  attendere il catalogo completo.

### Settimana 3 — Refactor `services.py` → loader catalog.json

- Spostare il registry hardcoded in `catalog.json`
- Tenere l'interfaccia di `services.py` invariata (mantiene tutti i call site)
- Aggiungere `tag_pillar_sito` per mantenere il mapping verso i P01-P20 SEO
  (scenario C)
- Aggiungere test che verificano che ogni servizio in catalog.json sia caricabile
  e ritorni gli stessi tipi del registry attuale
- Zero modifiche al frontend KBot e zero modifiche al system prompt

### Settimana 4 — Upsell statico post-Check

- Decidere in `catalog.json` 1 mapping `tag_pillar_sito → boost_suggerito`
  - Es. tag P01 → boost AdvisorBoost (per ora unico Boost reale)
- Dopo invio PDF report 19€, aggiungere sezione UI in
  `kbot/src/app/dashboard/page.tsx` o `/k-bot/grazie.html`:
  - "Sulla base della tua diagnosi (P01), il prossimo passo è AdvisorBoost
    (2.499€). Prenota una call →"
- CTA = form Airtable per qualificazione + call commerciale
- Tracking: log eventi `upsell_shown`, `upsell_clicked`, `upsell_converted` in
  `analytics_events`

**Output dei 30 giorni**: K-BOT identico in UX per il visitatore (zero
regressioni), ma con (a) catalogo esternalizzato e versionato, (b) primo upsell
statico funzionante, (c) baseline numerica per decidere se passare a Fase 2.

---

## 3. Cosa NON va toccato nei 30 giorni

Per ridurre rischio:

1. **Sito Vite** (pillar hub, homepage, copy): finché non chiuso scenario A/B/C
   in §1.1
2. **Skill library `skills sito k2-ai 2/`**: potrebbe essere base di partenza
   per gli orchestratori nuovi. Da inventariare ma non toccare
3. **Pricing report 19€**: resta finché non chiuso §1.1 e si decide se passare
   a 49€
4. **Sistema RAG BM25**: funziona, non va toccato anche se si introdurranno
   tool use più avanti
5. **Stripe configuration**: nessuna modifica finché non chiuso il prezzo

---

## 4. Open questions da girare al decisore

1. **Scenario A/B/C su §1.1**: ritiro totale, convivenza, o mappatura tag?
   Raccomandazione tecnica: C.
2. **Allineamento Luca** (owner repo): conferma scritta che approva la
   transizione.
3. **Gate quantitativi** delle fasi accettati? Sì/no.
4. **Schema catalog.json**: prima versione approvata?
5. **Stop blog-bot ORA**: ok procedere? Articoli pubblicati restano o redirect?
6. **AdvisorBoost come primo Boost pilota**: confermato o si parte da un Boost
   diretto?

---

## 5. In una frase

I 30 giorni di lavoro a basso rischio (misurazione + esternalizzazione catalogo
+ upsell statico) si possono partire SUBITO se viene confermata la mappatura
tag (scenario C) e fermato il blog-bot; tutto il resto attende decisioni
formali sul perimetro del cambio modello rispetto al sito vetrina e al lavoro
SEO esistente.

---

*Documento operativo. Aggiorna `docs/analisi-architettura-kbot-v2.md` con i
gate accettati e gli scenari scelti una volta chiuse le 6 open questions.*
