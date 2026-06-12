# Risposta — verifica piano KBot v2

**Da**: <compilare nome/ruolo>
**A**: team KBot (kai-website/kbot)
**Data**: <YYYY-MM-DD>
**Riferimento**: `docs/kbot-v2-piano-completo.md`, sezione "Domande di verifica al proponente"

---

## Istruzioni di compilazione

1. Rispondere a TUTTE le domande mantenendo la numerazione.
2. Risposte sintetiche ma complete. NO bullet vuoti, NO "ok", NO "vedi sopra".
3. Se non si sa: scrivere esattamente `DA DEFINIRE — proposta: <una proposta concreta>`. Non lasciare il campo vuoto.
4. Se una domanda non si applica: scrivere `NON APPLICABILE — motivo: <spiegazione>`.
5. Se serve allegare materiale (tabelle, schemi, esempi reali) → linkare il file con path nel repo o URL.
6. Dove c'è incertezza, indicarla esplicitamente: `INCERTEZZA: <descrizione>`.
7. Salvare il file come `docs/risposta-verifica-piano-kbot.md` e committarlo.

---

## A. Catalogo e modello commerciale

### A.1 — Boost diretti totali a regime

> Elencare tutti i Boost diretti previsti con: id catalogo, label commerciale, prezzo finale (€), tag pillar SEO associati (P01-P20).

**Risposta**:
<inserire tabella o elenco>

### A.2 — Percorsi a tappe totali a regime

> Per ogni percorso: id catalogo, destinazione (id+label+prezzo), elenco ordinato delle tappe (id+label+prezzo per ognuna), % sconto completamento.

**Risposta**:
<inserire tabella per ogni percorso>

### A.3 — Specifiche operative delle tappe

> Per ogni tappa prevista: durata erogazione (ore uomo/AI), output deliverable (PDF/dashboard/altro), SLA di consegna al cliente.

**Risposta**:
<inserire tabella>

### A.4 — Pricing tappe vs Boost completo

> Esempio AdvisorBoost: somma tappe (es. 299+349+449+449+701 = 2.247€) vs Boost completo 2.499€. Lo sconto completamento 24% si applica DOVE esattamente — su tappe successive man mano che si completano, o tutto a fine percorso?

**Risposta**:

### A.5 — Check Express vs prima tappa di Boost-a-percorso

> Il Check Express 19€ è un "consumo" distinto dalla prima tappa del percorso, o coincide? Se distinto: cliente che ha pagato Check Express deve ri-comprare ab-tappa-1?

**Risposta**:

### A.6 — Prezzo Check 19€ → 49€

> Quando si effettua il passaggio? Con quale giustificazione data al mercato? Cosa succede ai payment link 19€ già distribuiti (email, social, firme)?

**Risposta**:

### A.7 — Boost self-serve vs high-touch

> Per ogni Boost, indicare: self-serve totale (web puro), ibrido (Check self + Boost call), high-touch (tutto via call → contratto offline).

**Risposta**:
<inserire mapping Boost → modalità>

### A.8 — Limiti di acquisto per cliente

> Esiste un upper limit (max 1 Boost attivo, max N tappe/mese, ecc.)? Quali e perché?

**Risposta**:

---

## B. Skill orchestratori e deliverable

### B.1 — Mapping Boost/tappa → skill orchestratrice

> Per ogni servizio nel catalogo: nome esatto della directory skill in `lib/skills/`, se esiste o va creata.

**Risposta**:
<inserire tabella servizio_id → skill_directory → esiste sì/no>

### B.2 — Skill da creare: ownership e timeline

> Per le skill da creare ex novo: chi le scrive (team, persona)? Timeline? Effort stimato per ognuna in giorni-persona.

**Risposta**:

### B.3 — Skill esistenti: compatibilità

> Le skill esistenti in `kai-website/lib/skills/` e `skills sito k2-ai 2/` sono pronte come orchestratori dei nuovi Boost o vanno riadattate? Per ognuna che richiede modifiche: cosa cambia e perché.

**Risposta**:

### B.4 — Formati deliverable

> Tutti PDF o anche altri (dashboard HTML, JSON, Excel)? Per ogni formato: tooling di generazione (ReportLab, altro?).

**Risposta**:

### B.5 — Riproducibilità report

> Il PDF prodotto deve essere riproducibile (stesso input → stesso PDF byte-per-byte? o contenutisticamente simile?)? Come si gestisce il non-determinismo di Sonnet?

