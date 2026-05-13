# P07 — RAG e Knowledge Base
## Servizio K2-AI
Sistemi RAG (Retrieval-Augmented Generation) per ricerca intelligente su documenti aziendali, knowledge base unificata e digest automatici.

## Skill Claude disponibili

| Skill | Descrizione |
|-------|-------------|
| `enterprise-search:search` | Ricerca unificata su tutte le sorgenti connesse (Slack, email, Drive, Notion…) |
| `enterprise-search:digest` | Digest giornaliero/settimanale di attività da tutte le sorgenti |
| `enterprise-search:knowledge-synthesis` | Combina risultati multi-sorgente in risposta strutturata con attribuzione |
| `enterprise-search:search-strategy` | Decomposizione query e orchestrazione ricerca multi-sorgente |
| `enterprise-search:source-management` | Gestisce sorgenti connesse: priorità, rate limit, connessione nuove |
| `productivity:memory-management` | Memoria a due livelli: CLAUDE.md (working memory) + directory knowledge base |
| `productivity:task-management` | Gestione task su file TASKS.md condiviso |
| `productivity:start` | Avvia il sistema produttività e apre la dashboard |
| `productivity:update` | Sincronizza task e aggiorna memory da attività recente |

## Come usarle
Es: "trova tutti i documenti sul progetto X" → `enterprise-search:search`
Es: "cosa è successo questa settimana nei canali Slack?" → `enterprise-search:digest`
Es: "ricorda che il cliente Y preferisce comunicazioni via email" → `productivity:memory-management`

## Connettori compatibili
Slack, Gmail, Google Drive, Notion, Confluence, Box, SharePoint, Figma, Gong, Granola
