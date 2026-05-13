# Template Cruscotto XLSX — HostBoost

Struttura del cruscotto Excel consegnato al cliente. File operativo pensato per essere tenuto vivo dal titolare (o da chi tiene la contabilita) mese per mese. Generato via skill `xlsx`.

## Impostazione generale

- Formato: XLSX 2016+, compatibile Excel, Google Sheets, LibreOffice
- Dimensione pagina logica: A3 landscape per stampa eventuale
- Font default: Calibri 10 pt
- Riga intestazione: bold, sfondo `1F3864`, testo bianco, freeze pane
- Colori semaforo: verde `C6EFCE` / giallo `FFEB9C` / rosso `FFC7CE` (sfondi) con testo `006100` / `9C5700` / `9C0006`
- Formule vive ovunque possibile. Nessun valore hardcoded nelle celle di calcolo.

## Struttura a 5 tab

### Tab 1 — KPI Storici

Foglio contabile con 24 mesi (n-1 + n). Input mensile dell'utente sulle colonne grigie, calcolo automatico sulle colonne bianche.

Colonne:
| Colonna | Tipo | Fonte |
|---|---|---|
| A. Mese | testo (YYYY-MM) | input utente |
| B. Giorni apertura | num intero | input utente |
| C. Camere totali | num intero | input utente, tipicamente costante |
| D. Notti disponibili | formula `=B*C` | calcolo |
| E. Notti vendute | num intero | input utente |
| F. Ricavi camera (EUR) | num | input utente |
| G. ADR | formula `=IF(E>0,F/E,0)` | calcolo |
| H. Occupancy | formula `=IF(D>0,E/D,0)` formato % | calcolo |
| I. RevPAR | formula `=IF(D>0,F/D,0)` | calcolo |
| J. ADR YoY | formula `=IFERROR(G/INDEX(G:G,ROW()-12)-1,"")` formato % | calcolo |
| K. Occ YoY | formula simile | calcolo |
| L. RevPAR YoY | formula simile | calcolo |
| M. Ricavi F&B | num (opzionale) | input |
| N. Ricavi altri | num (opzionale) | input |
| O. TRevPAR | formula `=(F+M+N)/D` | calcolo |
| P. N. prenotazioni | num | input |
| Q. ALOS | formula `=IF(P>0,E/P,0)` | calcolo |
| R. Cancellazioni | num | input |
| S. Cancellation rate | formula `=IF(P+R>0,R/(P+R),0)` | calcolo |
| T. Semaforo Occupancy vs benchmark | formula `=IF(H>=$benchmark_high,"🟢",IF(H>=$benchmark_mid,"🟡","🔴"))` | calcolo |
| U. Semaforo RevPAR vs benchmark | formula simile | calcolo |

In fondo riga 27 con riepilogo annuale: somma notti, somma ricavi, ADR medio ponderato, Occupancy media ponderata, RevPAR annuale.

Grafico incorporato:
- Grafico 1: Linee RevPAR mensile n-1 e n sovrapposti, per visualizzare crescita o calo
- Grafico 2: Barre Occupancy mensile
- Grafico 3: Linee ADR mensile

### Tab 2 — Calendario Pricing 12 mesi

365 righe, una per giorno. Output del motore di pricing. Input manuale da parte del titolare per affinare.

Colonne:
| Colonna | Tipo | Contenuto |
|---|---|---|
| A. Data | data | 365 date future |
| B. Giorno settimana | formula `=TEXT(A,"ddd")` | calcolo |
| C. Fascia stagionale | testo | lookup tabella stagioni (alta/media/bassa/spalla) |
| D. DBI | num 0-10 | output motore |
| E. Evento | testo | lookup calendario eventi zona (Pasqua, ponti, fiere locali) |
| F. BAR suggerita base | num | output motore |
| G. BAR suggerita ottimistica | num | output motore +10-15% |
| H. BAR effettiva (input) | num | input utente, default uguale a F |
| I. Minimum stay | num (1-4) | lookup tabella stagione+giorno settimana |
| J. Non rimborsabile (da F) | formula `=H*0.93` | calcolo |
| K. Early booking | formula `=H*0.88` | calcolo |
| L. Note | testo libero | input |
| M. Semaforo scostamento | formula confronto H vs F | calcolo |

Formattazione condizionale:
- Colonna D (DBI) con scala colore da blu chiaro (0) a rosso (10)
- Colonna I con colore per minimum stay: 1=bianco, 2=verde chiaro, 3=giallo, 4=arancio

Grafico:
- Linea BAR mensile media su 12 mesi
- Heatmap 52 settimane x 7 giorni con DBI

### Tab 3 — Competitive Set

Confronto prezzi vs compset su 20 date campione. Input: 3-5 compset. Output: posizione relativa.

