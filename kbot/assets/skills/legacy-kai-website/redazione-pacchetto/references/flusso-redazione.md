# Flusso di Redazione — Pacchetto Autorizzativo Iliad

## Schema del Flusso Progressivo

```
INPUT INIZIALI                DOCUMENTI GENERABILI           INPUT AGGIUNTIVI
─────────────                 ────────────────────           ────────────────
Codice sito          ──►  1. SCIA art. 45 (bozza)
Nome sito            ──►  2. Delega presentazione
Indirizzo + Municipio──►  4. RT (sezioni base)
Dati catastali       ──►  6. ASSEVERAZIONI (base)
Coordinate           ──►  8. Impegno pagamento ARPA
Data                 ──►  9. DICH. SOSTITUTIVA ALPHA24
Tecnico incaricato   ──►  10. Atto d'obbligo
Sistema radiomobile  ──►

                          + Scheda Radio PDF ──►  6. ASSEVERAZIONI (tecnica completa)
                                              ──►  7. B40 sezioni 5 e 6 (scheda radio)

                          + FILETX.xlsx      ──►  7. B40 sezioni 7 e 8 (calcoli EM)
                                              ──►  6. ASSEVERAZIONI (conformità EM)

                          + Prog. Architettonico ──► 4. RT (stralci PRG/PTPR)
                                                ──► 7. B40 sezioni 4 e 7.2 (foto, planimetrie)

                          + Misure di campo   ──► 7. B40 sezione 7.2 (misure di fondo)

                          + PDM ARPA          ──► Incluso come doc 5 senza modifiche
```

---

## Dipendenze tra Documenti e Dati

### Documenti redazionali con soli dati base

I seguenti documenti si possono redigere **subito** con i dati minimi (codice, nome, indirizzo, catasto, coordinate, data, tecnico):

| Documento | Dati minimi sufficienti | Parti da completare in seguito |
|-----------|------------------------|-------------------------------|
| SCIA art. 45 | Sì | Elenco allegati completo |
| Delega alla presentazione | Sì | — |
| Impegno pagamento ARPA | Sì | — |
| DICH. SOSTITUTIVA ALPHA24 | Sì (ma manca α24h) | Valore α24h (da FILETX) |
| Atto d'obbligo | Sì | — |

### Documenti che richiedono dati aggiuntivi

| Documento | Dati aggiuntivi richiesti |
|-----------|--------------------------|
| RT (completa) | Stralci PRG/PTPR, descrizione sito, tipo intervento |
| ASSEVERAZIONI (conformità PRG) | Destinazione urbanistica del sito |
| B40/RELAIE (sezioni 5-6) | Scheda radio: frequenze, potenze, azimuth, tilt, tipo antenna |
| B40/RELAIE (sezioni 7-8) | FILETX.xlsx con risultati simulazione EM + misure di fondo ARPA |
| B40/RELAIE (sez. 4 e 7.2) | Foto sito, planimetrie, quote edifici circostanti |

---

## Ordine Operativo Consigliato

### Sessione 1 — Con soli dati base
1. Chiedi i dati minimi (codice, nome, indirizzo, catasto, coordinate, data, tecnico, sistema radio)
2. Redigi: SCIA, Delega, Impegno ARPA, DICH. SOSTITUTIVA, Atto d'obbligo
3. Prepara la struttura bozza di RT e ASSEVERAZIONI con `[DA COMPILARE]`
4. Prepara la struttura indice del B40 con tutte le sezioni e `[DA COMPILARE]`

### Sessione 2 — Con Scheda Radio / FILETX
1. Leggi il file PDF della scheda radio o il FILETX.xlsx
2. Estrai: frequenze, potenze EIRP, azimuth, tilt, tipo antenne per ciascun settore
3. Aggiorna la scheda radio nel B40 (sezione 6)
4. Compila le sezioni 5 del B40 (descrizione impianto, caratteristiche antenne)
5. Aggiorna il valore α24h nella DICH. SOSTITUTIVA

### Sessione 3 — Con Progetto Architettonico
1. Leggi le tavole del PE (architettonico)
2. Estrai: foto del sito, planimetrie dell'area, quote edifici, descrizione supporto
3. Aggiorna la sezione 4 del B40 (descrizione area, planimetria, documentazione fotografica)
4. Aggiorna la RT (descrizione dell'intervento, tipo supporto)
5. Aggiorna le ASSEVERAZIONI (stralci PRG/PTPR se inclusi nel PE)

### Sessione 4 — Con Misure di Campo EM
1. Ricevi i risultati del sopralluogo e delle misure ARPA (dal PDM)
2. Compila la sezione 7.2 del B40 (punti di misura, valori di fondo, documentazione fotografica)
3. Integra con i calcoli del FILETX per la sezione 8 (isolinee, volumi di rispetto)
4. Compila le conclusioni (sezione 9) con il giudizio di conformità

---

## Tabella Stato Redazione per Sessione

Usa questa tabella per tracciare lo stato di ogni documento durante la redazione:

| Doc | Titolo | Stato | Dati mancanti |
|-----|--------|-------|---------------|
| 1 | SCIA art. 45 | 🔴 Non iniziato | |
| 2 | Delega presentazione | 🔴 Non iniziato | |
| 3 | MISE-PROCURA | ✅ File fisso PDF | |
| 4 | RT | 🔴 Non iniziato | |
| 5 | PDM | ⏳ Da ricevere da ARPA | |
| 6 | ASSEVERAZIONI | 🔴 Non iniziato | |
| 7 | B40/RELAIE | 🔴 Non iniziato | |
| 8 | Impegno ARPA | 🔴 Non iniziato | |
| 9 | DICH. SOSTITUTIVA | 🔴 Non iniziato | |
| 10 | Atto d'obbligo | 🔴 Non iniziato | |
| 11 | Diagrammi Angolari | ⏳ Da software | |
| 13 | Nulla Osta Cellnex | ⏳ Da Cellnex | |

**Legenda:** 🔴 Non iniziato | 🟡 Bozza parziale | 🟠 Bozza completa da revisionare | ✅ Completato | ⏳ Attesa materiale esterno

---

## Come Leggere i File FILETX.xlsx

Il file FILETX.xlsx è il foglio dati per il software di simulazione del campo EM (RELAIE).

Struttura tipica delle colonne:
- **Settore** (S1, S2, S3 o numerazione analoga)
- **Azimuth** (gradi, 0=Nord)
- **Frequenza** (MHz)
- **Potenza EIRP** (dBm o W o dBW)
- **Tilt** (meccanico + elettrico, gradi)
- **Altezza** (dal suolo, metri)
- **Tipo antenna** (codice o nome commerciale)
- **α24h** (fattore di riduzione)

Quando leggi il file:
1. Organizza i dati per settore
2. Converti le unità se necessario (dBm → W: P_W = 10^((P_dBm - 30)/10))
3. Riporta nella tabella della scheda radio del B40 con le unità di misura appropriate

## Come Leggere la Scheda Radio (PDF B40/TSSR)

Cerca nel PDF:
- La tabella "Caratteristiche dei sistemi di antenna" (sezione 5.2 tipicamente)
- La tabella "Gamme di frequenza" (sezione 5.3)
- La "Scheda radio dell'impianto" (sezione 6)
- Le coordinate del sito (sezione 1)
- Il nome e codice impianto (frontespizio)
