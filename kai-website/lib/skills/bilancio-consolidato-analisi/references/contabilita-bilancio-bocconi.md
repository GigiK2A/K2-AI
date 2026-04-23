# Contabilità e Bilancio — Contenuto Bocconi Distintivo

Riferimento: Integrazione della skill `contabilita-bilancio` con casi numerici avanzati, consolidamento, transizione OIC-IAS/IFRS, analisi di bilancio quantitativa e rendiconti per flussi.

---

## Esempi Partita Doppia Avanzati (Casi Numerici Italiani)

### Caso 1: Acquisto con Resi e Sconti Commerciali

**Acquisto iniziale (30/9/2024):** Azienda XYZ acquista merci per 10.000 euro da fornitore con IVA 22%.

| Conto | Dare | Avere |
|-------|------|-------|
| Merci c/acquisti (+A) | 10.000 | |
| IVA sù acquisti (+A) | 2.200 | |
| Fornitori (-L) | | 12.200 |

**Reso parziale (15/10/2024):** Resi merce per 2.000 euro (difettose).

| Conto | Dare | Avere |
|-------|------|-------|
| Fornitori (+A) | 2.440 | |
| Merci c/resi (-A) | | 2.000 |
| IVA sù acquisti (-A) | | 440 |

**Sconto commerciale (20/10/2024):** Su residuo, sconto 5% = 400 euro.

| Conto | Dare | Avere |
|-------|------|-------|
| Fornitori (+A) | 488 | |
| Merci c/sconti (-A) | | 400 |
| IVA sù acquisti (-A) | | 88 |

**Saldo fornitori:** 12.200 – 2.440 – 488 = 9.272 euro.

### Caso 2: Nota di Credito per Fattura Errata

**Fattura di vendita (05/11/2024):** Quantità errata, totale 8.000 euro (IVA 22% = 1.760).

| Conto | Dare | Avere |
|-------|------|-------|
| Clienti (+A) | 9.760 | |
| Ricavi di vendita (+R/-E) | | 8.000 |
| IVA sù vendite (+L) | | 1.760 |

**Nota di credito (12/11/2024):** Riduzione fattura 3.000 euro.

| Conto | Dare | Avere |
|-------|------|-------|
| Ricavi di vendita (nota credito, -R) | 3.000 | |
| IVA sù vendite (-L) | 660 | |
| Clienti (-A) | | 3.660 |

**Saldo clienti:** 9.760 – 3.660 = 6.100 euro.

### Caso 3: Factoring (Cessione di Crediti)

**Credito originario (20/11/2024):** Cliente deve 5.000 euro (fattura con IVA).

| Conto | Dare | Avere |
|-------|------|-------|
| Clienti (+A) | 5.000 | |
| Ricavi (+R/-E) | | 5.000 |

**Cessione a factor (25/11/2024):** Prezzo di cessione 4.700 euro (sconto 300), commissione 200.

| Conto | Dare | Avere |
|-------|------|-------|
| Banca C/C (+A) | 4.700 | |
| Spese di gestione (+E) | 200 | |
| Clienti (-A) | | 5.000 |

**Utile/perdita:** -300 euro (differenza tra credito e incasso).

### Caso 4: Leasing Finanziario IAS 16/17

**Acquisizione via lease (01/01/2024):** Impianto valore presente: 50.000 euro, rate 5 annuali di 12.000 euro.

*Primo anno:*

| Data | Conto | Dare | Avere | Descrizione |
|------|-------|------|-------|-------------|
| 01/01 | Impianti c/leasing (+A) | 50.000 | | Riconoscimento asset |
| 01/01 | Debiti per lease (-L) | | 50.000 | Passività iniziale |
| 31/01 | Interessi passivi (+E) | 2.500 | | Quota interessi (5% su 50.000) |
| 31/01 | Debiti per lease (-L) | 9.500 | | Quota capitale |
| 31/01 | Banca C/C (-A) | | 12.000 | Pagamento rata |
| 31/12 | Ammortamento (+E) | 10.000 | | Quota annuale (50.000/5) |
| 31/12 | Fondo ammort. impianti (-A) | | 10.000 | Accumulo svalutazione |

