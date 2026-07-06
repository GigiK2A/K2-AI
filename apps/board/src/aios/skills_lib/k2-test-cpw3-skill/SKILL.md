---
name: k2-test-cpw3-skill
description: >
  Test sezioni 8-10 content-production-workflow. Attiva per: "test sezioni nuove".
---

# Test sezioni 8-10
## 8. Content complexity tiers (AI-friendly vs YMYL)

Non tutti i contenuti vanno prodotti con lo stesso mix AI/umano. Prima di iniziare un pezzo, classificarlo nel tier corretto e applicare il mix coerente. Sbagliare il tier (es. usare AI-heavy su contenuti YMYL) è la prima causa di disastri reputazionali e di responsabilità legale nel content marketing.

| Tier | Tipo contenuto | Rischio se sbagliato | Mix AI/Umano | Livello review |
|---|---|---|---|---|
| **AI-heavy** | Definizioni, glossari, how-to tecnici basic, comparazioni prodotto note, FAQ standard, descrizioni prodotto e-commerce | Basso (errore facilmente correggibile post-publish) | 70% AI + 30% umano | Review veloce (10 min) |
| **Hybrid** | Articoli informazionali di settore, case study anonimi, guide medio-lunghe, content di prodotto, comparazioni settoriali | Medio (errore crea imbarazzo ma recuperabile con correzione) | 50% AI + 50% umano | Review approfondita (30 min) |
| **Human-first** | Opinion piece, thought leadership, interviste, case study nominativi con cliente, position paper | Alto (errore danneggia rapporto con cliente o reputation brand) | 20% AI + 80% umano | Review + approvazione cliente |
| **YMYL** (Your Money Your Life) | Contenuti finanziari, legali, medici/salute, fiscali, previdenziali, sicurezza | Altissimo (errore = responsabilità legale, danno reale all'utente) | 0-10% AI solo per draft strutturale | Review + validazione esperto qualificato (avvocato, commercialista, medico) |

**Regola inviolabile**: non usare mai il mix AI-heavy su contenuti YMYL, anche sotto pressione di deadline. Meglio posticipare la pubblicazione di una settimana che pubblicare un contenuto YMYL non validato da specialista.

## 9. SOP validazione contenuti AI (obbligatoria pre-publish)

Ogni contenuto AI-assisted deve passare questo workflow prima di andare online. Nessuna eccezione, indipendentemente dal tier. Tempo medio stimato: 20-30 minuti per articolo 1500 parole.

### Check 1 — Fact-checking (10-20 min)

-  Ogni numero/statistica: verifica fonte primaria (ISTAT, Banca d'Italia, Eurostat, enti ufficiali di settore). Gli LLM inventano dati con sicurezza.
-  Ogni data: verifica (LLM sbagliano spesso anni/mesi, soprattutto eventi post-training)
-  Ogni nome proprio (persone, aziende, prodotti): verifica esistenza + grafia esatta
-  Ogni citazione normativa: verifica articolo, comma e data di vigenza del testo
-  Ogni URL esterno: verifica che esista, sia raggiungibile e pertinente
-  Ogni affermazione quantitativa generica ("il 90% delle aziende", "la maggior parte degli utenti"): o ha fonte verificata, o va rimossa/riformulata

### Check 2 — Originalità (5 min)

-  Plagi check: Copyscape o Quillbot Plagiarism su porzioni sospette (frasi molto piatte o troppo tecniche)
-  AI detector: GPTZero o Originality.ai su interezza — target di probabilità AI inferiore a 30%
-  Marker AI linguistici assenti: "Certamente!", "In sintesi", "Speriamo che questo articolo", "È importante notare che", "Nel mondo odierno", "In conclusione" (specialmente come attacco o chiusura)
-  Nessuna frase-preambolo inutile tipo "Procediamo ora ad analizzare..." o "Diamo uno sguardo a..."

### Check 3 — Brand voice (5 min)

-  Tono coerente con brand guide del cliente (verificare brief)
-  Terminologia specifica del cliente rispettata (consultare glossario in Notion)
-  Esempi italiani (non casi americani generici tradotti)
-  Registro adeguato al target: "tu" vs "lei", formale vs informale, tecnico vs divulgativo
-  Nessun jargon generico ("soluzioni innovative", "all'avanguardia", "sinergie", "ecosistema") a meno che non sia parte del tono esplicito del cliente

### Check 4 — Validazione specialistica (obbligatorio se YMYL)

-  Avvocato ha rivisto contenuti legali (firma scritta o email di approvazione)
-  Commercialista ha rivisto contenuti fiscali
-  Medico o farmacista ha rivisto contenuti sanitari
-  Consulente finanziario qualificato ha rivisto contenuti di investimento
-  Tecnico della sicurezza ha rivisto contenuti di safety

### Firma umana (sempre)

Ogni articolo pubblicato deve avere:

- **Firma autore reale** (persona esistente, con profilo LinkedIn verificabile, non pseudonimo o AI-generated)
- **Data ultima revisione umana** visibile in pagina
- **Disclaimer trasparente** consigliato: "Contenuto redatto con ausilio di AI e revisionato da [nome autore]" — opzionale ma aumenta fiducia e riduce rischi normativi AI Act

### Log di revisione

Tracciare in Notion (o tool equivalente) per ogni contenuto: chi ha fatto ciascun check, quando, durata. Serve per:
- Audit qualità mensile
- Individuare colli di bottiglia nel processo
- Evidenze di diligence in caso di contestazione

## 10. Prompt library per page-type

Libreria di prompt riutilizzabili per le tipologie di pagina più comuni in retainer PMI. Struttura standard: **Contesto + Input + Struttura attesa + Vincoli di stile + Output format**. Personalizzare con dati specifici cliente prima di eseguire. Conservare come template compilabili in Notion.

### Landing page prodotto/servizio

```
Contesto: landing page per [servizio cliente] di [azienda cliente italiana, settore].
Target: [persona decision-maker + seniority + settore aziendale].
Awareness stage: solution-aware (cerca attivamente fornitori come noi).
Obiettivo: conversione a form "Richiedi demo" o "Parla con noi".

Struttura attesa:
- H1 con promessa di valore chiara (beneficio concreto, non feature di prodotto)
- Sotto-headline che specifica a chi è rivolto
- 3 bullet di beneficio (outcome numerici concreti, non aggettivi vuoti)
- Sezione "Come funziona" in 3 step
- Sezione "Risultati tipici" con 2-3 case study anonimi numerici
- FAQ (6-8 domande) derivate dalle obiezioni reali del cliente
- CTA finale duplicata (form alto + form basso)

Vincoli:
- Italiano diretto, seconda persona (tu se B2C, voi se B2B)
- No jargon vuoto ("soluzioni innovative", "all'avanguardia")
- Ogni claim supportato da numero o evidenza
- Max 800 parole totali
- Non inventare dati: usa placeholder [DATO DA VERIFICARE] se non forniti nel contesto
```

### Articolo blog SEO informazionale (TOFU)

```
Contesto: articolo blog per [cliente], topic "[topic specifico]".
Target keyword: "[keyword]" (volume X/mese, KD Y, intent informazionale).
Target audience: [persona].
Awareness stage: problem-aware.
Funnel: TOFU.

Struttura:
- Hook di apertura (dato sorprendente o domanda provocatoria, max 2 righe)
- Definizione concetto in 40-60 parole (per citazione in AI Overview)
- 5-7 H2 che rispondono alle domande correlate (vedi "People Also Ask" per la keyword)
- Ogni H2: 150-300 parole, 1 esempio italiano concreto, 1 dato verificabile
- Sezione FAQ con schema FAQPage (5 domande pertinenti)
- Conclusione con CTA soft verso lead magnet o articolo correlato

Vincoli:
- Word count: [valore da brief]
- Keyword primaria: nei primi 100 parole + 1 H2 + meta description
- Integrare naturalmente 5 keyword secondarie (elencate di seguito)
- Nessun "In conclusione" — preferire sintesi in bullet
- Include 3-5 punti di internal link verso pagine pertinenti del cliente (indicare solo dove, il link lo inserisce l'editor)
- Tono diretto, seconda persona
```

### Case study cliente

```
Contesto: case study per [cliente fornitore], protagonista [nome azienda cliente finale + settore + dimensione].
Obiettivo: credibilità + conversione.

Struttura STAR:
- Situation (3-4 righe): contesto, dimensione business, periodo storico
- Task (2-3 righe): sfida specifica affrontata, KPI di partenza misurabili
- Action (paragrafo medio): cosa abbiamo fatto, approccio, metodologia, tool/strumenti
- Result (bullet): 3-5 KPI before/after con numeri specifici e periodo di misurazione

Vincoli:
- Solo dati preventivamente approvati dal cliente protagonista (verificare PRIMA di scrivere)
- Citare strumenti e metodologie in modo factual, senza vantarsi
- Una quote diretta del cliente (min 1, max 2) da intervista reale
- CTA: "Vuoi risultati simili? [link demo o contatto]"
- Tono factual, no superlativi ("incredibile", "rivoluzionario", "game-changer")
- Nessun dato inventato: se mancano numeri specifici, chiedere prima o usare placeholder
```

### Post LinkedIn (authority building)

```
Contesto: post LinkedIn pubblicato da [persona del team cliente, ruolo X].
Obiettivo: authority + engagement + conversione a DM.

Struttura Hook-Story-Offer:
- Hook (1 riga, line break dopo): dato, opinione controcorrente, domanda provocatoria
- Story (3-5 righe): esperienza specifica vissuta, errore comune osservato, insight pratico
- Tre insight principali (bullet o numerati)
- Offer/CTA (1-2 righe): invito a commentare, mandare DM, scaricare risorsa nei commenti

Vincoli:
- 200-300 parole totali
- Max 3 emoji, mai decorative (solo funzionali)
- Prima persona, esperienza vissuta (non teorica)
- Terminare con domanda aperta per stimolare commenti
- Nessun link esterno nel post (abbassa reach LinkedIn) — annunciare che il link è nei commenti
- Tono coerente con brand personal di [persona]: [indicare brand voice personale se definita]
```

### Newsletter short (weekly o monthly)

```
Contesto: newsletter per [cliente], target [persona subscriber].
Obiettivo: nurturing + traffic al sito + top-of-mind.

Struttura:
- Subject line: 40-50 caratteri, curiosity-driven o benefit-driven (genera 3 varianti)
- Preheader: 80-100 caratteri, completa il subject senza ripeterlo
- Saluto personale (prima persona singolare del founder/autore)
- Hook: cosa renderà il lettore contento di aver aperto questa mail (1-2 righe)
- Corpo: 150-250 parole, UN solo tema, un insight pratico
- CTA singolo (massimo due): link all'articolo o risorsa correlata
- Firma personale

Vincoli:
- Tono conversazionale, come email da collega a collega
- Nessuna formattazione elaborata (la newsletter funziona meglio in testo quasi-plain)
- No emoji invadenti
- Max un link principale (più link = CTR disperso)
```

Ogni prompt va personalizzato con i dati specifici del cliente (brand voice, esempi, glossario) prima di essere eseguito su LLM. Salvare in Notion come template compilabili, versionati, assegnati per tipologia cliente.

## Cross-skill references

- `marketing-strategico`: strategia content in piano marketing
- `seo-italia`: ottimizzazione SEO specifica IT + AI SEO/GEO
- `digital-marketing-performance`: email deliverability, distribuzione, CRO
- `psicologia-marketing`: copy persuasivo, hook, storytelling
- `marketing-analytics`: measurement attribution
- `k2-ai-marketing-consulenza`: orchestratore delivery retainer
- `linkedin-b2b-outreach`: distribuzione content LinkedIn authority
