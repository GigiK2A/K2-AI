---
name: k2-ai-marketing-consulenza
description: >
  Orchestratore della consulenza marketing K2-AI per PMI italiane. Attiva SEMPRE quando
  l'utente parla di servizio K2-AI Marketing, nuovo cliente PMI da onboardare, Radar Audit
  da produrre, retainer Growth/Pro/Starter da gestire, discovery call con prospect,
  presentazione Radar a cliente, piano marketing 90 giorni per PMI, report mensile retainer,
  pipeline commerciale K2-AI, proposta commerciale K2-AI, upsell cliente esistente,
  revisione trimestrale piano retainer, cliente B2B industriale, cliente PMI servizi,
  cliente e-commerce PMI. Attiva ANCHE per frasi come "nuovo cliente", "prepara il
  Radar Audit per [azienda]", "imposta il retainer per [cliente]", "piano mensile per
  [cliente]", "report mensile per [cliente]", "script discovery call", "come gestire
  obiezione cliente [X]", "proposta per PMI", "kickoff cliente K2-AI". Coordina le skill
  marketing-strategico, digital-marketing-performance, marketing-analytics,
  psicologia-marketing, seo-italia, crm-customer-experience, marketing-bocconi-trust,
  strategia-competitiva, benchmark-italia-business, it-law-privacy-ai in sequenza
  strutturata per ciascuna fase del ciclo commerciale (discovery, audit, closing,
  onboarding, delivery retainer, quality control, upsell).
---

# K2-AI Marketing — Orchestratore consulenza PMI

Questa skill gestisce l'intero ciclo di vita della consulenza K2-AI Marketing per PMI italiane. Non duplica contenuto delle altre skill: **le coordina** in sequenza produttizzata, applicando le linee guida K2-AI su pricing, deliverable, processo commerciale.

**Contesto operativo K2-AI** (riferimento vincolante):
- Target: PMI italiane 500k–25M fatturato, cross-settore
- Pacchetti: Radar Audit 1.900 € (entry) + Starter 800/m + Growth 1.800/m + Pro 3.500/m
- Modello: molti clienti, retainer ricorrente + audit entry + add-on progettuali
- Operatore: consulente senior umano assistito da AI (no automazione cieca)
- Brand: K2-AI dichiarato, AI come moltiplicatore di velocità/profondità

---

## Workflow della consulenza: 7 fasi

Quando l'utente menziona un'attività relativa a un cliente K2-AI, identifica la fase corrente e orchestra le skill appropriate.

### Fase 1 — Prospecting e discovery call (pre-vendita)

**Trigger utente**: "devo contattare un prospect", "script LinkedIn outreach", "prepara discovery call con [azienda]", "come approcciare [settore]".

**Azioni orchestrate**:
1. Raccogli info aziendali: sito, LinkedIn, settore, fatturato stimato (Cerved/Leanus) → web search + benchmark-italia-business
2. Identifica pain tipici del settore → marketing-strategico (orientamenti impresa) + benchmark-italia-business
3. Prepara approccio psicologicamente calibrato → psicologia-marketing (Pattern E: vendita e negoziazione)
4. Produci: messaggio LinkedIn outreach personalizzato, agenda discovery call 30 min, lista 8-10 domande diagnostiche, ipotesi pain dominanti da validare

**Output tipico**:
```
## Prospect: [Azienda]
**Profilo**: [settore, dim, posizionamento]
**Pain ipotizzati**: [3 ipotesi ordinate per probabilità]
**Messaggio LinkedIn iniziale** (max 300 caratteri)
**Agenda call 30 min**:
  - 5 min contesto
  - 10 min diagnosi (domande guidate)
  - 5 min visione obiettivo
  - 5 min proposta Radar Audit
  - 5 min obiection handling + next step
**Domande diagnostiche**: [8-10 domande aperte]
**Prezzo da proporre**: Radar 1.900 € (se settore/dimensione compatibile)
```

**Skill principali**: `psicologia-marketing` + `marketing-strategico` + `benchmark-italia-business`
**Skill di supporto**: web search per contesto cliente

---

### Fase 2 — Radar Audit (delivery entry-point in 5 giorni)

**Trigger utente**: "prepara Radar Audit per [cliente]", "nuovo audit", "inizia audit [azienda]".