**Bilancio 31/12/2024:** Impianto netto = 50.000 – 10.000 = 40.000 euro; Debito residuo = 50.000 – 9.500 = 40.500 euro.

### Caso 5: Aumento di Capitale in Contanti

**Decisione assembleare (15/02/2024):** Aumento di capitale: 100.000 azioni a 1,50 euro = 150.000 euro totali.
- Prezzo nominale per azione: 1 euro (capitale: 100.000 euro)
- Sovrapprezzo: 0,50 euro (50.000 euro)

| Conto | Dare | Avere |
|-------|------|-------|
| Banca C/C (+A) | 150.000 | |
| Capitale sociale (+SE) | | 100.000 |
| Sovrapprezzo azionario (+SE) | | 50.000 |

**Saldo capitale:** 150.000 euro; Saldo patrimonio netto: +150.000 euro.

### Caso 6: Distribuzione Utili e Dividendi

**Utile esercizio 2024:** 80.000 euro. Dividendo deliberato: 0,40 euro/azione (40.000 azioni in circolazione) = 16.000 euro.

**Data deliberazione (20/03/2025):**

| Conto | Dare | Avere |
|-------|------|-------|
| Utili esercizio (-SE) | 16.000 | |
| Dividendi pagabili (+L) | | 16.000 |

**Data pagamento (15/04/2025):**

| Conto | Dare | Avere |
|-------|------|-------|
| Dividendi pagabili (-L) | 16.000 | |
| Banca C/C (-A) | | 16.000 |

**Utile riportato:** 80.000 – 16.000 = 64.000 euro (reinvestito).

---

## Bilancio Consolidato (Area, Metodi, Elisioni)

### Area di Consolidamento

**Definizione:** Società controllate (direttamente/indirettamente possesso >50% diritti di voto) e collegate (20-50%) si consolidano con metodo integrale (controllate) o proporzionale/patrimonio netto (collegate).

**Esempio di Groupe:**
- S.p.A. Madre: Capitale 1.000.000 euro
  - Figlia 1 (100%): Capitale 500.000 euro; Patrimonio netto totale 600.000 euro
  - Figlia 2 (60%): Capitale 300.000 euro; Patrimonio netto totale 400.000 euro
  - Collegata (30%): Patrimonio netto totale 200.000 euro

### Metodo Integrale (Controllate)

**Principio:** Consolidamento linea per linea 100% dell'attivo/passivo, rettifica della quota di terzi.

**Figlia 1 (100%):**

| Elemento | Valore Individuale | Consolidamento | Nota |
|----------|---|---|---|
| Attivo netto | 600.000 | 600.000 | Integrato al 100% |
| Differenza di consolidamento | - | - | Nessuna (acquisito a valore libro) |
| Quota di terzi | - | - | Non esiste (100% controllata) |

**Figlia 2 (60%):**

| Elemento | Valore Individuale | % Consolidata | Importo | Nota |
|----------|---|---|---|---|
| Attivo netto | 400.000 | 100% | 400.000 | Consolidato integrale |
| Quota di terzi | 400.000 | 40% | 160.000 | Nel passivo (equity) |
| Quota Madre | 400.000 | 60% | 240.000 | Nel patrimonio netto |

**Differenza di consolidamento (avviamento):** Se Madre ha pagato per Figlia 2: 280.000 euro (vs 240.000 valore contabile), differenza 40.000 euro = **avviamento per acquisizione**.

### Metodo Patrimonio Netto (Collegate)

**Collegata (30%):** Contabilizzata al valore contabile di patrimonio netto × % di partecipazione, rettificato per variazioni reddituali.

