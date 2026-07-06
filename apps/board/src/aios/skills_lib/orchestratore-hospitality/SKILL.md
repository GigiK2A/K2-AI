---
name: orchestratore-hospitality
version: 0.1.0
description: >-
  Suite K2-AI Hospitality & Revenue Management strutture ricettive italiane (149-899 EUR + success
  fee 15% delta RevPAR). ATTIVA SEMPRE QUESTO ORCHESTRATORE K2-AI per: revenue management, pricing
  dinamico, RevPAR, ADR, occupancy, RevPAR index, fair share, market share, OTA dependency,
  Booking Expedia Airbnb, parita tariffaria, calendario prezzi, yield management, agriturismo,
  B&B, boutique hotel, glamping, villa di lusso, locazione turistica, dehors, P&L hospitality,
  GOPPAR, costi camera, food cost, beverage cost, HostBoost, check ricettivo, score 0-100,
  OTA disintermediation, direct booking, customer journey turistico, recensioni TripAdvisor.
  Workflow K2-AI: profilazione struttura (camere/villa/agriturismo/glamping), benchmark zona
  (RevPAR mediano area), score 6 KPI ricettivi, analisi OTA dependency e fair share, pricing
  dinamico stagionale + eventi locali + lead time, P&L hospitality, customer journey turistico
  (storytelling esperienziale), bridge agevolazioni turismo (Bandi regionali Bonus turismo).
  Differenziatori unici: focus PMI ricettive italiane (no catene), success fee model legato a
  delta RevPAR misurato, bridge marketing esperienziale (settori-creativi: experience goods).
allowed-tools:
  - WebFetch
  - WebSearch
  - Read
  - Write
  - Bash
---

# k2ai-hospitality — Orchestratore Hospitality & Revenue Management

Per strutture ricettive italiane 5-30 camere. Coordina 6 skill per produrre diagnosi RevPAR + piano pricing dinamico misurabile.

## Posizionamento competitivo

| Concorrente | Cosa fa | Cosa NON fa |
|---|---|---|
| Channel manager (BookingSuite, SiteMinder) | Distribuzione tariffe | Strategia, benchmark, narrativa cliente |
| Revenue manager freelance | 800-3.000 EUR/mese | Diagnosi rapida + pagamento basato su risultato |
| Software PMS (Octorate, Beddy) | Operations | Strategia OTA, marketing esperienziale |

**Tagline:** "Il revenue manager che ti pago solo se aumento il RevPAR. Per agriturismi, B&B e boutique hotel italiani 5-30 camere."

## Skill orchestrate (P20)

- `flusso-hostboost-ricettive` (orchestratore base)
- `check-host-express` (lead magnet)
- `property-management-revenue` (cuore: RevPAR, ADR, OTA, P&L)
- `marketing-strategico` (STP, yield)
- `marketing-settori-creativi` (experience goods, brand community)
- `crm-customer-experience` (loyalty, NPS, win-back)

**Base teorica K2-AI**:
- Bocconi: `marketing-bocconi-trust` (trust e community), `marketing-bemacs-quant` (RFM, CLV)
- Psy: `psy-decisioni` (cognitive biases sul pricing dinamico — host avversi a "scendere"), `psy-comportamentale` (apprendimento ospite ai prezzi)
- Math: `probabilita` (forecast occupancy), `statistica-applicata-bocconi` (test A/B su tariffe)

## Workflow (7 step)

1. **Profilazione**: tipo (agri/B&B/boutique/villa/glamping), n. camere, zona, stagionalita
2. **Benchmark zona**: RevPAR mediano area da `WebSearch` (STR, AirDNA pubblici) + competitor mapping
3. **Score 6 KPI**: occupancy, ADR, RevPAR, RevPAR index, OTA dependency %, direct booking %
4. **Analisi OTA**: parita tariffaria, fee Booking/Expedia/Airbnb, fair share vs market share
5. **Pricing dinamico**: stagionale + eventi locali + lead time + giorni settimana, simulazione 3 scenari
6. **P&L hospitality**: GOPPAR target, food cost, costi camera, payback su investimenti
7. **Bridge K2-AI + esperienziale**: customer journey turistico storytelling (`marketing-settori-creativi`), bridge `k2ai-agevolazioni` (Bandi regionali turismo, Bonus ristrutturazioni ricettive)