**Risposta**:

### B.6 — Passaggio contesto tra tappe

> Il deliverable di una tappa è input della tappa successiva? Come viene tecnicamente passato il contesto (file storage, JSONB nella sessione, altro)?

**Risposta**:

### B.7 — Input richiesti per ogni skill

> Per ogni skill orchestratrice: input obbligatori (es. dati bilancio, P.IVA, sito web, file PDF) + input opzionali. Schema strutturato.

**Risposta**:

### B.8 — File utente → skill

> Come vengono passati alla skill orchestratrice i file caricati dal cliente nel KBot? Via RAG BM25 esistente o parsing strutturato per tipo (es. parser bilancio XBRL)?

**Risposta**:

---

## C. MCP server interno (Uso A — coerenza report)

### C.1 — Fonti dati dinamiche previste

> Quali domini hanno fonti dinamiche da esporre via MCP interno? Per ognuno: frequenza aggiornamento, origine dato (manuale, API esterna, scraping).

**Risposta**:
<inserire tabella>

### C.2 — Stato implementativo

> MCP interno: già implementato, in lavorazione, o da progettare? Se in lavorazione: chi lo costruisce, quando è pronto, chi lo mantiene a regime.

**Risposta**:

### C.3 — Protocollo di trasporto

> KBot backend ↔ MCP interno: HTTP/REST, stdio MCP locale, gRPC, altro? Specificare porta/path.

**Risposta**:

### C.4 — Modalità di consumo della risposta MCP

> La risposta MCP arriva al KBot come dato strutturato iniettato nel prompt, o come tool result che Claude rielabora? Esempio pratico (bandi agevolazioni).

**Risposta**:

### C.5 — Citazione fonti nel report

> I dati ottenuti da MCP vengono citati esplicitamente nel report finale (fonte+data) o restano opachi? Esigenze compliance/audit?

**Risposta**:

### C.6 — Failure mode MCP

> MCP interno down durante generazione: il report fallisce? Si genera con caveat? Si attende? Definire SLA.

**Risposta**:

### C.7 — Impatto sul tempo di generazione PDF

> Tempo medio attuale ~30s. Con 5-10 tool call MCP può diventare 2-3 minuti. Accettabile o serve ottimizzazione (parallelismo, cache)?

**Risposta**:

---

## D. MCP server esterno (Uso B — partner)

### D.1 — Partner concreto già identificato

> Esiste un partner reale interessato (nome, contesto, tempistica)? O è un'opzione strategica futura senza partner attuale?

**Risposta**:

### D.2 — Client MCP del partner

> Claude Desktop, custom GPT, propria app, altro? Quale tecnologia esatta?

**Risposta**:

### D.3 — Modello commerciale partner

> Fee fissa per lead, revenue share %, white-label totale, altro? Specificare.

**Risposta**:

### D.4 — Versioning catalogo per partner

> Servono cataloghi differenziati (prezzi diversi, prodotti hide per partner)? Schema multi-tenant?

**Risposta**:

---

## E. Wallet crediti e abbonamenti

### E.1 — Validazione abbonamenti Pro 49€ / Business 149€

> Già testati con clienti reali (quanti? quale risposta?) o solo ipotetici? Esiste interesse documentato?

**Risposta**:

### E.2 — Cosa include ogni piano oltre ai crediti

> Pro 49€/mese e Business 149€/mese: supporto prioritario, anteprima nuove skill, sessioni consulente? Definire il valore non monetario.

**Risposta**:

### E.3 — IVA su crediti

> Prezzo crediti 1:1 € è netto IVA o lordo? Come si presenta in fattura?

**Risposta**:

### E.4 — Sconto piano: perimetro applicabilità

> Lo sconto Pro -10% / Business -20% si applica a: solo tappe, solo Boost, entrambi, altro?

**Risposta**:

### E.5 — Decadenza 12 mesi: comportamento esatto

> Decadenza dell'intero saldo, o solo dei crediti non utilizzati dell'ultima ricarica? Reminder a 11 mesi?

**Risposta**:

### E.6 — Refund policy disdetta abbonamento

> Cliente disdice: crediti residui usabili per X giorni? Persi? Rimborsati?

**Risposta**:

### E.7 — Crediti promozionali vs pagati

> Stesso comportamento o vincoli aggiuntivi (es. non rimborsabili, scadenza propria)?

**Risposta**:

---

## F. Mapping sito ↔ KBot (scenario C)

