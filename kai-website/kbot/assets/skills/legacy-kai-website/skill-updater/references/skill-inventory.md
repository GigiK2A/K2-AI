# Inventario Skill — Aggiornato aprile 2026

Questo file elenca tutte le skill custom dell'utente da monitorare.
Viene usato come riferimento dalla skill-updater per sapere cosa scansionare.

## Skill locali (~/.claude/skills/)

### Ingegneria e TLC
| Skill | Dominio | Note |
|---|---|---|
| impianti-elettrici | Impianti BT/MT, norme CEI | Ha 18 file references |
| impianti-termici-hvac | Termotecnica, pompe di calore, VMC | Normativa EPBD 2024, Conto Termico 3.0 |
| progettista-strutturale | NTC 2018, Eurocodici, sismica | |
| progettazione-architettonica | Edilizia, CILA/SCIA, urbanistica | |
| diagnosi-energetica-ege | Audit energetico, UNI TS 11300 | |
| verifica-pe-terzi | Verifica PE iliad fornitori | |

### Sicurezza
| Skill | Dominio | Note |
|---|---|---|
| psc-coordinamento-sicurezza | PSC, Allegato XV, D.Lgs. 81/08 | |
| cse-coordinatore-sicurezza | CSE operativo in cantiere | |
| consulente-sicurezza-lavoro | DVR, formazione, TU 81/08 | |

### Diritto e Fiscale
| Skill | Dominio | Note |
|---|---|---|
| diritto-italiano | Civile, penale, amministrativo, tributario | Ha 7 file references |
| diritto-societario-italiano | Forme societarie, governance, M&A | |
| fiscale-tributario-italiano | IRPEF, IVA, regime forfettario | |
| ss-trust-italiano | Società semplice, trust, protezione patrimoniale | |

### Edilizia e Valutazione
| Skill | Dominio | Note |
|---|---|---|
| agibilita | SCIA agibilità, DPR 380/2001 | |
| perizia-estimo-immobiliare | Stime, perizie CTU, quotazioni OMI | |
| direzione-lavori | DL, SAL, contabilità cantiere | |
| architetto-beni-monumentali | Beni vincolati, Soprintendenza, D.Lgs. 42/2004 | |

### Finanza e Investimenti
| Skill | Dominio | Note |
|---|---|---|
| trading | ICT, Elliott Wave, Hurst, Wyckoff | |
| tokenizzazione-immobiliare | Blockchain, STO, MiCAR, DLT Pilot | |
| teoria-dei-giochi-decisioni | Decision theory, Nash, minimax | |

## Skill da plugin (read-only — solo report, no modifiche)

### Plugin Cellnex
- cellnex:rinforzi-pali
- cellnex:nuovi-siti
- cellnex:impianti-elettrici-sito
- cellnex:sicurezza-duvri
- cellnex:strutture-porta-antenne
- cellnex:verifica-strutture-esistenti
- cellnex:verifica-progetto-terzi

### Plugin iliad
- iliad:progetto-esecutivo-iliad
- iliad:documentazione-pe
- iliad:elaborati-architettonici
- iliad:elaborati-civili
- iliad:elaborati-impianti
- iliad:installazione-apparati
- iliad:relazioni-strutturali
- iliad:verifica-pe-terzi
- iliad:aweud-mmwave

### Plugin gestione cantiere
- gestione-cantiere-tlc:inizializza-progetto
- gestione-cantiere-tlc:esegui-fase
- gestione-cantiere-tlc:aggiorna-stato
- gestione-cantiere-tlc:report-avanzamento

### Plugin PSC legale
- psc-legale:psc-legale

### Plugin TSSR/B40
- tssr-b40-filler:scheda-radio-reader
- tssr-b40-filler:compila-tssr

### Plugin Report CAR
- report-caratterizzazione-iliad:compila-report-car

> **Nota**: Le skill da plugin sono in directory read-only. La skill-updater
> può solo analizzarle e produrre raccomandazioni nel report, ma non può
> modificarle direttamente. L'utente dovrà aggiornare i plugin separatamente.
