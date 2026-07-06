# Dati del Sito e Dati Fissi — Redazione Pacchetto Iliad

## Dati Fissi Iliad Italia S.p.A. (invarianti)

| Campo | Valore |
|-------|--------|
| Ragione sociale | ILIAD ITALIA S.p.A. a Socio Unico |
| Sede legale | Viale Francesco Restelli 1/A, Milano (MI) 20124 |
| CF e P. IVA | 13970161009 |
| REA | MI-2126511 |
| Registro Imprese | Milano |
| Procuratore speciale | Sig. Andrea Longari, nato a Roma il 27/04/1974 |
| Notaio procura | Dott. Luca AMATO, Notaio in Roma |
| Data procura | 10 aprile 2024 |
| Repertorio procura | n. 63403/18598 |
| Registrazione procura | Agenzia delle Entrate di Roma 5, 10/04/2024, n. 3697 Serie 1T |
| Autorizzazione MISE | 25 luglio 2016 (MNO - Mobile Network Operator), artt. 25 e 27 D.Lgs. 259/2003 |
| PEC Iliad | svilupporete.iliaditalia@legalmail.it |
| Permit Coordinator | Arch. Benedetta Bellussi — cell. 3519174637 — bbellussi@it.iliad.com |

---

## Tecnici Incaricati K2A s.r.l.s.

### Ing. Luca Rossi
| Campo | Valore |
|-------|--------|
| CF | RSSLCU73A23H501U |
| Ordine | Ordine degli Ingegneri della Provincia di Perugia |
| N. iscrizione | A2212 |
| Sede studio | c/o K2A s.r.l.s., Via Alessandro Manzoni, n. 84, Perugia (PG) |
| Qualifica nei documenti | "Ing. Luca Rossi, in qualità di tecnico incaricato da ILIAD ITALIA S.p.A. con studio c/o K2A s.r.l.s. in via A. Manzoni n°84, Perugia; Iscritto all'Ordine degli Ingegneri della Provincia di Perugia con il n. A2212" |

### Ing. Jessica Romanelli
| Campo | Valore |
|-------|--------|
| CF | RMNJSC87T50D653J |
| Ordine | Ordine Professionale degli ingegneri della Provincia di Perugia |
| N. iscrizione | A3537 |
| Sede studio | c/o K2A s.r.l.s., Via Alessandro Manzoni, n. 84, Perugia (PG) |
| Qualifica nei documenti | "Ing. Jessica Romanelli C.F. RMNJSC87T50D653J, iscritto all'Ordine Professionale degli ingegneri della Provincia di Perugia con il n. A3537, domiciliato per la carica presso K2A Srls in Via Alessandro Manzoni, 84 – Perugia (PG)" |

---

## Dati Variabili da Raccogliere per il Sito

### Dati identificativi

| Campo | Da dove estrarlo | Formato |
|-------|-----------------|---------|
| Codice sito | Briefing utente / scheda radio | `RM[5cifre]_[3cifre]` |
| Nome sito | Briefing utente / scheda radio | Toponomastica breve |
| Indirizzo completo | Briefing utente / PE / scheda radio | Via, n. civico |
| Comune | Briefing utente / PE | |
| Municipio (solo Roma) | Briefing utente / verifica mappa | Es. "XIV (ex XIX)" |
| Dati catastali | Briefing utente / visura / PE | Foglio, P.lla, Sez. |
| Coordinate WGS84 | Scheda radio / PE / GPS | Lat. [gradi] N; Long. [gradi] E |
| Coordinate UTM | Scheda radio / FILETX | UTMX, UTMY |
| Quota s.l.m. | PE / scheda radio | metri |
| Proprietà sito | Briefing utente | Cellnex / altro |

### Dati tecnici radio