## Domande standard per pacchetto

### Pagellino Hospitality Express (49 EUR)
1. Tipo struttura + n. camere
2. Comune + provincia
3. Fatturato 2024 totale
4. Mesi di apertura nell'anno
5. Tariffa media bassa/media/alta stagione
6. % prenotazioni via OTA vs dirette

### HostBoost Standard (449 EUR)
1-6 +
7. Storico mensile occupancy + ADR ultimi 12 mesi (XLSX o tabella)
8. Top 3 OTA usate + commissioni %
9. PMS attuale (Octorate, Beddy, ecc.)
10. Recensioni Google/Booking: rating + numero
11. Foto struttura (5-10) per check brand
12. Eventi locali noti che impattano occupancy
13. Investimenti pianificati prossimi 12 mesi

### Pro 899 EUR + 15% success fee
1-13 +
14. Accesso API channel manager (per ricalibrazione live)
15. Dati clienti: profilo target attuale + provenienza
16. Revenue per segmento (BLT/ Leisure/MICE/altro)
17. Costi diretti per camera (pulizia, lavanderia, energia, OTA fee)

## JSON output schema

```json
{
  "tier": "express|standard|pro",
  "struttura": {"tipo":"agriturismo|bb|boutique|villa|glamping","camere":0,"zona":""},
  "kpi_attuali": {"occupancy":0,"adr":0,"revpar":0,"revpar_index":0,"ota_dep":0,"direct":0},
  "benchmark_zona": {"revpar_mediano":0,"posizione":"top|medio|basso"},
  "score_globale": 0-100,
  "ota_analysis": {"fair_share":0,"market_share":0,"gap":""},
  "pricing_proposta": [{"periodo":"","adr_attuale":0,"adr_proposto":0,"delta_revpar_atteso":0}],
  "pl": {"goppar_attuale":0,"goppar_target":0,"interventi":[]},
  "customer_journey": {"narrativa":"","touchpoints":[]},
  "agevolazioni_turismo": [],
  "deliverable": {"docx":"","calendario_pricing_xlsx":"","narrativa":""}
}
```

## Tiering pricing

| Versione | Prezzo | Cosa include |
|---|---|---|
| Express | 49 EUR | Score 0-100 + 5 azioni rapide |
| HostBoost | 449 EUR | Diagnosi + pricing 12 mesi + P&L + bridge bandi |
| Pro | 899 EUR + 15% delta RevPAR | HostBoost + ricalibrazione mensile + accesso live + 2 call |

## Bridge K2-AI

- → `k2ai-agevolazioni` (Bandi regionali turismo, Bonus mobili 50% se rinnovo arredi)
- → `k2ai-marketing-seo` (SEO ricettivo + Local SEO Italia per direct booking)
- → `k2ai-edilizia-pmi` se ristrutturazione/ampliamento ricettivo
- ← chiamato da `k2ai-pmi-strategy` se settore ricettivo

## Test prompts

1. (forzato) "Usa k2ai-hospitality per agriturismo 8 camere in Toscana, fatturato 320k, OTA dep 75%"
2. (cliente reale) "Il mio B&B a Roma e' sempre pieno ad agosto ma vuoto a febbraio, cosa faccio?"
3. (cliente reale) "Booking mi mangia il 18%, voglio passare al diretto"
4. (cliente reale) "Voglio aprire un glamping in Sardegna, da dove parto?"
5. (A/B) "revenue management agriturismo italiano con OTA dependency 80%"

## Note implementative

- Per "agriturismo" verifica sempre cofiscale (Reg. CEE prevalenza attivita agricola se vuole regime fiscale agricolo)
- Pricing dinamico: il bias dell'host e' "non scendere mai sotto X" — quantifica costo opportunita di camera vuota
- OTA disintermediation: NON promettere "passi al 100% diretto" — irrealistico. Target realistico: dal 70-80% OTA al 50-60%
- Stagionalita italiana: 90% delle strutture extralberghiere ha 4-6 mesi di apertura. Inseriscilo nel forecast