| Data | Conto | Dare | Avere | Descrizione |
|------|-------|------|-------|-------------|
| 01/01 | Partecipazioni in collegate (+A) | 60.000 | | Valore iniziale (200.000 × 30%) |
| 31/12 | Utile esercizio collegata: 20.000 euro | | | |
| 31/12 | Partecipazioni in collegate (+A) | 6.000 | | Quota utile (20.000 × 30%) |
| 31/12 | Ricavi finanziari (+R/-E) | | 6.000 | Reddito da collegata |

**Saldo fine esercizio:** 60.000 + 6.000 = 66.000 euro.

### Elisioni Intra-Gruppo

**Transazioni eliminate nel consolidato:**

1. **Reciprocità crediti-debiti:** Se Figlia 1 ha fatturato a Madre merci 50.000 euro non ancora pagate:
   - Nel bilancio consolidato: Ricavi di Figlia 1 (-50.000) e Costo merci di Madre (-50.000)
   - Reciproca: Clienti di Figlia 1 (-50.000) e Fornitori di Madre (-50.000)

2. **Utili/perdite in rimanenze:** Se Figlia 2 ha venduto a Madre con ricarico 20%, rimangono 10.000 euro in magazzino Madre:
   - Utile implicito in rimanenze: 10.000 × 20/(100+20) = 1.667 euro
   - Elisione: Costo merci (+1.667) e Rimanenze finali (-1.667)
   - Impatto su utile consolidato: -1.667 euro

3. **Dividendi inter-gruppo:** Se Figlia ha pagato dividendi a Madre 30.000 euro:
   - Bilancio Madre: Ricavi finanziari (+30.000), Banca (+30.000)
   - Bilancio Figlia: Dividendi (-30.000), Banca (-30.000)
   - Consolidato: Entrambe eliminate (operazione interna)

---

## OIC vs IAS/IFRS: Tabella Comparativa Voce per Voce

| Voce Bilancio | OIC (Italia) | IAS/IFRS (Internazionale) | Impatto Principale |
|---|---|---|---|
| **AVVIAMENTO** | Ammortamento sistematico (max 10 anni) | Impairment test annuale (non ammortizza se vita utile indefinita) | Fair value superiore; utili incrementali nel medio termine |
| **Immobili (IAS 16)** | Costo storico deprezzato (ammortamento lineare) | Fair value model o costo; rivalutazioni periodiche | Volatilità maggiore in bilancio se mercato esposto |
| **Leasing (IAS 17/16)** | Off-balance (nota integrativa); canoni a conto economico | Riconoscimento asset + passività (diritto uso + obbligazione); ammortamento + interessi | Attivi e passivi aumentano; utile iniziale ridotto |
| **Rimanenze (IAS 2)** | Costo specifico o FIFO/LIFO (valore minore tra costo e mercato) | Costo (FIFO/media ponderata); LIFO non ammesso; valutazione a netto di realizzo | Possibile rivalutazione se LIFO usato in Italia |
| **Crediti (IFRS 9)** | Costo ammortizzato; svalutazione per perdite effettive (incurred loss) | Fair value attraverso utile o OCI; modello expected loss (perdite attese) | Maggior accantonamento subito per rischio crediti |
| **Strumenti finanziari (IFRS 9)** | Costo o fair value secondo natura | 3 bucket: costo ammortizzato, OCI, utile (mark-to-market su alcuni) | Volatilità bilancio; cambio fair value → utili/perdite |
| **Benefici dipendenti IAS 19** | Accantonamento a fondo basato su stime INPS (Italia); TFR a fondo | Valutazione attuariale complessa; obbligazioni pensionistiche esplicite | Fondo TFR possibile ridotto se non obbligatorio |
| **Ricavi IFRS 15** | Realizzo/principio competenza (fatturato + crediti) | 5-step model: identificare contratto, obbligazioni, prezzo, allocazione, riconoscimento | Posticipo ricavi su contratti pluriennali |
| **Immobilizzazioni immateriali** | Costi di ricerca capitalizzabili se sviluppo; marchio non capitalizzato se interno | Capitalizzazione ristretta (solo progetti in fase avanzata); marchi acquisiti capitalizzati | Riduzione attivo se marchi interni |
| **Imposte differite** | IRES/IRAP: differenze temporanee tra bilancio civilistico e fiscale | Imposta corrente e differita (entity approach); full provision | Maggior passivo se differenze negative |
| **Consolidamento** | Proporzionale o integrale (OIC non usato comunemente) | Integrale controllate, patrimonio netto collegate, fair value investimenti | Armonizzazione con IFRS 10-11 |

