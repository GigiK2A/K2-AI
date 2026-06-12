# KBot v2 — Piano di lavoro completo

**Stato decisioni**: chiuse.

- ✅ Scenario C: il sito vetrina + blog continuano col modello SEO 20 P01-P20.
  Il KBot vende il modello nuovo (Check Express + Boost diretti + Boost-a-percorsi).
  Mapping `P01-P20 ↔ servizi nuovi` lato catalogo.
- ✅ Blog-bot continua a pubblicare (NON va fermato).
- ✅ Backend KBot esistente (FastAPI + Supabase + Stripe + Resend + ReportLab) si
  riusa al 100%.
- ✅ Catalogo come fonte unica: `catalog.json` nel repo KBot, no MCP remoto.
- ✅ Approccio incrementale a gate quantitativi.
- ✅ Wallet/abbonamenti/MCP remoto: rimandati a fasi tardive con gate di domanda
  reale.

**Documento di riferimento**: i 2 documenti `docs/analisi-architettura-kbot-v2.md`
e `docs/kbot-v2-follow-up-decisioni.md`. Questo file è il piano operativo
definitivo.

---

## Sommario in 30 secondi

8 fasi sequenziali, ognuna con gate. Riusa 100% del K-BOT esistente. Cambia
SOLO cosa il KBot vende e come instrada (non l'infrastruttura). Sito vetrina e
blog continuano paralleli col modello 20 P01-P20 — sono il funnel SEO che alimenta
il KBot. Mapping tra i due via `tag_pillar_sito` nel `catalog.json`.

Tempo totale fino a Fase 6 inclusa: ~12-16 settimane. Fasi 7 e 8 partono solo se
i gate quantitativi sono raggiunti.

---

## Architettura finale target (dopo Fase 6)

```
┌─────────────────────────────────────────────────────────┐
│  SITO VETRINA (kai-website/src/, Vite + HTML)           │
│  • Homepage, pillar P01-P20 in /suite-ai/*.html        │
│  • Blog-bot continua a pubblicare articoli pillar      │
│  • Funnel SEO → CTA "Apri K-BOT" con ?tag=P01...       │
└───────────────────┬────────────────────────────────────┘
                    │ utente clicca CTA
                    ▼
┌─────────────────────────────────────────────────────────┐
│  K-BOT (kai-website/kbot/, Next.js + FastAPI)          │
│  • Login Supabase                                       │
│  • Chat agentica: legge tag SEO → propone Check/Boost  │
│  • Vende: Check 19€, Boost diretti, percorsi a tappe   │
│  • Catalogo letto da catalog.json (fonte unica)        │
└───┬─────────────────────────────────────────────────────┘
    │
    ├── Catalog.json (kbot/backend/app/data/catalog.json)
    │   • Servizi, percorsi, tappe, sconti
    │   • tag_pillar_sito per mapping verso 20 P01-P20
    │
    └── Orchestratori (skill-based, in lib/skills/)
        • diagnosi-ai-operativa-pmi → Check Express
        • flusso-advisorboost-pmi → Boost finale
        • check-pmi-express, analisi-settore-pmi, ecc. → tappe
        • Output: PDF/dashboard via ReportLab + Sonnet
```

---

## Mappa Sito ↔ KBot (scenario C)

Funnel: visitatore arriva sul sito via SEO → entra nel KBot col contesto del
pillar → KBot capisce il dominio e propone il servizio del catalogo nuovo.

| Pillar SEO sito | Tag | Boost suggerito | Check ingresso |
|---|---|---|---|
| Agenti AI Email & CRM | P01 | Boost CRM Automation (1.499€) | Check Express 19€ |
| Automazioni amministrative | P02 | Boost ControlBoost (1.499€) | Check Express 19€ |
| AI Legale & Contratti | P03 | Boost Legale Tier 1 (1.499€) | Check Express 19€ |
| AI Ingegneria | P04 | AdvisorBoost (2.499€) o BuildBoost | Check Express 19€ |
| Microapp Documenti tecnici | P05 | Boost Microapp custom (1.499€) | Check Express 19€ |
| AI Customer Service | P06 | Boost Customer AI (1.499€) | Check Express 19€ |
| RAG & Knowledge Base | P07 | Boost RAG (1.999€) | Check Express 19€ |
| AI Compliance & Audit | P08 | Boost Compliance (2.499€) | Check Express 19€ |
| AI Controllo gestione | P09 | ControlBoost (1.499€) | Check Express 19€ |
| Integrazione gestionali ERP | P10 | Boost ERP Integration | Check Express 19€ |
| ... (P11-P20) | ... | ... | ... |

**Implementazione tecnica**:
- Il CTA sul pillar passa `?tag=P01` (o equivalente) al `/app/`
- Frontend KBot legge query param → invia in `POST /api/kbot/session` come
  `collected_data.tag_pillar = "P01"`
- System prompt v2 (`prompts.py`) include il tag nel contesto
- Quando arriva il momento dell'upsell, `services.py` lookup
  `catalog.json → trova servizi con tag P01 → suggerisce il Boost giusto`

Vantaggio: zero modifiche al sito vetrina, blog-bot continua, il KBot eredita il
contesto SEO e vende il modello nuovo.

---

## Fase 0 — Setup e misurazione baseline

**Durata**: 1 settimana.
**Obiettivo**: avere numeri reali per dimensionare le fasi successive.
**Codice nuovo**: zero (solo query analytics).

### 0.1 Estrazione metriche K-BOT esistente (3 giorni)

Query da fare contro Supabase `kbot_sessions`, `analytics_events`,
`kbot_conversions`:

```sql
-- Sessioni create per mese (ultimi 90 giorni)
SELECT date_trunc('month', created_at) AS mese,
       count(*) AS sessioni,
       count(*) FILTER (WHERE user_id IS NOT NULL) AS sessioni_loggate,
       count(*) FILTER (WHERE status = 'paid') AS sessioni_pagate
FROM kbot_sessions
WHERE created_at >= now() - interval '90 days'
GROUP BY 1 ORDER BY 1;

-- Conversion funnel
SELECT
  count(*) AS sessioni_totali,
  count(*) FILTER (WHERE jsonb_array_length(messages) > 0) AS sessioni_attive,
  count(*) FILTER (WHERE collected_data->>'reportReady' = 'true') AS report_pronti,
  count(*) FILTER (WHERE status = 'paid') AS pagamenti,
  count(*) FILTER (WHERE pdf_url IS NOT NULL) AS pdf_consegnati
FROM kbot_sessions
WHERE created_at >= now() - interval '30 days';

-- Distribuzione per service_id
SELECT collected_data->>'service_id' AS service,
       count(*) AS n,
       count(*) FILTER (WHERE status = 'paid') AS paid
FROM kbot_sessions
WHERE created_at >= now() - interval '90 days'
GROUP BY 1 ORDER BY 2 DESC;

-- Retention (utenti con >1 sessione)
SELECT user_id, count(*) AS sessioni
FROM kbot_sessions
WHERE user_id IS NOT NULL
  AND created_at >= now() - interval '180 days'
GROUP BY 1
HAVING count(*) > 1
ORDER BY 2 DESC;
```

### 0.2 Costi LLM (1 giorno)

Estrarre dal dashboard Anthropic Console:
- Token Haiku input/output ultimi 90 giorni
- Token Sonnet input/output ultimi 90 giorni
- Costo totale mensile in €
- Costo medio per sessione

Salvare in `docs/tracking/kbot-baseline-2026-06.md`.

### 0.3 Output Fase 0 (1 giorno)

File `docs/tracking/kbot-baseline-2026-06.md` con:
- Sessioni/mese
- Conversion rate sessione → pagamento 19€
- Costo LLM medio per sessione pagata
- Top 5 `service_id` selezionati dagli utenti
- Numero utenti ricorrenti

**Gate per Fase 1**: nessuno, si parte comunque. Ma i numeri determinano se
spingere il volume (più investimenti SEO/ads) o lavorare prima sulla conversion.

---

## Fase 1 — Catalog.json + refactor services.py

**Durata**: 2 settimane.
**Obiettivo**: esternalizzare il catalogo, mantenere comportamento KBot identico.
**Codice nuovo**: ~200 righe (loader + tests).

### 1.1 Schema catalog.json (3 giorni)

Definire e congelare lo schema. Versione iniziale completa.

File `kai-website/kbot/backend/app/data/catalog.json`:

```json
{
  "version": "1.0.0",
  "updated_at": "2026-06-15",
  "tipi_listino": {
    "consumo":   {"label": "Check Express", "ruolo": "entry"},
    "tappa":     {"label": "Tappa percorso", "ruolo": "intermedio"},
    "servizio":  {"label": "Boost", "ruolo": "destinazione"},
    "retainer":  {"label": "Abbonamento", "ruolo": "post-boost"}
  },
  "servizi": [
    {
      "id": "check-express",
      "tipo": "consumo",
      "label": "Check Express PMI",
      "descrizione_breve": "Diagnosi rapida 20 minuti, report PDF.",
      "prezzo_eur": 19,
      "skill_orchestratore": "diagnosi-ai-operativa-pmi",
      "tag_pillar_sito": ["P01","P02","P03","P04","P05","P06","P07","P08",
                          "P09","P10","P11","P12","P13","P14","P15","P16",
                          "P17","P18","P19","P20"]
    },
    {
      "id": "advisorboost",
      "tipo": "servizio",
      "label": "AdvisorBoost",
      "descrizione_breve": "Diagnosi strategica completa + roadmap operativa.",
      "prezzo_eur": 2499,
      "tappe_ordinate": ["ab-tappa-1","ab-tappa-2","ab-tappa-3","ab-tappa-4","ab-tappa-5"],
      "sconto_completamento_pct": 24,
      "skill_orchestratore": "flusso-advisorboost-pmi",
      "tag_pillar_sito": ["P12","P09","P04"]
    },
    {
      "id": "ab-tappa-1",
      "tipo": "tappa",
      "label": "Tappa 1 — Check di partenza",
      "prezzo_eur": 299,
      "percorso_padre": "advisorboost",
      "ordine": 1,
      "skill_orchestratore": "check-pmi-express"
    }
    // ... le altre 4 tappe AdvisorBoost
    // ... gli altri Boost diretti (CRM, Legale, Compliance, ecc.)
  ],
  "percorsi": [
    {
      "id": "advisorboost",
      "destinazione_id": "advisorboost",
      "tappe_id_ordinate": ["ab-tappa-1","ab-tappa-2","ab-tappa-3","ab-tappa-4","ab-tappa-5"],
      "sconto_completamento_pct": 24
    }
  ],
  "abbonamenti": [],
  "mapping_tag_to_servizi": {
    "P01": {"check": "check-express", "boost_primario": "boost-crm-automation"},
    "P02": {"check": "check-express", "boost_primario": "controlboost"},
    "P12": {"check": "check-express", "boost_primario": "advisorboost"}
  }
}
```

JSON Schema in `catalog.schema.json` per validazione CI:

```json
{
  "$schema": "http://json-schema.org/draft-07/schema#",
  "type": "object",
  "required": ["version", "tipi_listino", "servizi", "percorsi"],
  "properties": {
    "version": {"type": "string", "pattern": "^\\d+\\.\\d+\\.\\d+$"},
    "tipi_listino": {"type": "object"},
    "servizi": {
      "type": "array",
      "items": {
        "type": "object",
        "required": ["id", "tipo", "label", "prezzo_eur"],
        "properties": {
          "id": {"type": "string", "pattern": "^[a-z0-9-]+$"},
          "tipo": {"enum": ["consumo", "tappa", "servizio", "retainer"]},
          "label": {"type": "string", "minLength": 1},
          "prezzo_eur": {"type": "integer", "minimum": 0},
          "skill_orchestratore": {"type": "string"},
          "tag_pillar_sito": {
            "type": "array",
            "items": {"type": "string", "pattern": "^P[0-9]{2}$"}
          }
        }
      }
    }
  }
}
```

Validazione CI in `.github/workflows/`:

```yaml
- name: Validate catalog.json
  run: |
    pip install jsonschema
    python -c "import json, jsonschema; \
      jsonschema.validate( \
        json.load(open('kbot/backend/app/data/catalog.json')), \
        json.load(open('kbot/backend/app/data/catalog.schema.json')))"
```

### 1.2 Loader Python (2 giorni)

File `kai-website/kbot/backend/app/lib/catalog.py`:

```python
"""Catalog loader — fonte unica prezzi/servizi/percorsi."""
from __future__ import annotations

import json
import logging
from functools import lru_cache
from pathlib import Path
from typing import Optional

from ..settings import CATALOG_PATH  # nuova env var

log = logging.getLogger(__name__)


@lru_cache(maxsize=1)
def load_catalog() -> dict:
    try:
        return json.loads(Path(CATALOG_PATH).read_text(encoding="utf-8"))
    except Exception as exc:
        log.error("Catalog load failed: %s", exc)
        return {"version": "0", "servizi": [], "percorsi": [], "mapping_tag_to_servizi": {}}


def invalidate() -> None:
    load_catalog.cache_clear()


def get_servizio(servizio_id: str) -> Optional[dict]:
    return next((s for s in load_catalog().get("servizi", [])
                 if s["id"] == servizio_id), None)


def get_percorso(percorso_id: str) -> Optional[dict]:
    return next((p for p in load_catalog().get("percorsi", [])
                 if p["id"] == percorso_id), None)


def lista_percorsi() -> list[dict]:
    return list(load_catalog().get("percorsi", []))


def lista_servizi(tipo: Optional[str] = None) -> list[dict]:
    s = load_catalog().get("servizi", [])
    return [x for x in s if tipo is None or x.get("tipo") == tipo]


def prezzo_per_piano(servizio_id: str, piano: Optional[str]) -> int:
    s = get_servizio(servizio_id)
    if not s:
        return 0
    base = s["prezzo_eur"]
    abbonamenti = {a["id"]: a for a in load_catalog().get("abbonamenti", [])}
    sconto_pct = abbonamenti.get(piano, {}).get("sconto_tappa_pct", 0)
    return int(round(base * (100 - sconto_pct) / 100))


def servizio_per_tag(tag: str, kind: str = "boost_primario") -> Optional[dict]:
    """Lookup: dato un tag P01-P20, ritorna il servizio mappato (check o boost)."""
    mapping = load_catalog().get("mapping_tag_to_servizi", {}).get(tag, {})
    servizio_id = mapping.get(kind)
    if not servizio_id:
        return None
    return get_servizio(servizio_id)


def scheda_percorso(percorso_id: str) -> Optional[dict]:
    """Restituisce percorso + tappe complete con prezzi."""
    p = get_percorso(percorso_id)
    if not p:
        return None
    tappe = [get_servizio(t_id) for t_id in p.get("tappe_id_ordinate", [])]
    tappe = [t for t in tappe if t is not None]
    return {
        **p,
        "destinazione": get_servizio(p["destinazione_id"]),
        "tappe": tappe,
        "prezzo_tappe_totale": sum(t["prezzo_eur"] for t in tappe),
    }
```

Settings: aggiungere `CATALOG_PATH` in `settings.py`:

```python
CATALOG_PATH = Path(
    _env("KBOT_CATALOG_PATH", default=str(ROOT / "app" / "data" / "catalog.json"))
).resolve()
```

### 1.3 Refactor services.py (3 giorni)

`services.py` esistente: hardcoded registry `SUITE_AI_SERVICES` + intent keyword.

Modifica:

```python
# kai-website/kbot/backend/app/lib/services.py
from . import catalog
from typing import Optional


# Manteniamo i 20 servizi P01-P20 ESCLUSIVAMENTE come tag SEO sito.
# Il catalogo commerciale vero del KBot è in catalog.json.
LEGACY_PILLAR_TAGS = {f"P{i:02d}" for i in range(1, 21)}


def normalize_tag(value: Optional[str]) -> Optional[str]:
    if not value:
        return None
    v = str(value).strip().upper()
    return v if v in LEGACY_PILLAR_TAGS else None


def get_pillar_tag(session: dict) -> Optional[str]:
    """Estrai il tag pillar dalla sessione (sostituisce service_id)."""
    collected = session.get("collected_data") or {}
    return normalize_tag(collected.get("tag_pillar") or collected.get("service_id"))


def resolve_check_for_session(session: dict) -> Optional[dict]:
    """Quale Check Express proporre — di solito sempre check-express, ma future-proof."""
    return catalog.get_servizio("check-express")


def resolve_boost_for_session(session: dict) -> Optional[dict]:
    """Quale Boost suggerire all'utente in base al tag pillar."""
    tag = get_pillar_tag(session)
    if not tag:
        return None
    return catalog.servizio_per_tag(tag, kind="boost_primario")


def resolve_skills_for_session(session: dict, forced: Optional[list[str]] = None) -> list[str]:
    """Decide quali skill caricare nel system prompt.

    Logica:
    1. Skill base sempre presente (diagnosi-ai-operativa-pmi)
    2. Se forced_skills passate dal frontend: usale
    3. Se sessione ha già selezionato un servizio specifico: carica skill_orchestratore
    4. Altrimenti, se ha tag pillar: carica skill del Boost suggerito
    """
    skills = ["diagnosi-ai-operativa-pmi"]
    if forced:
        skills.extend(s for s in forced if s not in skills)
        return skills

    collected = session.get("collected_data") or {}
    servizio_attivo = collected.get("servizio_attivo")
    if servizio_attivo:
        s = catalog.get_servizio(servizio_attivo)
        if s and s.get("skill_orchestratore"):
            if s["skill_orchestratore"] not in skills:
                skills.append(s["skill_orchestratore"])

    boost = resolve_boost_for_session(session)
    if boost and boost.get("skill_orchestratore"):
        if boost["skill_orchestratore"] not in skills:
            skills.append(boost["skill_orchestratore"])

    return skills


# Intent detection KEYWORD-BASED: tiene il pattern attuale ma mappa ai tag P01-P20
# (resta come fallback se il tag non arriva dal frontend).
_INTENT_KEYWORDS_BY_TAG: dict[str, list[str]] = {
    "P01": ["email", "crm", "lead generation", "outreach", "agenti email"],
    "P02": ["amministr", "fatture", "contabilità", "riconciliazion", "bilancio"],
    # ... (riprendi keyword esistenti)
}


def infer_tag_from_session(session: dict) -> Optional[str]:
    """Fallback: inferisce il tag pillar da keyword nel primo messaggio utente."""
    msgs = session.get("messages") or []
    first_user = next((m for m in msgs if m.get("role") == "user"), None)
    if not first_user:
        return None
    text = str(first_user.get("content") or "").lower()
    for tag, keywords in _INTENT_KEYWORDS_BY_TAG.items():
        if any(kw in text for kw in keywords):
            return tag
    return None
```

### 1.4 Aggiornare sessioni per accettare `tag_pillar` (1 giorno)

`kbot/backend/app/api/session.py`:

```python
class SessionCreateBody(BaseModel):
    serviceId: Optional[str] = Field(default=None, alias="service_id")
    tagPillar: Optional[str] = Field(default=None, alias="tag_pillar")  # NUOVO
    mode: Optional[str] = None
    # ...
```

`kbot/backend/app/lib/sessions.py`:

```python
def create_session(*, tag_pillar: Optional[str], mode: Optional[str], user_id: Optional[str]) -> dict:
    tag = normalize_tag(tag_pillar)
    collected_data: dict = {"mode": _coerce_mode(mode), "extractedData": {}}
    if tag:
        collected_data["tag_pillar"] = tag
    # ...
```

Frontend Next.js: `kbot/src/lib/api.ts` aggiunge il parametro nella chiamata
`ensureSession()`. Letto da `useSearchParams()` su `/app/?tag=P01`.

### 1.5 Test (2 giorni)

File `kbot/backend/tests/test_catalog.py`:

```python
import pytest
from app.lib import catalog

def test_catalog_loads_with_required_servizi():
    cat = catalog.load_catalog()
    assert "servizi" in cat
    assert any(s["id"] == "check-express" for s in cat["servizi"])

def test_get_servizio_returns_correct():
    s = catalog.get_servizio("check-express")
    assert s is not None
    assert s["prezzo_eur"] == 19
    assert s["tipo"] == "consumo"

def test_servizio_per_tag_p12():
    s = catalog.servizio_per_tag("P12", kind="boost_primario")
    assert s is not None
    assert s["id"] == "advisorboost"

def test_prezzo_per_piano_business():
    # Business = -20%, AdvisorBoost = 2499 → 1999
    prezzo = catalog.prezzo_per_piano("advisorboost", "business")
    assert prezzo == 1999

def test_scheda_percorso_advisorboost():
    sp = catalog.scheda_percorso("advisorboost")
    assert sp is not None
    assert len(sp["tappe"]) == 5
    assert sp["destinazione"]["prezzo_eur"] == 2499
```

File `kbot/backend/tests/test_services.py`: test che `resolve_boost_for_session`
ritorni AdvisorBoost per sessione con `tag_pillar=P12`.

### 1.6 Verifica fase 1

- ✅ `services.py` non contiene più `SUITE_AI_SERVICES` hardcoded
- ✅ `kbot_sessions` accetta `tag_pillar` ma resta retrocompatibile con
  `service_id` (mapping interno)
- ✅ System prompt v2 carica le skill corrette in base al tag
- ✅ Test catalog passano
- ✅ Sessione cold start senza tag: comportamento attuale invariato (chiede tipo
  di analisi)
- ✅ Sessione con `?tag=P12`: KBot orienta verso AdvisorBoost

**Gate per Fase 2**: nessuno tecnico. Si procede.

---

## Fase 2 — Sito vetrina: aggiungere `?tag=` ai CTA pillar

**Durata**: 1 settimana.
**Obiettivo**: alimentare il KBot col contesto pillar dal sito SEO.
**File toccati**: solo sito Vite (`kai-website/src/`).

### 2.1 Identificare i CTA "Apri K-BOT" (1 giorno)

Greppare il sito per CTA esistenti che linkano a `/app/`:

```bash
grep -rn "/app/" kai-website/src/ --include="*.html" --include="*.js"
```

Verosimile: CTA in `suite-ai.html`, `k-bot.html`, `per-te.html`, e nei pillar
hub man mano che vengono creati (`/suite-ai/*.html`).

### 2.2 Aggiungere tag al CTA (2 giorni)

Pattern: ogni pillar hub passa il proprio tag al KBot.

Esempio in `/suite-ai/agenti-email-crm.html`:

```html
<a href="/app/?tag=P01&utm_source=pillar-p01" class="cta-kbot">
  Apri K-BOT — pronto per agenti email/CRM
</a>
```

Pages da aggiornare quando esistono:
- `/suite-ai/agenti-email-crm.html` → `?tag=P01`
- `/suite-ai/automazioni-amministrative.html` → `?tag=P02`
- ... (per tutti i 20 pillar quando vengono pubblicati)

Per la homepage e pagine generaliche dove non c'è un tag specifico: nessun
parametro (KBot fa cold start come oggi).

### 2.3 Frontend KBot legge il tag (2 giorni)

`kbot/src/app/page.tsx` o equivalente entry point:

```tsx
import { useSearchParams } from 'next/navigation';

export default function ChatPage() {
  const params = useSearchParams();
  const tag = params.get('tag');  // "P01", "P12", ecc.

  useEffect(() => {
    if (!sessionId) {
      ensureSession({ mode: 'report', tag_pillar: tag });
    }
  }, [tag]);
  // ...
}
```

`kbot/src/lib/api.ts`:

```ts
export async function ensureSession(args: {
  mode: 'report' | 'lead';
  tag_pillar?: string | null;
}) {
  const res = await fetch(`${BACKEND}/api/kbot/session`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({
      mode: args.mode,
      tag_pillar: args.tag_pillar ?? undefined,
    }),
  });
  return res.json();
}
```

### 2.4 System prompt riconosce il tag (1 giorno)

`kbot/backend/app/lib/prompts.py` — aggiungere blocco al system prompt v2:

```python
def _tag_context_block(session: dict) -> str:
    tag = (session.get("collected_data") or {}).get("tag_pillar")
    if not tag:
        return ""

    # Lookup catalogo: che Boost mostriamo? Che descrizione?
    from . import catalog
    boost = catalog.servizio_per_tag(tag, kind="boost_primario")
    if not boost:
        return f"\nL'utente arriva dal pillar SEO {tag}. Orienta domande in quel dominio.\n"

    return (
        f"\nCONTESTO INGRESSO UTENTE: pillar SEO {tag}.\n"
        f"L'utente probabilmente cerca aiuto in quell'ambito.\n"
        f"Al momento giusto, proporre come prossimo passo: {boost['label']} "
        f"({boost['prezzo_eur']}€) — {boost.get('descrizione_breve', '')}.\n"
        f"NON spingere il Boost subito: prima fai diagnosi (Check Express, 19€) "
        f"e proponi il Boost solo dopo che il problema è chiaro.\n"
    )
```

E in `build_system_prompt_v2`:

```python
def build_system_prompt_v2(skill_names, session):
    # ... (codice esistente)
    tag_context = _tag_context_block(session)
    # ... append tag_context al prompt finale
```

### 2.5 Verifica fase 2

- ✅ Cliente clicca CTA su `/suite-ai/agenti-email-crm.html` → arriva su
  `/app/?tag=P01` → KBot sa che è P01
- ✅ KBot non spara subito il Boost: prima fa diagnosi (Check Express)
- ✅ Cold start (no tag) si comporta come oggi
- ✅ Tag invalido viene scartato silentemente

**Gate per Fase 3**: vedere ≥30 sessioni con tag nei primi 14 giorni di
deploy. Se zero, il funnel SEO → KBot non funziona e va investigato (CTA non
visibili? Sito non riceve traffico?).

---

## Fase 3 — Upsell statico post-Check

**Durata**: 2 settimane.
**Obiettivo**: vendere il primo Boost dopo il Check Express. Senza tool use,
senza agente complesso.
**Codice nuovo**: ~300 righe (UI + endpoint + tracking).

### 3.1 Endpoint suggerimento Boost (2 giorni)

`kbot/backend/app/api/upsell.py` (nuovo):

```python
"""GET /api/kbot/upsell/{session_id} — suggerisce il prossimo Boost."""
from fastapi import APIRouter, HTTPException
from ..lib import sessions, services, catalog

router = APIRouter()

@router.get("/upsell/{session_id}")
def get_upsell(session_id: str):
    session = sessions.get_session(session_id)
    if not session:
        raise HTTPException(404, "session not found")

    # Suggerisci solo se Check è stato pagato
    if session.get("status") != "paid":
        return {"available": False, "reason": "check non ancora pagato"}

    boost = services.resolve_boost_for_session(session)
    if not boost:
        # Fallback: AdvisorBoost se non c'è tag
        boost = catalog.get_servizio("advisorboost")

    return {
        "available": True,
        "boost": {
            "id": boost["id"],
            "label": boost["label"],
            "prezzo_eur": boost["prezzo_eur"],
            "descrizione": boost.get("descrizione_breve", ""),
        },
        "cta": {
            "type": "form_airtable",
            "url": "https://airtable.com/embed/<form_id>?prefill_tag=" + 
                   (services.get_pillar_tag(session) or ""),
        },
    }
```

### 3.2 UI upsell post-pagamento (4 giorni)

`kbot/src/components/report/ReportCard.tsx` — aggiungere sezione "Prossimo passo":

```tsx
import { useEffect, useState } from 'react';
import { fetchUpsell } from '@/lib/api';

export function UpsellPanel({ sessionId }: { sessionId: string }) {
  const [upsell, setUpsell] = useState<UpsellData | null>(null);

  useEffect(() => {
    fetchUpsell(sessionId).then(setUpsell);
  }, [sessionId]);

  if (!upsell?.available) return null;

  return (
    <div className="upsell-panel mt-8 p-6 border rounded-lg bg-amber-50">
      <h3 className="font-bold">Il tuo prossimo passo</h3>
      <p className="mt-2">{upsell.boost.descrizione}</p>
      <div className="mt-4 flex items-baseline gap-2">
        <span className="text-2xl font-bold">{upsell.boost.label}</span>
        <span className="text-xl">{upsell.boost.prezzo_eur}€</span>
      </div>
      <a
        href={upsell.cta.url}
        target="_blank"
        rel="noopener"
        className="mt-4 inline-block btn btn-primary"
        onClick={() => trackUpsellClicked(sessionId, upsell.boost.id)}
      >
        Prenota call gratuita →
      </a>
    </div>
  );
}
```

Posizionamento: appare DOPO che il PDF è stato consegnato (`pdf_url` presente),
sia in chat sia in `/dashboard`.

### 3.3 Form Airtable + tracking (2 giorni)

Creare form Airtable con campi:
- email (prefilled da Supabase)
- tag pillar (prefilled da query)
- servizio interessato (prefilled)
- note libere

Tracking eventi in `analytics_events`:

```python
# kbot/backend/app/api/upsell.py
@router.post("/upsell/{session_id}/clicked")
def upsell_clicked(session_id: str, boost_id: str):
    from ..lib.analytics import track_server
    track_server("upsell_clicked", session_id=session_id, payload={"boost_id": boost_id})
    return {"ok": True}
```

Frontend: chiamare endpoint al click prima di aprire il form.

### 3.4 Notifica email per Luca (1 giorno)

Quando arriva una nuova submission Airtable → webhook Airtable → endpoint
FastAPI `POST /api/kbot/lead-qualified` → email a Luca via Resend.

### 3.5 Verifica fase 3

- ✅ Utente paga Check 19€ → PDF consegnato → vede pannello upsell
- ✅ Click apre Airtable prefilled
- ✅ Submission → email a Luca
- ✅ Tracking eventi visibile in `analytics_events`
- ✅ Cold start senza tag: comunque mostra AdvisorBoost come fallback

**Gate per Fase 4**: ≥2 Boost venduti (anche tramite call) entro 60 giorni
dal deploy. Se zero, il problema NON è il sistema — è il prodotto o il
traffico. Da indagare prima di costruire il percorso a tappe.

---

## Fase 4 — Primo percorso pilota (AdvisorBoost)

**Durata**: 4 settimane.
**Obiettivo**: implementare il pattern "tappe sequenziali con sconto
completamento" per UN solo percorso (AdvisorBoost).
**Codice nuovo**: ~800 righe (5 endpoint tappe + UI + state machine + skill
orchestratrici).

### 4.1 Schema acquisti (3 giorni)

Nuova tabella Supabase `kbot_purchases`:

```sql
-- migration 004
CREATE TABLE IF NOT EXISTS kbot_purchases (
  id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  user_id         UUID NOT NULL REFERENCES auth.users(id) ON DELETE CASCADE,
  servizio_id     TEXT NOT NULL,
  servizio_tipo   TEXT NOT NULL CHECK (servizio_tipo IN ('consumo','tappa','servizio','retainer')),
  percorso_id     TEXT,
  prezzo_pagato_cents INT NOT NULL,
  stripe_session_id TEXT,
  paid_at         TIMESTAMPTZ NOT NULL DEFAULT now(),
  deliverable_url TEXT,
  status          TEXT NOT NULL DEFAULT 'paid' CHECK (status IN ('paid','delivered','refunded'))
);

CREATE INDEX kbot_purchases_user_path
  ON kbot_purchases (user_id, percorso_id, paid_at);

ALTER TABLE kbot_purchases ENABLE ROW LEVEL SECURITY;

CREATE POLICY kbot_purchases_select_own ON kbot_purchases
  FOR SELECT USING (auth.uid() = user_id);
```

### 4.2 Skill orchestratrici per le 5 tappe (10 giorni)

Per ogni tappa AdvisorBoost serve una skill in `lib/skills/`:

| Tappa | Skill | Output |
|---|---|---|
| 1 — Check di partenza | `check-pmi-express` (esiste già) | PDF diagnosi 5 pagine |
| 2 — Analisi settore | `analisi-settore-pmi` (esiste già) | PDF analisi settore 10 pagine |
| 3 — Analisi bilancio | `analisi-bilancio-pmi` (esiste già) | PDF analisi finanziaria 15 pagine |
| 4 — Posizionamento | `posizionamento-pmi` (DA CREARE) | PDF posizionamento 10 pagine |
| 5 — Sintesi AdvisorBoost | `flusso-advisorboost-pmi` (DA ASSEMBLARE) | PDF completo 30+ pagine |

Per le skill da creare/assemblare, replicare il pattern esistente:
- `SKILL.md` con system prompt specifico
- Eventuali `references/*.md` con framework di settore
- `generate-pdf` endpoint richiama il modello configurato (Sonnet) con la skill
  caricata + i dati raccolti

### 4.3 State machine acquisti tappa (5 giorni)

`kbot/backend/app/lib/percorsi.py` (nuovo):

```python
"""State machine percorsi a tappe."""
from . import catalog, supabase_admin

def get_progress(user_id: str, percorso_id: str) -> dict:
    """Ritorna lo stato di completamento di un percorso per un utente."""
    sp = catalog.scheda_percorso(percorso_id)
    if not sp:
        return {}

    client = supabase_admin.get_admin_client()
    purchases = client.table("kbot_purchases") \
        .select("servizio_id, paid_at") \
        .eq("user_id", user_id) \
        .eq("percorso_id", percorso_id) \
        .execute().data or []

    paid_ids = {p["servizio_id"] for p in purchases}
    tappe_status = []
    for t in sp["tappe"]:
        tappe_status.append({
            "tappa": t,
            "paid": t["id"] in paid_ids,
        })

    next_tappa = next((t for t in tappe_status if not t["paid"]), None)
    completato = all(t["paid"] for t in tappe_status)

    return {
        "percorso": sp,
        "tappe_status": tappe_status,
        "next_tappa": next_tappa["tappa"] if next_tappa else None,
        "completato": completato,
        "sconto_completamento_pct": sp.get("sconto_completamento_pct", 0) if completato else 0,
    }


def can_purchase_tappa(user_id: str, tappa_id: str) -> tuple[bool, str]:
    """Verifica se l'utente può acquistare questa tappa (ordine + non già pagata)."""
    tappa = catalog.get_servizio(tappa_id)
    if not tappa or tappa["tipo"] != "tappa":
        return False, "non è una tappa valida"

    percorso = tappa.get("percorso_padre")
    progress = get_progress(user_id, percorso)
    paid_ids = {t["tappa"]["id"] for t in progress["tappe_status"] if t["paid"]}

    if tappa_id in paid_ids:
        return False, "tappa già pagata"

    # Tappa N può essere acquistata solo se tappe 1..N-1 sono pagate
    sp = catalog.scheda_percorso(percorso)
    for t in sp["tappe"]:
        if t["id"] == tappa_id:
            break
        if t["id"] not in paid_ids:
            return False, f"prima devi acquistare {t['label']}"

    return True, ""
```

### 4.4 Checkout dinamico per tappa (4 giorni)

`kbot/backend/app/api/checkout.py` — estendere:

```python
class CheckoutBody(BaseModel):
    sessionId: str = Field(..., alias="session_id")
    servizioId: str = Field(..., alias="servizio_id")  # NUOVO
    email: Optional[EmailStr] = None

@router.post("/checkout")
def checkout(body: CheckoutBody, user: AuthUser = Depends(require_user)):
    # ... ownership check, ecc.

    s = catalog.get_servizio(body.servizioId)
    if not s:
        raise HTTPException(404, "servizio non trovato")

    # Se è una tappa, verifica ordine
    if s["tipo"] == "tappa":
        ok, reason = percorsi.can_purchase_tappa(user.id, body.servizioId)
        if not ok:
            raise HTTPException(409, reason)

    # Crea Stripe Checkout dinamica
    checkout_session = stripe.checkout.Session.create(
        mode="payment",
        line_items=[{
            "price_data": {
                "currency": "eur",
                "unit_amount": s["prezzo_eur"] * 100,
                "product_data": {"name": s["label"]},
            },
            "quantity": 1,
        }],
        success_url=...,
        cancel_url=...,
        metadata={
            "kbot_session_id": body.sessionId,
            "user_id": user.id,
            "servizio_id": body.servizioId,
            "percorso_id": s.get("percorso_padre", ""),
        },
        client_reference_id=body.sessionId,
    )
    return {"url": checkout_session.url}
```

### 4.5 Webhook estendere (3 giorni)

`kbot/backend/app/api/webhook.py` — gestire pagamento tappa:

```python
@router.post("/stripe/webhook")
async def stripe_webhook(request, stripe_signature):
    # ... verifica firma esistente

    obj = event["data"]["object"].to_dict()
    metadata = obj.get("metadata") or {}
    user_id = metadata.get("user_id")
    servizio_id = metadata.get("servizio_id")

    # CASO 1: Check Express (vecchio flusso, retro-compat)
    if not servizio_id:
        # Comportamento attuale
        return _handle_legacy_checkout(obj)

    # CASO 2: pagamento di un servizio del catalogo (tappa o Boost)
    s = catalog.get_servizio(servizio_id)
    if not s:
        log.warning("Servizio sconosciuto: %s", servizio_id)
        return {"ok": True}

    # Registra acquisto
    client = supabase_admin.get_admin_client()
    client.table("kbot_purchases").insert({
        "user_id": user_id,
        "servizio_id": servizio_id,
        "servizio_tipo": s["tipo"],
        "percorso_id": s.get("percorso_padre"),
        "prezzo_pagato_cents": obj.get("amount_total"),
        "stripe_session_id": obj.get("id"),
        "status": "paid",
    }).execute()

    # Triggera generazione deliverable della tappa
    if s.get("skill_orchestratore"):
        _trigger_deliverable_generation(user_id, servizio_id, s["skill_orchestratore"])

    return {"ok": True}
```

### 4.6 UI percorso e tappe (5 giorni)

`kbot/src/components/percorso/PercorsoPanel.tsx` (nuovo):

```tsx
export function PercorsoPanel({ percorsoId, userId }: Props) {
  const { progress } = useProgress(userId, percorsoId);

  if (!progress) return <Skeleton />;

  return (
    <div className="percorso-panel">
      <h2>{progress.percorso.destinazione.label}</h2>
      <div className="tappe-list">
        {progress.tappe_status.map((t, i) => (
          <TappaCard
            key={t.tappa.id}
            tappa={t.tappa}
            paid={t.paid}
            isNext={progress.next_tappa?.id === t.tappa.id}
            order={i + 1}
          />
        ))}
      </div>
      {progress.completato && (
        <div className="completion-banner">
          ✅ Percorso completato! Hai risparmiato {progress.sconto_completamento_pct}%
        </div>
      )}
    </div>
  );
}
```

### 4.7 Tracking conversione percorso (1 giorno)

Eventi `analytics_events`:
- `percorso_iniziato` (tappa 1 pagata)
- `tappa_completata` (per ogni tappa)
- `percorso_completato` (tutte le tappe)
- `percorso_abbandonato` (60 giorni senza nuove tappe)

### 4.8 Verifica fase 4

- ✅ Utente con tag P12 vede AdvisorBoost suggerito post-Check
- ✅ Compra tappa 1 (299€) → riceve deliverable PDF tappa 1
- ✅ Vede UI con 4 tappe rimanenti, può comprare solo la prossima in ordine
- ✅ Completa tutte le 5 tappe → vede sconto applicato (24%)
- ✅ Tappe pagate sono tracciate in `kbot_purchases`
- ✅ Tentativo di saltare ordine viene bloccato con messaggio chiaro

**Gate per Fase 5**: ≥5 percorsi AdvisorBoost completi venduti nei primi 90
giorni di deploy fase 4. Se zero/uno: percorso non funziona, ripensare prima
di replicare ad altri Boost.

---

## Fase 5 — Tool use selettivo per routing

**Durata**: 2-3 settimane.
**Obiettivo**: sostituire intent detection keyword con tool use Claude quando
ambiguo. Solo dove serve.
**Codice nuovo**: ~500 righe.

### 5.1 Quando attivare tool use (1 settimana)

Definire criterio: tool use attivo SOLO se l'utente NON ha tag pillar nella
sessione (cold start). Se ha già `tag_pillar=P01`, il routing è deterministico
dal catalog.

In cold start, il KBot chiama tool Claude per classificare:

```python
# kbot/backend/app/lib/tools.py (nuovo)
TOOLS = [
    {
        "name": "classifica_bisogno",
        "description": "Classifica il bisogno dell'utente in uno dei pillar P01-P20.",
        "input_schema": {
            "type": "object",
            "properties": {
                "tag_pillar": {
                    "type": "string",
                    "enum": ["P01","P02","P03","P04","P05","P06","P07","P08",
                             "P09","P10","P11","P12","P13","P14","P15","P16",
                             "P17","P18","P19","P20", "UNCLEAR"]
                },
                "confidence": {"type": "number", "minimum": 0, "maximum": 1},
                "reasoning": {"type": "string"},
            },
            "required": ["tag_pillar", "confidence", "reasoning"],
        },
    },
    {
        "name": "scheda_servizio",
        "description": "Ottieni dettagli (prezzo, descrizione) di un servizio del catalogo.",
        "input_schema": {
            "type": "object",
            "properties": {
                "servizio_id": {"type": "string"},
            },
            "required": ["servizio_id"],
        },
    },
    {
        "name": "scheda_percorso",
        "description": "Ottieni composizione di un percorso (tappe ordinate, prezzi).",
        "input_schema": {
            "type": "object",
            "properties": {
                "percorso_id": {"type": "string"},
            },
            "required": ["percorso_id"],
        },
    },
]
```

### 5.2 Loop agentico tool use (1 settimana)

`kbot/backend/app/api/message.py` — estendere per gestire tool use:

```python
async def _run_agentic_loop(client, messages, system, max_iterations=5):
    """Loop Claude → tool → Claude finché non esce risposta finale."""
    for _ in range(max_iterations):
        response = await client.messages.create(
            model=ANTHROPIC_MODEL,
            messages=messages,
            system=system,
            tools=TOOLS,
            max_tokens=4096,
        )

        if response.stop_reason != "tool_use":
            return response  # risposta finale

        # Esegui tool calls
        tool_results = []
        for block in response.content:
            if block.type != "tool_use":
                continue
            result = _execute_tool(block.name, block.input)
            tool_results.append({
                "type": "tool_result",
                "tool_use_id": block.id,
                "content": json.dumps(result),
            })

        messages.append({"role": "assistant", "content": response.content})
        messages.append({"role": "user", "content": tool_results})

    return response


def _execute_tool(name: str, args: dict) -> dict:
    if name == "classifica_bisogno":
        # Salva nella sessione, return ack
        return {"ok": True, "saved": args["tag_pillar"]}
    if name == "scheda_servizio":
        return catalog.get_servizio(args["servizio_id"]) or {"error": "not found"}
    if name == "scheda_percorso":
        return catalog.scheda_percorso(args["percorso_id"]) or {"error": "not found"}
    return {"error": "unknown tool"}
```

### 5.3 Decisione modello: quando Sonnet (3 giorni)

Tool use con Haiku è meno affidabile (errori più frequenti nella scelta dei
tool, parametri sbagliati). Heuristic:

- Cold start (no tag) + primo messaggio: usare Haiku con tool. Se classificazione
  ha confidence < 0.7 → retry con Sonnet (1 sola volta).
- Conversazione successiva: Haiku senza tool (più economico).
- Generazione PDF: Sonnet (come oggi).

Costo stimato per sessione: da 0.01-0.05€ attuale → 0.05-0.15€ con tool use.
Compatibile col budget se le sessioni restano <500/mese.

### 5.4 Fallback se tool use fallisce (2 giorni)

Se Claude non chiama il tool entro 3 turni, fallback a keyword intent detection
(comportamento attuale). Logga l'evento per debug.

### 5.5 Verifica fase 5

- ✅ Cold start senza tag: Claude chiama `classifica_bisogno` e salva il
  risultato
- ✅ KBot propone Boost coerente con la classificazione
- ✅ Costi LLM monitorati ogni settimana, alert se >50€/mese
- ✅ Sessioni con tag esplicito: zero overhead tool use

**Gate per Fase 6**: tool use accuracy ≥80% (verifica manuale su 20 sessioni
campione) E costo LLM <2x baseline. Altrimenti rollback.

---

## Nota architetturale — MCP server: due usi distinti

Nel documento di architettura proposto si parla di "MCP server" in due sensi
che vanno tenuti separati perché hanno scopo, gate e implementazione diversi:

### Uso A — MCP interno per coerenza dei deliverable

**Obiettivo**: garantire che il KBot produca report con riferimenti **autoritativi
e riproducibili**. Stessa norma UNI = stessa risposta sempre. Stesso framework
= applicato in modo identico. Nessuna invenzione del modello.

**Causa della variabilità nei report** scomposta in 4 fonti:

| Causa | Soluzione | MCP server interno aiuta? |
|---|---|---|
| Temperature LLM ≠ 0 | `temperature=0` nelle chiamate | NO |
| Prompt che varia tra sessioni | Skill loader stabile (già in `lib/skills/`) | NO |
| Modello che inventa numeri/norme | Iniezione fonti autoritative nel contesto | **SÌ** ✅ |
| References skill incoerenti | SKILL.md + `references/*.md` versionati | Parzialmente |

MCP interno copre **causa 3**. Le altre 3 vanno gestite a prescindere.

**Quando MCP interno batte references statici nelle SKILL.md**:

| Dominio K2-AI | Cambia? | Volume | Tecnologia consigliata |
|---|---|---|---|
| Framework analisi (5 forze, SWOT, BSC) | Mai | Piccolo | `references/*.md` (già implementato) |
| Norme UNI/CEI consolidate | Raro | Medio | `references/*.md` con estratti |
| Leggi italiane consolidate (Codice civile) | Raro | Medio | `references/*.md` |
| **Bandi agevolazioni aperti/chiusi** | Spesso | Medio | **MCP server interno** |
| **Schede prodotto/fornitori** | Spesso | Medio | DB Supabase o MCP |
| **Tassi BCE, indici ISTAT, cambi** | Mensile | Piccolo | API esterna via tool |
| **Visure camerali, P.IVA lookup** | Realtime | Piccolo | API esterna via tool |

**Regola**: MCP interno SOLO per dati dinamici (cambiano >1/mese) o lookup
parametrici (es. "verifica bando X per P.IVA Y"). Per tutto il resto, le
references in SKILL.md fanno lo stesso lavoro con 1/10 del costo.

**Dove vive l'MCP interno**: container Railway separato (o sub-route dello
stesso backend FastAPI) che il KBot interroga server-side. Non passa
dall'API Claude come "remote MCP connector" — il KBot legge il dato dal
proprio MCP e lo inietta nel system prompt come dato strutturato.

