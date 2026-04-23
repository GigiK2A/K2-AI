---
name: programmazione-controllo
description: >-
  Programmazione e controllo di gestione (Management Accounting). Analisi CVR,
  BEP, margine di contribuzione, leva operativa, classificazione costi,
  CMS tradizionali e ABC, decisioni marketing e produzione, master budget,
  budget flessibili, analisi scostamenti, centri di responsabilità, balanced
  scorecard, ROI EVA, costo pieno vs variabile, job/process costing, allocazione
  costi, delta assorbimento. Basato su corso Bocconi. Usa SEMPRE per: analisi
  costi-volumi-risultati, break even point, margine contribuzione, leva
  operativa, costi fissi variabili, ABC activity based costing, budget,
  scostamenti prezzo efficienza, centri costo profitto investimento, BSC,
  ROI ROS EVA, make or buy, costo opportunità, job costing, process costing.
  Attiva per "calcolo BEP", "analisi costi", "budget aziendale", "scostamenti",
  "make or buy", "margine di contribuzione", "controllo di gestione".
---

# Programmazione e Controllo di Gestione (Management Accounting)

Skill basata sul corso Bocconi 30007 — Management Accounting / Programmazione e Controllo.
Copre la contabilità direzionale (CtrlGe) per le decisioni interne, distinta dalla contabilità generale (CoGe) per la comunicazione esterna.

---

## 1. SISTEMA AZIENDALE DI CONTROLLO (SAC)

### CoGe vs CtrlGe
| Dimensione | Contabilità Generale | Controllo di Gestione |
|---|---|---|
| **Destinatari** | Esterni (azionisti, banche, fisco) | Interni (manager, direzione) |
| **Oggetto** | Azienda nel complesso | Segmenti (prodotti, divisioni, clienti) |
| **Regole** | OIC, IAS/IFRS | Nessun vincolo normativo |
| **Orientamento** | Passato (consuntivo) | Futuro (preventivo) + passato |
| **Frequenza** | Annuale / trimestrale | Mensile o on-demand |

### Contabilità Direzionale: finalità
- **Pianificazione**: definire obiettivi e allocare risorse
- **Controllo**: confronto consuntivo vs preventivo, individuazione scostamenti
- **Decision-making**: supporto a decisioni operative e strategiche

---

## 2. CLASSIFICAZIONE DEI COSTI

### Per comportamento rispetto al volume
- **Costi Variabili (CV)**: variano proporzionalmente al volume di attività (materie prime, provvigioni, energia di processo)
- **Costi Fissi (CF)**: restano costanti al variare del volume entro il range rilevante (affitti, ammortamenti, stipendi direzione)
- **Costi Semi-variabili**: componente fissa + componente variabile (es. utenze con quota fissa + consumo)

### Per modalità di attribuzione all'oggetto di costo
- **Costi Diretti (CD)**: attribuibili in modo univoco e conveniente all'oggetto di costo (MP, MOD)
- **Costi Indiretti (CI)**: non attribuibili direttamente, richiedono basi di allocazione (CGP, ammortamenti comuni, affitto stabilimento)
- **Costi Non-allocabili (CN)**: costi comuni non ripartibili su singoli oggetti

### Configurazioni di costo del prodotto
1. **Costo Primo** = MP + MOD (solo costi diretti di produzione)
2. **Costo Industriale** = Costo Primo + CGP (Costi Generali di Produzione)
3. **Costo Pieno (Full Cost)** = Costo Industriale + Costi Commerciali + Costi Amministrativi + Costi Generali
4. **Full Costing Industriale (FCI)** = MP + MOD + CIP (Costi Indiretti di Produzione)
5. **Costo del Venduto** = FCI delle unità vendute

---

## 3. ANALISI COSTI-VOLUMI-RISULTATI (CVR) E BREAK-EVEN