**Azioni orchestrate** (ordine rigoroso, 5 giorni):

#### Giorno 1 — Raccolta dati e audit digitale
- Raccogli accessi: GA4, Search Console, GBP, Ads account, CRM, email tool
- Esegui audit tecnico sito → `digital-marketing-performance` (sezione On-Page + Technical)
- Audit SEO Italia → `seo-italia` (GBP, directory IT, NAP, schema)
- Test AI visibility (ChatGPT/Perplexity/Google AI Overview) → `seo-italia`

#### Giorno 2 — Competitor e benchmark
- 3 competitor principali: posizionamento, traffico, keyword, AI visibility → `strategia-competitiva` + `seo-italia`
- Benchmark di settore italiano → `benchmark-italia-business`
- KPI tree proposta → `marketing-analytics` (attribution, funnel)

#### Giorno 3 — Posizionamento e brand
- Analisi brand personality attuale (Big Five) → `marketing-strategico`
- Trust assessment → `marketing-bocconi-trust`
- Diagnosi POP/POD e anti-posizionamento → `marketing-strategico`
- Piano 90 giorni prioritizzato → `marketing-strategico` (template piano) + `psicologia-marketing` (priorizzazione per impatto/effort)

#### Giorno 4 — Redazione deliverable
- Compila template Radar Audit (file 02) capitoli 1-7
- Capitolo 8 (teaser retainer 12 mesi) → **CRITICO**: questo è il pezzo che converte in retainer
- Executive summary 2 pagine
- PDF brandizzato K2-AI

#### Giorno 5 — Consegna
- Setup Notion condiviso con piano 90 giorni
- Call presentazione 90 min: 60 min report + 30 min teaser retainer (proposta commerciale integrata)
- Proposta retainer Growth (default) o Pro (se fatturato >8M) con CTA chiaro

**Skill principali**: tutte le skill marketing in sequenza coordinata. Vedi tabella skill-per-capitolo nel file 02-Template-Radar-Audit.

**Deliverable**:
- PDF 30-40 pagine brandizzato
- Executive summary 2 pagine
- Piano 90 giorni in Notion
- Registrazione presentazione
- Proposta retainer allegata

**Tempo target**: 32-40 ore di lavoro effettivo distribuite su 5 giorni solari.

**Check qualità pre-consegna**:
- [ ] Ogni raccomandazione ha impatto stimato + effort
- [ ] Capitolo 8 (teaser retainer) presente e convincente
- [ ] Nessun errore dati su cliente
- [ ] Benchmark cited con fonti
- [ ] AI visibility test incluso (differenziatore K2-AI)
- [ ] Tono: competente, diretto, italiano chiaro

---

### Fase 3 — Closing e firma retainer

**Trigger utente**: "cliente ha ricevuto audit, aspetto risposta", "cliente chiede sconto", "obiezioni su retainer", "prepara contratto per [cliente]".

**Azioni orchestrate**:

#### Gestione obiezioni comuni (script pronti)

| Obiezione cliente | Risposta orchestrata |
|---|---|
| "Costa troppo" | Applica `psicologia-marketing` (reframing: confronto con marketing manager interno 35-50k/anno, scomposizione prezzo giornaliero, TCO a 12 mesi vs risultato atteso) |
| "Voglio provare 1-2 mesi" | Spiega razionale 6 mesi minimi: i primi 2 mesi sono fondazione, risultati visibili mese 4+. Alternativa: 6 mesi ma con break point a mese 3 con review |
| "Mi manda qualche case study" | Se nuovo: proponi altre 2 chiamate con clienti attivi (permesso). Se ne hai: 3 case study rilevanti per dimensione/settore. `marketing-bocconi-trust` per autorità dimostrata |
| "Ci devo pensare" | `psicologia-marketing` scarcity vera: slot disponibili per il mese, primi 30 giorni con quick wins gratuiti, scadenza proposta 14 giorni |
| "Voglio un mese di prova gratis" | Rifiuta professionalmente: "Gli audit li paghi perché producono valore. I retainer partono pagati perché il valore inizia dal giorno 1. Se vuoi testare il nostro approccio, c'è il Radar Audit" |
| "Lo fa anche mio cugino / un'agenzia low-cost" | `strategia-competitiva`: differenziazione. Non competiamo sul prezzo ma sulla combinazione strategia+esecuzione+AI. Se cerca solo esecuzione a basso costo, non siamo fit |

