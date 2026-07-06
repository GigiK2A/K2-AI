---
name: property-management-revenue
description: >-
  Revenue management per strutture ricettive italiane (hotel, agriturismi, B&B,
  ville): RevPAR, ADR, occupancy, pricing dinamico, ottimizzazione OTA,
  P&L hospitality, KPI benchmark, strategie stagionali.
---

# Revenue Management — Strutture Ricettive

## KPI fondamentali hospitality

| KPI | Formula | Target Italia (hotel 3-4 stelle) |
|-----|---------|----------------------------------|
| **Occupancy** | Camere vendute / Camere disponibili | 65-75% annuo |
| **ADR** (Average Daily Rate) | Ricavi camere / Camere vendute | Dipende da categoria/location |
| **RevPAR** | Occupancy × ADR (o Ricavi / Camere disponibili) | ADR × occupancy |
| **TRevPAR** | Ricavi totali (camere + F&B + servizi) / Camere disponibili | RevPAR × 1.3-1.6 |
| **GOPPAR** | GOP (gross operating profit) / Camere disponibili | 30-40% di RevPAR |

## Pricing dinamico — principi base

```
BASSA STAGIONE           ALTA STAGIONE
(occupancy < 40%)        (occupancy > 70%)

Price floor              Price ceiling
= costo variabile + min  = massimo mercato
  margine operativo        sopporta

Regola: aumenta il prezzo quando la domanda supera l'offerta disponibile
        (non aspettare il last minute — il last minute gestito male svende)
```

**Segmentazione tariffaria**:

| Segmento | Anticipo | Flessibilità | Prezzo relativo |
|----------|----------|--------------|-----------------|
| Early bird | > 60gg | Non rimborsabile | -15% vs rack |
| Standard | 14-60gg | Rimborsabile | Rack rate |
| Last minute | < 7gg | Non rimborsabile | -5% / +10% secondo occupancy |
| Corporate | Anno | Fatturazione aziendale | -10% vs rack, volume commitment |
| Gruppi | > 60gg | Dipende da contratto | -20% vs rack, min camere |

## Ottimizzazione OTA (Online Travel Agencies)

### Mix canali raccomandato

| Canale | Target % ricavi | Commissione tipica |
|--------|----------------|-------------------|
| **Diretto** (sito + telefono) | > 35% | 0% |
| **Booking.com** | 25-35% | 15-18% |
| **Expedia/Hotels.com** | 10-15% | 18-22% |
| **Airbnb** (per B&B/ville) | 10-20% | 3% host + 14% guest |
| **Altri OTA** (lastminute, etc.) | 5-10% | 15-20% |

**Parità tariffaria**: Booking.com richiede rate parity per mantenere ranking. Strategia: offri valore aggiunto (colazione, late checkout, upgrade) sul diretto, non prezzo inferiore.

### Ottimizzare ranking Booking.com

1. **Tasso risposta**: rispondi a tutti i messaggi entro 1h → +ranking
2. **Punteggio review**: obiettivo > 8.5/10 (sollecita review dopo check-out)
3. **Disponibilità**: no chiusure eccessive → penalizza ranking
4. **Foto**: min 20 foto professionali, camera principale in primo piano
5. **Genius program**: aderisci per visibilità aggiuntiva (vedi se profittevole per la tua categoria)

## P&L struttura ricettiva — schema semplificato

```
RICAVI
  Camere (accommodation)          [€]
  F&B (colazione, ristorante)     [€]
  Servizi accessori               [€]
  TOTALE RICAVI                   [€]  100%

COSTI VARIABILI
  Commissioni OTA                 [€]  8-12%
  Costi colazione/F&B             [€]  3-5%
  Pulizie (se esternalizzate)     [€]  5-8%
  Amenities / consumabili         [€]  1-2%
  TOTALE VARIABILI                [€]

COSTI FISSI
  Personale (front desk, housekeeping se fisso)  [€]  25-35%
  Affitto/mutuo                   [€]
  Utenze (energia, acqua)         [€]  4-6%
  Manutenzione                    [€]  2-3%
  Marketing/OTA fisso             [€]
  Assicurazioni                   [€]
  TOTALE FISSI                    [€]

EBITDA = Ricavi - Variabili - Fissi
Margine EBITDA target: > 25% dei ricavi totali
```

## Stagionalità — gestione prezzi

**Estate (luglio-agosto)** in destinazioni balneare/montagna:
- Apri early bird a gennaio con sconto 15%
- Chiudi tariffe scontate a giugno
- Last minute: mantieni prezzo pieno o alza se occupancy > 85%

**Bassa stagione**:
- Tariffe pacchetto weekend (2 notti + colazione + esperienza)
- Promozioni specifiche: Capodanno, Pasqua, ponti festivi
- Convenzioni aziendali per viaggi business

## Benchmark settoriale Italia

| Tipologia | ADR medio | Occupancy media | RevPAR medio |
|-----------|-----------|-----------------|--------------|
| Hotel 4★ città | 130-180€ | 70% | 91-126€ |
| Hotel 4★ mare | 120-200€ | 65% (stagionale) | 78-130€ |
| Agriturismo | 90-140€ | 55-65% | 50-91€ |
| B&B premium | 80-130€ | 60-70% | 48-91€ |
| Villa/dimora storica | 250-500€ | 45-60% | 113-300€ |

Fonte: elaborazione dati STR/ISTAT 2023-2024 (indicativi, variano per location).

## Revenue Management tool stack (PMI)

| Strumento | Costo | Funzione |
|-----------|-------|----------|
| **Channel Manager** (Cloudbeds, SiteMinder) | 100-250€/mese | Sincronizza prezzi e disponibilità su tutti i canali |
| **PMS** (Property Management System) | 80-200€/mese | Gestione prenotazioni, check-in, report |
| **RMS** (Revenue Management System) | 100-300€/mese | Pricing dinamico automatico (opzionale per < 20 camere) |
| **Booking engine diretto** | incluso nel PMS | Prenotazioni dirette con pagamento online |

Alternativa budget: Google Sheets + Booking.com Extranet per strutture < 10 camere.