### Uso B — MCP esterno per partner/multi-client

**Obiettivo**: esporre il catalogo K2-AI come MCP server pubblico così che
**agenti Claude di terzi** (consulenti partner, custom GPT, Claude Desktop di
clienti) possano interrogarlo.

Questo è il caso "marketplace": ha senso SOLO con partner reali esterni che
vogliono vendere/proporre i Boost K2-AI da loro agente. È la **Fase 8** del
piano.

### Riepilogo: chi-quando-cosa

| Uso MCP | Fase | Pre-requisito | Container |
|---|---|---|---|
| A — Coerenza report (bandi, dati dinamici) | 6 (per dominio specifico) | Skill orchestratore con quel dominio attivo | Interno, Railway |
| B — Partner esterni (catalogo) | 8 (gated) | ≥1 partner formalmente interessato | Pubblico, autenticato |

Le due implementazioni condividono il loader `catalog.py` ma espongono
interfacce diverse (interno = funzioni Python chiamate dal backend, esterno =
endpoint MCP protocol pubblici).

---

## Fase 6 — Estensione catalogo ad altri Boost

**Durata**: 4-8 settimane (1-2 settimane per Boost).
**Obiettivo**: aggiungere altri Boost al catalogo, uno alla volta.

**Sub-decisione per ogni Boost**: per ogni dominio attivato, identificare le
fonti di dati che il deliverable usa. Se le fonti sono **statiche** (framework,
norme consolidate) → metterle come `references/*.md` nella skill orchestratrice.
Se sono **dinamiche** (bandi aperti, tassi, visure) → valutare un MCP server
interno dedicato a quel dominio (vedi nota architetturale sopra).

