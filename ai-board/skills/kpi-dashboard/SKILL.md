---
name: kpi-dashboard
description: KPI commerciali K2-AI, alert threshold, formato dashboard mensile e forecast
---

# KPI Dashboard

## KPI da tracciare sempre

| KPI | Target benchmark |
|---|---|
| Lead/settimana | in crescita |
| Tasso risposta outreach | >15% |
| Conversione call → proposta | >40% |
| Conversione proposta → chiuso | >30% |
| Ticket medio | monitorare trend |
| CAC (Costo Acquisizione Cliente) | <ticket_medio/3 |
| MRR (Monthly Recurring Revenue) | in crescita |

## Alert automatici 🔴

Segnala immediatamente se:
- MRR scende 2 mesi consecutivi
- CAC supera ticket_medio/3
- Pipeline attiva sotto 3 opportunità aperte
- Nessun nuovo lead da >2 settimane

## Dashboard mensile

Struttura obbligatoria:
- 📊 Pipeline: valore totale opportunità attive, numero lead per stadio
- 🔥 Lead caldi: top 3 opportunità con prossima azione
- 💰 Ricavi: MRR attuale, delta mese precedente, fatturato YTD
- 📉 Costi stimati e margine lordo
- ⚠️ Alert: problemi da risolvere
- 💡 Raccomandazione: una azione prioritaria

## Forecast

Proiezione 3 mesi basata su: pipeline attiva × tasso conversione storico.
Indica sempre le assunzioni usate per il forecast.

## Regole

- Output sempre con numeri arrotondati — mai decimali spurii.
- Se mancano dati, indica esplicitamente quali dati servono e come raccoglierli.
- Quando i numeri sono buoni, dillo — non solo quando c'è un problema.
- Classifica rischio: 🟢 verde (ok) | 🟡 giallo (attenzione) | 🔴 rosso (azione immediata).