### Margine di Contribuzione (MdC)
```
MdC unitario = Prezzo di vendita − Costo variabile unitario
MdC totale = Ricavi totali − Costi variabili totali
MdC% = MdC unitario / Prezzo di vendita × 100
```

### Break-Even Point (BEP)
```
BEP (quantità) = CF / MdC unitario
BEP (fatturato) = CF / MdC%
```

### Margine di Sicurezza
```
MdS = Volume attuale − Volume BEP
MdS% = MdS / Volume attuale × 100
```

### Analisi del profitto target
```
Q_target = (CF + Profitto desiderato) / MdC unitario
Q_target (post-tax) = (CF + Profitto/(1−t)) / MdC unitario
```

### Leva Operativa (GLO)
```
GLO = MdC totale / RO
ΔRO = GLO × Δ%Volumi × RO
```
Interpretazione: il GLO misura la sensibilità del Risultato Operativo a variazioni percentuali del volume di vendita. Più alto è il GLO, più l'azienda ha una struttura di costi fissi elevata → maggiore rischio operativo ma anche maggiore potenziale di leva.

### MdC composto (mix di prodotti)
```
MdC% composto = Σ (MdC%_i × %Ricavi_i)
BEP (fatturato mix) = CF / MdC% composto
```
Il BEP a fatturato composto si riproporziona poi per prodotto in base alla % dei ricavi.

---

## 4. SISTEMI DI MISURAZIONE DEI COSTI (CMS)

### CMS Tradizionali — Base Unica
```
CdA (Coefficiente di Allocazione) = CI Totali / Base di allocazione unica
CI allocati al prodotto = CdA × Consumo della base da parte del prodotto
```
Basi comuni: ore MOD, ore macchina, costo MOD, costo MP.

**Limiti**: se i prodotti consumano le risorse in modo diverso dalla singola base, si generano sussidi incrociati (cross-subsidization).

### CMS Tradizionali — Base Multipla
Si usano più basi di allocazione, una per ogni aggregato di costi indiretti:
```
CdA_j = CI del pool j / Base di allocazione del pool j
CI totali prodotto = Σ (CdA_j × Consumo_j del prodotto)
```

### Activity Based Costing (ABC)
L'ABC identifica le **attività** come cause del consumo di risorse e utilizza **activity driver** specifici:

**Processo a 4 fasi:**
1. Identificare le **attività** rilevanti
2. Assegnare i costi alle attività (resource driver)
3. Calcolare il **CdA per attività** = Costo attività / Driver totale attività
4. Imputare i costi ai prodotti: CI = CdA × Consumo driver del prodotto

**Gerarchia delle attività (Cooper):**
- **Unit-level**: per ogni unità prodotta (ore macchina, kWh)
- **Batch-level**: per ogni lotto (setup, ispezioni per lotto)
- **Product-level**: per ogni linea di prodotto (progettazione, pubblicità specifica)
- **Facility-level**: per l'intera struttura (affitto, direzione generale)

**Quando l'ABC è più accurato dei CMS tradizionali**: prodotti diversificati, elevata incidenza CI, attività non correlate al volume, prodotti a basso volume che consumano risorse sproporzionate.

---

## 5. DECISIONI DI MARKETING

### Ordine di vendita speciale (OdV)
Accettare se il prezzo speciale ≥ costi incrementali (variabili + eventuali CF incrementali).
I CF esistenti sono **irrilevanti** (sunk) se c'è capacità produttiva inutilizzata.

```
ΔRO = Ricavi incrementali − Costi incrementali
Accettare se ΔRO > 0
```

### Eliminazione di un prodotto/segmento
Eliminare solo se i costi eliminabili > ricavi persi.
**Attenzione**: i costi allocati (CI) spesso non sono eliminabili e vengono riallocati.
```
Costi eliminabili = CV del prodotto + CF specifici (tracciabili ed eliminabili)
Mantenere se: MdC del prodotto > CF specifici eliminabili
```