Esempio concreto: Boost Agevolazioni (P13) → ha senso un MCP `k2a-mcp-bandi`
con lookup `bandi_aperti(settore, regione, dimensione_azienda)` perché i bandi
cambiano spesso. Boost AdvisorBoost (P12) → references statiche bastano (5
forze Porter, framework Hambrick, ecc.).

### 6.1 Priorità Boost da aggiungere (3 giorni di analisi)

Determinare ordine in base a:
1. Volume traffico SEO sui pillar associati (da Search Console)
2. Conversioni AdvisorBoost dimostrate (se ha funzionato, replica pattern)
3. Disponibilità skill orchestratrici già scritte

Ordine suggerito (rivedibile coi dati):
1. **ControlBoost** (P09 + P02) — controllo gestione + amministrazione, skill
   già presenti
2. **BuildBoost** (P14 + P04) — edilizia, skill già in `lib/skills/`
3. **Boost CRM Automation** (P01) — alto volume SEO
4. **Boost Compliance** (P08) — alto valore percepito

### 6.2 Per ogni Boost nuovo (1-2 settimane)

Replicare pattern AdvisorBoost:
1. Aggiungere entry in `catalog.json` (tappe, prezzi, sconto)
2. Mappare tag SEO → boost in `mapping_tag_to_servizi`
3. Verificare skill orchestratrici: esistono? Vanno create/aggiornate?
4. Aggiungere tappa-skill mapping
5. Test end-to-end: utente con tag arriva → KBot propone → flow completo
6. Smoke test su sessioni reali