### F.1 — Mapping completo P01-P20 → Boost destinazione

> Per ognuno dei 20 pillar SEO, indicare il Boost destinazione (oppure "ancora da decidere"). Schema da inserire in `catalog.json → mapping_tag_to_servizi`.

**Risposta**:
<inserire tabella P01-P20 → boost_id>

### F.2 — Pillar con più Boost alternativi

> Un tag può puntare a più Boost (es. P09 → ControlBoost o AdvisorBoost)? Come decide il KBot quale proporre?

**Risposta**:

### F.3 — Link blog → KBot

> Articoli blog pillar devono linkare al KBot con tag pre-compilato? In quale posizione dell'articolo (footer, callout intermedio, intro)?

**Risposta**:

### F.4 — Citazioni vecchio pricing HOST/WEB/STUDIO

> Sito vetrina cita ancora "HOST/WEB/STUDIO": vanno rimossi/aggiornati per coerenza col nuovo modello, o coesistono temporaneamente?

**Risposta**:

### F.5 — Refresh copy delle pagine `/suite-ai/*`

> Le pagine pillar con SEO già attivo: la copy interna va allineata al modello Boost? Quando? Chi scrive?

**Risposta**:

---

## G. Architettura tecnica e interfaccia col KBot

### G.1 — Schema definitivo catalog.json v1

> Confermare i campi del draft (vedere §1.1 del piano). Aggiungere/togliere campi se necessario. Indicare owner del file (chi può modificare via PR).

**Risposta**:
<inserire schema confermato + owner>

### G.2 — Location e sync catalog.json

> Repo KBot (`kai-website/kbot/backend/app/data/`) o repo separato? Se separato, meccanismo di sync (sub-module, CI, fetch periodico)?

**Risposta**:

### G.3 — Versioning catalogo

> Ogni modifica = release semver? KBot legge sempre l'ultima o si può pinnare a una versione per riproducibilità?

**Risposta**:

### G.4 — Dimensione system prompt post-refactor

> Stima caratteri/token system prompt finale (skill orchestratrice + references + tag context + tool definitions). Resta sotto i limiti Haiku/Sonnet (context window)?

**Risposta**:

### G.5 — Tool use schema

> Schema formale dei tool Claude per "navigare orchestratori". Gestione errori (tool non esiste, parametro sbagliato, response non valida).

**Risposta**:

### G.6 — Crescita di `kbot_sessions.collected_data`

> Limit di dimensione JSONB? Strategia di compaction quando si sfora (es. archivia messaggi vecchi, drop RAG chunks vecchi)?

**Risposta**:

### G.7 — Più percorsi attivi per cliente

> Cliente può avere AdvisorBoost + ControlBoost in parallelo? Una sessione per cliente o una per percorso?

**Risposta**:

---

## H. Economics e costi

### H.1 — Budget LLM mensile target

> 65€/mese di CLAUDE.md §3 resta vincolante post-espansione? Se sì: quante sessioni/mese sostiene? Se no: nuovo budget approvato?

**Risposta**:

### H.2 — Costo per sessione atteso

> Calcolo token (input + output) e prezzo per: Check Express, tappa intermedia, Boost completo. Per ogni tipologia + modello.

**Risposta**:
<inserire tabella>

### H.3 — Margine per Boost

> Prezzo - costi LLM - costi infra - lavoro umano - fee Stripe = margine. Calcolo per AdvisorBoost 2.499€ e per gli altri Boost. Margine target accettabile?

**Risposta**:

### H.4 — Revisione umana pre-consegna

> Ogni Boost richiede revisione umana? Quante ore? Chi? Costo orario interno? Incluso nel pricing?

**Risposta**:

### H.5 — Stripe fee assorbimento

> Su Boost 2.499€ fee Stripe ~35€: incluso nel prezzo o margine assorbe?

**Risposta**:

---

## I. Roadmap, responsabilità, deploy

### I.1 — Esecutori per fase

> Chi esegue ogni fase del piano (0-8)? Sviluppatore unico, team, freelance? Indicare per ogni fase responsabile.

**Risposta**:
<inserire tabella fase → responsabile>

### I.2 — Cadenza review

> Review piano: settimanale, bisettimanale, dopo ogni gate? Chi convoca?

**Risposta**:

### I.3 — Infrastruttura deploy

> Railway resta per tutte le fasi? Servono nuovi container (MCP server interno, altro)? Costi mensili attesi.