### Risorse scarse (vincoli di capacità)
**Un solo vincolo**:
```
Priorità = MdC unitario / Consumo fattore scarso per unità
```
Si produce nell'ordine decrescente di questa priorità fino a esaurimento capacità.

**Vincoli multipli**: si usa la **programmazione lineare** (metodo grafico o Simplex) — funzione obiettivo max MdC totale soggetta ai vincoli di capacità.

---

## 6. DECISIONI DI PRODUZIONE

### Make or Buy
```
Confronto: Costi eliminabili del "make" vs Costo di acquisto esterno
Esternalizzare se: Costo acquisto < Costi eliminabili produzione interna
```
Considerare anche:
- **Costo opportunità**: se la capacità liberata può essere usata per attività redditizie
- Fattori qualitativi: qualità, affidabilità fornitore, flessibilità, know-how

### Costi congiunti e split-off
- **Costi congiunti**: costi sostenuti prima del punto di separazione (split-off) per produrre più prodotti contemporaneamente
- I costi congiunti sono **irrilevanti** per la decisione se lavorare ulteriormente un co-prodotto dopo lo split-off
```
Lavorare ulteriormente se:
Ricavo incrementale post-split-off > Costo incrementale post-split-off
```

---

## 7. MASTER BUDGET

Il master budget è il piano economico-finanziario complessivo dell'azienda per un periodo futuro.

### Sequenza dei budget operativi
1. **Budget delle vendite** → punto di partenza (driver della pianificazione)
2. **Budget della produzione** = Vendite previste + RF PF desiderate − RI PF
3. **Budget acquisto materiali** = Fabbisogno produzione + RF MP − RI MP
4. **Budget MOD** = Ore necessarie × Costo orario
5. **Budget CGP (Costi Generali di Produzione)** = CGP fissi + CGP variabili
6. **Budget costo del venduto** = RI PF + Costo produzione − RF PF
7. **Budget costi commerciali e amministrativi**
8. **Conto Economico Preventivo**
9. **Budget di cassa** (incassi/pagamenti)
10. **Stato Patrimoniale Preventivo**

### Budget di cassa
```
Saldo finale = Saldo iniziale + Incassi − Pagamenti
Se Saldo < minimo → necessità finanziamento
Se Saldo > soglia → investimento eccedenze
```

---

## 8. BUDGET FLESSIBILI E COSTI STANDARD

### Budget Flessibile
A differenza del master budget (statico, basato su un solo volume), il budget flessibile **ricalcola i costi al volume effettivo**:
```
Budget flessibile = CF programmati + (CV unitario standard × Volume effettivo)
```

### Costi Standard
- **Standard ideali**: condizioni perfette (irraggiungibili)
- **Standard attualmente raggiungibili**: efficienza elevata ma realistica (motivanti)
- **Standard storici**: basati su dati passati (comodi ma non stimolanti)

---

## 9. ANALISI DEGLI SCOSTAMENTI

### Scostamenti dei costi diretti (MP, MOD)
```
Scostamento di Prezzo: ΔP = (P_eff − P_std) × Q_eff
Scostamento di Efficienza: ΔE = (Q_eff − Q_std×V_eff) × P_std
Scostamento totale (Budget Flessibile): ΔBdgFlex = ΔP + ΔE
```

### Scostamenti dei costi indiretti variabili (CIV)
```
Scostamento di Tariffa: ΔS = CIV_eff − (Q_eff × P_std)
Scostamento di Efficienza: ΔE = [Q_eff − (Q_std × V_eff)] × P_std
ΔBdgFlex = ΔS + ΔE
```

### Scostamenti dei CIF (costi indiretti fissi) — Sistema a Costo Pieno
```
Scostamento di Spesa: ΔS = CIFP − CIFE  (CIF programmati − CIF effettivi)
Scostamento di Volume: ΔV = CIFA − CIFP  (CIF allocati − CIF programmati)
  oppure: ΔV = (V_eff − V_progr) × CAP_CIF
ΔAssorbimento = CIFA − CIFE = ΔSpesa + ΔVolume
```