#### Produzione lettera d'incarico retainer

Template con sezioni:
1. Parti (K2-AI + cliente)
2. Oggetto: servizio retainer [tier] per X mesi
3. Scope dettagliato (da file 01 catalogo servizi)
4. Corrispettivi e tempistiche pagamento (pagamento anticipato mensile o trimestrale)
5. Durata e rinnovo
6. Proprietà intellettuale (deliverable di proprietà cliente, framework K2-AI)
7. Riservatezza reciproca
8. Privacy e GDPR (K2-AI come responsabile del trattamento dati cliente) → `it-law-privacy-ai`
9. Limitazione responsabilità
10. Clausole di uscita: 30 gg preavviso dopo il minimo 6 mesi
11. Legge applicabile + foro competente

**Skill principali**: `psicologia-marketing` + `it-law-privacy-ai` + `diritto-italiano` (solo per contratto)

---

### Fase 4 — Onboarding retainer (primi 7 giorni dopo firma)

**Trigger utente**: "kickoff [cliente]", "onboarding [cliente]", "primo mese [cliente]".

**Azioni orchestrate**:

#### Giorno 1 — Kickoff call (90 min)
Agenda:
- Presentazione team K2-AI e referenti cliente
- Review piano 90 giorni concordato (derivato da Radar Audit)
- Allineamento aspettative: tempi, frequenze, canali comunicazione
- Accessi: GA4, Search Console, GBP, Ads, CRM, email tool, sito CMS
- Credenziali salvate in password manager sicuro
- Canale Slack/Teams condiviso creato

#### Giorno 2-3 — Setup tracking e misurazione
- Verifica GA4 + Consent Mode v2 → `seo-italia` + `it-law-privacy-ai`
- Setup Looker Studio dashboard cliente-specifica → `marketing-analytics`
- Tag Manager audit + pulizia eventi non utilizzati
- Baseline KPI del mese 0 (per misurare delta)

#### Giorno 4-5 — Quick wins attivati
Dai il segnale che "sta già succedendo qualcosa":
- Fix title/meta 10 pagine chiave
- Setup GBP se mancante, foto aggiornate
- Attivazione recensioni Google (link in firma email)
- Cookie banner conforme Garante se mancante

#### Giorno 6-7 — Piano mese 1 consegnato
- Documento "Piano mese 1" in Notion condiviso con owner + deadline
- Primo report settimanale con quick wins completati
- Schedulazione call mensili ricorrenti (Starter: 1/mese; Growth: 2/mese; Pro: 4/mese)

**Skill principali**: `marketing-strategico` (piano) + `digital-marketing-performance` (setup tracking) + `seo-italia` (GBP, Consent Mode) + `marketing-analytics` (dashboard)

**Deliverable onboarding**: documento onboarding 5 pagine consegnato al cliente, dashboard condivisa attiva, piano mese 1 approvato.

---

### Fase 5 — Delivery retainer mensile

**Trigger utente**: "piano mensile per [cliente]", "cosa devo fare questo mese per [cliente]", "attività retainer [cliente]".

**Azioni orchestrate** — workflow mensile per tier:

#### Workflow Starter (4h/mese)
- Settimana 1: call strategica 60 min + review KPI → `marketing-strategico` + `marketing-analytics`
- Settimana 2: deliverable del mese (audit puntuale, revisione copy, analisi competitor) → skill specifica a richiesta
- Settimana 3: assistenza asincrona via email
- Settimana 4: mini-report mensile 2 pagine + raccomandazione mese successivo

#### Workflow Growth (12h/mese) — pacchetto standard
- Settimana 1:
  - Call strategica 1/2 (60 min): review mese precedente + piano mese corrente
  - Ottimizzazione 4 pagine SEO → `seo-italia` + `digital-marketing-performance`
  - Setup/ottimizzazione campagne ads bimestrali → `digital-marketing-performance` + `psicologia-marketing` (copy)
