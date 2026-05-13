# P04 — AI Ingegneria e Progettazione
## Servizio K2-AI
Agenti AI specializzati per ingegneria TLC, strutturale, edile e impiantistica. Redazione PE, verifiche statiche, PSC, elaborati tecnici.

## Skill Claude disponibili

### TLC — Progettazione Esecutiva iliad
| Skill | Descrizione |
|-------|-------------|
| `iliad-progettazione-esecutiva:progetto-esecutivo-iliad` | Skill principale PE iliad: elenco elaborati, new site, transfer, colocation |
| `iliad-progettazione-esecutiva:documentazione-pe` | Frontespizio, relazione tecnica, foto ante-operam, schede radio |
| `iliad-progettazione-esecutiva:elaborati-architettonici` | Tavole architettoniche: stato di fatto, progetto, comparazione |
| `iliad-progettazione-esecutiva:elaborati-civili` | Fondazioni, platee, recinzioni, carpenteria raw land e roof top |
| `iliad-progettazione-esecutiva:elaborati-impianti` | Impianti elettrici, schema unifilare, rete di terra, LPS |
| `iliad-progettazione-esecutiva:relazioni-strutturali` | Calcolo palo, fondazione, verifica strutture esistenti, geotecnica |
| `iliad-progettazione-esecutiva:installazione-apparati` | Apparati Nokia AirScale T1/T3, FCOB, ACOC, NodeBox, cablaggio |
| `iliad-progettazione-esecutiva:aweud-mmwave` | AWEUD mmWave 5G, 24/26GHz, staffa AMTA, cavo OCTIS |
| `iliad-progettazione-esecutiva:verifica-pe-terzi` | Controllo qualità PE iliad di fornitori/appaltatori terzi |
| `pe-verifica:verifica-pe` | Verifica sistematica PE iliad con report conformità completo |
| `aie-verifica:verifica-aie` | Verifica AIE (Autorizzazione Impianti Energetici) |

### TLC — Pacchetti Autorizzativi
| Skill | Descrizione |
|-------|-------------|
| `pacchetti-autorizzativi-iliad:redazione-pacchetto` | Redige SCIA art. 45 D.Lgs. 259/2003 per siti iliad |
| `pacchetti-autorizzativi-iliad:verifica-pacchetto` | Verifica completezza e conformità pacchetto autorizzativo iliad |

### TLC — Progettazione Cellnex
| Skill | Descrizione |
|-------|-------------|
| `cellnex-progettazione-esecutiva:nuovi-siti` | PE nuovo sito Cellnex: raw land, roof top, fondazioni, shelter |
| `cellnex-progettazione-esecutiva:strutture-porta-antenne` | Pali poligonali, tralicci, sbracci, scale, ballatoi Cellnex |
| `cellnex-progettazione-esecutiva:rinforzi-pali` | Rinforzo strutturale pali: flangia, tronco, plinto, tirafondo |
| `cellnex-progettazione-esecutiva:impianti-elettrici-sito` | QAR-MOM 4.0, impianto di terra, alimentazioni operatori |
| `cellnex-progettazione-esecutiva:sicurezza-duvri` | PSC e DUVRI per siti Cellnex, D.Lgs. 81/08 |
| `cellnex-progettazione-esecutiva:verifica-progetto-terzi` | Controllo qualità progetti di fornitori terzi Cellnex |

