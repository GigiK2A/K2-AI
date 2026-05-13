# Benchmark PMI integrato — AdvisorBoost

Tabelle di riferimento per confronto PMI italiane 5-50 dipendenti. Servono come fallback locale quando la skill `benchmark-italia-business` non dispone del dato puntuale, e come sintesi integrata per l'executive summary di AdvisorBoost.

## Fasce dimensionali di riferimento

| Fascia | Fatturato | Dipendenti | Esempi tipici |
|---|---|---|---|
| Micro | < 500k | 1-4 | Studio professionale solo-titolare, artigiano |
| Piccola bassa | 500k - 2M | 5-9 | PMI familiare, piccolo studio ingegneria |
| Piccola alta | 2M - 10M | 10-24 | PMI manifatturiera regionale |
| Media | 10M - 50M | 25-50 | PMI manifatturiera export, consorzio servizi |

AdvisorBoost si posiziona sulle fasce Piccola bassa, Piccola alta e (in alcuni casi) Micro evoluta e Media bassa.

## Margini mediani per macro-settore

### Manifattura (ATECO C)
| Indicatore | Piccola bassa | Piccola alta | Media |
|---|---|---|---|
| EBITDA margin | 8-12% | 10-15% | 12-18% |
| ROI | 6-10% | 8-14% | 10-16% |
| ROE | 8-14% | 10-18% | 12-22% |
| PFN/EBITDA | 2-4x | 2-3.5x | 1.5-3x |
| D/E | 0.8-1.5 | 0.6-1.2 | 0.5-1.0 |
| CCC (gg) | 80-120 | 70-100 | 60-90 |
| Rotazione attivo | 0.9-1.3 | 1.0-1.5 | 1.1-1.6 |

### Servizi B2B professionali (ATECO M)
| Indicatore | Piccola bassa | Piccola alta | Media |
|---|---|---|---|
| EBITDA margin | 15-25% | 18-28% | 20-30% |
| ROI | 12-20% | 15-22% | 18-25% |
| ROE | 18-28% | 22-35% | 25-40% |
| PFN/EBITDA | 0-2x | 0.5-2.5x | 0.5-2.5x |
| D/E | 0.2-0.8 | 0.3-1.0 | 0.3-1.0 |
| CCC (gg) | 40-80 | 40-70 | 35-60 |
| Ricavi per dipendente | 80-120k | 100-150k | 120-180k |

### Commercio all'ingrosso (ATECO G46)
| Indicatore | Piccola bassa | Piccola alta | Media |
|---|---|---|---|
| EBITDA margin | 4-7% | 5-9% | 6-10% |
| ROI | 8-14% | 10-16% | 12-18% |
| PFN/EBITDA | 2-5x | 2-4x | 1.5-3.5x |
| D/E | 1.0-2.0 | 0.8-1.8 | 0.7-1.5 |
| CCC (gg) | 60-100 | 50-90 | 40-80 |
| Rotazione magazzino | 4-8x | 5-10x | 6-12x |

### Retail specializzato (ATECO G47)
| Indicatore | Piccola bassa | Piccola alta | Media |
|---|---|---|---|
| EBITDA margin | 6-10% | 7-12% | 8-13% |
| ROI | 10-16% | 12-18% | 14-20% |
| Giorni magazzino | 60-120 | 50-100 | 40-80 |
| Scontrino medio (EUR) | dipende | dipende | dipende |
| Vendite per m² | 1.500-3.000 | 2.000-4.000 | 2.500-5.000 |

### Costruzioni (ATECO F)
| Indicatore | Piccola bassa | Piccola alta | Media |
|---|---|---|---|
| EBITDA margin | 5-9% | 6-11% | 7-12% |
| ROI | 6-12% | 8-14% | 10-16% |
| PFN/EBITDA | 2-5x | 2-4x | 1.5-3.5x |
| CCC (gg) | 100-180 | 90-150 | 80-130 |

### TLC e IT (ATECO J61-J62)
| Indicatore | Piccola bassa | Piccola alta | Media |
|---|---|---|---|
| EBITDA margin | 12-20% | 15-25% | 18-28% |
| ROI | 14-22% | 16-25% | 20-30% |
| Ricavi per dipendente | 100-150k | 120-180k | 150-220k |
| CCC (gg) | 50-90 | 40-80 | 30-70 |

### Ricettivo e ristorazione (ATECO I)
| Indicatore | Piccola bassa | Piccola alta | Media |
|---|---|---|---|
| EBITDA margin | 10-20% | 12-22% | 15-25% |
| ROI | 4-10% | 6-12% | 8-14% |
| D/E | 1.5-3.0 | 1.2-2.5 | 1.0-2.0 |
| Revpar / Fatturato per coperto | specifici | specifici | specifici |

Per ricettivo rimandare alle tabelle specifiche di `check-host-express/references/scoring-model-host.md`.

## Multipli EV/EBITDA per settore

PMI italiane non quotate, prezzi osservati in operazioni M&A 2023-2025.

