# Checklist Avanzata di Verifica Progetti Terzi — Cellnex

## Come Usare Questa Checklist

Usa questa checklist per ogni progetto ricevuto da fornitori/appaltatori. Compila ogni voce come:
- ✅ CONFORME
- ❌ NON CONFORME (indica la classe: Bloccante / Maggiore / Minore)
- ⚠️ NON VERIFICABILE (indica qual è la documentazione mancante)
- N/A non applicabile al tipo di progetto

---

## A. VERIFICA FORMALE

| ID | Elemento | Riferimento | Verifica |
|----|---------|-------------|---------|
| A1 | Firma e timbro tecnico laureato iscritto all'Albo professionale | DPR 380/2001 | |
| A2 | Paragrafo "Normativa di riferimento" esplicitato nel documento | CNP_TS21_002 §1 | |
| A3 | Data e numero di revisione del documento | — | |
| A4 | Tracciabilità materiali dichiarata | NTC 2018 | |
| A5 | Aderenza alle DGR della Regione | DPR 380/2001 | |

---

## B. PARAMETRI PROGETTUALI CELLNEX

| ID | Parametro | Valore richiesto | Valore nel progetto | Conforme? |
|----|-----------|------------------|---------------------|-----------|
| B1 | Vita nominale | 50 anni | | |
| B2 | Classe d'uso | 2 | | |
| B3 | Vita di riferimento | 100 anni | | |
| B4 | Periodo di ritorno TR | 100 anni | | |
| B5 | Categoria suolo (default) | D (salvo autorizzazione Cellnex) | | |
| B6 | Cp antenne sistemi radianti | ≥ 1,2 | | |
| B7 | Cp parabole/RRU | ≥ 1,3 | | |
| B8 | Tabella coefficienti Cp adottati | Presente in relazione | | |
| B9 | **Zona di vento** — se software WinStrand: verificare Vr numerico, non l'etichetta zona | Vr coerente con NTC 2018 del sito + TR=100 anni (es. Roma: Vr=29,76 m/s) | | |

> **Nota WinStrand:** La numerazione interna delle zone di vento in WinStrand (ENEXSYS) è diversa da quella NTC 2018. "Zona 6 WinStrand" per un sito a Roma (Zona 3 NTC 2018) è corretto se Vr=29,76 m/s. Classificare come **Osservazione** (non NC) e richiedere nota esplicativa in relazione.

---

## C. VERIFICA STATICA STRUTTURE ESISTENTI (se applicabile)

| ID | Elemento | Riferimento | Verifica |
|----|---------|-------------|---------|
| C1 | Livello di Conoscenza (LC1/LC2/LC3) dichiarato e motivato | CNP_TS21_002 §2 | |
| C2 | Fattore di Confidenza FC applicato (1,35/1,20/1,00) | CNP_TS21_002 §2.3 | |
| C3 | Livello di criticità giunti saldati valutato | CNP_TS21_002 §3 | |
| C4 | Report fotografico sopralluogo allegato | CNP_TS21_002 §4 | |
| C5 | Verifica visiva e dimensionale in sito dichiarata | CNP_TS21_002 §4 | |
| C6 | Piano di manutenzione incluso | CNP_TS21_002 §4 | |
| C7 | Condizioni di carico C1 e C2 esplicitate separatamente | CNP_TS21_002 §4.1 | |
| C8 | Tutte le 5 combinazioni di carico presenti (SLU C1, SLU C1+C2, Sismica, SLE C1, SLE C1+C2) | CNP_TS21_002 §4.2 | |
| C9 | SLE con vento costante (non a raffica) | CNP_TS21_002 §4.2 | |
| C10 | Percentuali di sfruttamento per C1 e C1+C2 riportate | CNP_TS21_002 §4.3 | |
| C11 | Incremento di sfruttamento C2 evidenziato | CNP_TS21_002 §4.3 | |
| C12 | Coefficiente dinamico CsCd con procedimento 1, Annex B EN1991-1-4 | CNP_TS21_002 §4.3 | |
| C13 | Verifica deformabilità SLE per C1 e C1+C2 | CNP_TS21_002 §4.3 | |
| C14 | Verifiche a fatica saldature giunti flangia (EN 1993-1-9) | CNP_TS21_002 §4.3 | |
| C15 | Verifica plinto/fondazione (DM 17.01.2018) | CNP_TS21_002 §4.3 | |
| C16 | Verifica vortex shedding (stabilità aero-elastica) | CNP_TS21_002 §4.3 | |
| C17 | Per Roof Top: verifica sottostrutture edificio fino a fondazione | CNP_TS21_002 §4.3 | |
| C18 | Esito dichiarato (idonea/non idonea C1/non idonea C1+C2) | CNP_TS21_002 §4.3 | |