### 6.3 Verifica fase 6

- ✅ ≥3 Boost completi nel catalogo (oltre ad AdvisorBoost)
- ✅ Tracking conversion per Boost (quale converte di più?)
- ✅ Documentazione per Luca: come aggiungere un nuovo Boost senza coinvolgere
  developer (modifica `catalog.json` + PR)

**Gate per Fase 7**: ≥3 utenti distinti che hanno acquistato >1 Boost o tappa
nell'arco di 6 mesi. Se zero ricorrenze, non c'è valore commerciale negli
abbonamenti/wallet — skip Fase 7.

---

## Fase 7 — Wallet crediti + abbonamenti (gated)

**Pre-requisito**: gate Fase 6 superato.
**Durata**: 4-6 settimane.
**Obiettivo**: introdurre meccanica abbonamento Pro/Business con sconto + wallet
crediti.

Sketch (non dettaglio finché non si arriva qui):

1. Nuova migration `005_kbot_credits.sql`:
   - `kbot_credits (user_id PK, saldo INT, updated_at)`
   - `kbot_credit_movements (id, user_id, delta, motivo, ts, ref_purchase_id)`
2. Stripe Subscription per Pro (49€/mese) e Business (149€/mese)
3. Webhook estende `customer.subscription.created/updated/deleted`
4. Cron job notturno per:
   - Accredito mensile crediti agli abbonati
   - Decadenza crediti dopo 12 mesi inattività + email reminder Resend