| Settore | EV/EBITDA basso | Mediana | Alto |
|---|---|---|---|
| Manifattura meccanica | 4x | 5-6x | 7-8x |
| Food processing | 5x | 6-7x | 8-9x |
| Software B2B SaaS | 6x | 8-10x | 12-15x |
| Agenzie marketing / consulenza | 3x | 4-5x | 6-7x |
| Studi professionali tecnici (ingegneria) | 3x | 4-5x | 5-6x |
| E-commerce con brand proprio | 5x | 7-8x | 10-12x |
| Costruzioni | 3x | 4-5x | 5-6x |
| TLC infrastrutture | 6x | 7-8x | 9-10x |
| Ricettivo extra-alberghiero | 5x | 6-8x | 9-11x |
| Hotel 4-5 stelle turismo | 8x | 10-12x | 14-16x |

Ai multipli applicare sconto di liquidita 20-30% per PMI non quotate e dipendenza da titolare.

## WACC tipico PMI italiane

Formula: `WACC = E/(E+D) × Ke + D/(E+D) × Kd × (1-t)`

Parametri tipici 2025:
- **Ke (costo equity)** = Rf + Beta × ERP + Size premium
  - Rf (BTP 10Y): 3.5-4.0%
  - ERP (equity risk premium Italia): 6.0-7.0%
  - Beta settoriale Damodaran rilevered
  - Size premium PMI: +2-4%
  - **Range pratico Ke PMI: 10-14%**

- **Kd (costo debito)**: tassi bancari medi PMI 4.5-6.5% 2025
- **t (tax rate)**: 24% IRES + 3.9% IRAP = 27.9%
- **WACC range**: 8-11% per PMI stabili, 11-14% per PMI rischiose o growth

Semplificazione operativa: WACC 10% base, +2% se PMI in crisi, -1% se PMI con contratti pluriennali e basso churn.

## CAGR tipici 3-5 anni

| Settore | CAGR ricavi base | CAGR ricavi buoni |
|---|---|---|
| Manifattura classica | 2-4% | 5-8% |
| Food processing | 3-5% | 6-10% |
| Software B2B | 10-20% | 25-40% |
| Servizi professionali | 4-7% | 8-15% |
| E-commerce | 8-15% | 20-35% |
| Costruzioni (finestra PNRR) | 5-10% | 10-20% |
| TLC infra | 3-6% | 6-12% |
| Retail specializzato | 2-4% | 5-8% |

Anomalie 2025-2027:
- **PNRR effect**: costruzioni, riqualificazione energetica, ICT PA: +3-5pp extra.
- **Post-Superbonus hangover**: ristrutturazioni residenziali -10-20% 2024-2026.
- **AI shift**: servizi professionali con componente high-value-add in crescita, low-value-add sotto pressione.

## KPI operativi per tipologia

### Studio professionale (ingegneria, architettura, commercialisti)
- Ore fatturate / ore totali: target > 65%
- Tariffa media oraria vs mediana Ordine
- Ricavi / dipendente: > 100k benchmark
- % clienti ricorrenti (> 2 anni): > 60%
- Backlog commesse: > 6 mesi coperti

### E-commerce / D2C
- Conversion rate: 1.5-3% sito, 5-8% email
- AOV (Average Order Value): settore-dipendente
- Repeat rate: > 25% sano
- LTV/CAC: > 3x target
- Gross margin: > 50% per brand proprio

### Manifattura B2B
- OEE (Overall Equipment Effectiveness): > 70%
- Tasso difetti: < 1%
- Giorni consegna medio vs promesso
- Concentrazione primo cliente: < 30% (se > 50% alert rischio)
- Export %: benchmark settoriale

### Ricettivo
Vedi `check-host-express/references/scoring-model-host.md` per dettagli completi.

### Servizi B2B ricorrenti (SaaS, servizi gestiti)
- MRR / ARR
- Churn annuo: < 10% sano, < 5% ottimo
- NRR (Net Revenue Retention): > 100% sano, > 115% eccellente
- CAC payback: < 18 mesi
- Rule of 40 (growth + margine): > 40%

## Soglie alert rapide

Segnalare come **rosso** nell'executive se:
- EBITDA margin < 50% della mediana di settore
- PFN/EBITDA > mediana + 50%
- ROE < 0 (perdita)
- CCC > mediana settore × 1.5
- Concentrazione cliente top > 40%
- Ricavi per dipendente < 70% mediana di settore
- CAGR 3 anni < 0% in settore in crescita

Segnalare come **giallo**:
- EBITDA margin 50-80% mediana
- CCC > mediana ma < 1.5x
- Concentrazione cliente 30-40%
- Ricavi per dipendente 70-90% mediana

## Aggiornamento tabelle

Questi benchmark vanno rivisti ogni 12 mesi con fonti:
- Atoka / Cerved Market Outlook
- Banca d'Italia — Bilanci aziende non finanziarie
- Mediobanca — R&S dati cumulativi
- Eurostat — Structural business statistics
- AIDA Bureau van Dijk (campioni ATECO)
- ISTAT — Statistiche strutturali imprese

Versione: 2025-Q4.
