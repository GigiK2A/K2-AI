# Se lasciassi K2-AI gestita dall'AI — simulazione reale, read-only

_Generato il 2026-06-07 · 1 ciclo operativo ("una giornata") · autonomia L1 (solo proposte)._

## In breve

Questo non e' uno scenario inventato: e' una **esecuzione reale** dei 6 agenti di dominio di K2-AI (marketing, vendite, finance, operations, legal, hr) sui **dati veri** presenti nel sistema. Ogni agente ha letto i propri sensori e ha prodotto proposte tramite LLM (Claude Haiku). Tutto in **sola lettura**: nessuna scrittura su database, nessun pagamento, nessuna azione eseguita.

In **un solo ciclo** l'AI ha messo in coda **51 decisioni** che aspettano l'ok umano. Nessuna e' stata approvata: con l'autonomia attuale (L1) l'AI **propone, non agisce**. Tempo macchina totale: **251 secondi**.

- Reparti che hanno prodotto proposte: **6/6**
- Proposte che diventerebbero una **scrittura operativa mirata** su una tabella interna: **3**
- Proposte che restano **comunicazione/analisi** (diventano un task da validare): **48**
- Deliverable gia' archiviati nel sistema prima di oggi: **0**

### Proposte per tipo (reali)

- `processo`: 5
- `dashboard`: 2
- `KPI_e_digest`: 1
- `account_research`: 1
- `accounts_receivable`: 1
- `alert_assicurazioni`: 1
- `alert_contratti`: 1
- `alert_gdpr_kbot`: 1
- `alert_marchi`: 1
- `analytics`: 1
- `analytics / win_loss`: 1
- `audit_board`: 1
- `audit_consensi_kbot`: 1
- `audit_fornitori_dpa`: 1
- `audit_gdpr`: 1
- `automation`: 1
- `autorità_e_traffico`: 1
- `blocco_critico`: 1
- `cash_control`: 1
- `change_management`: 1
- `compliance_policy`: 1
- `content`: 1
- `controllership`: 1
- `cost_control`: 1
- `creative`: 1
- `demand_gen`: 1
- `discovery`: 1
- `documentazione`: 1
- `enablement`: 1
- `forecasting`: 1
- `gestione_risorse`: 1
- `kpi`: 1
- `lead_gen / qualification`: 1
- `paid`: 1
- `pipeline_mgmt`: 1
- `pr`: 1
- `product_mkt`: 1
- `qualification`: 1
- `research`: 1
- `revenue`: 1
- `social`: 1
- `strategia`: 1
- `strategy`: 1
- `tax_compliance`: 1
- `tracciamento_rischi`: 1
- `visibilità_operativa`: 1

### Riepilogo per reparto

| Reparto | Sensori ok/tot | Righe lette | Proposte | di cui scrittura DB | Tempo |
|---|---|---|---|---|---|
| Marketing (CMO) | 19/19 | 138 | 11 | 0 | 60.6s |
| Vendite / CRM (CRO) | 8/8 | 87 | 8 | 2 | 33.4s |
| Finance (CFO) | 11/11 | 25 | 8 | 1 | 41.8s |
| Operations (COO) | 8/8 | 61 | 8 | 0 | 35.7s |
| Legal & Compliance | 11/11 | 5 | 8 | 0 | 37.0s |
| HR / People (CHRO) | 10/10 | 101 | 8 | 0 | 42.3s |

---

## Cosa farebbe ogni reparto, nel dettaglio

### Marketing (CMO)

**Cosa ha letto (dati reali):** `leggi_servizi` (25), `leggi_topics` (15), `leggi_profilo_ig` (4), `leggi_post_ig` (6), `leggi_insight_ig` (4), `leggi_calendario` (1), `leggi_iscritti` (4), `leggi_newsletter` (7), `leggi_analytics` (4), `leggi_voce_clienti` (25), `leggi_funnel_web` (7), `leggi_brand_mentions` (15), `leggi_calendario_contenuti` (1), `leggi_suite` (20).
**Sensori vuoti (0 righe):** `leggi_ranking_seo`, `leggi_competitor_web`, `leggi_ads_meta`, `leggi_ads_google`, `leggi_costi`.

**Cosa PROPONE (11 azioni, tutte da approvare):**

