# Checklist Compilazione RT — Dati Necessari per la Relazione Tecnica

Questa checklist va compilata e presentata all'utente PRIMA di iniziare la redazione di qualsiasi documento. Per ciascun dato indicare: valore trovato, sorgente, e eventuali discordanze.

---

## Sezione 1 — Dati Identificativi Impianto

| # | Dato | Sorgente primaria | Fallback | Valore | Stato |
|---|------|-------------------|----------|--------|-------|
| 1 | Codice sito | Scheda Radio | Preesistenza | | ☐ |
| 2 | Nome sito | Scheda Radio | Preesistenza | | ☐ |
| 3 | Indirizzo (via, n. civico) | Preesistenza | PE → Scheda Radio | | ☐ |
| 4 | Comune | Preesistenza | PE | | ☐ |
| 5 | Municipio (solo Roma) | Preesistenza | Verifica web | | ☐ |
| 6 | Dati catastali — Foglio | Preesistenza | PE | | ☐ |
| 7 | Dati catastali — Particella | Preesistenza | PE | | ☐ |
| 8 | Dati catastali — Sezione | Preesistenza | PE | | ☐ |
| 9 | Coordinate WGS84 — Lat N | Scheda Radio | PE | | ☐ |
| 10 | Coordinate WGS84 — Long E | Scheda Radio | PE | | ☐ |
| 11 | Quota s.l.m. (m) | PE | Scheda Radio | | ☐ |
| 12 | Tipo sito (RT/RL/Palo su ed.) | PE | Preesistenza | | ☐ |
| 13 | Proprietà infrastruttura | Preesistenza | Utente | | ☐ |

---

## Sezione 2 — Dati Urbanistici (PRG Roma)

**ATTENZIONE: le tavole PRG variano per zona della città. Non copiare ciecamente dalla preesistenza se il sito è in zona diversa. Verificare SEMPRE tramite WebGIS Roma o ricerca online.**

| # | Dato | Sorgente primaria | Fallback | Valore | Stato |
|---|------|-------------------|----------|--------|-------|
| 14 | Sistemi e regole (Tav. 3_10) | Verifica web PRG Roma | Preesistenza (se stessa zona) | | ☐ |
| 15 | Rete ecologica (Tav. 4_10) | Verifica web PRG Roma | Preesistenza (se stessa zona) | | ☐ |
| 16 | Carta per la qualità (Tav. G1_10) | Verifica web PRG Roma | Preesistenza (se stessa zona) | | ☐ |

---

## Sezione 3 — Dati Paesaggistici (PTPR Lazio)

| # | Dato | Sorgente primaria | Fallback | Valore | Stato |
|---|------|-------------------|----------|--------|-------|
| 17 | Sistemi ed ambiti paesaggio (Tav. A) | Verifica web PTPR | Preesistenza | | ☐ |
| 18 | Beni paesaggistici (Tav. B) | Verifica web PTPR | Preesistenza | | ☐ |
| 19 | Beni culturali (Tav. C) | Verifica web PTPR | Preesistenza | | ☐ |

---

## Sezione 4 — Vincoli e Legittimità

**REGOLA CRITICA: vincoli e wording legittimità vanno presi ESCLUSIVAMENTE dalla preesistenza. Se non c'è preesistenza, chiedere esplicitamente all'utente.**

| # | Dato | Sorgente | Valore | Stato |
|---|------|----------|--------|-------|
| 20 | Vincolo paesaggistico D.Lgs. 42/2004 | SOLO preesistenza | | ☐ |
| 21 | Vincolo monumentale | SOLO preesistenza | | ☐ |
| 22 | Altri vincoli (idrogeologico, SIC, ZPS) | SOLO preesistenza | | ☐ |
| 23 | Wording legittimità impianto (testo esatto) | SOLO preesistenza | | ☐ |

---

## Sezione 5 — Dati Tecnici Radio

| # | Dato | Sorgente primaria | Fallback | Valore | Stato |
|---|------|-------------------|----------|--------|-------|
| 24 | Sistema radiomobile | Scheda Radio | FILETX.xlsx | | ☐ |
| 25 | Numero settori | Scheda Radio | FILETX.xlsx | | ☐ |
| 26 | Frequenze per settore | Scheda Radio | FILETX.xlsx | | ☐ |
| 27 | Potenza EIRP per frequenza | FILETX.xlsx | Scheda Radio | | ☐ |
| 28 | Azimuth per settore | Scheda Radio | FILETX.xlsx | | ☐ |
| 29 | Tilt (meccanico + elettrico) | Scheda Radio | FILETX.xlsx | | ☐ |
| 30 | Tipo antenna per settore | Scheda Radio | Datasheet | | ☐ |
| 31 | Altezza antenna dal suolo (m) | PE | Scheda Radio | | ☐ |
| 32 | α24h | FILETX.xlsx | Utente | | ☐ |

---

## Sezione 6 — Dati Progetto e Zona Sismica

| # | Dato | Sorgente primaria | Fallback | Valore | Stato |
|---|------|-------------------|----------|--------|-------|
| 33 | Zona sismica | PE (relazione strutturale) | Preesistenza | | ☐ |
| 34 | Descrizione supporto (edificio/palo/traliccio) | PE | Sopralluogo | | ☐ |
| 35 | Altezza edificio (se RT) | PE | Utente | | ☐ |
| 36 | N. piani edificio (se RT) | PE | Utente | | ☐ |

---

## Sezione 7 — Dati Procedurali

| # | Dato | Sorgente | Valore | Stato |
|---|------|----------|--------|-------|
| 37 | Data redazione | Utente | | ☐ |
| 38 | Tecnico incaricato | Utente | | ☐ |
| 39 | Tipologia intervento (nuovo/modifica) | Preesistenza / Utente | | ☐ |

---

## Regole di Compilazione

1. **Stato ☐** → da compilare. Aggiornare a ✅ (trovato), ❌ (non trovato), ⚠️ (discordanza)
2. **Se discordanza** tra sorgenti → riportare entrambi i valori e chiedere all'utente
3. **Se dato non trovato** in nessuna sorgente → segnare ❌ e indicare `[DA COMPILARE — richiede: ...]`
4. **Tavole PRG**: NON copiare dalla preesistenza se non si è certi che il sito ricade nella stessa zona — le tavole del PRG Roma sono divise in quadranti (es. Tav. 3_10, 3_11, 3_12...) e cambiano per zona
5. **Vincoli**: SOLO dalla preesistenza. Se la preesistenza non è disponibile, i vincoli NON vanno assunti
6. **Wording legittimità**: copiare LETTERALMENTE dalla preesistenza, inclusi errori di battitura e formattazione originale