### Commenti Critici

- **Avviamento:** L'impairment test (IAS) è meno conservativo dell'ammortamento (OIC) se azienda genera flussi positivi; utile impatto positivo su ROE.
- **Leasing:** Il riconoscimento asset IAS aumenta indebitamento e riduce ROI nel primo anno; importante per analisi di bilancio.
- **IFRS 15 (Ricavi):** I contratti costruzione e vendita differita subiscono compressione temporale di ricavi; attenzione a trend di crescita apparente.
- **Benefici dipendenti:** IAS 19 comporta svalutazione attuariale del TFR; impatto su leverage se fondo importante.

---

## Analisi di Bilancio Quantitativa Avanzata

### Indici Completi e Formule Esatte

#### 1. ROE (Return on Equity) Scomposto — DuPont

**Formula base:**
```
ROE = Utile netto / Patrimonio netto medio
```

**Scomposizione 3-fattori (Dupont):**
```
ROE = (Utile netto / Ricavi) × (Ricavi / Attivo totale) × (Attivo totale / Patrimonio netto)
    = Margine netto × Rotazione asset × Leva finanziaria
```

**Esempio numerico:**
- Utile netto: 100.000 euro
- Ricavi: 1.000.000 euro
- Attivo totale medio: 500.000 euro
- Patrimonio netto medio: 250.000 euro

```
ROE = (100.000 / 1.000.000) × (1.000.000 / 500.000) × (500.000 / 250.000)
    = 10% × 2,0 × 2,0 = 40%

Lettura: Margine 10% (efficienza operativa), rotazione 2x (utilizzo asset),
leva 2x (sfruttamento debito). ROE 40%.
```

#### 2. ROI (Return on Investment) Scomposto

**Formula base:**
```
ROI = EBIT / Capitale investito medio (totale passivo + PN)
```

**Relazione ROE/ROI (spread di leva):**
```
ROE = ROI + (ROI - i) × (Debito / PN)

Dove i = costo medio del debito (Interessi / Debito medio)
```

**Esempio:**
- EBIT: 150.000 euro
- Capitale investito medio: 500.000 euro
- Debito medio: 250.000 euro; Interessi pagati: 15.000 euro
- PN medio: 250.000 euro

```
ROI = 150.000 / 500.000 = 30%
i (costo debito) = 15.000 / 250.000 = 6%

ROE = 30% + (30% - 6%) × (250.000 / 250.000)
    = 30% + 24% = 54%

Spread positivo: leva finanzaria amplifica ROE perché ROI > i.
```

#### 3. Leverage e Solvibilità

**Debt-to-Equity:**
```
D/E = Debito totale / Patrimonio netto
```

**Debt-to-Assets:**
```
D/A = Debito totale / Attivo totale
```

**Interest Coverage:**
```
IC = EBIT / Interessi = 150.000 / 15.000 = 10x

(Capacità coprire oneri finanziari; soglia prudenziale > 2.5x)
```

#### 4. Indici di Redditività Operativa

**EBITDA Margin:**
```
EBITDA Margin = EBITDA / Ricavi

Dove EBITDA = EBIT + Ammortamenti + Accantonamenti
```

**EBIT Margin (Operating Margin):**
```
EBIT Margin = EBIT / Ricavi
```

**Esempio:**
- Ricavi: 1.000.000 euro
- EBITDA: 200.000 euro
- EBIT: 150.000 euro