### TLC — Verifiche Statiche
| Skill | Descrizione |
|-------|-------------|
| `verifica-statica-iliad-cellnex:vs-orchestratore` | Orchestratore VS completa per pali iliad e Cellnex |
| `verifica-statica-iliad-cellnex:vs-input-dati` | Raccolta dati input: geometria palo, antenne, materiali, LC |
| `verifica-statica-iliad-cellnex:vs-schema-statico` | Classificazione schema statico (mensola, strallata, reticolare) |
| `verifica-statica-iliad-cellnex:vs-azioni-ambientali` | Calcolo vento, neve, ghiaccio, sisma (CNR-DT 207, NTC) |
| `verifica-statica-iliad-cellnex:vs-sollecitazioni` | Calcolo M, V, N fusto e pennone per tutte le combinazioni SLU |
| `verifica-statica-iliad-cellnex:vs-verifiche-fusto` | Verifiche SLU fusto: Von Mises, instabilità globale e locale |
| `verifica-statica-iliad-cellnex:vs-verifiche-giunti` | Verifiche flange bullonate, piastra di base, tirafondi, ancoraggi |
| `verifica-statica-iliad-cellnex:vs-verifiche-fatica` | Verifica fatica Palmgren-Miner, curva S-N (EN 1993-1-9) |
| `verifica-statica-iliad-cellnex:vs-verifiche-fondazione` | Verifiche plinto c.a.: portanza, scorrimento, ribaltamento |
| `verifica-statica-iliad-cellnex:vs-verifiche-sle` | SLE: deformabilità, rotazioni parabole, fessurazione |
| `verifica-statica-iliad-cellnex:vs-redazione-documento` | Redazione DOCX finale VS (16 capitoli + appendici) |
| `verifica-statica-iliad-cellnex:vs-template-paline-rt` | Template paline Roof Top (mensola, strallata, reticolare) |
| `relsta-unificata:relsta-unificata` | RELSTA unificata per tutti gli operatori (iliad, Cellnex, WindTre…) |
| `verifica-statica-iliad-cellnexvs-rinforzi-proposta` | Proposte rinforzo strutturale post-verdetto NV |
| `verifica-statica-iliad-cellnexvs-sismica-avanzata` | Analisi sismica avanzata: modale multi-modo, pushover N2 |
| `verifica-statica-iliad-cellnexvs-verifiche-fatica` | Verifica fatica avanzata pali snelli zona vento 3-9 |

### TLC — Gestione Cantieri e Fatturazione
| Skill | Descrizione |
|-------|-------------|
| `gestione-cantiere-tlc:inizializza-progetto` | Crea tracker Excel PM cantieri TLC (iliad, Cellnex) |
| `gestione-cantiere-tlc:esegui-fase` | Orchestratore fasi lavorative: PE, autorizzazioni, PSC, BEF |
| `gestione-cantiere-tlc:aggiorna-stato` | Aggiorna stato fasi nel tracker: vidima, NC, note |
| `gestione-cantiere-tlc:report-avanzamento` | Report avanzamento cantieri: siti bloccati, prossime azioni |
| `fatturazione-cellnex:genera-richiesta-bef` | Genera file Excel BEF e CDMS per fatturazione Cellnex |
| `tssr-b40-filler:scheda-radio-reader` | Legge Scheda Radio PDF iliad/TDC |
| `tssr-b40-filler:compila-tssr` | Compila TSSR B40 da Scheda Radio PDF |
| `report-caratterizzazione-iliad:compila-report-car` | Report di Caratterizzazione Strutturale iliad (muratura/c.a.) |
| `flusso-tlcboost-studio` | Orchestratore TLCBoost: PM completo dal PE alla consegna BEF |

### Ingegneria Civile e Strutturale
| Skill | Descrizione |
|-------|-------------|
| `progettista-strutturale` | Calcolo strutturale: NTC 2018, EC2/EC3/EC7/EC8, c.a., acciaio |
| `progettazione-architettonica` | Progetto architettonico, CILA/SCIA/PDC, fotomontaggio, render |
| `impianti-elettrici` | Impianti elettrici italiani: CEI 64-8, DM 37/2008, FV, ATEX |
| `impianti-termici-hvac` | HVAC: caldaie, pompe di calore, VMC, APE, NZEB |
| `psc-coordinamento-sicurezza` | PSC completo: art. 100 D.Lgs. 81/08, stima costi sicurezza |
| `cse-coordinatore-sicurezza` | CSE operativo: gestione cantiere attivo, sopralluoghi, verbali |
| `direzione-lavori` | DL: SAL, ordini di servizio, varianti, contabilità di cantiere |
| `architetto-beni-monumentali` | Relazione paesaggistica, beni vincolati, Soprintendenza |
| `cci-impianti-produzione` | CCI per impianti FV ed eolici MT: delibera ARERA 385/2025 |

## Come usarle
Es: "fai il PE per un new site iliad raw land" → `iliad-progettazione-esecutiva:progetto-esecutivo-iliad`
Es: "verifica statica del palo RM00234_001" → `verifica-statica-iliad-cellnex:vs-orchestratore`
Es: "genera la richiesta BEF di aprile" → `fatturazione-cellnex:genera-richiesta-bef`