5. UI wallet in `dashboard/` con saldo, movimenti, prossima ricarica
6. Logica acquisto: prima usa crediti, poi Stripe per la differenza
7. Sconto piano L3 (-10% Pro, -20% Business) applicato in `prezzo_per_piano`

**Gate per Fase 8**: ≥20 abbonati attivi.

---

## Fase 8 — MCP server pubblico per partner (gated) — Uso B

**Pre-requisito**: gate Fase 7 + ≥1 partner formalmente interessato.
**Durata**: 3-4 settimane.
**Obiettivo**: esporre `catalog.json` come MCP server pubblico per partner
esterni che vendono Boost K2-AI tramite proprio agente Claude (consulenti,
custom GPT brandizzati, agenzie partner).

Questa fase copre l'**Uso B** della nota architetturale (multi-client). Per
l'**Uso A** (MCP interno per coerenza report su dati dinamici) le decisioni
vanno prese caso per caso in Fase 6.

Sketch:

1. MCP server wrapper sopra `catalog.py` (riusa stesso loader)
2. Hosting: container Railway separato o sub-route dello stesso backend
3. Autenticazione: API key per partner
4. Tool esposti: `lista_servizi`, `scheda_servizio`, `scheda_percorso`, `prezzo_per_piano`
5. Endpoint per registrazione acquisto da partner (con fee tracking)
6. Documentazione per partner