---

## D. STRUTTURE PORTA ANTENNE (se applicabile)

| ID | Elemento | Riferimento | Verifica |
|----|---------|-------------|---------|
| D1 | Deflessione max in sommità ≤ 30' (0,5°) con vento 100 km/h | CNP_TS23_010 §2 | |
| D2 | Superficie equivalente minima ≥ 10 m² in sommità | CNP_TS23_010 §2 | |
| D3 | Acciaio S355J0 per fusto, flange e tirafondi | CNP_TS23_010 §2.1 | |
| D4 | Bulloneria classe 8.8/10.9 zincata a caldo | CNP_TS23_010 §2.1 | |
| D5 | Zincatura ≥ 80 micron | CNP_TS23_010 §2.1 | |
| D6 | Saldature: penetrazione min 80% (100% nelle zone d'incastro) | CNP_TS23_010 §2.1 | |

---

## E. RINFORZI STRUTTURALI (se applicabile)

| ID | Elemento | Riferimento | Verifica |
|----|---------|-------------|---------|
| E1 | Incremento capacità dichiarato (+50%/+30%/+20%) | CNP_TS21_001 §4 | |
| E2 | Calcolo strutturale ante e post intervento entrambi presenti | CNP_TS21_001 §7 | |
| E3 | Dettagli costruttivi per ogni intervento (scala ≥ 1:20) | CNP_TS21_001 §7 | |
| E4 | Tavole esecutive dei rinforzi presenti | CNP_TS21_001 §7 | |

---

## F. IMPIANTI ELETTRICI (se applicabile)

| ID | Elemento | Riferimento | Verifica |
|----|---------|-------------|---------|
| F1 | Tipologia QARMOM 4.0 rispettata | QARMOM 4.0 | |
| F2 | Analisi rischio trasformatore di isolamento eseguita | CNP_TS21_006 | |
| F3 | Impianto terra progettato con R ≤ 50 Ω | CNP_TS21_008 §5.1.7 | |
| F4 | Anello di terra con min 4 pozzetti e dispersori ø20 mm | CNP_TS21_008 §5.1.7 | |
| F5 | Corde ≥ 50 mm² materiale diverso dal rame | CNP_TS21_008 §5.1.7 | |
| F6 | Selettività protezioni garantita | QARMOM 4.0 | |
| F7 | Raggio curvatura cavi coax ≥ 60 cm | CNP_TS21_008 §5.1.5 | |
| F8 | Certificazioni ab-origine dispositivi dichiarate | CNP_TS21_006 §1 | |

---

## G. SICUREZZA (se applicabile)

| ID | Elemento | Riferimento | Verifica |
|----|---------|-------------|---------|
| G1 | PSC redatto se obbligatorio (> 1 impresa esecutrice) | D.Lgs. 81/08 art. 90 | |
| G2 | DUVRI compilato per interferenze con operatori | DUVRI Cellnex Rev.01 | |
| G3 | Costi della sicurezza non soggetti a ribasso indicati | D.Lgs. 81/08 Allegato XV | |
| G4 | Notifica preliminare prevista se necessaria | D.Lgs. 81/08 art. 99 | |

---

## Classificazione Non Conformità

| Classe | Definizione | Azione |
|--------|-------------|--------|
| **NC Bloccante** | Parametro Cellnex obbligatorio non rispettato (TR, Cp, LC errato, FC non applicato) | Stop — revisione obbligatoria prima di qualsiasi approvazione |
| **NC Maggiore** | Contenuto minimo mancante (verifica fatica assente, vortex shedding, analisi rischio trasformatore) | Integrazione obbligatoria prima dell'approvazione |
| **NC Minore** | Aspetto formale o di dettaglio non conforme | Integrazione raccomandata — eventuale accettazione con riserva |
| **Osservazione** | Suggerimento migliorativo non vincolante | Da valutare con il progettista |

## Template Report di Verifica

```
REPORT DI VERIFICA PROGETTO
============================
Documento verificato: [Titolo - Rev. - Data - Estensore]
Tipologia intervento: [Nuovo sito RL / Roof Top / Verifica statica / Rinforzo / ...]
Linee guida applicabili: [CNP_TS21_XXX, ...]
Data verifica: [gg/mm/aaaa]

NON CONFORMITÀ RILEVATE:
| ID | Descrizione | Classe | Rif. Cellnex | Rif. Norma | Azione richiesta |
|----|------------|--------|--------------|------------|------------------|
| ...

GIUDIZIO: [APPROVATO / APPROVATO CON RISERVA / NON APPROVATO — REVISIONE RICHIESTA]

AZIONI RICHIESTE PRIMA DELL'APPROVAZIONE:
1. ...
2. ...
```