```
EBITDA Margin = 200.000 / 1.000.000 = 20%
EBIT Margin = 150.000 / 1.000.000 = 15%

Ammortamenti = 200.000 – 150.000 = 50.000 euro.
```

#### 5. Indici di Liquidità

**Current Ratio:**
```
Current Ratio = Attivo circolante / Passivo corrente

(Soglia normale: 1.5 – 2.0)
```

**Quick Ratio (Acid Test):**
```
Quick Ratio = (Attivo circolante – Rimanenze) / Passivo corrente

(Soglia: > 1.0)
```

**Cash Ratio:**
```
Cash Ratio = Disponibilità liquide / Passivo corrente

(Conservativo; soglia > 0.3)
```

### Riclassificazione dello SP: Due Metodi

#### Metodo Liquidità/Esigibilità (Classico)

Ordina per velocità di conversione in liquidità.

**ATTIVO**
- A) **Disponibilità liquide:** Cassa, banca
- B) **Crediti a breve:** Clienti (< 1 anno), anticipi dipendenti
- C) **Rimanenze**
- D) **Attivo corrente vario**
- E) **Immobilizzazioni finanziarie:** Partecipazioni, titoli > 1 anno
- F) **Immobilizzazioni materiali:** Impianti, immobili (netti)
- G) **Immobilizzazioni immateriali:** Avviamento, marchi

**PASSIVO**
- 1) **Debiti a breve:** Fornitori, anticipi clienti, ratei passivi (< 1 anno)
- 2) **Debiti finanziari breve:** Mutui < 1 anno, anticipi bancari
- 3) **Patrimonio netto:** Capitale, sovrapprezzo, riserve, utili
- 4) **Debiti a lungo:** Mutui > 1 anno, prestiti obbligazionari
- 5) **Fondi per rischi e oneri**

**Analisi CCN (Capitale Circolare Netto):**
```
CCN = (A+B+C+D) – (1+2) = Attivo circolante – Passivo corrente

Positivo = solidità liquidità; Negativo = rischio insolvibilità
```

#### Metodo Funzionale (Dinamico — Bocconi)

Ordina per funzione operativa.

**ATTIVO**
- **Gestione caratteristica:** Clienti, magazzino, fornitori (segregati)
- **Gestione finanziaria:** Cassa, titoli, investimenti finanziari
- **Gestione investimenti:** Impianti, edifici, avviamento (immobilizzazioni)

**PASSIVO**
- **Finanziamento da operazioni:** Fornitori, ratei passivi
- **Finanziamento proprio:** Capitale, riserve, utili
- **Finanziamento esterno:** Banche, obbligazioni

**Utilità:** Identifica chiaramente ciclo operativo vs finanziamento.

### Rendiconto Finanziario (Metodo Indiretto) — Quadratura

**Struttura:**

```
Flussi da attività operativa (CFO):
  Utile netto esercizio               +100.000
  + Ammortamenti (non cash)           +50.000
  + Accantonamenti fondi              +10.000
  - Incremento crediti (capitale circolante)  -20.000
  - Decremento fornitori              -15.000
  + Incremento rimanenze              +5.000
  = CFO                               = +130.000

Flussi da attività investimento (CFI):
  - Acquisizione impianti             -80.000
  - Acquisizione titoli               -30.000
  + Vendita immobili                  +20.000
  = CFI                               = -90.000

Flussi da attività finanziamento (CFF):
  + Aumento capitale                  +50.000
  - Rimborso mutui                    -40.000
  - Pagamento dividendi               -20.000
  = CFF                               = -10.000

Variazione cassa (CFO + CFI + CFF)    = +30.000

Cassa inizio esercizio                = +100.000
Cassa fine esercizio                  = +130.000
```

**Quadratura:** Variazione effettiva cassa = -100.000 + 130.000 = +30.000 ✓

---

## Rendiconto Finanziario e Analisi per Flussi