- Settimana 2:
  - 2 articoli SEO (1500 parole ciascuno) → `digital-marketing-performance` + `seo-italia` + `psicologia-marketing`
  - 8 post social pianificati
- Settimana 3:
  - Call strategica 2/2 (60 min)
  - 1 newsletter (segmented, con CTA) → `digital-marketing-performance` + `psicologia-marketing`
  - A/B test su landing / ads
- Settimana 4:
  - Report mensile 8-12 pagine brandizzato → `marketing-analytics` + template K2-AI
  - Piano mese successivo

#### Workflow Pro (28h/mese)
- Settimana 1: call settimanale + revisione strategica + piano podcast/video
- Settimana 2: call settimanale + content pillar + campagne multi-canale + digital PR
- Settimana 3: call settimanale + analytics approfonditi (CLV, CAC, attribution)
- Settimana 4: call settimanale + report direzionale + allineamento CdA
- Trimestrale: presenza CdA / meeting direzionali del cliente

**Skill principali coordinate**: tutte le marketing-* + `crm-customer-experience` per retention + `it-law-privacy-ai` per compliance tracking

---

### Fase 6 — Quality control e revisione trimestrale

**Trigger utente**: "review trimestrale [cliente]", "cliente non vede risultati", "KPI non migliorano", "rinnovo retainer".

**Azioni orchestrate**:

#### Check salute cliente (ogni 3 mesi)
1. KPI tree: andamento vs baseline → `marketing-analytics`
2. NPS cliente (survey 1 domanda via email)
3. Marginalità ore-per-cliente (controllo interno): se ore > ore-pacchetto + 20%, alert per rinegoziazione
4. Engagement nei canali comunicazione (call presentate, feedback, decisioni)

#### Se cliente churned-at-risk
1. Diagnosi: perché non è soddisfatto? (pricing, risultati, comunicazione, fit)
2. Intervento correttivo: call direzionale + piano di recovery
3. Se pricing: proposta downgrade temporaneo (Growth → Starter per 3 mesi)
4. Se risultati: review obiettivi (erano realistici? orizzonte temporale giusto?)
5. Se fit: uscita pulita con transizione ad altro partner (protegge reputazione)

**Skill principali**: `marketing-analytics` + `psicologia-marketing` (Pattern E negoziazione) + `crm-customer-experience` (churn management)

---

### Fase 7 — Upsell, cross-sell, referral

**Trigger utente**: "upsell [cliente]", "cliente Growth pronto per Pro", "proposta add-on", "referral".

**Azioni orchestrate**:

#### Upsell tier (Starter → Growth, Growth → Pro)
Indicatori che il cliente è pronto:
- Fatturato cresciuto → budget marketing cresce
- Complexity aumentata (nuovo mercato, nuovo prodotto)
- Cliente chiede attività fuori scope frequentemente
- Team cliente più maturo sul marketing

Proposta: review strategica 60 min con scenario "cosa potremmo fare con il tier superiore" + calcolo ROI incrementale.

#### Cross-sell add-on (per tutti i tier)
Add-on tipici da proporre:
- Nuovo sito (4.500–7.500 €): sito vecchio di >3 anni
- Brand refresh (3.500 €): mismatch brand personality rilevato nel Radar
- Sales funnel B2B (3.800 €): cliente B2B con ciclo vendita lungo
- Formazione team (2.400 €): team interno cliente in crescita
- SEO deep audit (2.500 €): dopo 6-12 mesi di retainer, per upgrade strategico

#### Referral program clienti
- Sconto 10% retainer per 3 mesi in cambio di referral convertito
- Case study congiunto (con consenso)
- Offerta commerciale dedicata al contatto segnalato

**Skill principali**: `marketing-strategico` + `psicologia-marketing` (reciprocità per referral) + `corporate-finance` (calcolo ROI upsell)

---

## Decision tree per tipologia cliente

Quando un nuovo cliente entra, adatta il mix skill in base al profilo:

### Cliente B2B industriale/manifatturiero
Skill enfatizzate:
- `marketing-strategico` (STP B2B macro/micro, derived demand)
- sezione B2B in marketing-strategico (buying center, ABM, MEDDIC)
- LinkedIn B2B → `digital-marketing-performance`
- Content tecnico, white paper, case study
- `benchmark-italia-business` (se manifatturiero: ha dati dedicati)

