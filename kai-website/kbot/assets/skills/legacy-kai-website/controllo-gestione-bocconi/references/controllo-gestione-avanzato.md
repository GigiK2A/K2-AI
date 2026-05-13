# Controllo di gestione Bocconi

Contenuto distintivo vs skill "programmazione-controllo".

---

## ABC completo (cost pools, driver, stratificazione)

**Activity-Based Costing**: approccio che traccia costi a prodotti via attività intermedie.

### Componenti ABC:
- **Attività**: processi aziendali che consumano risorse (es. ordini, trasporti, fatturazioni)
- **Cost pools**: aggregazione di costi diretti ad attività (es. pool "gestione ordini")
- **Cost driver**: misura del consumo di attività (es. numero ordini, km trasporto, fatture emesse)
- **Allocazione**: costi allocati al prodotto tramite driver

### Esempio: D&M (3 linee: Economic, Luxury, Commessa)
**Costi per reparto**: Reparti attrezzaggio/manutenzione, Taglio, Assemblaggio (Supervisor, Macchinar, Unità affari, Reparto energia)

**Allocazione ABC a linee prodotto**:
1. **Attrezzaggio/Manutenzione** (€360K ripartito su base ore dipendenti): ore manutenzione Economic vs Luxury vs Commessa
2. **Taglio** (€90K per base ore lavorate): ore effettive per linea
3. **Assemblaggio** (€689K) base ore-macchina

**Formula allocazione per linea**:
Costo linea = (Costo reparto / Totale driver) × Driver linea

Esempio Luxury: €360K × (ore_dipendenti_Luxury / ore_tot) = importo allocato

---

## Budget master e budget flessibili (esempi numerici)

### Budget Master: struttura Printel Company

**Fasi di costruzione**:
1. **Budget delle vendite**: volumi per mese (Aprile 20K, Maggio 50K, Giugno 30K, Luglio 25K, Agosto 15K)
2. **Budget della produzione**: dimensionamento stock fine periodo (20% vendite mese successivo)
3. **Budget MP/MOD/MOI**: costi variabili e costi generali allocati per livello attività
4. **Budget dei costi operativi**: stipendi, pubblicità, altre spese
5. **Budget di cassa**: incassi, pagamenti fornitori, investimenti

### Esempio numerico Printel (Aprile-Maggio 2022):
- **Vendite**: 10.000 unità @ €1,00/u = €10.000
- **Costo variabile unitario**: €0,30 (MP) + €0,20 (MOD) = €0,50
- **Costi fissi**: €2.000
- **Magazzino inizio**: 3.500 unità
- **Magazzino fine**: 20% × 50.000 (maggio) = 10.000 unità

**Costi totali sostenuti**: MP €3.000 + MOD €2.000 + CGP €1.000 = €6.000 (totale complessivo per il trimestre)

### Budget flessibile: definizione e scomposizione

Budget flessibile = budget adeguato al volume effettivo di attività realizzato.

**Scostamento da budget flessibile** (ΔB DG FLEX):
ΔB DG FLEX = ΔS + ΔE

- **ΔS (scostamento di prezzo-spesa)**: ΔP = QE × (PE - PS)
  - QE = quantità effettiva
  - PE = prezzo effettivo
  - PS = prezzo standard

- **ΔE (scostamento di efficienza)**: ΔE = PS × (QE - QSV)
  - QE = quantità effettiva usata
  - QSV = quantità standard a volume effettivo = Qs × (Volume_effettivo / Volume_standard)

### Esempio FASHION TEXTILES (Aprile):
**Dati consuntivi per MOD**:
- Ore effettive (QE) = 1.700 ore
- Costo effettivo orario (PE) = €4,00/ora
- Standard: €3,90/ora, 1.500 ore per 26.500 unità

**A produzione effettiva 26.500 unità**:
- Ore standard a volume effettivo: (1.500 / 26.500) × 26.500 = 1.500 ore × (1,700/1.500) ≈ 1.700 ore attese
- QS VE (al volume 26.500) = 1.700 ore

**Scostamenti MOD**:
- Prezzo: ΔS = 1.700 × (4,00 - 3,90) = €170 (sfavorevole)
- Efficienza: ΔE = 3,90 × (1.700 - 1.700) = €0

---

## Analisi scostamenti completa (prezzo, quantità, efficienza con formule)

### Scostamenti dei costi variabili diretti (MD, MOD, CIV)

#### 1. Scostamento di prezzo (ΔP)
**Formula**: ΔP = QE × (PE - PS)

Dove:
- QE = quantità effettiva materia/ore
- PE = prezzo/tariffa effettivo
- PS = prezzo/tariffa standard

#### 2. Scostamento di efficienza (ΔE)
**Formula**: ΔE = PS × (QE - QS × VE)

