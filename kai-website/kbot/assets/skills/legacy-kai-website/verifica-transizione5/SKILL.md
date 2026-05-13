---
name: verifica-transizione5
description: >-
  Verifica ammissibilità e calcolo beneficio Transizione 5.0 (D.L. 19/2024):
  checklist requisiti GSE, calcolo risparmio energetico 3/6/10%, aliquote per
  fascia di investimento, cumulabilità, timeline comunicazioni obbligatorie.
---

# Verifica Requisiti Transizione 5.0

## Checklist ammissibilità — 10 domande

Rispondere SÌ a tutte per accedere al credito:

1. **Il bene è strumentale?** Usato in attività produttiva dell'impresa, non rivenduto
2. **È nuovo?** Beni usati esclusi
3. **È interconnesso?** Integrato con sistemi aziendali (MES, ERP, SCADA) via rete
4. **Genera risparmio energetico?** Riduzione ≥ 3% consumi del processo (o ≥ 3% struttura)
5. **L'impresa è residente in Italia?** Sede o stabile organizzazione in IT
6. **L'impresa non è in difficoltà?** No procedure concorsuali, bilancio in ordine
7. **Comunicazione preventiva al GSE inviata PRIMA dell'ordine?** Obbligatoria
8. **C'è un EGE o Energy Auditor per la perizia?** Certificato UNI CEI 11339
9. **L'investimento avviene entro 31/12/2025?** (Data fattura + pagamento + interconnessione)
10. **I costi non sono già coperti da altri contributi sugli stessi beni?** No doppio finanziamento

## Calcolo risparmio energetico — metodo

### Risparmio processo produttivo (obbligatorio, soglia minima)

```
Risparmio% = (Consumo_prima - Consumo_dopo) / Consumo_prima × 100

Consumo_prima = kWh/unità prodotta PRIMA del nuovo bene (baseline 3 mesi)
Consumo_dopo  = kWh/unità prodotta CON il nuovo bene (misurato post-installazione)

Metodologia: IPMVP Option A o B (misura diretta preferita per GSE)
```

**Soglie e aliquote processo**:
- ≥ 3% e < 6%: aliquota base (35% fino 2,5M€)
- ≥ 6% e < 10%: aliquota media (40% fino 2,5M€)
- ≥ 10%: aliquota massima (45% fino 2,5M€)

### Risparmio struttura produttiva (opzionale, per aliquote alte)

Riduzione consumi dell'intera azienda (non solo del processo):
```
Risparmio struttura% = (Tot_kWh_anno_prima - Tot_kWh_anno_dopo) / Tot_kWh_anno_prima × 100
```
Misurato su fatture energia dell'anno precedente vs anno post-investimento.

## Aliquote complete per fascia

| Fascia investimento | Risparmio 3-6% | Risparmio 6-10% | Risparmio >10% |
|---------------------|----------------|-----------------|----------------|
| 0 — 2.500.000€      | **35%**        | **40%**         | **45%**        |
| 2.500.001 — 10M€    | **15%**        | **20%**         | **25%**        |
| 10.000.001 — 50M€   | **5%**         | **10%**         | **15%**        |
| > 50M€              | Non agevolato  | Non agevolato   | Non agevolato  |

## Esempio calcolo

```
Investimento macchinario: 1.200.000€
Risparmio processo: 7,5% → fascia 6-10%
Aliquota applicabile: 40% (fascia fino 2,5M€)

Credito d'imposta = 1.200.000 × 40% = 480.000€

Fruizione: compensazione F24 in 3 rate
Rate: 160.000€ nel 2025, 160.000€ nel 2026, 160.000€ nel 2027
```

## Timeline obbligatoria GSE

```
FASE 1 — PRENOTAZIONE (prima dell'ordine/contratto)
  → Comunicazione preventiva a GSE su portale dedicato
  → Allega: descrizione progetto, investimento previsto, perizia EX-ANTE EGE

FASE 2 — INVESTIMENTO (entro 31/12/2025)
  → Ordina e paga il bene
  → Installa e interconnetti
  → Misura consumi prima/dopo

FASE 3 — CONSUNTIVO (entro 28/02/2026)
  → Comunicazione ex-post a GSE
  → Allega: fatture, perizia EX-POST, attestazione interconnessione
  → GSE valida → conferma credito → fruizione F24
```

**Attenzione**: se risparmio ex-post risulta inferiore alla soglia dichiarata ex-ante → credito ridotto o annullato. Mai gonfiare le stime.

## Beni FV e BESS

Impianti fotovoltaici e sistemi di accumulo sono ammissibili SE:
- Abbinati a un bene strumentale 5.0 (non stand-alone)
- Per autoconsumo dell'impresa (non cessione in rete)
- Potenza proporzionata al fabbisogno del processo agevolato

Aliquote FV/BESS: stesse del bene principale a cui sono abbinati.

## Cumulabilità

| Con | Ammesso | Nota |
|-----|---------|------|
| Nuova Sabatini | ✓ | Su stessi beni: verifica plafond |
| Credito R&S | ✓ | Costi distinti |
| PNRR altri bandi | Verifica | Rispettare massimale aiuto |
| Transizione 4.0 | ✗ | Stesso bene non ottiene entrambi |
| Conto Termico | Verifica | Evitare overlap costi energetici |