### Cliente B2C e-commerce
Skill enfatizzate:
- `digital-marketing-performance` (funnel, CRO, ads)
- `psicologia-marketing` (copy prodotto, CTA, abbandono carrello)
- `marketing-analytics` (CLV, RFM, cohort)
- `crm-customer-experience` (retention, loyalty)
- `seo-italia` (local se store fisici + e-commerce, schema Product)

### Cliente B2C servizi locali (ristoranti, studi, negozi)
Skill enfatizzate:
- `seo-italia` (local SEO, GBP, directory IT, TripAdvisor/TheFork se food)
- `marketing-bocconi-trust` (trust + recensioni)
- `digital-marketing-performance` (Google Ads local, Meta geotargeting)
- `psicologia-marketing` (riprova sociale, scarsità, prova esperienziale)

### Cliente professionisti (studi legali, commercialisti, medici)
Skill enfatizzate:
- `marketing-strategico` (services marketing IHIP, 7P, SERVQUAL)
- `marketing-bocconi-trust` (fiducia come risorsa)
- `it-law-privacy-ai` (vincoli deontologici pubblicità professionale)
- `digital-marketing-performance` (contenuto educativo, lead magnet)
- `psicologia-marketing` (autorità dimostrata, non dichiarata)

### Cliente settore creativo/culturale
Skill enfatizzate:
- `marketing-settori-creativi` (experience goods, co-produzione)
- `psicologia-marketing` (storytelling emozionale)
- `marketing-strategico` (brand personality + narrative)

### Cliente PMI in internazionalizzazione
Skill enfatizzate:
- `marketing-strategico` (international marketing, CAGE, Hofstede)
- `seo-italia` (hreflang IT/EN, SEO internazionale)
- `digital-marketing-performance` (LinkedIn B2B internazionale, ABM)
- `consulente-policy-ue` (se export UE)

---

## Output template standardizzati K2-AI

Per coerenza di brand e velocità di delivery, usa sempre questi formati:

### Template "Proposta commerciale K2-AI"
```
# Proposta K2-AI per [Cliente]
Data: [data] | Validità: 14 giorni

## Il vostro obiettivo
[1 paragrafo — riformula quello che il cliente ha detto]

## La nostra proposta
Pacchetto consigliato: K2-AI [Tier]
Investimento: [€]/mese per [X] mesi minimi

## Cosa riceverete ogni mese
[Scope dal catalogo]

## Roadmap primi 90 giorni
[Estratto dal Radar Audit]

## Risultati attesi a 6-12 mesi
[Range realistico con disclaimer]

## Prossimi passi
1. Firma lettera d'incarico entro [data]
2. Kickoff call il [data]
3. Primo report mensile il [data]

## Perché K2-AI
[3 proof points, differenziazione vs agenzie/freelance]
```

### Template "Report mensile retainer"
```
# Report mensile K2-AI — [Cliente] — [Mese/Anno]

## Executive summary
- KPI chiave del mese: [delta % vs mese precedente]
- 3 successi del mese
- 2 aree di attenzione
- Priorità mese successivo

## Attività svolte
[Dettaglio con ore e owner]

## KPI dashboard
[Tabella metriche: traffico, lead, conversion, ROAS, ecc.]

## Approfondimento del mese
[1 topic strategico — es. "Come sta performando la nuova landing"]

## Piano mese successivo
[Azioni concrete con timing]

## Budget update
[Speso vs pianificato]
```

### Template "Script discovery call"
```
[0-5 min] Rompighiaccio + contesto
- "Come avete conosciuto K2-AI?"
- "Cosa vi ha fatto decidere di parlarne ora?"

[5-15 min] Diagnosi
- "Raccontatemi il vostro marketing attuale"
- "Quali canali vi portano clienti oggi?"
- "Cosa non funziona che vorreste cambiare?"
- "Quanto spendete in marketing ora — tra interni, freelance, tool?"

[15-20 min] Obiettivo + vincoli
- "Dove vorreste essere tra 12-24 mesi?"
- "Quali vincoli avete — budget, tempo, team?"

[20-25 min] Proposta Radar Audit
- Presentazione servizio e prezzo (1.900 €)
- Cosa include, cosa no
- Timing (5 giorni)

[25-30 min] Next step
- "Se siete interessati, vi mando la lettera d'incarico oggi e partiamo la prossima settimana"
- Gestione obiezioni
- Chiusura: appuntamento o follow-up scadenza
```

