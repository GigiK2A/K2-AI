# Modello di Scoring Finanziario

Modello di calcolo per il semaforo finanziario PMI italiane. 5 KPI con soglie settoriali, pesi e formula dello score globale.

---

## 1. ROE (Return on Equity)

- **Formula**: `Utile Netto / Patrimonio Netto x 100`
- **Peso**: 5 (massimo)
- **Cosa misura**: quanto rende ogni euro investito dai soci nell'azienda
- **Spiegazione semplice**: "Se hai messo 100.000 euro nella tua azienda e il ROE e 12%, vuol dire che quei soldi ti hanno fruttato 12.000 euro quest'anno. In banca avresti preso molto meno."

### Soglie per settore

| Settore | Verde (buono) | Giallo (attenzione) | Rosso (critico) |
|---------|--------------|--------------------|-----------------| 
| Manifatturiero | > 10% | 4% - 10% | < 4% |
| Servizi | > 15% | 6% - 15% | < 6% |
| Commercio | > 12% | 5% - 12% | < 5% |
| Ristorazione | > 10% | 3% - 10% | < 3% |
| Edilizia | > 8% | 3% - 8% | < 3% |
| IT | > 18% | 8% - 18% | < 8% |
| Trasporti | > 8% | 3% - 8% | < 3% |
| Professionisti | > 20% | 8% - 20% | < 8% |

---

## 2. Current Ratio (Indice di Liquidita Corrente)

- **Formula**: `(Crediti Commerciali + Magazzino) / Debiti a Breve`
- **Peso**: 4
- **Nota**: se il magazzino non e fornito, usa solo Crediti Commerciali. Se debiti a breve non forniti, usa Debiti Commerciali oppure 40% dei Debiti Totali come proxy.
- **Cosa misura**: se l'azienda riesce a pagare i debiti che scadono entro 12 mesi
- **Spiegazione semplice**: "Se questo numero e sopra 1,5 vuol dire che per ogni euro che devi pagare a breve, ne hai almeno 1,50 pronti. Se e sotto 1, sei in difficolta: devi piu di quello che puoi incassare a breve."

### Soglie per settore

| Settore | Verde (buono) | Giallo (attenzione) | Rosso (critico) |
|---------|--------------|--------------------|-----------------| 
| Manifatturiero | > 1.5 | 1.0 - 1.5 | < 1.0 |
| Servizi | > 1.3 | 0.9 - 1.3 | < 0.9 |
| Commercio | > 1.4 | 1.0 - 1.4 | < 1.0 |
| Ristorazione | > 1.2 | 0.8 - 1.2 | < 0.8 |
| Edilizia | > 1.3 | 0.9 - 1.3 | < 0.9 |
| IT | > 1.6 | 1.1 - 1.6 | < 1.1 |
| Trasporti | > 1.3 | 0.9 - 1.3 | < 0.9 |
| Professionisti | > 1.5 | 1.0 - 1.5 | < 1.0 |

---

## 3. Indebitamento (D/E - Debt to Equity)

- **Formula**: `Debiti Totali / Patrimonio Netto`
- **Peso**: 4
- **Cosa misura**: quanto pesa il debito rispetto al capitale proprio
- **Spiegazione semplice**: "Se questo numero e 3, vuol dire che per ogni euro tuo ce ne sono 3 di debiti. Piu e alto, piu la tua azienda dipende dalle banche e dai fornitori. Se succede qualcosa di imprevisto, sei piu vulnerabile."

### Soglie per settore

| Settore | Verde (buono) | Giallo (attenzione) | Rosso (critico) |
|---------|--------------|--------------------|-----------------| 
| Manifatturiero | < 2.0 | 2.0 - 4.0 | > 4.0 |
| Servizi | < 1.5 | 1.5 - 3.0 | > 3.0 |
| Commercio | < 2.5 | 2.5 - 4.5 | > 4.5 |
| Ristorazione | < 2.0 | 2.0 - 4.0 | > 4.0 |
| Edilizia | < 3.0 | 3.0 - 5.0 | > 5.0 |
| IT | < 1.0 | 1.0 - 2.5 | > 2.5 |
| Trasporti | < 2.5 | 2.5 - 4.5 | > 4.5 |
| Professionisti | < 1.0 | 1.0 - 2.0 | > 2.0 |

**Nota**: per D/E il semaforo e invertito (valori bassi = verde, valori alti = rosso).

---

## 4. Margine Netto

- **Formula**: `Utile Netto / Fatturato x 100`
- **Peso**: 3
- **Cosa misura**: quanto guadagno reale resta su ogni euro di fatturato, dopo aver pagato tutto
- **Spiegazione semplice**: "Se fatturi 1 milione e il margine netto e 5%, vuol dire che di quel milione ti restano in tasca 50.000 euro. Il resto se ne va in costi, stipendi, tasse. Piu e alto, meglio e."

### Soglie per settore