---

## Riepilogo timeline

| Fase | Durata | Cumulativo |
|---|---|---|
| 0 — Misurazione baseline | 1 sett | 1 sett |
| 1 — Catalog.json + refactor services.py | 2 sett | 3 sett |
| 2 — Sito vetrina passa `?tag=` | 1 sett | 4 sett |
| 3 — Upsell statico post-Check | 2 sett | 6 sett |
| 4 — Percorso pilota AdvisorBoost | 4 sett | 10 sett |
| 5 — Tool use selettivo | 2-3 sett | 13 sett |
| 6 — Estensione 3+ Boost | 4-8 sett | 17-21 sett |
| 7 — Wallet + abbonamenti (gated) | 4-6 sett | +4-6 sett |
| 8 — MCP server pubblico (gated) | 3-4 sett | +3-4 sett |

Fasi 0-6 in ~5 mesi calendar. Fasi 7-8 solo se i gate quantitativi vengono
raggiunti.

---

## Rischi e mitigazioni

| Rischio | Probabilità | Mitigazione |
|---|---|---|
| Conversion Check → Boost troppo bassa | Alta | Fase 0 misura baseline. Gate Fase 4 a 2 Boost/60 giorni — se non raggiunto, fermarsi |
| Costi LLM esplodono con tool use | Media | Tool use solo cold start. Monitoring settimanale costi. Cap su sessione |
| Skill orchestratrici nuove producono output scarso | Media | Smoke test manuale su ogni nuova skill prima di aprirla al pubblico |
| Catalogo cambia spesso = confusione | Bassa | JSON schema + CI validation + PR review forzata |
| Sito SEO genera traffico ma KBot non converte | Media | UTM tracking + funnel analysis dopo 30gg |
| Disallineamento tra team backend e ecosistema | Media | Schema catalogo è il contratto. Decisioni in PR con changelog |

---

## Decisioni operative ancora aperte (non bloccanti, da chiudere prima di Fase 3)

1. **Pricing Check**: 19€ resta o passa a 49€? Decisione consigliata: 19€
   resta per validare il funnel attuale. Cambio a 49€ valutabile dopo Fase 3
   con dati di conversion.
2. **AdvisorBoost self-serve completo o ibrido**: tappa 1 sicuramente self-serve,
   tappe 4-5 potrebbero richiedere call. Da decidere dopo prime vendite reali.
3. **Email da chi**: notifiche upsell partono da `noreply@k2-ai.it` (Resend) o
   da Luca direttamente? Decisione bassa priorità.