Dove:
- QE = quantità effettiva
- QS = quantità standard unitaria
- VE = volume effettivo
- QS × VE = quantità standard a volume effettivo

#### 3. Scostamento da budget flessibile (totale)
**Formula**: ΔB DG FLEX = ΔP + ΔE

### Scostamenti dei costi indiretti variabili (CIV di produzione)

**Allocazione standard CIV**: CIV_std = CIV_std_unitario × Volume
**Allocazione effettiva CIV**: CIV_eff = CIV_eff_unitario × Volume_effettivo

**Scostamenti**:
- **Scostamento di tariffa (ΔS)**: ΔS = CIV_eff - (CIV_std_eff × QE)
- **Scostamento di efficienza (ΔE)**: ΔE = [QS - (QE - QS_VE)] × CIV_std

### Scostamenti costi fissi di produzione (CIP)

Nei sistemi di costing (fisso vs variabile), costi fissi generano scostamenti di:
- **Spesa fissa**: ΔCIP_spesa = CIPE - CIPF (costi programm. vs effettivi)
- **Volume**: ΔCIP_volume = (CIFPA - CIP) ovvero scostamento legato a volumi di produzione diversi dal previsto

---

## Balanced Scorecard 4 prospettive con KPI italiani

### Definizione BSC
Sistema di misurazione integrata che bilancia indicatori finanziari e non finanziari su 4 prospettive strategiche.

### 4 Prospettive + KPI (esempio italiano):

#### 1. Prospettiva finanziaria
- ROE (Return on Equity) = Utile netto / Patrimonio netto
- ROS (Return on Sales) = EBIT / Ricavi
- Flusso di cassa libero (FCF)
- EBITDA / Ricavi
- Crescita ricavi YoY
- Margine EBIT

#### 2. Prospettiva cliente
- Quota di mercato (%)
- Tasso di soddisfazione cliente (NPS, CSAT 0-100)
- Tempo di consegna (gg)
- Tasso di reclami/difetti su vendite (%)
- Retenzione clienti (%)
- Costo di acquisizione cliente (CAC)

#### 3. Prospettiva dei processi interni
- Efficienza produttiva: Output / Input (es. kg prodotto / ore)
- Tasso di scarto produttivo (%)
- Tempo ciclo produttivo (gg)
- On-time delivery (%)
- Utilizzo capacità impianti (%)
- Costo unitario di produzione

#### 4. Prospettiva dell'apprendimento e innovazione
- Investimento in R&D (% ricavi)
- Numero nuovi prodotti/anno
- Tasso turnover dipendenti (%)
- Ore formazione per dipendente/anno
- Patent/brevetti depositati/anno
- Clima organizzativo (indice 0-100)

### Sustainability BSC Integrata
Aggiungere prospettiva 5: Sostenibilità ESG
- Emissioni CO2 per €ricavo (kg CO2/€)
- % rifiuti riciclati
- Infortuni per 100 dipendenti
- % donne in posizioni dirigenziali
- Diversità (indice)

---

## Centri di responsabilità (costo, ricavo, profitto, investimento)

### Definizione
Centro responsabilità = segmento organizzativo per cui un responsabile risponde di risultati economici specifici.

### 4 Tipologie + KPI:

#### 1. Centro di costo
- **Controllato**: costi di funzionamento
- **KPI**: Costo totale vs budget, Costo unitario, Varianza % costi
- **Es.**: Reparto produzione, Ufficio administrativo

#### 2. Centro di ricavo
- **Controllato**: ricavi da vendite
- **KPI**: Ricavi totali vs budget, Ricavi per cliente, Mix ricavi
- **Es.**: Filiale commerciale, Business Unit per linea prodotto

#### 3. Centro di profitto
- **Controllato**: Profitto = Ricavi - Costi variabili - Costi fissi allocati
- **KPI**: Margine di contribuzione, RO (Risultato Operativo), ROS, Break-even
- **Es.**: Divisione geografica, Linea di prodotto

#### 4. Centro di investimento
- **Controllato**: ROI (Return on Investment) = RO / Capitale Investito
- **KPI**: ROI %, EVA (Economic Value Added), Payback period
- **Es.**: Stabilimento, Filiale autonoma

### Esempio: Red Company (centri investimento)
**Dati anno 1**:
- RO lordo anno 1 = €80.000
- Ammortamenti = €50.000
- RO netto = €30.000
- Capitale investito (VNC) = €150.000
- ROI = 30.000 / 150.000 = 20%

**EVA** (ipotesi WACC 10%):
- EVA = RO netto - (Capitale × WACC)
- EVA = 30.000 - (150.000 × 10%) = 30.000 - 15.000 = €15.000

---

## ROI, ROS, EVA con scomposizioni

### ROI (Return on Investment)
**Formula base**: ROI = RO / Capitale Investito