| Settore | Verde (buono) | Giallo (attenzione) | Rosso (critico) |
|---------|--------------|--------------------|-----------------| 
| Manifatturiero | > 5% | 2% - 5% | < 2% |
| Servizi | > 8% | 3% - 8% | < 3% |
| Commercio | > 3% | 1% - 3% | < 1% |
| Ristorazione | > 5% | 2% - 5% | < 2% |
| Edilizia | > 4% | 1.5% - 4% | < 1.5% |
| IT | > 10% | 4% - 10% | < 4% |
| Trasporti | > 4% | 1.5% - 4% | < 1.5% |
| Professionisti | > 15% | 6% - 15% | < 6% |

---

## 5. Giorni Crediti (DSO - Days Sales Outstanding)

- **Formula**: `(Crediti Commerciali / Fatturato) x 365`
- **Peso**: 3
- **Cosa misura**: quanti giorni in media passano prima di incassare dai clienti
- **Spiegazione semplice**: "Se i tuoi giorni crediti sono 90, vuol dire che dopo aver fatto il lavoro e mandato la fattura, aspetti in media 3 mesi prima di vedere i soldi. Nel frattempo devi comunque pagare stipendi, fornitori, affitto. Piu questo numero e basso, meglio respiri."

### Soglie per settore

| Settore | Verde (buono) | Giallo (attenzione) | Rosso (critico) |
|---------|--------------|--------------------|-----------------| 
| Manifatturiero | < 60 gg | 60 - 90 gg | > 90 gg |
| Servizi | < 45 gg | 45 - 75 gg | > 75 gg |
| Commercio | < 30 gg | 30 - 60 gg | > 60 gg |
| Ristorazione | < 15 gg | 15 - 30 gg | > 30 gg |
| Edilizia | < 75 gg | 75 - 120 gg | > 120 gg |
| IT | < 50 gg | 50 - 80 gg | > 80 gg |
| Trasporti | < 60 gg | 60 - 90 gg | > 90 gg |
| Professionisti | < 40 gg | 40 - 70 gg | > 70 gg |

**Nota**: per Giorni Crediti il semaforo e invertito (valori bassi = verde, valori alti = rosso).

---

## Score Globale: Formula Ponderata

### Calcolo

1. Per ogni KPI, assegna un punteggio grezzo:
   - **Verde** = 100 punti
   - **Giallo** = 50 punti
   - **Rosso** = 10 punti

2. Moltiplica per il peso:
   - ROE: peso 5
   - Current Ratio: peso 4
   - Indebitamento D/E: peso 4
   - Margine Netto: peso 3
   - Giorni Crediti: peso 3

3. Formula:

```
Score = (P_roe x 5 + P_cr x 4 + P_de x 4 + P_mn x 3 + P_gc x 3) / (5 + 4 + 4 + 3 + 3)
```

Dove `P_xxx` e il punteggio grezzo (100, 50 o 10) del singolo KPI.

- **Somma pesi** = 19
- **Score massimo** = 100 (tutti verdi)
- **Score minimo** = 10 (tutti rossi)

### Esempio

| KPI | Semaforo | Punti | Peso | Contributo |
|-----|----------|-------|------|------------|
| ROE | Verde | 100 | 5 | 500 |
| Current Ratio | Giallo | 50 | 4 | 200 |
| D/E | Verde | 100 | 4 | 400 |
| Margine Netto | Rosso | 10 | 3 | 30 |
| Giorni Crediti | Giallo | 50 | 3 | 150 |

Score = (500 + 200 + 400 + 30 + 150) / 19 = **67.4** (Sufficiente)

---

## Le 5 Fasce

### Critico (0-30)

- **Messaggio**: "La tua azienda e in zona rossa. Servono interventi immediati per evitare problemi seri nei prossimi mesi."
- **CTA upsell**: "Con l'Analisi Bilancio PMI completa identifichiamo esattamente dove intervenire e costruiamo un piano d'azione in 48 ore. Prenota la call gratuita."

### Fragile (31-50)

- **Messaggio**: "La tua azienda ha delle fragilita importanti. Non e in pericolo immediato, ma servono correzioni per non peggiorare."
- **CTA upsell**: "L'Analisi Bilancio PMI ti dice esattamente quali leve muovere per passare da fragile a solido. Costa meno di quello che stai perdendo ogni mese."

### Sufficiente (51-70)

- **Messaggio**: "La tua azienda tiene, ma ci sono margini di miglioramento. Con qualche aggiustamento puoi fare un salto di qualita."
- **CTA upsell**: "Sei a un passo dal diventare un'azienda solida. L'Analisi Bilancio PMI ti mostra i 3 interventi che fanno la differenza."

### Solido (71-85)

- **Messaggio**: "Complimenti! La tua azienda e in buona salute. Ci sono ancora aree da ottimizzare, ma la base e solida."
- **CTA upsell**: "Per passare da solido a eccellente e proteggere la tua azienda nel lungo periodo, l'Analisi Bilancio PMI ti da la roadmap completa."

### Eccellente (86-100)

- **Messaggio**: "La tua azienda e in ottima forma! I numeri sono sopra la media del settore. Ora il focus e mantenere e crescere."
- **CTA upsell**: "Numeri eccellenti. L'Analisi Bilancio PMI ti aiuta a pianificare la crescita: nuovi investimenti, acquisizioni, espansione. Parliamone."