| Campo | Da dove estrarlo |
|-------|-----------------|
| Sistema radiomobile | Scheda radio / FILETX.xlsx |
| Numero settori | Scheda radio |
| Azimuth per settore | Scheda radio / FILETX.xlsx |
| Frequenze operative | Scheda radio / FILETX.xlsx |
| Potenza EIRP per frequenza | FILETX.xlsx / scheda radio |
| Tipo antenna | Scheda radio (datasheet) |
| Altezza antenna | PE / scheda radio |
| Tilt meccanico/elettrico | Scheda radio / FILETX.xlsx |
| Guadagno antenna | Datasheet antenna |

### Dati urbanistici (RT)

| Campo | Da dove estrarlo |
|-------|-----------------|
| Destinazione PRG (Tav. 3_10) | Verifica PRG Roma online |
| Rete ecologica (Tav. 4_10) | Verifica PRG Roma |
| Carta per la qualità (Tav. G1_10) | Verifica PRG Roma |
| PTPR — Sistemi e ambiti (Tav. A) | Verifica PTPR Lazio |
| PTPR — Beni paesaggistici (Tav. B) | Verifica PTPR Lazio |

### Dati ambientali e fotografici

| Campo | Da dove estrarlo |
|-------|-----------------|
| Descrizione terreno circostante | Sopralluogo / Google Maps / PE |
| Documentazione fotografica sito | Sopralluogo / PE |
| Valori EM di fondo | PDM + misure ARPA |
| Punti significativi | Sopralluogo / planimetria area |

---

## Formula SCIA — Testo Boilerplate

### Premessa SCIA (invariante)

```
Premesso che
in data 25.07.2016, Iliad Italia S.p.A. ha ottenuto da parte del Ministero dello Sviluppo
Economico, ai sensi degli articoli 25 e 27 del D.Lgs. 259/2003, Autorizzazione Generale
per il servizio MNO – Mobile Network Operator;

in forza della suddetta Autorizzazione Generale, Iliad Italia S.p.A. ha il diritto di
progettare, costruire, gestire e modificare una propria rete radiomobile nel rispetto degli
obblighi normativi applicabili;

con Legge n. 36/2001, è stata approvata la "Legge quadro sulla protezione dalle esposizioni
a campi elettrici, magnetici ed elettromagnetici";

il Codice delle Comunicazioni Elettroniche, D.Lgs. 259/2003, prevede procedure agevolate e
accelerate per la installazione delle infrastrutture e degli impianti di telefonia e, ai
sensi dell'art. 43, qualifica le infrastrutture per reti pubbliche di telecomunicazioni quali
"opere di urbanizzazione primaria" di cui all'art.16, comma 7, D.P.R. 380/2001;

l'art. 45 D.Lgs. 259/2003 disciplina [...]
```

### Intestazione Procura (invariante per tutti i documenti)

```
in persona del Sig. Andrea Longari, nato a Roma il 27 Aprile 1974, domiciliato ai fini
dell'incarico presso la Sede Legale, munito dei necessari poteri in forza di Procura
Speciale autenticata dal notaio Luca Amato in Roma in data 10/04/2024 Rep.n.63403/18598,
registrata presso l'Agenzia delle Entrate di Roma in data 10/04/2024 al n. 3697 Serie 1T
```

### Testo Atto d'Obbligo (invariante salvo dati sito)

```
SI IMPEGNA
Entro il termine di 3 mesi a far data dalla fine dell'utilizzazione dell'Impianto
denominato [CODICE] – [NOME SITO], a dismettere l'impianto, a smontare, demolire ed
asportare tutto quanto installato ed a ricostruire lo stato dei luoghi preesistente
a propria cura e spese.
```

---

## Estratto Tipi di Sito Gestiti

| Tipo | Caratteristiche | Note strutturali |
|------|----------------|-----------------|
| Rooftop (edificio) | Antenne su terrazza/lastrico solare | Cita l'edificio come supporto; struttura non progettata da K2A |
| Raw Land | Sito a terra su terreno proprio | Palo/traliccio su fondazione |
| Palo su edificio | Palina installata su copertura | Intermedio tra rooftop e raw land |

Per i siti Cellnex (tower sharing), aggiungere riferimento al "Nulla Osta Ospitalità" nell'elenco allegati della SCIA.
