# Template Simulatore Benefici XLSX — AgevolazioniBoost

## Struttura del file Excel

Il simulatore è un file `.xlsx` con **5 tab** interconnesse da formule. Il titolare può modificare i dati di input (celle gialle) e vedere immediatamente l'impatto sui benefici stimati.

---

## TAB 1 — INPUT

**Sezione A: Profilo Aziendale**

| Campo | Valore | Note |
|---|---|---|
| Ragione sociale | [input] | |
| Codice Fiscale | [input] | Per ricerca RNA |
| Settore ATECO | [input] | Codice + descrizione |
| Regione | [input] | Sede operativa |
| Dimensione | [dropdown: micro/piccola/media] | Parametri UE |
| Dipendenti | [input numerico] | |
| Fatturato ultimo anno (EUR) | [input numerico] | |
| Totale attivo (EUR) | [input numerico] | |
| Forma giuridica | [dropdown] | SRL/SPA/SNC/ditta individuale/ecc. |
| Startup innovativa | [dropdown: SI/NO] | |
| PMI innovativa | [dropdown: SI/NO] | |
| Zona speciale | [dropdown: Nessuna/ZES/Area interna/Cratere sisma] | |

**Sezione B: Investimenti Pianificati**

| # | Tipo investimento | Importo stimato (EUR) | Anno previsto | Note |
|---|---|---|---|---|
| 1 | [dropdown tipologia] | [input] | [input] | |
| 2 | | | | |
| 3 | | | | |
| 4 | | | | |
| 5 | | | | |

Dropdown tipologie investimento: Beni strumentali 4.0 / Beni strumentali ordinari / Software e digitalizzazione / Ricerca e sviluppo / Innovazione tecnologica / Design / Internazionalizzazione / Assunzioni / Formazione 4.0 / Efficienza energetica / Brevettazione e IP

**Sezione C: De Minimis**

| Campo | Valore | Formula |
|---|---|---|
| De minimis consumato esercizio N-2 (EUR) | [input] | |
| De minimis consumato esercizio N-1 (EUR) | [input] | |
| De minimis consumato esercizio N (EUR) | [input] | |
| **Totale consumato (EUR)** | | =SOMMA(C2:C4) |
| **Soglia massima (EUR)** | 300.000 | fisso |
| **De minimis residuo (EUR)** | | =C6-C5 |
| **Spazio disponibile (%)** | | =C7/C6 |

---

## TAB 2 — STRUMENTI

Tabella di tutti gli strumenti agevolativi valutati, con scoring e stato.

| ID | Strumento | Tipo | Riferimento normativo | Stato | Requisiti soddisfatti | Score priorità (1-5) | Score valore (1-5) | Score accessibilità (1-5) | Score urgenza (1-5) | Score complessivo | Incluso nel piano |
|---|---|---|---|---|---|---|---|---|---|---|---|
| T5 | Transizione 5.0 | Tax credit | Art. 38 D.L. 19/2024 | [aperto/chiuso] | [SI/NO/PARZIALE] | [1-5] | [1-5] | [1-5] | [1-5] | =MEDIA(...) | [SI/NO] |
| SAB | Nuova Sabatini | Contrib. interessi | L. 134/2012 | | | | | | | | |
| SAB-G | Sabatini Green | Contrib. interessi | L. 134/2012 | | | | | | | | |
| SAB-S | Sabatini Sud | Contrib. interessi | L. 134/2012 | | | | | | | | |
| MCC | Fondo Garanzia MCC | Garanzia | L. 662/1996 | | | | | | | | |
| SIM | SIMEST Fondo 394 | Fin. agevolato + FP | D.Lgs. 143/1998 | | | | | | | | |
| RS | Tax credit R&S | Tax credit | L. 160/2019 | | | | | | | | |
| IT | Tax credit Innovazione | Tax credit | L. 160/2019 | | | | | | | | |
| DES | Tax credit Design | Tax credit | L. 160/2019 | | | | | | | | |
| ZES | ZES Unica Mezzogiorno | Tax credit | D.L. 124/2023 | | | | | | | | |
| DEC | Decontribuzione assunzioni | Bonus | INPS | | | | | | | | |
| FOR | Tax credit Formazione 4.0 | Tax credit | L. 205/2017 | | | | | | | | |
| BRE | Brevetti+ | Fondo perduto | D.M. UIBM | | | | | | | | |
| REG | Bando regionale | [tipo] | [riferimento] | | | | | | | | |

**Formattazione condizionale consigliata:**
- Stato "aperto" → cella verde
- Stato "chiuso" → cella rossa
- Stato "in attesa riapertura" → cella gialla
- Score complessivo ≥ 4 → grassetto evidenziato
- Requisiti "PARZIALE" → cella arancione

---

## TAB 3 — BENEFICI

Per ogni strumento incluso nel piano (Incluso = SI in TAB 2), calcolo dei benefici nei 3 scenari.

**Intestazione:**
- Azienda: [link a TAB 1]
- Data elaborazione: [oggi]
- Avvertenza: "Stime soggette a istruttoria — verificare con professionista abilitato"

**Tabella benefici per strumento:**

| Strumento | Spesa agevolabile (EUR) | Aliquota / intensità (%) | Beneficio lordo (EUR) | Costi gestione stimati (EUR) | Carico fiscale stimato (EUR) | Beneficio netto (EUR) | Timing (mesi) | Scenario base | Scenario ottimistico | Scenario massimo |
|---|---|---|---|---|---|---|---|---|---|---|
| [nome] | [input o link a TAB1] | [input] | =C*D/100 | [input %] | [input %] | =E-F-G | [input] | [formula] | [formula] | [formula] |