4. **Branding Boost**: rinominare "AdvisorBoost" mantenendo lo stesso prodotto?
   Decisione marketing, non blocca tecnico.

---

## Cheat sheet — comandi e file principali

```
# Sviluppo locale K-BOT
cd kai-website/kbot/backend && uvicorn app.main:app --reload --port 8000
cd kai-website/kbot && npm run dev

# Validare catalog.json
python -c "import json, jsonschema; \
  jsonschema.validate( \
    json.load(open('kai-website/kbot/backend/app/data/catalog.json')), \
    json.load(open('kai-website/kbot/backend/app/data/catalog.schema.json')))"

# Test backend
cd kai-website/kbot/backend && pytest tests/

# Deploy Railway (entrambi i servizi)
cd kai-website/kbot/backend && railway up --detach
cd kai-website/kbot && railway up --detach

# Modificare il catalogo
vim kai-website/kbot/backend/app/data/catalog.json
git checkout -b feat/catalog-<descrizione>
git commit -m "feat(catalog): aggiungi servizio X"
gh pr create
```

| File | Cosa contiene |
|---|---|
| `kbot/backend/app/data/catalog.json` | Catalogo (prezzi, servizi, percorsi) |
| `kbot/backend/app/data/catalog.schema.json` | JSON Schema per validazione |
| `kbot/backend/app/lib/catalog.py` | Loader Python del catalogo |
| `kbot/backend/app/lib/services.py` | Resolver skill + tag pillar (refactorato) |
| `kbot/backend/app/lib/percorsi.py` | State machine percorsi (Fase 4) |
| `kbot/backend/app/lib/tools.py` | Tool definitions per Claude (Fase 5) |
| `kbot/backend/app/api/upsell.py` | Endpoint upsell (Fase 3) |
| `kbot/backend/app/api/checkout.py` | Esteso per checkout dinamico (Fase 4) |
| `kbot/backend/app/api/webhook.py` | Esteso per pagamenti tappa (Fase 4) |
| `kbot/src/components/percorso/PercorsoPanel.tsx` | UI percorso tappe (Fase 4) |
| `kbot/src/components/report/UpsellPanel.tsx` | UI upsell post-Check (Fase 3) |
| `kbot/supabase/migrations/004_kbot_purchases.sql` | Schema acquisti (Fase 4) |
| `kbot/supabase/migrations/005_kbot_credits.sql` | Schema wallet (Fase 7) |

---

## Domande di verifica al proponente del modello

> **Istruzioni per il destinatario**: rispondere in un file Markdown
> `risposta-verifica-piano-kbot.md` con la stessa numerazione delle domande.
> Risposte sintetiche ma complete (no bullet vuoti). Dove non si sa, scrivere
> esplicitamente "DA DEFINIRE — proposta:" e mettere una proposta concreta. Non
> lasciare campi senza testo.
>
> Le domande coprono: catalogo, percorsi, skill/orchestratori, MCP, deliverable,
> economics, governance, edge case. Servono a verificare che ogni pezzo del
> modello sia stato pensato fino in fondo prima di costruirlo.

### A. Catalogo e modello commerciale

A.1 — Quanti **Boost diretti** in totale prevedete nel modello a regime? Elencarli
con id, label, prezzo finale, e tag pillar SEO associati (P01-P20).

A.2 — Quanti **percorsi a tappe** prevedete? Per ognuno: id, destinazione,
elenco ordinato delle tappe con id+label+prezzo, sconto completamento %.

A.3 — Per ogni **tappa** prevista, indicare: durata stimata di erogazione
(quante ore di lavoro umano/AI?), output deliverable (PDF, dashboard, altro?),
SLA di consegna al cliente (immediato? 24h? 7gg?).

A.4 — Quale è il rapporto **prezzo tappa singola vs prezzo Boost completo**?
Esempio per AdvisorBoost: somma tappe = 2.247€ (299+349+449+449+701)? Boost
completo = 2.499€? Sconto completamento 24% applicato dove esattamente — sulle
tappe successive man mano che si completano, o tutto a fine percorso?

A.5 — Il **Check Express 19€** è realmente un "consumo" diverso dalla prima
tappa del Boost-a-percorso, o coincide con `ab-tappa-1`? Se coincide, l'utente
che ha pagato Check Express ha automaticamente la prima tappa di AdvisorBoost
o deve ri-comprarla?

A.6 — Il prezzo del Check va portato da 19€ a 49€? Quando? Con quale
giustificazione data al mercato? Cosa succede ai payment link 19€ già
distribuiti via email/social/firme?

A.7 — Tutti i Boost sono **acquistabili self-serve** dal portale (web puro) o
alcuni richiedono call → contratto offline? Mappare per ogni Boost.

A.8 — Esiste un **upper limit** al numero di Boost/tappe acquistabili da
singolo cliente in un periodo? (Per evitare abuse o errori). Es. max 1 Boost
attivo per cliente, max N tappe/mese.

### B. Skill orchestratori e deliverable

B.1 — Per **ogni Boost e tappa** del catalogo proposto, indicare la skill
orchestratrice corrispondente: nome esatto della directory in `lib/skills/`,
se esiste già o va creata.

B.2 — Per le skill **da creare ex novo**, chi le scrive? Quando? Sono in
backlog del team ecosistema o le scrive il team KBot? Stima di effort per
ognuna.

B.3 — Le skill esistenti in `kai-website/lib/skills/` e `skills sito k2-ai 2/`
sono compatibili come orchestratori dei nuovi Boost, o vanno **riadattate**?
Per quali skill servono modifiche e perché?

B.4 — Output dei deliverable: tutti PDF o anche **altri formati** (dashboard
HTML interattiva, JSON strutturato, Excel)? Per ogni tipologia, quale tooling
genera il file?

B.5 — Il **report PDF generato deve essere riproducibile** (stesso input →
stesso PDF)? Se sì, come si gestisce la non-determinismo intrinseco di Sonnet
con temperature > 0? Si accetta variabilità contenutistica purché la struttura
sia identica?

B.6 — Il deliverable di una tappa va **riusato** dalle tappe successive (es.
diagnosi tappa 1 è input di tappa 2)? Come viene passato il contesto tra tappe
nello stesso percorso?

B.7 — Le skill possono **richiedere input strutturati** all'utente che il KBot
deve raccogliere prima dell'erogazione (es. dati di bilancio, P.IVA, sito web,
file da caricare)? Per ogni skill: elenco input obbligatori e opzionali.

B.8 — Se l'utente ha caricato file (PDF, Excel) nel KBot, questi vengono
**passati alla skill orchestratrice**? Come? Tramite il sistema RAG BM25
esistente o tramite parsing strutturato per tipologia?

### C. MCP server interno (Uso A — coerenza)

C.1 — Quali **fonti dati dinamiche** prevedete di esporre via MCP interno
(bandi, fornitori, tassi, visure, altro)? Per ognuna: aggiornamento previsto
(quotidiano/settimanale/mensile), origine del dato (manuale, API esterna,
scraping).

C.2 — L'MCP interno è **già implementato**, in lavorazione, o ancora da
progettare? Se in lavorazione: quando è pronto? Da chi viene mantenuto?

C.3 — Quale **protocollo di trasporto** tra KBot backend e MCP interno?
HTTP/REST? Stdio MCP locale? gRPC? Su che porta/path?

C.4 — Le risposte MCP arrivano al KBot **come dato strutturato iniettato nel
prompt**, o come tool result che Claude poi rielabora? Esempio pratico per il
caso bandi.

C.5 — Il dato di un MCP interno è **citato esplicitamente** nel report finale
("fonte: bando MIMIT del 12 marzo 2026"), o resta opaco? Per compliance/audit
serve traccia delle fonti?

C.6 — Cosa succede se l'MCP interno è **down** durante una generazione? Il
report fallisce? Si genera lo stesso con caveat? Si attende?

C.7 — Costi: ogni tool call MCP interno costa tempo (+200-500ms?). Su un
report che potenzialmente chiama 5-10 tool, il **tempo di generazione PDF**
può passare da 30s a 2-3 minuti. Accettabile?

### D. MCP server esterno (Uso B — partner)

D.1 — Esiste un **partner concreto** già individuato (consulente, agenzia,
studio professionale) che venderebbe Boost K2-AI tramite proprio agente? Nome,
contesto, tempistica realistica.

D.2 — Il partner usa Claude Desktop, custom GPT, propria app, o altro? Quale
client MCP-compatibile?

D.3 — Quale **modello commerciale partner**: fee fissa per lead, revenue
share, white-label totale, altro?

D.4 — Servono **versioni differenziate** del catalogo per partner (prezzi
diversi, prodotti hide)? Schema multi-tenant del catalogo?

### E. Wallet crediti e abbonamenti

E.1 — Sono già stati **testati con clienti** i piani Pro 49€/mese e Business
149€/mese, o sono solo ipotetici? Esiste interesse documentato?

E.2 — Cosa **include** ogni piano oltre ai crediti (es. supporto prioritario,
nuove skill in anteprima, sessioni con consulente)? Definire il valore non
monetario.

E.3 — Il **prezzo dei crediti 1:1 € è netto IVA o lordo**? PMI italiane
ragionano IVA esclusa per B2B — chiarire come si presenta in fattura.

E.4 — Il wallet **dà diritto a sconto sui Boost**, o si applica solo alle
tappe singole? Definire perimetro applicabilità.

