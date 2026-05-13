# P06 — AI Customer Service
## Servizio K2-AI
Agenti AI per la gestione automatica del supporto clienti: triage ticket, ricerca knowledge base, risposta guidata, escalation a team umano.

## Skill Claude disponibili

| Skill | Descrizione |
|-------|-------------|
| `customer-support:ticket-triage` | Categorizza ticket P1-P4, assegna priorità, verifica duplicati e routing |
| `customer-support:customer-research` | Ricerca multi-sorgente su domande clienti con attribuzione fonte |
| `customer-support:kb-article` | Redige articoli knowledge base da ticket risolti o domande frequenti |
| `customer-support:customer-escalation` | Pacchettizza escalation per engineering/product con contesto completo |
| `customer-support:draft-response` | Genera risposte professionali al cliente: domande, escalation, bad news |
| `crm-customer-experience` | Loyalty program, churn prediction, NPS, CSAT, CES, win-back framework |
| `enterprise-search:knowledge-synthesis` | Combina risultati da più sorgenti in risposta strutturata con fonte |

## Come usarle
Es: "smista questo ticket e assegna priorità" → `customer-support:ticket-triage`
Es: "scrivi una risposta al cliente per questo problema" → `customer-support:draft-response`
Es: "crea un articolo KB da questa risoluzione" → `customer-support:kb-article`