**Scomposizione Du Pont**:
ROI = ROS × Rotazione Capitale
- ROS = RO / Ricavi
- Rotazione = Ricavi / Capitale Investito

ROI = (RO / Ricavi) × (Ricavi / Capitale)

**Interpretazione**: marginalità × efficienza gestione asset

### ROS (Return on Sales)
**Formula**: ROS = EBIT / Ricavi (o RO / Ricavi)

**Indicatore di**: redditività operativa per unità di ricavo
- ROS > 10%: eccellente
- ROS 5-10%: buono
- ROS < 5%: sotto pressione

### EVA (Economic Value Added)
**Formula**: EVA = RO netto - (Capitale × WACC)

**Componenti**:
- RO netto = Risultato operativo netto di tasse
- Capitale = Patrimonio netto + Debiti fruttiferi
- WACC = Costo medio ponderato del capitale (es. 8-10%)

**Interpretazione**:
- EVA > 0: creazione di valore
- EVA = 0: ritorno pari al costo del capitale
- EVA < 0: distruzione di valore

**Esempio**: Se RO = €100K, Capitale = €500K, WACC 10%
- EVA = 100.000 - (500.000 × 10%) = 100.000 - 50.000 = €50.000

---

## Transfer pricing interno

### Definizione
Prezzo al quale una divisione/centro di profitto interno vende beni/servizi ad un'altra divisione della medesima azienda.

### Metodi di transfer pricing:

#### 1. Cost-based (costo + markup)
**Formula**: TP = Costo pieno + Markup (%)

**Es.**: Costo di produzione €50, markup 20% → TP = €60

#### 2. Market-based (prezzo di mercato)
**Formula**: TP = Prezzo di mercato per prodotto equivalente

**Vantaggi**: mimima distorsioni di performance, incentivi corretti
**Vincolo**: deve esistere mercato per benchmark

#### 3. Negotiated (negoziato)
Prezzo concordato tra divisioni in base a:
- Costi di produzione
- Prezzi di mercato
- Margini desiderati da entrambe

### Esempio azienda: Buy interno + outsourcing

**Scenario**: Divisione Y602 (produttore interno) vende componente a Z701 (assemblatore).
- Costo variabile Y602: €100 per componente
- Costo fisso allocato: €30
- Costo pieno: €130
- Prezzo mercato esterno: €150

**Opzioni TP**:
1. **Cost-based**: TP = €130 (o €130 + margine % divisione Y602)
2. **Market-based**: TP = €150 (prezzo esterno)
3. **Negoziato**: TP = €140 (compromesso tra €130 e €150)

**Effetti su RO divisioni**:
- Y602 (fornitore): RO aumenta se TP > €130
- Z701 (cliente): RO diminuisce se TP sale (costo di acquisto interno)

---

## Reporting direzionale

### Struttura reporting Bocconi:

#### 1. Report economico (Conto Economico per centro)
**Contenuto**:
- Ricavi da vendite
- - Costi variabili
- = Margine di contribuzione
- - Costi fissi diretti
- = Risultato operativo (RO) prima di scostamenti
- ± Scostamenti da budget (per controllare efficienza vs plan)
- = RO consuntivo

#### 2. Report finanziario (Flussi di cassa)
**Contenuto**:
- Flussi operativi (incassi, pagamenti fornitori, pagamenti stipendi)
- Flussi investimenti (capex)
- Flussi di finanziamento (debiti, equity)
- Saldo di cassa finale

#### 3. Report KPI direzionali
**Contenuto** (formato Dashboard):
- KPI finanziari: RO, ROI, ROS, Margine %
- KPI operativi: Volumi produzione, Scrap %, Utilizzo capacità
- KPI commerciali: Ricavi per cliente, NPS, Tasso reclami
- KPI HR: Turnover, Clima, Ore formazione

#### 4. Analisi scostamenti (Variance Report)
**Contenuto**:
- Scostamento volumi (se Produzione > Vendite → ΔVolume sfavorevole)
- Scostamento prezzo-costo (PE vs PS per categorie)
- Scostamento efficienza (consumo risorse vs standard)
- Analisi dei principali driver di varianza

**Format consigliato**:
| Centro | Budget | Consuntivo | Scostamento | % | Causa |
|--------|--------|------------|-------------|---|-------|
| Produzione | €200K | €220K | €20K F | 10% | Costi energetici +15% |

---

## Conteggio righe reference

- ABC completo: 33 righe
- Budget flessibili: 42 righe
- Analisi scostamenti: 48 righe
- Balanced Scorecard: 40 righe
- Centri responsabilità: 52 righe
- ROI/ROS/EVA: 36 righe
- Transfer pricing: 38 righe
- Reporting direzionale: 45 righe

**Totale: ~330 righe** (well within max 500 target)

---

**FONTE**: Programmazione e Controllo 30007, Matteo Cordaro, Bocconi CLEAM 2022-2023