Colonne:
| Colonna | Tipo | Contenuto |
|---|---|---|
| A. Data campione | data | 20 date distribuite stagionalmente |
| B. BAR cliente | num | da tab 2 |
| C. BAR Compset 1 | num | input (scraping o manuale) |
| D. BAR Compset 2 | num | input |
| E. BAR Compset 3 | num | input |
| F. BAR Compset 4 | num | input (opzionale) |
| G. BAR Compset 5 | num | input (opzionale) |
| H. Mediana compset | formula `=MEDIAN(C:G)` | calcolo |
| I. Delta cliente vs mediana | formula `=B-H` | calcolo |
| J. Delta % | formula `=B/H-1` formato % | calcolo |
| K. Posizione | formula `=RANK(B,B:G)/COUNT(B:G)` | calcolo |
| L. Semaforo posizionamento | formula basata su J: -20%/-5% giallo, -5%/+5% verde, +5%/+20% giallo, fuori rosso | calcolo |

In alto riga con dati compset (nome, rating Booking, stelle, indirizzo). In basso riepilogo: prezzo medio cliente vs mediana compset, posizione media.

Grafico:
- Scatter cliente vs compset con diagonale di parita
- Barre confronto date selezionate

### Tab 4 — Recensioni Theme Analysis

Analisi ricorrenze temi dalle ultime 50 recensioni. Semi-manuale: titolare incolla recensioni, skill estrae temi.

Sezione A — Rating per piattaforma (righe 1-8):
| Piattaforma | Rating attuale | Rating YoY | Numero recensioni | Target | Semaforo |
|---|---|---|---|---|---|
| Booking.com | input | input | input | 9.0 | formula |
| TripAdvisor | input | input | input | 4.5 | formula |
| Google | input | input | input | 4.7 | formula |
| Airbnb | input | input | input | 4.8 | formula |

Sezione B — Top temi positivi (righe 10-20):
| Tema | Frequenza % | Esempi citazioni |
|---|---|---|
| Colazione | input | input (2-3 brevi) |
| Posizione | input | input |
| Pulizia | input | input |
| Accoglienza | input | input |
| Camera | input | input |

Sezione C — Top temi negativi (righe 22-32):
Stessa struttura della B.

Sezione D — Risposte alle recensioni:
| Metrica | Valore | Target | Semaforo |
|---|---|---|---|
| Response rate | % | 90% | formula |
| Response time mediano | giorni | < 2 | formula |
| Ultima risposta data | data | - | - |

Grafico:
- Barre orizzontali top 5 temi positivi e 5 negativi con frequenza
- Gauge rating per piattaforma

### Tab 5 — Piano Azioni 12 mesi

Le 5 azioni prioritarie in formato GANTT semplificato.

Colonne:
| Colonna | Tipo | Contenuto |
|---|---|---|
| A. Priorita | num 1-5 | input |
| B. Azione | testo | input |
| C. Categoria | dropdown | [Pricing / Canali / Prodotto / Reputation / Marketing] |
| D. Impatto stimato RevPAR | % | input |
| E. Fattibilita | dropdown | [Alta / Media / Bassa] |
| F. Costo una tantum (EUR) | num | input |
| G. Costo ricorrente (EUR/mese) | num | input |
| H. Tempo implementazione (settimane) | num | input |
| I. Data inizio | data | input |
| J. Data fine | formula `=I+H*7` | calcolo |
| K. Responsabile | testo | input |
| L. Stato | dropdown | [Non iniziato / In corso / Completato / Bloccato] |
| M-X. Barre GANTT mensili | formula condizionale: 1 se mese tra I e J, 0 altrimenti | calcolo |

Sezione B — Proiezione impatto cumulato:
| Azione | Delta RevPAR singolo | Delta RevPAR cumulato | Ricavi addizionali annui |
|---|---|---|---|
| Azione 1 | % | formula | EUR |
| Azione 2 | % | formula | EUR |
| ... | | | |

Grafico:
- GANTT mensili orizzontali colorati per categoria
- Barre cumulative impatto RevPAR

## Istruzioni d'uso incorporate

Prima riga di ogni tab con nota gialla:
- Tab 1: "Aggiorna questa tabella a fine mese. Inserisci solo dati nelle colonne grigie."
- Tab 2: "Modifica la colonna H (BAR effettiva) per derogare dal suggerimento. Le altre colonne si aggiornano."
- Tab 3: "Aggiorna una volta al mese i prezzi compset. Usa scraping o osservazione diretta su Booking.com."
- Tab 4: "Compila ogni trimestre. Aggiorna dopo almeno 20 nuove recensioni."
- Tab 5: "Rivedi ogni mese. Cambia lo stato e aggiungi commenti nella colonna note."

## Protezione fogli

Tab 1-5: sbloccare solo colonne di input (grigie), proteggere colonne calcolo (bianche con formule) senza password — solo per evitare cancellazioni accidentali, non per sicurezza.

## Grafici e validazioni

Usare grafici Excel nativi (bar, line, scatter, pie) dove supportato. Per grafici complessi (heatmap) generare PNG pre-calcolato in Python/matplotlib e incorporare come immagine.

Validazioni dati:
- Date valide solo (nessun testo)
- Numeri positivi sui KPI
- Dropdown su colonne con valori ammessi
- Condizionale per evitare divisioni per zero con IFERROR