### Interpretazione scostamenti
- **Favorevole (F)**: costi effettivi < costi standard/programmati
- **Sfavorevole (S)**: costi effettivi > costi standard/programmati

### Scostamento volume di vendita
```
ΔVolume vendita = (Volume eff. − Volume budget) × MdC unitario std
```

### Scostamento di mix
```
ΔMix = Σ [(Mix% eff_i − Mix% budget_i) × Volume tot eff × MdC unitario std_i]
```

---

## 10. SISTEMI DI CONTROLLO DI GESTIONE

### Centri di Responsabilità
| Tipo | Responsabilità | Misura chiave |
|---|---|---|
| **Centro di Costo** | Solo costi | Scostamento costi vs budget |
| **Centro di Ricavo** | Solo ricavi | Scostamento ricavi vs budget |
| **Centro di Profitto** | Ricavi e costi | Margine / RO della divisione |
| **Centro di Investimento** | Ricavi, costi e capitale investito | ROI, EVA |

### Prezzi di trasferimento
- **Costo pieno**: semplice ma può generare decisioni sub-ottimali
- **Costo pieno + mark-up**: simula un prezzo di mercato
- **Prezzo di mercato**: ideale se esiste un mercato esterno attivo
- **Prezzo negoziato**: flessibile ma potenzialmente conflittuale

---

## 11. BALANCED SCORECARD (BSC)

Modello di Kaplan e Norton — misura la performance lungo 4 prospettive integrate:

### Le 4 Prospettive
1. **Prospettiva Finanziaria**: ROI, EVA, crescita ricavi, riduzione costi
2. **Prospettiva del Cliente**: soddisfazione, fidelizzazione, quota di mercato, acquisizione clienti
3. **Prospettiva dei Processi Interni**: efficienza operativa, innovazione, qualità, time-to-market
4. **Prospettiva di Apprendimento e Crescita**: formazione, competenze, sistemi informativi, clima aziendale

### Mappa Strategica
Collega le 4 prospettive con relazioni causa-effetto: investimenti in formazione → processi migliori → clienti soddisfatti → risultati finanziari.

### Sustainability BSC
Tre interpretazioni:
- **BSC originale modificata**: sostenibilità integrata nella prospettiva dei processi interni
- **BSC Integrata**: CSR/ESG pervade tutte le prospettive (complementarità business-sostenibilità)
- **BSC Adattiva**: quinta prospettiva "non-market" dedicata alla sostenibilità

---

## 12. IMPRESE DECENTRALIZZATE — ROI, EVA, VNC vs VLC

### ROI (Return on Investment)
```
ROI = RO / CI = ROS × Asset Turnover
dove:
  ROS = RO / Ricavi (redditività delle vendite)
  Asset Turnover = Ricavi / CI (rotazione del capitale)
```

### EVA (Economic Value Added)
```
EVA = RO rettificato (netto imposte) − Costo del Capitale × CI
```
Il ROI è un indicatore relativo (%), l'EVA è assoluto (€) — il ROI può indurre a rifiutare investimenti con ROI > costo del capitale ma < ROI attuale della divisione.

### Valore Netto Contabile (VNC) vs Valore Lordo Contabile (VLC)
```
VNC = Costo storico − Ammortamento accumulato
VLC = Costo storico (lordo dell'ammortamento)
```
- **VNC**: ROI crescente nel tempo (effetto ammortamento) → rischio di non sostituire asset
- **VLC**: ROI costante nel tempo → favorisce rinnovo tecnologico

---

## 13. ESG E REPORTING DI SOSTENIBILITÀ

- **CSR**: integrazione volontaria di dimensioni sociali e ambientali nelle operazioni aziendali
- **Criteri ESG**: Environmental, Social, Governance — crescente rilevanza nei rating e nelle decisioni di investimento
- **Framework**: GRI (Global Reporting Initiative), IIRC (reporting integrato), bilancio ambientale, bilancio sociale
- **Direttiva UE 2014/95**: obbliga le grandi imprese a rendicontare indicatori sociali e ambientali
- **Agenda 2030**: 17 SDGs dell'ONU