**Risposta**:

### I.4 — Branch strategy

> Per ogni fase un branch dedicato o uno per sub-task? Chi fa review PR?

**Risposta**:

### I.5 — Misurazione gate quantitativi

> Chi misura i numeri dei gate? Con quale strumento (query SQL, dashboard, Notion, altro)? Cadenza?

**Risposta**:

### I.6 — Comportamento se un gate non è raggiunto

> Si stoppa il piano? Si modifica il prodotto? Si itera sulla fase precedente? Definire azione per ogni gate.

**Risposta**:

---

## J. Edge case e governance prodotto

### J.1 — Deliverable fallisce generazione

> Crash Sonnet, timeout, errore parsing. Cosa vede l'utente? Refund automatico? Retry? Notifica a Luca? SLA di risoluzione?

**Risposta**:

### J.2 — Abbandono percorso

> Cliente paga tappa 1 e non torna. Soglia di "abbandonato" (giorni)? Email reminder? Sconto per recupero?

**Risposta**:

### J.3 — Disdetta Boost in corso

> Politica refund parziale? Scritta dove?

**Risposta**:

### J.4 — Versioning prezzi (grandfather)

> Aumento prezzo da 2.499€ → 2.999€. Clienti con tappa 1 al vecchio prezzo completano al vecchio o nuovo? Politica grandfather scritta.

**Risposta**:

### J.5 — Check Express già pagato → entra in AdvisorBoost

> Si sconta automaticamente il Check già fatto da tappa 1? Tappa 1 INCLUDE il Check? Esplicitare flow.

**Risposta**:

### J.6 — Cutover modelli LLM (Haiku/Sonnet new release)

> Chi decide quando aggiornare? Si misurano differenze in regression test prima del cutover? Test su quale set?

**Risposta**:

### J.7 — Compliance GDPR su deliverable

> Cifratura at-rest in Supabase Storage? Retention policy (quanti giorni)? Diritto all'oblio: procedura?

**Risposta**:

---

## K. Allineamento organizzativo

### K.1 — Decisore vs owner repo

> "Decisore" del modello e Luca (owner repo) sono la stessa persona? Se distinti: come si risolvono conflitti di direzione (es. Luca vetera una scelta)?

**Risposta**:

### K.2 — Team backend ecosistema vs team KBot

> Stesso team o distinti? Se distinti: coordinamento deploy, on-call produzione, ownership dei pezzi.

**Risposta**:

### K.3 — Canale di comunicazione strutturato

> Slack/Notion/daily sync esistente tra i due lati? Se no, va creato prima di iniziare.

**Risposta**:

### K.4 — Cambi futuri modello SEO

> Se il modello SEO (20 pillar P01-P20) verrà consolidato, chi aggiorna `tag_pillar_sito` nel catalogo?

**Risposta**:

### K.5 — KPI prioritari a 6 mesi

> 3-5 KPI quantificabili per dimostrare che il modello complessivo funziona, da misurare 6 mesi dopo Fase 6 completata.

**Risposta**:

---

## L. Validazione e segnali di stop

### L.1 — Zero conversioni Boost dopo Fase 3

> Se 0 Boost venduti in 60 giorni: si ferma il piano o si continua? Quale soglia di "zero" si accetta?

**Risposta**:

### L.2 — Segnali precoci di fallimento

> 5 segnali quantificabili che indicano il modello non funziona (es. NPS basso post-Check, drop-off chat >50% al messaggio 3, CAC > LTV). Chi li monitora, a chi vanno comunicati.

**Risposta**:

### L.3 — Strategia di scale-up se i numeri superano le aspettative

> Es. 50 Boost/mese vs 2-3 attesi: hire? riserve infra? scaling automatico?

**Risposta**:

### L.4 — Accettazione formale del meccanismo a gate

> Il decisore conferma per iscritto che, se i gate quantitativi non vengono raggiunti, le fasi successive NON partono (anche se i deliverable sarebbero "interessanti")?

**Risposta**:

---

## Note finali del compilatore

> Spazio libero per: punti che ritieni non coperti dalle domande, dubbi residui, proposte di modifica al piano, materiale di supporto da allegare.

**Note**:

---

*Documento di risposta. Compilare e committare in `docs/risposta-verifica-piano-kbot.md` (senza `.template`). Una volta committato, il team KBot ne discuterà i contenuti e aggiornerà `kbot-v2-piano-completo.md` con le decisioni emerse.*