E.5 — Decadenza 12 mesi: **decadenza totale** del saldo o solo dei crediti
non utilizzati nell'ultima ricarica? Reminder email a 11 mesi?

E.6 — **Refund policy**: cosa succede se cliente disdice abbonamento? Crediti
residui sono usabili per X giorni? Vengono persi? Rimborsati?

E.7 — Crediti regalati/promozionali si comportano come quelli pagati? Possono
essere scambiati o solo spesi?

### F. Mapping sito ↔ KBot (scenario C)

F.1 — Tutti i 20 pillar P01-P20 hanno un Boost destinazione **già definito** o
solo alcuni? Per ognuno: completare la tabella `mapping_tag_to_servizi`.

F.2 — Un pillar SEO può puntare a **più Boost** alternativi (es. P09 →
ControlBoost o AdvisorBoost a seconda del cliente)? Come decide il KBot?

F.3 — Il blog-bot continua a pubblicare articoli pillar. Gli articoli devono
**linkare al KBot** con tag pre-compilato? In quale punto dell'articolo
(footer, callout intermedio, intro)?

F.4 — Sito vetrina cita prezzi del modello vecchio (HOST/WEB/STUDIO)? Vanno
rimossi/aggiornati per evitare incoerenza col modello nuovo, o coesistono?

F.5 — Le pagine `/suite-ai/*.html` con SEO già attivo: cambia la copy interna
per allinearsi al modello Boost? Quando? Chi?

### G. Architettura tecnica e interfaccia col KBot

G.1 — Schema **definitivo** di `catalog.json` v1: confermare i campi del
draft in §1.1 del piano. Aggiungere/togliere campi se necessario. Indicare
**owner** del file (chi può modificare via PR).

G.2 — Catalogo viene mantenuto nel repo KBot (`kai-website/kbot/backend/app/data/`)
o in un repo separato? Se separato, come si **sincronizza**?

G.3 — Versioning catalogo: ogni modifica catalog.json è una **release** (semver)?
KBot legge sempre l'ultima o si può fissare la versione per riproducibilità?

G.4 — System prompt del KBot post-refactor sarà **molto più lungo** (carica
skill orchestratrice + references + tag context + tool definitions): stima
caratteri/token attesi? Resta sotto i limiti Haiku/Sonnet?

G.5 — Tool use Claude per "navigare orchestratori": quali tool esatti? Schema
formale dei tool definitions. Come si gestiscono **errori di chiamata** (tool
non esiste, parametro sbagliato)?

G.6 — Sessione `kbot_sessions.collected_data` cresce con: tag, servizio_attivo,
percorso_id, tappe_completate, file caricati, URL, RAG chunks. **Limit di
dimensione** JSONB? Strategia di compaction quando si sfora?

G.7 — Il KBot deve **gestire un cliente che ha più percorsi attivi**
contemporaneamente (es. AdvisorBoost + ControlBoost in parallelo)? Una sola
sessione per cliente o una per percorso?

### H. Economics e costi

H.1 — Budget LLM mensile target: 65€/mese (CLAUDE.md §3) è vincolante anche
post-espansione? Se sì, quante sessioni/mese sostiene? Se no, qual è il nuovo
budget?

H.2 — **Costo per sessione** atteso per ogni tipologia: Check Express, tappa
intermedia, Boost completo. Calcolo dei token attesi (input + output) e prezzo
modello.

H.3 — **Margine atteso** per Boost: prezzo - costi LLM - costi infrastruttura
- eventuale lavoro umano. Per AdvisorBoost a 2.499€ deve coprire (a) 5
generazioni PDF Sonnet, (b) eventuali ore di revisione umana, (c) overhead
Stripe/Resend/Supabase, (d) margine target.

H.4 — Se il Boost richiede **revisione umana** prima di essere consegnato
(per evitare errori), quante ore stimate? Chi? Costo orario interno?

H.5 — Stripe fee: 1.4% + 0.25€ per transazione UE. Su un Boost 2.499€ = ~35€
fee. Inclusi nel prezzo o margine assorbe?

### I. Roadmap, responsabilità, deploy

I.1 — Chi **esegue** ogni fase del piano? Sviluppatore unico Luca? Team
esteso? Freelance? Indicare per ogni fase chi è on-call.

I.2 — **Cadenza di review** del piano: settimanale? Bisettimanale? Dopo ogni
gate? Chi convoca?

I.3 — Deploy: oggi Railway per backend FastAPI + Next.js frontend (CLAUDE.md
mem `feedback_railway_deploy.md`). Resta così per tutte le fasi? Servono
servizi extra (es. MCP server interno) → nuovi container Railway?

I.4 — **Branch strategy**: per ogni fase, branch dedicato `feat/kbot-v2-fase-N`
o uno per ogni sub-task? PR review da chi?

I.5 — Gate quantitativi (vedi tabella in §0): chi **misura** i numeri? Quando?
Con quale strumento (query SQL, dashboard, Notion)?

I.6 — Cosa succede se un gate **non è raggiunto**? Si stoppa il piano? Si
modifica il prodotto? Si itera sulla fase precedente?

### J. Edge case e governance prodotto

J.1 — Utente paga una tappa ma il deliverable **fallisce** la generazione
(crash Sonnet, timeout, errore parsing). Cosa vede l'utente? Refund automatico?
Retry? Notifica a Luca?

J.2 — Utente **abbandona** un percorso (paga tappa 1, mai più tappa 2). Dopo
quanto tempo si considera abbandonato? Email di reminder? Si scontano le
tappe rimanenti per recuperarlo?

J.3 — Utente compra Boost **ma poi vuole disdire** prima della completa
erogazione: refund parziale? Politica scritta?

J.4 — Versioning prezzi: se domani aumenti AdvisorBoost da 2.499€ a 2.999€,
i clienti che hanno **già acquistato tappa 1 al vecchio prezzo** completano
le altre 4 al vecchio o nuovo prezzo? Politica grandfather?

J.5 — Cliente che ha già pagato Check Express 19€ e poi entra in AdvisorBoost
(tappa 1 = 299€): si **sconta** automaticamente il Check già fatto? Oppure
tappa 1 include il Check? Esplicitare.

J.6 — Modelli LLM cambiano (Haiku 4.5 → 5, Sonnet 4.5 → 5): chi decide
quando aggiornare? Si misurano differenze in regression test prima del cutover?

J.7 — **Compliance GDPR**: i deliverable contengono dati del cliente
(P.IVA, bilanci, dati interni). Sono cifrati a riposo in Supabase Storage?
Retention policy? Diritto all'oblio?

### K. Allineamento organizzativo

K.1 — Il "decisore" citato nel doc di allineamento è la stessa persona di
Luca (owner repo)? Se persone diverse, **come si risolvono conflitti** di
direzione (es. Luca dice no a una scelta del decisore)?

K.2 — Il "team backend ecosistema" che mantiene catalogo + orchestratori +
MCP è **lo stesso** team che mantiene il KBot, o team distinti? Se distinti:
come si coordinano i deploy? Chi è on-call se qualcosa si rompe in produzione?

K.3 — Esiste un **canale di comunicazione** strutturato tra i due lati (Slack
channel, Notion DB, daily sync)? Se no, va creato prima di iniziare.

K.4 — Il blog-bot continua a pubblicare i 20 pillar P01-P20. Cosa succede se
il **modello SEO** del sito un giorno verrà rivisto (es. consolidamento da 20
a 10 pillar)? Il mapping `tag_pillar_sito` nel catalogo va aggiornato — chi
lo fa?

K.5 — Misurazione successo del modello complessivo: a **6 mesi** dal deploy
Fase 6, quali KPI dimostrano che il modello funziona? Numero clienti? Margine?
Retention? Definire 3-5 KPI prioritari.

### L. Validazione e segnali di stop

L.1 — Se dopo Fase 3 (upsell statico) **zero clienti** convertono su Boost in
60 giorni, il piano si ferma o continua? Quale soglia di "zero" si accetta?

L.2 — Quali sono i **segnali precoci** che il modello non sta funzionando, e a
chi vanno comunicati per innescare un cambio di rotta? Lista 5 segnali
quantificabili (es. NPS basso post-Check, drop-off chat >50% al messaggio 3,
costo CAC > LTV, ecc.).

L.3 — Se i numeri **superano** le aspettative (es. 50 Boost/mese a fronte di
2-3 attesi), c'è una strategia di scale-up? Necessità di hire? Riserve infra?

L.4 — Il decisore accetta che, se i gate **non vengono raggiunti**, le fasi
successive non partono (anche se i deliverable sarebbero "interessanti")? Confermare
per iscritto.

---

## In una frase

8 fasi sequenziali a gate quantitativi, riuso totale del backend FastAPI esistente,
catalogo esternalizzato in `catalog.json`, mapping `P01-P20 SEO ↔ servizi nuovi`
che lascia intatto il funnel del sito e blog; le prime 6 fasi costruiscono e
validano il modello commerciale Check → Boost → percorsi senza wallet/abbonamenti/
MCP esterno, che entrano in scena solo se i numeri lo giustificano; MCP interno
per coerenza report è opzionale per dominio in Fase 6, MCP esterno multi-client
è Fase 8 gated.

---

*Piano operativo. Aggiornare questo file in coda a ogni fase completata con i
numeri reali e le decisioni emerse.*