- **Diagnosi funnel: bottleneck tra apertura e conversione** — Dati PostHog mostrano 18 session_created ma zero report_generated nei giorni analizzati. Il K-BOT ha un funnel collapse a valle dell'interazione. Proposta: ins…
- **Ridurre hashtag spam, aumentare reach con nomi di problemi concreti** — I post IG hanno 2 like su 6 followers (engagement <0.3%). Analisi: caption usa 9-11 hashtag generici (#DigitalTransformation, #AIperPMI) che non targetizzano l…
- **Convertire voice-of-customer K-BOT in 3 articoli pillar da mesi** — Sessione K-BOT ha estratto il brief perfetto: pubblico = proprietari immobili + PMI locali; tono professionale semplice; mix 60% servizi / 40% formazione. Prop…
- **Nutrire 4 iscritti newsletter attivi con sequenza email da 30 giorni** — Hai 3 email confermati attivi + 1 da riconfermare. Proposta: inviare sequenza nurture settimanale specifico per each persona (non broadcast massa). Es.: lunedì…
- **Posizionare P01 (Email & CRM) come entry point, non commodità** — Email & CRM è il servizio più tangibile e rapido a ROI (70% email auto, 2 min risposta). Proposta messaging: invece di «Automatizza le email», dire «Le tue com…
- **Test Meta Ads: 300€/mese su 3 audience micro per demand gen Email & CRM** — [strategia: dati non collegati – non ho budget spend storico]. Proposta operativa: investire 300€/mese (10€/giorno) su Meta (Instagram + Facebook) per 30 giorn…
- **Configurare UTM standard e taggare tutti i canali + impostare CRM sync** — Newsletter, IG, blog, landing non hanno UTM parametri tracciati. Proposta: standard globale K2-AI: utm_source (email, instagram, blog, paid-meta, direct); utm_…
- **Creare 2 asset + prompt per carousel IG settimanale su casi concreti** — [strategia: visual concept non ho storico]. Proposta: creare brief per 2 carousel settimanali alternati su temi: (1) prima/dopo: «2 ore al giorno in email spaz…
- **Scouting: brand mention da AgendaDigitale + Fastweb, ma ripubblicati su news aggregator** — Hai 3 mention in Google News (Agenda Digitale, Fastweb) ma sono su modelli AI cinesi (Kimi K2), non su K2-AI. False positive nei dati. Proposta: (1) configurar…
- **Piano trimestrale T3 2026: 4 pilastri demand gen, priorità Email & CRM + lead nurture** — Sintesi strategica di cui sopra: (1) Aumentare qualified lead da 4 a 20+ iscritti newsletter attivi, con nurture sequenza 30gg, CTR 25%+ (Iulio-agosto). (2) La…
- **Survey 1-domanda su 4 iscritti: «Qual è il dolore #1 nel tuo ruolo?»** — [strategia: dati non collegati]. Proposta: inviare email personale ai 4 iscritti attivi con subject «Chiedo 2 min: aiutami a capire il tuo lavoro». Body: una s…

**Impatto atteso (qualitativo):** decisioni basate su dati, non a sensazione, presenza social piu' curata, pipeline contenuti alimentata, generazione domanda dalla pipeline, messaggi prodotto piu' chiari, ipotesi su canali a pagamento (da validare), igiene dati e workflow, meno lavoro manuale, brief/asset creativi pronti, monitoraggio reputazione/menzioni, piano che lega le iniziative, voce del cliente raccolta.
_Nessuna di queste tocca direttamente una tabella operativa: sono analisi e comunicazioni che diventerebbero task da validare._
> Stato: **da approvare**. Niente e' stato eseguito.

### Vendite / CRM (CRO)

**Cosa ha letto (dati reali):** `leggi_lead` (15), `leggi_memo_vendite` (20), `leggi_clienti` (4), `leggi_lead_kbot` (28), `leggi_suite` (20).
**Sensori vuoti (0 righe):** `leggi_ricavi_chiusi`, `leggi_inbox`, `leggi_calendario_google`.

**Cosa PROPONE (8 azioni, tutte da approvare):**

- **Qualificare Mario Rossi (Studio XYZ) — ICP match chiaro** — Mario ha scritto un pain point specifico: 'automatizzare onboarding clienti manuale e lento'. Studio di servizi professionali (5-50 dipendenti presumibili) in…
- **Ricerca LinkedIn + web su Studio XYZ — dati mancanti: size, revenue, stakeholder** — [strategia: dati non collegati] Prima di qualsiasi contatto, verifica: (1) n. dipendenti via LinkedIn; (2) servizi offerti (legal, consulting, tax?); (3) se es…
- **Preparare 3 domande discovery per Mario — focus ROI onboarding** — Quando contatti (via task sopra), poni: (1) 'Quanti clienti acquisite/mese e quanto tempo impiega oggi l'onboarding cartaceo?'; (2) 'Chi decidere se implementa…
- **Ripulire lead da test — 7 su 9 sono mock, 0 fit** — Analisi CRM: 7 lead (Test, Test User, Test Contatti, Direct Test, Proxy Test 2, mario@test.it, luigi@gmail.com 'studio legale') sono test/noise. Solo Mario Ros…
- **Creare battlecard — Automazione onboarding per studi professionali** — [strategia: dati non collegati] Dati mancano: fatturato/caso tipo Mario, timeline implementazione, costi infrastruttura. Bozza battlecard: Pain: 'onboarding ma…
- **Stato pipeline: 1 lead qualificabile, 8 rumore. Forecast: FERMO** — Snapshot attuale: • Opportunities in pipeline = 0 (nessun lead ha scadenza close, value_eur, o stage avanzato). • Lead → Qualified: solo Mario (score 8, in dis…
- **Forecast 30/60/90gg: €0 fino a Mario conversion** — [strategia: dati non collegati] Numeri: • Opportunities chiuse anno corrente = 0. • Value in pipeline tracciabile = €0. • Probability weighted value = €0. • Be…
- **Analytics baseline: 0 dati storici, setup tracking obbligatorio** — [strategia: dati non collegati] CRM ha zero traccia di: win/loss reasons, ciclo medio, conversion per stage, churn rate. Setup urgente: (1) aggiungere campo 'r…

**Impatto atteso (qualitativo):** fit ICP e priorita' lead, voce del cliente raccolta, azione operativa concreta da valutare, lead caldi intercettati, igiene pipeline, lead fermi sbloccati, previsione vendite pesata, decisioni basate su dati, non a sensazione.
_2 di queste, se approvate, scriverebbero direttamente su una tabella operativa interna (es. pipeline lead, fatture, task di commessa); le altre diventerebbero task da lavorare._
> Stato: **da approvare**. Niente e' stato eseguito.

### Finance (CFO)

**Cosa ha letto (dati reali):** `leggi_conversioni` (4), `leggi_valore_commesse` (1), `leggi_suite` (20).
**Sensori vuoti (0 righe):** `leggi_revenue`, `leggi_memoria_finance`, `leggi_costi`, `leggi_stripe_ricavi`, `leggi_stripe_saldo`, `leggi_fatture`, `leggi_giornale`, `leggi_organico`.

**Cosa PROPONE (8 azioni, tutte da approvare):**

- **Stripe non collegato — revenue tracking offline** — I dati Stripe sono vuoti (leggi_stripe_ricavi, leggi_stripe_saldo assenti). Senza integrazione, non vediamo incassi reali né cash position. MRR da K-BOT conver…
- **Treasury: runway assunto vs reale — stress test 30gg** — [strategia: dati non collegati] Senza Stripe e senza memory finance, assumo: - Team tech ridotto (1-2 dev?), budget SaaS ~65€/mese (anomalia evidente: irrisori…
- **Budget SaaS 65€/mese — impossibile, risanare** — Il dato indicato (budget tech 65€/mese) è irrealistico per un'azienda AI che deve pagare: - Cloud (AWS/Vercel/Railway): minimo 200-400€ - LLM API (OpenAI, Anth…
- **Calendario adempimenti fiscali Apr-Giu 2026 — scadenze in 5-15gg** — [9_tax_compliance_IT] Aprile-Maggio critico: - IVA mensile scadenza 16 aprile (5 giorni fa — CONTROLLARE se in bonis) - LIPE trimestrale (1° trim): scadenza 20…
- **B&B COM in bonis? Fatture, termini, solleciti** — Commessa B&B COM (status active, valore=null, progress=0%) è nera: - Valore non registrato - Progress 0% suggerisce non è stata ancora fatturata OR fattura non…
- **MRR e KPI vendita: 4 contatti, nessuno quantificato in €** — [6_kpi] K-BOT conversions di aprile: - 4 path_b_contact registrate (25, 23 apr) - 0€ di valore dichiarato - 2 email valide (test@k2ai.com è interna, rluigiluca…
- **Riconciliazione costi vs suite — budget inesistente per suite K2A** — Ledger costi è vuoto (leggi_costi assente). Eppure K2-AI produce 17 prodotti (P01-P17, suite HOST/WEB/STUDIO). Costi allocabili: - Dev time per maintenance/bug…
- **Month-end close Apr 2026: checklist completa — DATO ZERO** — [7_month_end_close] Chiusura mese standard: ✗ Riconciliazione estratto conto bancario vs ledger ✗ Incassi fatture (AR aging) — B&B COM UNKNOWN ✗ Pagamenti forn…

**Impatto atteso (qualitativo):** azione operativa concreta da valutare, spesa SaaS sotto la soglia, rischio normativo ridotto, incassi sollecitati.
_1 di queste, se approvate, scriverebbero direttamente su una tabella operativa interna (es. pipeline lead, fatture, task di commessa); le altre diventerebbero task da lavorare._
> Stato: **da approvare**. Niente e' stato eseguito.

### Operations (COO)

**Cosa ha letto (dati reali):** `leggi_commesse` (1), `leggi_fasi` (4), `leggi_documenti` (2), `leggi_task_operativi` (54).
**Sensori vuoti (0 righe):** `leggi_task_commessa`, `leggi_team`, `leggi_change_requests`, `leggi_strumenti`.

**Cosa PROPONE (8 azioni, tutte da approvare):**

- **Commessa B&B Com — nessun milestone e nessuna stima: definisci il piano entro domani** — Commessa attiva da 7 giorni (start 2026-04-07), progress 0%, 4 fasi tutte 'pending' senza date stimate né completate. Client non sa quando consegnerai. Dati ma…
- **15 lead in coda dal form — assegnali e filtra noise entro 48h** — Task operativi: 15 'Nuovo lead dal sito' tutti pending e assegnati genericamente a 'lead_generation', più 6 'Diagnosi K-BOT' assegnate a 'solution_architect' (…
- **Carica subito la capacity della tua squadra — 3 persone, quante ore/settimana ciascuno?** — Zero visibilità su chi fa cosa. Vedo task assegnate a 'lead_generation', 'solution_architect', 'orchestrator' come team, non a persone. B&B Com in progress, 15…
- **Monitora B&B Com: setup alert su slittamenti (ritardo >2gg warning, >5gg CRITICO)** — B&B Com non ha nemmeno date stimate, quindi non puoi fare warning automatico quando una fase scivola. Oggi impossibile sapere se Discovery slitterà: non c'è bl…
- **B&B Com: ogni fase chiusa = checkpoint documentazione (design doc, test result, consegna…** — Vedo 2 doc uploadati il 7 aprile (guida-tecnica-interna.html, proposta-commerciale), ma nessun piano documentazione per le 4 fasi. Chi prepara il doc di conseg…
- **Blog pillar: copia esatto del messaggio B&B Com in un articolo 'Quanto dura davvero una c…** — [S] Strategia: il B&B è un case fragile (discovery spesso 'vago', cliente impreparato). Trasformalo in articolo pillar: quanto tempo serve, step per step, cosa…
- **Crea template: quando il cliente chiede scope change, rispondi in <4h con impatto giorni…** — Zero visible process. Se B&B Com client domani chiede 'aggiungi modulo booking', chi valuta? Chi dice sì/no? Quanto costa? Quanti giorni aggiungi?
- **Rilancia ops_digest settimanale: founder vede ogni lunedì ore 08:00 — Telegram, max 5 met…** — [S] Oggi zero visibilità operativa centralizzata. Luigi non sa: quante commesse active, quali in ritardo, capacity utilization, on-time delivery %, revenue pip…

**Impatto atteso (qualitativo):** azione operativa concreta da valutare.
_Nessuna di queste tocca direttamente una tabella operativa: sono analisi e comunicazioni che diventerebbero task da validare._
> Stato: **da approvare**. Niente e' stato eseguito.

### Legal & Compliance

**Cosa ha letto (dati reali):** `leggi_iscritti_newsletter` (4), `leggi_consensi_kbot` (1).
**Sensori vuoti (0 righe):** `leggi_documenti_legali`, `leggi_registro_trattamenti`, `leggi_fornitori`, `leggi_marchi`, `leggi_atti_societari`, `leggi_contenziosi`, `leggi_assicurazioni`, `leggi_formazione_compliance`, `leggi_policy`.

**Cosa PROPONE (8 azioni, tutte da approvare):**

- **Audit consensi newsletter: opt-in mancante e revoche attive** — Dai dati leggi_iscritti_newsletter emergono non conformità art. 7 GDPR: • luigilucarossi10@icloud.com: confirmed=false, is_active=true, newsletter_ai=true → ma…
- **Verifica dichiarazione AI Act art. 50 sul K-BOT (comunicazione trasparenza)** — La funzione 13 (termini & licenze) richiede: il K-BOT deve dichiarare chiaramente all'utente che interagisce con un sistema AI (art. 50 AI Act).  Dai dati legg…
- **Verifica opt-in marketing K-BOT: marketing_accepted=false, mancata registrazione timestamp** — Da leggi_consensi_kbot: luigilucarossi@gmail.com ha marketing_accepted=false e marketing_accepted_at=null. Ciò significa: l'utente ha esplicitamente RIFIUTATO…
- **Avvio monitoraggio scadenze contratti: check 60/30/7 giorni** — Funzione 1 (contratti). Dai dati leggi_documenti_legali risulta vuoto → non è stato centralizzato nessun contratto in registro compliance.  Azione strategica […
- **Audit fornitori art. 28 GDPR: verifica DPA e SCC per extra-UE** — Funzione 5 (fornitori/DPA). Dati leggi_fornitori: vuoto → nessun registro contratti processamento dati.  Azione strategica [S]: (1) Inventariare tutti i fornit…
- **Redazione Privacy Policy e Cookie Policy: K-BOT e toS conformi AI Act** — Funzione 13 (termini & licenze). Dati leggi_documenti_legali: vuoto. K2-AI opera con K-BOT ma non ha centralizzato documenti legali pubblici.  Azione: (1) Revi…
- **Verifica scadenze marchi K2-AI e K-BOT: rinnovi UIBM** — Funzione 8 (marchi). Dati leggi_marchi: vuoto → nessun tracking scadenze protezione marchio.  Azione strategica [S]: (1) Reperire certificati UIBM (Italian Pat…
- **Audit scadenze RC professionale e cyber insurance: coperture AI** — Funzione 14 (assicurazioni). Dati leggi_assicurazioni: vuoto → nessun registro polizze attive.  Azione strategica [S]: (1) Reperire copie polizze K2-AI in cors…

**Impatto atteso (qualitativo):** adempimento privacy presidiato, azione operativa concreta da valutare, scadenze contrattuali coperte, rischio normativo ridotto.
_Nessuna di queste tocca direttamente una tabella operativa: sono analisi e comunicazioni che diventerebbero task da validare._
> Stato: **da approvare**. Niente e' stato eseguito.

### HR / People (CHRO)

**Cosa ha letto (dati reali):** `leggi_assegnatari` (100), `leggi_skills` (1).
**Sensori vuoti (0 righe):** `leggi_dipendenti`, `leggi_candidati`, `leggi_ferie`, `leggi_review`, `leggi_formazione`, `leggi_sicurezza`, `leggi_offboarding`, `leggi_hr_analytics`.

**Cosa PROPONE (8 azioni, tutte da approvare):**

- **Template Recruiting + Screening CV — baseline per PMI** — Dati: candidati e job description vuoti. Propongo di creare 3 template operativi riutilizzabili:  1. **Job Description + Canali** — template con sezioni: ruolo…
- **Onboarding 30-60-90 gg — Piano strutturato** — Dati: employees vuoto. Propongo template onboarding con milestone concrete:  **Day 0-1:** Setup IT (email, VPN, strumenti), firma modulistica (CCNL, privacy, D…
- **HR Compliance + People Ops — Scadenzario automatico** — Dati: employees vuoto → strategia: dati non collegati. Creerò template Excel riempibile con:  **Colonne:** Dipendente | Data Assunzione | Fine Prova (alert -7g…
- **Payroll Coordination — Foglio Input Cedolino** — Dati: employees vuoto. Propongo template input payroll riutilizzabile:  **Foglio Input Mensile (Excel scaricabile):** Colonne: Dipendente | RAL CCNL | Giorni L…
- **Time & Attendance + Leave Management — Tracking Ferie/Permessi** — Dati: employees vuoto. Propongo sistema leggero:  **Foglio Centralizzato (Excel o Google Sheets):** Colonne: Dipendente | Ferie Diritto Annuo (CCNL: 20gg stand…
- **Performance Review Cycle + Calibrazione — Baseline annuale** — [strategia: dati non collegati — nessun dipendente in sistema]  Propongo ciclo annuale strutturato:  **Frequenza:** 1 review formale = Dicembre (fine anno) + 2…
- **Org Chart + Headcount Planning — Capacity vs Commesse** — Dati: employees vuoto. Propongo template planning:  **Org Chart (Excel):** Colonne: Posizione | Incumbent (nome) | Data Assunzione | Ruolo | Costo Annuo | Skil…
- **Offboarding Checklist — Uscita dipendente strutturata** — Dati: employees vuoto. Propongo checklist offboarding operativa:  **Timeline:** 2 settimane prima uscita: 1. Comunicazione IT: disattivare email, VPN, accessi…

**Impatto atteso (qualitativo):** azione operativa concreta da valutare.
_Nessuna di queste tocca direttamente una tabella operativa: sono analisi e comunicazioni che diventerebbero task da validare._
> Stato: **da approvare**. Niente e' stato eseguito.

---

## Cosa farebbe oggi l'AI in autonomia (se le dessi L2/L3)

Con l'autonomia attuale **L1** ogni proposta passa dall'approvazione umana. Salendo di livello, una parte di queste azioni potrebbe partire da sola. La linea di sicurezza la traccia gia' l'attuatore del kernel.

**Candidabili ad automazione (L2, basso rischio, reversibili):**

- Creazione di **task operativi** interni (board/commessa) a partire da segnali letti dai sensori: e' il caso piu' frequente in questo ciclo.
- **Igiene dati**: aggiornare lo stato di un lead fermo in pipeline, riconciliare una voce di costo, programmare una bozza in calendario contenuti.
- **Promemoria e alert** su scadenze (SAL di commessa, scadenze fiscali, rinnovi contratti): l'AI li accoda gia' come task, automatizzarli toglie lavoro manuale.

**Devono restare con approvazione umana (L1, sempre):**

- **Denaro**: qualsiasi movimento su ricavi, conversioni, Stripe. L'attuatore ha gia' queste tabelle in blocklist e non puo' scriverci.
- **Contratti e firme**: offerte ai clienti, NDA, atti societari, deposito bilancio.
- **Dati personali**: consensi, registro trattamenti, dati degli utenti del K-BOT.
- **Persone**: assunzioni, licenziamenti, offboarding.
- **Comunicazioni verso l'esterno**: nessun contatto a clienti/lead parte senza ok.

## Rischi e limiti osservati (reali, in questo ciclo)

- **Sensori vuoti**: 36 sensori restituiscono 0 righe (es. leggi_ranking_seo, leggi_competitor_web, leggi_ads_meta, leggi_ads_google, leggi_costi, leggi_ricavi_chiusi). L'AI lavora in modalita' strategia su quelle aree: utile, ma non e' lettura di dati reali.
- **Dipendenza da un LLM**: le proposte sono buone quanto il modello e i dati che legge. Su dati scarsi puo' restare sul generico: serve sempre il filtro umano prima di alzare l'autonomia.

## In conclusione

In **una giornata simulata**, lasciata a se' stessa, l'AI di K2-AI metterebbe in coda **51 decisioni** su tutti e sei i reparti — coperti in **251 secondi** di calcolo. Oggi sono tutte proposte: niente e' partito, niente e' stato scritto, nessun euro si e' mosso.

Per **alzare l'autonomia in sicurezza** servono, nell'ordine:

1. **Collegare i sensori ancora vuoti** (CRM, Stripe, analytics): senza dati reali l'AI ragiona in astratto.
2. **Partire da L2 solo sulle azioni reversibili e a basso rischio** (task, igiene dati, promemoria), tenendo denaro/contratti/persone/dati personali sempre a L1.
3. **Far maturare il track record**: il kernel promuove a L2 solo dopo una serie di esiti puliti approvati. La fiducia si guadagna sui numeri, non si concede a priori.

---

### Nota di sicurezza

Simulazione **read-only** verificata: backend audit/approvals/policy del kernel spostati in memoria, client Supabase in sola lettura (GET).
- Tentativi di scrittura intercettati e neutralizzati dal guard: **14** (tutti resi no-op, nessuna riga scritta).
- Approval risolti / azioni eseguite / movimenti di denaro: **0**.
