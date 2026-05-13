# P14 — AI Edilizia & Costruzioni
## Servizio K2-AI
Agenti AI per il ciclo edilizio civile completo: iter autorizzativo, progettazione architettonica e strutturale, impianti, sicurezza cantiere, direzione lavori, agibilità. (Distinto da P04 che copre TLC.)

## Skill Claude disponibili

### Orchestratori e Check Express
| Skill | Descrizione |
|-------|-------------|
| `anthropic-skills:flusso-buildboost-studio` | Diagnostica edilizia completa: iter autorizzativo → chiusura lavori |
| `anthropic-skills:flusso-structboost-studio` | Diagnostica strutturale: verifica statica, vulnerabilità sismica, interventi |
| `anthropic-skills:flusso-safetyboost-studio` | Diagnostica sicurezza: PSC, DVR, formazione, responsabilità legali |
| `anthropic-skills:flusso-mepboost-studio` | Consulenza energetica e impiantistica: audit, EEM, costi-benefici |
| `anthropic-skills:check-edilizia-express` | Pagellino iter edilizio rapido (score 0-100) |
| `anthropic-skills:check-strutturale-express` | Pagellino strutturale rapido per edifici esistenti |
| `anthropic-skills:check-sicurezza-express` | Pagellino sicurezza cantiere D.Lgs. 81/2008 |
| `anthropic-skills:check-impianti-express` | Pagellino conformità impianti elettrici e HVAC |

### Progettazione Architettonica
| Skill | Descrizione |
|-------|-------------|
| `anthropic-skills:progettazione-architettonica` | CILA/SCIA/PDC, verifica urbanistica, SUL/SC/RAI, fotomontaggio, render |
| `anthropic-skills:architetto-beni-monumentali` | Relazione paesaggistica, vincoli, Soprintendenza, DPR 31/2017 |
| `anthropic-skills:agibilita` | SCIA agibilità, certificato agibilità, checklist documenti, art. 24-25 DPR 380 |

### Progettazione Strutturale
| Skill | Descrizione |
|-------|-------------|
| `anthropic-skills:progettista-strutturale` | NTC 2018, EC2/EC3/EC8, c.a., acciaio, fondazioni, analisi sismica |
| `anthropic-skills:progetto-strutturale-gc-tlc` | Progetto strutturale per deposito Genio Civile su infrastrutture |

### Impianti
| Skill | Descrizione |
|-------|-------------|
| `anthropic-skills:impianti-elettrici` | CEI 64-8, DM 37/2008, FV, BESS, ATEX, EV, domotica, emergenza |
| `anthropic-skills:impianti-termici-hvac` | Caldaie, pompe di calore, VMC, APE, NZEB, UNI TS 11300 |
| `anthropic-skills:cci-impianti-produzione` | CCI per FV ed eolici MT: delibera ARERA 385/2025, CEI 0-16 |

### Sicurezza Cantiere
| Skill | Descrizione |
|-------|-------------|
| `anthropic-skills:psc-coordinamento-sicurezza` | PSC completo: art. 100 D.Lgs. 81/08, Allegato XV, stima costi |
| `anthropic-skills:cse-coordinatore-sicurezza` | CSE operativo: gestione cantiere attivo, verbali, inadempienze |
| `anthropic-skills:consulente-sicurezza-lavoro` | DVR, RSPP, formazione, sorveglianza sanitaria, D.Lgs. 81/2008 |
| `psc-legale:psc-legale` | Aspetti legali PSC: responsabilità penale CSE/CSP, tutela patrimoniale |

### Direzione Lavori e Contabilità
| Skill | Descrizione |
|-------|-------------|
| `anthropic-skills:direzione-lavori` | DL: giornale lavori, SAL, ordini di servizio, varianti, conto finale |

## Come usarle
Es: "posso fare la ristrutturazione? cosa serve?" → `anthropic-skills:flusso-buildboost-studio`
Es: "redigi il PSC per questo cantiere" → `anthropic-skills:psc-coordinamento-sicurezza`
Es: "verifica la struttura di questo edificio esistente" → `anthropic-skills:flusso-structboost-studio`