### Self-Financing (Autofinanziamento)

**Formula:**
```
Self-Financing = CFO – Dividendi pagati

= Utile + Ammortamenti + Accantonamenti – Variazione CCN – Dividendi
```

**Esempio:**
```
CFO: +130.000 euro
Dividendi pagati: -20.000 euro

Self-Financing = 130.000 – 20.000 = +110.000 euro

(Capacità finanziamento investimenti senza ricorso a debito/capitale).
```

### Variazione Capitale Circolante Netto (∆CCN)

**Calcolo:**

```
∆CCN = (Crediti anno 2 – Crediti anno 1) 
      + (Rimanenze anno 2 – Rimanenze anno 1)
      – (Fornitori anno 2 – Fornitori anno 1)

Segno: Positivo = assorbimento liquidità (investimento operativo)
       Negativo = rilascio liquidità (fonte di liquidità)
```

**Esempio numerico:**

| Voce | Anno 1 | Anno 2 | Variazione | Segno |
|-----|-------|-------|-----------|-------|
| Clienti | 80.000 | 100.000 | +20.000 | Negativo CFO |
| Rimanenze | 120.000 | 130.000 | +10.000 | Negativo CFO |
| Fornitori | 90.000 | 110.000 | +20.000 | Positivo CFO |
| **∆CCN** | | | | **-10.000** |

(Capitale circolante assorbe 10.000 euro; riduce CFO di 10.000).

### Cash Conversion Cycle (CCC) — Giorni

**Formula:**
```
CCC = (Giorni crediti) + (Giorni rimanenze) – (Giorni fornitori)
    = (Clienti / Ricavi) × 365 + (Rimanenze / COGS) × 365 – (Fornitori / COGS) × 365
```

**Esempio:**
- Ricavi: 1.000.000 euro
- COGS: 600.000 euro
- Clienti: 80.000 euro → 29 giorni
- Rimanenze: 120.000 euro → 73 giorni
- Fornitori: 90.000 euro → 55 giorni

```
CCC = 29 + 73 – 55 = 47 giorni

(Azienda finanzia operazioni per 47 giorni in media).
```

---

## Note di Integrazione

### Formule Numeratore/Denominatore Esatte

1. **ROE dupont:** (UN / Ricavi) × (Ricavi / AT) × (AT / PN)
2. **ROI:** EBIT / (Debito + PN)
3. **Spread leva:** (ROI – i) × (D / PN)
4. **Leva finanziaria:** D / PN (multiplo su ROE)
5. **Margine netto:** UN / Ricavi
6. **Rotazione asset:** Ricavi / AT medio
7. **Current ratio:** AC / PC
8. **Quick:** (AC – Rim) / PC
9. **Debt-to-Equity:** D / PN
10. **Interest coverage:** EBIT / Interessi

### Standard Contabili Citati

- **OIC (Organismo Italiano Contabilità):** Base bilancio Italia; ammortamento avviamento (10 anni max), valutazione prudenziale rimanenze.
- **IFRS/IAS (IASB):** Internazionali; impairment test avviamento, fair value, expected loss crediti IFRS 9.
- **Art. 2423 Codice Civile italiano:** Principi bilancio: chiarezza, fedele rappresentazione, riconciliabilità tra voci.

### Contesti di Applicazione

- **Analisi interna (management):** Riclassificazione funzionale; indici gestione caratteristica vs finanziaria.
- **Analisi esterna (creditori/investor):** Current ratio, leverage, coverage; impatto rating.
- **Valutazione M&A:** Free cash flow (CFO – Capex); self-financing, CCC.
- **Bilancio consolidato:** Elisioni intra-gruppo, quota di terzi, avviamento; impatto ROE holding.

---

**File metadata:**
- Righe: 598
- Sezioni: 5 (PD avanzati, consolidato, OIC-IAS, indici, flussi)
- Esempi numerici: 15+ con conti italiani esatti
- Formule: 20+ con numeratore/denominatore preciso
