# Audit architetturale K2-AI — luglio 2026

Audit richiesto da Luca (spec "principal engineer", 15 lug 2026) su tutta la filiera
chat → diagnosi → routing → generazione → PDF/Excel. Verificato sul codice a `origin/main`
(commit `8cbf4bd`), non sulla memoria degli stress test.

## 1. Pipeline reale end-to-end (com'è oggi)

```
Utente → chat Next.js (/app) → FastAPI kbot (container website)
  message.py: prompt consulente (signals SSOT, DIAGNOSI_STATO, stop rule, quality gate)
  → CONSULENZA_SUMMARY (trigger) → routing keyword catalog.suggest_boost → boost_suggerito
  → /deliverables/auto:
      readiness deterministico (identità = unico gate; altri mancanti → PARTIAL)
      autofill LLM (Haiku): conversazione → dict inputs del form blueprint   ← UNICO canale dati
      alignment checker LLM (catalog-aware, 409 reroute)
  → POST 8e /v1/deliverables {service_id, inputs, auth_level}                ← niente transcript/summary
8e (Railway separato, LLM locale gpt-oss via tunnel):
  route → gate identità → resolve(facts det.) → generazione sezioni LLM
  → apply_deterministic_bindings (finance/control/tax/quant… per-skill)
  → senior critic → scrub placeholder/legal → validazione schema → gate grounding → render PDF
Excel: kbot /deliverables/{job}/xlsx ← JSON 8e → xlsx_renderer
```

## 2. Bug della spec: stato reale

### Già risolti (con commit e test — non rifare)
| Classe | Fix | Dove |
|---|---|---|
| A. Troppe domande | Stop rule 4 condizioni + EVI + cap deterministico `KBOT_MAX_INTAKE_TURNS` | `44ecfbd`, quality_gate |
| B. Si ferma troppo presto | Stop rule bilanciata + dichiarazione insufficienza | `44ecfbd` |
| C. Dichiara ma non genera | regex inline + `_ensure_summary_block` + auto-generate | `8fd4ca0`, `59bb7d9`, `e28a285` |
| D. Genera→torna a domande | cap anti-oscillazione + gate EVI | `6d6dfc9` |
| E. Richiede dati già dati | DIAGNOSI_STATO persistito e re-iniettato (memoria di lavoro) | `e9e55bc` |
| F. Utente-consulente | prompt: fatti osservabili, mai "che report vuoi" | `8a21be7` |
| G. Routing M&A | keyword IT + alignment checker catalog-aware con reroute | `ded5704`, `8a21be7` |
| I. Campi template bloccanti | `_TEMPLATE_FIELD_IDS` = domanda leggera; mancante → PARTIAL | `8a21be7` |
| P. Report vuoti | 5 sezioni senior REQUIRED + senior critic (Finance+Strategy) | `5c5fecb` |
| — | 16 test regressione intake + 3 shape-tests 8e | `e9e55bc`, `8cbf4bd` |

### Aperti — verificati oggi sul codice (per severità)

**S1 — Il report non vede la conversazione (classe K).** All'8e arriva SOLO il dict
`inputs` dell'autofill (`engine.py:60-64`): niente transcript, summary, diagnosi. Tutto
ciò che il cliente ha detto ma non entra nei campi del form è perso per costruzione
(multi-filiale: margini per sede forniti in chat, report che non li usa).

**S2 — Numeri utente riformulati da un LLM senza cross-check (classe M).** L'autofill è
Haiku (`autofill.py:202-212`): la copia di "EBITDA 720.000" passa per il modello e nessuno
verifica che il numero estratto esista nel testo chat (720k→230k).

**S3 — Numeri hard-financial inventati: etichettati e consegnati (classi L/M/S).**
`pipeline.py:885-892`: se i block del gate sono tutti value-codes, il job NON rifiuta —
etichetta "(SCENARIO ASSUNTIVO)" e spedisce. Vale anche per €/EBITDA/ROI fabbricati su
boost finanziari. Contraddice "MEGLIO NESSUN NUMERO CHE UN NUMERO SBAGLIATO".

**S4 — Placeholder deterministici non bloccati (classe L).** Sezione degradata →
`_det_sample`: `"esempio"` (`llm.py:571`), `"K2AI-2026"` (`:604`), numerico default `1`
(`:646` — il "KPI = 1" visto nei test), pad `"K2-AI"` (`:1067`). Nessuno è nella blocklist
placeholder (`grounding.py:29-41`) → arrivano nel PDF.

**S5 — Mancante → 0 in punti sparsi (classe L).** `tax.py:74,79,82` (imponibile assente →
imposta 0), `quant.py:136` (debiti_finanziari→0 = leva sottostimata), `llm.py:1020`
(stringa non parsabile → 0). I moduli nuovi (control/host/calc) fanno già missing→None.

**S6 — Routing senza `report_stage` né multidominio (classi G/J).** Keyword-only: il caso
multi-filiale (assessment di controllo di gestione) va sul cruscotto operativo MENSILE —
dominio quasi giusto, stage completamente sbagliato. Nessun lead/supporting domain.

**S7 — Allegati fissi per blueprint (classe Q).** Triage/review/due-diligence legale =
stesso blueprint = stesso bundle: l'M&A si porta a casa i template del legale generico.

**S8 — Owner senza matrice ruolo→azione (classe R).** L'owner delle azioni lo decide la
prosa LLM; nessun check `can_recipient_execute`. (Mitigato solo al routing dal checker.)

**S9 — Benchmark**: soglie hardcoded senza fonte dichiarata (`finance.py:440-450`) e
benchmark LLM solo warn (`grounding.py:164-170`). Score: LegalBoost score è LLM
(range-validato, non spiegato); i 3 check senza binder hanno KPI interamente LLM.

## 3. Primi 5 interventi (impatto/rischio)

1. **Verità numerica**: (a) cross-check deterministico autofill→testo chat, numero non
   trovato → campo scartato (meglio PARTIAL che sbagliato); (b) hard-financial inventati →
   N/D + limitazione, non etichetta+consegna; (c) missing→0 eliminati; (d) placeholder
   det-sample → "N/D" espliciti + blocklist.
2. **Case facts pass-through**: summary+diagnosi della chat → payload 8e → iniettati nei
   prompt di sezione ("usa SOLO questi fatti"). Chiude S1, il singolo difetto più grave.
3. **Pre-export validator** deterministico (severity WARNING/BLOCKING/FATAL): placeholder
   estesi, zero-sospetto, range %, timeline corrotte (en-dash), score senza formula.
4. **Routing tipizzato**: `report_stage` + subject/recipient + lead/supporting domains nel
   verdetto del checker; multidominio come workstream nel report, non blueprint nuovo.
5. **Matrice owner + bundle per scenario** (S7/S8): allowlist ruolo→categoria-azione;
   variante allegati M&A per il blueprint legale.

## 4. Piano di migrazione (senza fermare la produzione)

- Ogni intervento dietro flag env, default ON ma fail-open (pattern già in uso:
  `KBOT_*`, `K2A_8E_*`): spegnibile senza deploy.
- Ordine: 1→2 (stessa ondata, entrambi additivi), poi 3, poi 4-5.
- kbot = container website (auto-deploy da main, ~5-8 min di 502); 8e = `railway up`
  manuale. Test: suite intake (16) + shape (3) + nuovi test per ogni fix.
- Nessun cambio di schema DB, nessun cambio API breaking: `case_facts` è campo opzionale.