**Totali:**

| | Scenario base | Scenario ottimistico | Scenario massimo |
|---|---|---|---|
| **Totale benefici lordi (EUR)** | =SOMMA(...) | =SOMMA(...) | =SOMMA(...) |
| **Totale benefici netti (EUR)** | =SOMMA(...) | =SOMMA(...) | =SOMMA(...) |
| **% su investimento totale** | =B2/TOTINV | =C2/TOTINV | =D2/TOTINV |

**Note ipotesi scenari:**
- **Base**: solo strumenti con requisiti pienamente soddisfatti, aliquote minime, bandi aperti
- **Ottimistico**: include strumenti parzialmente soddisfatti, aliquote medie, considera riaperture attese
- **Massimo**: cumulo massimo consentito, aliquote massime, tutti i bandi attivabili

---

## TAB 4 — ROADMAP

Calendario delle azioni su 24 mesi con indicatore urgenza.

**Colonne:**
| Mese | Anno | Strumento | Azione | Responsabile | Urgenza | Scadenza | Stato | Note |

**Urgenza — formattazione condizionale:**
- ALTA (≤ 30 giorni) → rosso
- MEDIA (31-90 giorni) → giallo/arancione
- BASSA (> 90 giorni) → verde

**Righe pre-compilate (da adattare al piano specifico):**

| Mese | Anno | Strumento | Azione | Responsabile |
|---|---|---|---|---|
| 1 | 2026 | Calcolo de minimis | Consultare RNA + dichiarazione aziendale | Commercialista |
| 1 | 2026 | Fondo Garanzia MCC | Contattare banca per verifica disponibilità | Azienda + banca |
| 1-2 | 2026 | Transizione 5.0 | Raccogliere preventivi beni 4.0, avviare pratica GSE | Azienda + perito |
| 2 | 2026 | Nuova Sabatini | Delibera bancaria (NON ordinare beni prima) | Banca |
| 3 | 2026 | Nuova Sabatini | Acquisto beni post-delibera, conservare fatture | Azienda |
| 4 | 2026 | SIMEST | Monitorare apertura sportello, preparare doc | Azienda |
| 6 | 2026 | Tax credit R&S/Inn. | Verifica perizia asseverata, preparare quaderno | Commercialista + perito |
| 12 | 2026 | Transizione 5.0 | Rendicontazione finale GSE | Azienda + perito |
| 12 | 2026 | Decontribuzione | Verifica adempimenti INPS, riconciliazione F24 | Consulente lavoro |

**GANTT semplificato:**
Utilizzare la funzione grafico a barre di Gantt di Excel (o barre condizionali) per visualizzare la timeline di ogni strumento su 24 mesi:
- Colonne mese 1-24
- Riga per ogni strumento
- Cella colorata = attività in quel mese
- Colore: rosso = scadenza/azione critica, giallo = attività in corso, verde = completato

---

## TAB 5 — DE MINIMIS TRACKER

Registro degli aiuti de minimis ricevuti e calcolo dello spazio residuo.

**Sezione A: Aiuti ricevuti (da RNA + dichiarazione azienda)**

| # | Strumento / Ente | Data concessione | Importo nominale (EUR) | Tipo calcolo ESL | ESL (EUR) | Esercizio fiscale | Regime | In scadenza? | Note |
|---|---|---|---|---|---|---|---|---|---|
| 1 | | | | [dropdown: FP/Finanz./Garanzia] | | | [dropdown: de minimis/GBER/altro] | =SE(anno<ANNO()-2,"SI","NO") | |

**Formule automatiche:**

| Campo | Formula |
|---|---|
| Totale ESL esercizio N-2 | =SOMMA.SE(G:G, ANNO()-2, F:F) |
| Totale ESL esercizio N-1 | =SOMMA.SE(G:G, ANNO()-1, F:F) |
| Totale ESL esercizio N | =SOMMA.SE(G:G, ANNO(), F:F) |
| **TOTALE CONSUMATO** | =SOMMA degli ultimi 3 |
| **DE MINIMIS RESIDUO** | =300.000 - TOTALE CONSUMATO |
| **SEMAFORO** | =SE(RESIDUO>150000,"VERDE",SE(RESIDUO>50000,"GIALLO","ROSSO")) |

**Sezione B: Agevolazioni pianificate (impatto de minimis)**

| Strumento | Importo agevolazione (EUR) | Regime | Conta su de minimis? | Impatto de minimis (EUR) | Post-agevolazione residuo (EUR) |
|---|---|---|---|---|---|
| Transizione 5.0 | | GBER | NO | 0 | = residuo attuale |
| Nuova Sabatini | | de minimis | SI | = importo | = residuo - importo |
| Brevetti+ | | de minimis | SI | = importo | |

---

## Note operative per la skill

Quando invochi la skill `xlsx` per generare questo simulatore:

1. Usa `openpyxl` in Python — è la libreria standard nel sistema K2-AI per la generazione XLSX
2. Applica formattazione condizionale alle celle urgenza (TAB 4) e semaforo (TAB 5)
3. Blocca le righe di intestazione (freeze_panes) su tutte le tab
4. Proteggi le celle con formule (solo celle input/gialle modificabili)
5. Aggiungi uno stile coerente: intestazioni in blu scuro (#003366) con testo bianco, righe alternate grigio chiaro
6. Il file deve essere self-contained — non richiedere macro o connessioni esterne
7. Nome file suggerito: `AgevolazioniBoost_[NomeAzienda]_[AnnoMese].xlsx`