---

## 14. ALLOCAZIONE DEI COSTI

### Metodi di allocazione dai centri di servizio ai reparti operativi

**Metodo Diretto**: i costi dei centri di servizio sono allocati direttamente ai reparti operativi, ignorando le interazioni tra centri di servizio.

**Metodo Sequenziale (a cascata)**: i centri di servizio vengono allocati uno alla volta in ordine di importanza; il centro allocato per primo distribuisce anche ai centri di servizio successivi, ma il metodo è unidirezionale.

### Allocazione con coefficienti multipli
- **Costi variabili**: allocati a tariffa di budget × utilizzo effettivo
- **Costi fissi**: allocati in proporzione alla capacità di picco richiesta dal reparto operativo

---

## 15. VALORI NORMALIZZATI E DELTA ASSORBIMENTO

### Sistema a valori normalizzati (CAP)
```
CAP = CI (FIX + VAR) programmati / Base di allocazione programmata
CI allocati = CAP × Base di allocazione effettiva
```

### Delta Assorbimento
```
ΔAssorbimento = CI Assorbiti (allocati via CAP) − CI Effettivi
```
- **Sovra-assorbimento** (CI assorbiti > CI effettivi): riduzione del CdV
- **Sotto-assorbimento** (CI assorbiti < CI effettivi): incremento del CdV

### Trattamento contabile del ΔAssorbimento
- **Storno immediato**: si imputa integralmente al CdV (quando il Δ è modesto)
- **Distribuzione proporzionale**: si ripartisce pro-quota tra Magazzino SL, Magazzino PF e CdV (quando il Δ è elevato)

### Costo Pieno vs Costo Variabile
| Aspetto | Costo Pieno | Costo Variabile |
|---|---|---|
| CIF produzione | Costo di prodotto (inventariato a SP) | Costo di periodo (spesato a CE) |
| Finalità | Comunicazione istituzionale | Reporting interno |
| Effetto volume produzione su RO | Sì (ΔVolume) | No |
| Orientamento | Produzione | Vendite |

```
ΔRO tra i due sistemi = (RF PF − RI PF) × CAP_CIF
```

---

## 16. JOB COSTING E PROCESS COSTING

### Job Costing (Misurazione su commessa)
- Per prodotti unici o piccole serie (edilizia, aeronautico, arredamento)
- **Consuntivo di commessa**: accumula MP + MOD + CIPA per ogni commessa
- CIPA = CAP × Driver effettivo della commessa
- Scritture contabili: contabilità analitica (mastrini per commessa) + contabilità generale

### Process Costing (Misurazione per processo)
- Per prodotti omogenei in grande quantità (petrolio, cemento, vernice)
- Costo unitario = Costi totali del processo / Unità prodotte
- Metodo di accumulazione per reparto o fase tecnologica

---

## FORMULE RIEPILOGATIVE

### Analisi CVR
```
MdC_u = P − CV_u
BEP_Q = CF / MdC_u
BEP_FATT = CF / MdC%
GLO = MdC / RO
```

### Scostamenti costi diretti
```
ΔPrezzo = (P_eff − P_std) × Q_eff
ΔEfficienza = (Q_eff − Q_std × V_eff) × P_std
```

### Scostamenti CIF (costo pieno)
```
ΔSpesa = CIFP − CIFE
ΔVolume = (V_eff − V_progr) × CAP_CIF
ΔAssorbimento = ΔSpesa + ΔVolume
```

### Performance divisionale
```
ROI = RO/CI = ROS × Asset Turnover
EVA = RO_netto − WACC × CI
ΔRO (CP vs CV) = (RF_PF − RI_PF) × CAP_CIF
```