---

## Quality control K2-AI (pre-delivery check)

Ogni deliverable passa 3 filtri prima di andare al cliente:

### Filtro 1 — Tecnico
- [ ] Dati verificati con fonti citate
- [ ] Nessun errore su nome cliente, numeri, date
- [ ] Tutti i link funzionanti
- [ ] Formattazione coerente al brand K2-AI

### Filtro 2 — Valore cliente
- [ ] Ogni raccomandazione ha impatto + effort stimati
- [ ] Priorità chiara (quick win vs strategic)
- [ ] Azionabilità: il cliente può iniziare domani?
- [ ] Lingua: italiano chiaro, no jargon inutile

### Filtro 3 — Posizionamento K2-AI
- [ ] Brand K2-AI visibile ma non invadente
- [ ] Tono: competente, diretto, professionale
- [ ] Differenziazione chiara (strategia + AI + senior)
- [ ] Teaser upsell presente se rilevante

---

## Segnali di allarme da gestire subito

Quando durante una consulenza emergono questi segnali, interrompi il workflow standard e applica la procedura dedicata:

| Segnale | Azione |
|---|---|
| Cliente chiede attività fuori scope ripetutamente | Call direzionale + proposta upsell o chiarimento scope |
| KPI peggiorano 2 mesi consecutivi | Intervento correttivo + review piano strategico |
| NPS cliente < 7 | Call soddisfazione + diagnosi root cause |
| Cliente smette di rispondere | 3 follow-up graduali, se non risponde → call diretta |
| Cliente chiede sconto retainer | Mai scontare il prezzo base. Proporre downgrade tier o break temporaneo |
| Referenti cliente cambiano | Re-kickoff con nuovo referente, non dare per scontato allineamento |
| Cliente vuole ritirare accessi tool | Red flag serio: cliente vuole uscire. Call urgente |

---

## Integrazione con altre skill (cross-reference)

Questa skill orchestra ma non duplica. Per contenuti specifici rimanda a:

- Posizionamento, brand, piano marketing, 4P, STP, Big Five → `marketing-strategico`
- SEO italiana (GBP, directory IT, AI SEO, Consent Mode) → `seo-italia`
- SEO/SEM generico, ads, email, CRO, growth → `digital-marketing-performance`
- Modelli quantitativi (CLV, attribution, PID, PCA) → `marketing-analytics`
- Copy persuasivo, CTA, UX psychology → `psicologia-marketing`
- Trust, fiducia, Castaldo → `marketing-bocconi-trust`
- Analisi competitor (5 forze, raggruppamenti) → `strategia-competitiva`
- Benchmark settoriali italiani → `benchmark-italia-business`
- GDPR, cookie, Garante → `it-law-privacy-ai`
- CRM, loyalty, journey, retention → `crm-customer-experience`
- Contratto retainer, privacy, foro → `diritto-italiano`
- ROI marketing, payback, margini → `corporate-finance`
- Settori creativi/culturali → `marketing-settori-creativi`
- Formati documenti: PDF report → `pdf`; slide presentazione → `pptx`; report dati → `xlsx`; lettera d'incarico → `docx`

---

## Metriche di successo dell'orchestratore K2-AI (self-monitoring)

Questa skill funziona bene se, trimestralmente, si misurano:

- **Conversion Radar Audit → retainer**: target ≥ 40%
- **Tempo medio Radar Audit**: target ≤ 40 ore/audit
- **Tempo medio mensile per tier**: Starter ≤ 4h, Growth ≤ 14h, Pro ≤ 32h
- **Churn rate 6 mesi retainer**: target ≤ 15%
- **NPS cliente medio**: target ≥ 50
- **MRR growth**: target +15%/mese in fase early, +5%/mese a regime

Se un cliente richiede sistematicamente ore molto superiori al pacchetto, suggerisci **upsell tier** o **ridefinizione scope**. Se un tier ha churn > 20%, suggerisci **review del pricing o dello scope** del pacchetto.
