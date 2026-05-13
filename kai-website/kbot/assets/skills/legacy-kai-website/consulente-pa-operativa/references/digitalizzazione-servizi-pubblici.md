# Digitalizzazione e Servizi Pubblici

## CAD: Codice dell'Amministrazione Digitale

**Decreto Legislativo 7 marzo 2005, n. 82 ("Codice dell'Amministrazione Digitale", aggiornato a D.Lgs. 217/2017 e oltre):** Quadro normativo che obbliga PA a trasformazione digitale. Costringe PA a: (a) comunicare con cittadini online, (b) usare identità digitale (SPID), (c) ricevere pagamenti via PagoPA, (d) pubblicare dati pubblici in formati aperti.

### Principi CAD

**Principio Digitale per Impostazione:** PA deve offrire servizio digitale come opzione primaria (cartaceo è opzione secondaria, non obbligo). Cittadino che vuole procedimento digitale ha diritto.

**Accesso Paritario:** Piattaforme digitali PA devono essere accessibili a cittadini diversabili (WCAG 2.1 AA standard), progettate secondo principi universal design.

**Interoperabilità:** Sistemi informatici PA devono comunicare tra loro (no "silos"). Se cittadino accede a servizio comune, dati non devono essere ri-immessi (PA usa banche dati centrali: ANPR, tributaria, ecc.).

**Cloud First:** PA deve migrare infrastrutture verso cloud (SaaS, PaaS, IaaS) da fornitori certificati (es. AWS, Azure con certificazione ISO cloud PA). Eccezione: dati sensibili che restano on-premise se rischio di sicurezza è critico.

**API-first:** Servizi PA devono esporre API (Application Programming Interface) per permettere integrazioni di terzi (cittadini, fornitori, altre PA).

### Implementazione CAD in PA Locale

**Comune deve offrire:**
- Sito web responsive (mobile-first)
- Sportello virtuale (ticketing online)
- Consultazione atti via accesso civico (download online)
- Procedimenti digitali (SUAP/SUE online)
- Pagamento online tramite PagoPA

**Scadenza compliance:** 2026 è data limite per piena compliance CAD. Comuni che non rispettano hanno rischio sanzioni (es. 200.000-500.000 euro).

**Per TLC:** Se progetto è "infrastrutturazione comune per digitale PA", è coperto da PNRR (Missione 1.2 "Digitalizzazione della PA"). Costi realizzazione rete, piattaforme, formazione sono finanziati. Rivolgersi a comune + regione per cofinanziamento.

## Identità Digitale: SPID, CIE, CartaID

### SPID (Sistema Pubblico di Identità Digitale)

**SPID:** Credenziali digitali nazionali per accedere a servizi PA online. Cittadino si registra su SPID (tramite uno di 11 Identity Provider privati: Lepida, Aruba, PagoPa, TimID, ecc.), riceve username+password (o biometrico). Usa SPID per accedere siti PA, banche, servizi aziendali.

**Livelli di assicurazione:**
- **L1 (basso):** Username + password (meno sicuro, accesso servizi basici).
- **L2 (medio):** Username + password + OTP via email/SMS.
- **L3 (alto):** Certificato digitale client + OTP hardware (token). Usato per transazioni sensibili (tasse, diritti).

**Costo cittadino:** Gratis (SPID è diritto, PA non può chiedere pagamento per registrazione).

**Obbligatorietà:** Dal 28 febbraio 2024, PA è obbligata offrire SPID come unico metodo di accesso per cittadini a servizi online. Vecchi sistemi di login (username/password comunali) sono deprecated.

**Per TLC:** Se ente sta implementando accesso SPID a suoi servizi, ha necessità tecnica: infrastruttura di autenticazione federata OIDC/SAML che dialoga con hub SPID nazionale. Progetto TLC è "portale PA digitale con autenticazione SPID", candidatura PNRR rilevante.

### CIE (Carta d'Identità Elettronica) e CartaID

**CIE:** Documento d'identità con chip NFC (Near Field Communication). Cittadini italiani da 2024 ricevono CIE al rinnovo (vecchia carta d'identità è carta). Chip contiene: anagrafe, dati biometrici (impronta digitale), certificato digitale X.509.

**Funzione CIE come identità digitale:** Cittadino accede a servizi PA usando CIE (chip NFC tramite smartphone con app "CieID"). Più sicuro di SPID (biometrico certificato), usato per transazioni ad alto valore (rinnovo patente, tasse).

**CartaID (CartaID):** Progetto in fase pilota (2024-2025). Estensione di CIE per cittadini UE. Permette a cittadini europei accedere servizi PA italiano usando carta d'identità nazionale (EU standard eIDAS).

**Implicazione PA:** Comuni devono supportare autenticazione CIE in portali. Costo tecnico: setup lettore NFC, setup server PKIX/X.509, gestione certificati digitali. PNRR finanzia upgrading.

**Per TLC:** Se progetto è "interoperabilità CIE con servizi PA locale", è coperto PNRR. Fornitori di software gestionali PA (produttori ERPsystem) hanno mercato per certificazione CIE.

## PagoPA: Pagamenti Digitali della PA

**PagoPA:** Piattaforma nazionale centralizzata per pagamenti verso PA. Cittadino o impresa che deve pagare tassa/muulta/tariffa verso comune/provincia/Stato, usa portale PagoPA (app o sito web). Scelto strumento pagamento (carta di credito, bonifico, Apple Pay). Importo è versato direttamente in conto tesoro (no intermediazione).

### Vantaggi Cittadino

- **Trasparenza:** Sa esattamente quanto deve pagare, niente intermediari che lucrano su versamento.
- **Velocità:** Pagamento è istantaneo, ricevuta generata automaticamente.
- **Accesso multiplo:** PagoPA integra metodi pagamento diversi (carta, bonifico, SEPA, rateizzazione). Cittadino sceglie.

### Vantaggi PA

- **Riconciliazione automatica:** Pagamento è automaticamente riconciliato (sistema capisce quale cittadino ha pagato quale tassa).
- **Costo ridotto:** Commissions bancarie su PagoPA sono negoziati a livello centrale (0.5-1% commissione, vs 2-3% carta tradizionale).
- **Compliance legale:** Riduce corruzione (no assegni contanti, tutto tracciato).

### Adozione Obbligatoria

**D.Lgs. 33/2013 e CAD:** Ogni ente pubblico è obbligato offrire PagoPA come canale pagamento entro 2026. Comune non può rifiutare pagamento via PagoPA.

**Per TLC:** Se lavori con fornitore TLC che fattura a PA, fattura è pagata via PagoPA (non assegno). Ente invia avviso di pagamento via PagoPA, tu paghi online, ricevuta è automatica.

## ANPR: Anagrafe Nazionale della Popolazione Residente

**ANPR (D.Lgs. 179/2016, L. 132/2016):** Banca dati centrale unica anagrafe cittadini italiani. Sostituisce 8.000 anagrafi comunali separate.

### Funzioni ANPR

- **Unicità dati:** Un cittadino ha un'unica scheda anagrafe (no duplicati). Se cambia residenza da comune A a comune B, trasloco è registrato istantaneamente (no ritardi).
- **Servizi digitali:** Cittadino accede a servizi PA (iscrizione scuola, indennità disoccupazione, bonus fiscali) senza fornire certificati anagrafici (ente li legge da ANPR).
- **Interoperabilità:** Agenzia Entrate, INPS, comuni, ospedali accedono ANPR (con permessi) per verificare anagrafe, no documenti cartacei.

### Migrazione ANPR (2016-2024)

**Timeline:** Comuni hanno migrato anagrafe locale su ANPR in fasi (2016-2021). Entro 2021, 100% comuni italiani dovevano essere on-line ANPR. Ritardi sono stati frequenti (alcuni comuni ancora in 2024 non completamente migrati).

**Impatto per TLC:** Se progetto richiede integrazione con dati anagrafici (es. notifiche AI cittadini per bollo auto), devi integrare con API ANPR (non con anagrafe comunale). ANPR è il provider unico.

**Accesso ANPR:** Attraverso portale nazionale ANPR (anagrafenazionale.interno.it). Solo enti autorizzati accedono.

## IO: App Nazionale Cittadini

**IO (Interfaccia Operativa):** App nazionale italiana per interazione cittadino-PA. Cittadino scarica app (iOS/Android), autentica con SPID, riceve notifiche da enti pubblici (avvisi pagamento, comunicazioni, scadenze). App integra PagoPA, PEC, firme digitali.

### Funzioni IO

- **Notifiche PA:** Ente invia avviso pagamento (es. bolletta rifiuti) via IO (notifica push). Cittadino apre app, vede avviso, paga subito via PagoPA integrato.
- **Documenti:** Certificati anagrafici, tessere sanitaria sono visualizzabili in app (no pdf scaricato).
- **Messaggistica:** Cittadino scrive ente via app (es. "Domanda: quando esce delibera?"). RUP vede messaggio in back-office e risponde.
- **Identità verificate:** Integrazione SPID/CIE consente trasmissione documenti digitalmente firmati.

### Adozione IO

**D.Lgs. 217/2017 e PNRR:** Ogni ente è incoraggiato adottare IO (PNRR finanzia integrazione). Deadline: 2026 per compliance piena.

**Costo integrazione:** Per ente, setup API IO è gratuito (PagoPA spa gestisce piattaforma). Costo è personale interno sviluppo software per integrare back-office ente con API IO.

**Per TLC:** Se comune sta digitalizzando servizi, IO è piattaforma di notifica canale primario. Se lavori su progetto "notifiche cittadini" (es. avvisi scadenza certificati), integrazione IO è required.

## PND: Patrimonio Naturalistico Digitale

**PND (2023, D.Lgs. 106/2023):** Catalogazione sistematica dati pubblici in formati aperti (open data). Ogni ente pubblica dataset strutturato (CSV, JSON, RDF) di info pubblica (bilanci, bandi, trasporti, ambiente, urbanistica).

### Open Data Standard

**Formato:** Dati sono in CSV/JSON/RDF (facilmente leggibili da script, algoritmi). No PDF scansionato (illeggibile a macchina).

**Licensing:** Dati sono pubblicati con licenza CC-BY (Creative Commons Attribution) o simile (chiunque può scaricare, modificare, ridistribuire con attribuzione).

**Aggiornamento:** Dataset è aggiornato periodicamente (almeno mensilmente). API sono disponibili per scarichi programmatici.

### Dati Aperti Tipici

- **Bilanci enti:** Voci di bilancio comune in formato strutturato
- **Bandi e appalti:** Elenco gare pubbliche in corso, importi, aggiudicatari
- **Trasporto pubblico:** Orari e percorsi autobus, stazioni metro
- **Ambiente:** Inquinamento aria/acqua, rifiuti, consumi energia
- **Urbanistica:** Mappatura zonizzazione, piani regolatori, vincoli paesaggistici

**Per TLC:** Ricerca dataset "Infrastrutture TLC" da enti pubblici. Se comune ha censito reti telecom esistenti in open data, è evidenza che ente ha capacità digitale avanzata (partner più affidabile).

## FSE: Fascicolo Sanitario Elettronico

**FSE (L. 537/1992, D.L. 179/2012, PNRR Missione 6):** Dossier medico digitale di cittadino. Contiene: ricette medico generico, referti laboratorio, esami imaging, prescrizioni ospedaliere. Cittadino accede via SPID, vede storico medico (10+ anni).

### Implementazione PNRR

**Timeline FSE:** Fino 2021, FSE era frammentario (ogni regione gestiva dati diversamente). PNRR 2021-2026 centralizza FSE (Missione 6). Investimento: ~600 milioni euro per infrastruttura dati sanitari nazionale.

**Impatto per TLC:** Se progetto è "infrastrutturazione digitale sanitaria" (datacenter, rete alta velocità verso ospedali, cybersecurity per dato sensibile), è finanziato PNRR Missione 6 (Salute). Partner: Ministero Salute, Regioni, Aziende Sanitarie.

## Cybersecurity e Guidelines AgID

### D.Lgs. 106/2021 (Direttiva NIS, Cybersecurity Italia)

**NIS = Network Information Security.** Direttiva UE 2016/1148, recepita in Italia con D.Lgs. 106/2021. Obbliga enti pubblici critici (PA, sanità, energia, trasporti) a implementare misure cybersecurity di base.

**Misure obbligatorie:**
- Gestione patch (aggiornamenti software regolari, no vulnerabilità note).
- Segmentazione rete (no accesso indiscriminato a dati sensibili).
- Backup e disaster recovery (data è replicato, recuperabile se attacco).
- Incident management (procedura rispondere a furto dati/ransomware).
- Formazione personale (anticyclical phishing, no password weak).
- Verifica fornitori (subappaltatori devono rispettare security standard).

**Compliance deadline:** 2026 per PA locale. Entità che non rispettano: sanzioni fino a 10 milioni euro.

### AgID: Agenzia Governativa Digitale

**AgID (Agenzia per l'Italia Digitale):** Ente pubblico che emette linee guida digitale, cybersecurity, cloud. È advisor governo su trasformazione digitale.

**Guidelines chiave:**
- **Cloud PA (2021):** Quali cloud provider (AWS, Azure, GCP) sono certificati per PA. Certificazione è "cloud-silver" (dati non sensibili) o "cloud-gold" (dati sensibili ammessi).
- **Cybersecurity Baseline (2022):** Checklist misure cybersecurity per enti. Include: firewall, antivirus, MFA (multi-factor authentication), logging, monitoring.
- **API Interoperabilità (2023):** Standard API PA (REST, SOAP). Se due enti devono comunicare, devono usare API standard AgID (no proprietarie).

### Compliance Cybersecurity per TLC

**Se fornisci infrastruttura TLC a PA:**
- Infrastruttura deve supportare MFA (autenticazione multifattore).
- Logging deve essere abilitato (registrare accessi, modifiche, cancellazioni).
- Backup automatico ogni 24h (RPO ≤ 24h, RTO ≤ 4h = ripristino entro 4 ore se disastro).
- Encryption in transit (TLS 1.2+) e at rest (AES 256).
- Vulnerability assessment annuale (penetration test per identificare debolezze).

**Costo compliance:** Significativo (encryption, backup, monitoring continuo). PNRR copre costi per infrastrutturazione digitale (approx 50-70% costo). Ente copre resto (o negozia con fornitore per risk-sharing).

## Relazioni Soprintendenze e Digitalizzazione Paesaggistica

### Soprintendenze e PNRR

**Soprintendenze (MiC):** Enti che tutelano paesaggio, beni culturali, archivi. Hanno procedure lente (cartacei, autorizzazioni manuali). PNRR Missione 2 finanzia "Digitalizzazione Soprintendenze" (2021-2026).

**Progetto PNRR:** Digitalizzazione procedimenti Soprintendenze:
- Portale online per istanze paesaggistico (no cartaceo).
- Gestione digitale fascicoli (no archivi fisici).
- Geolocalizzazione beni (cartografia SIT - Sistemi Informativi Territoriali).
- Integrazione con autorizzazioni ambientali/edilizia (conferenza di servizi asincrona online).

### SUAP e Soprintendenze

**SUAP digitale (vedi performance-bilancio):** Per procedimenti SUAP, comune invita Soprintendenza in conferenza di servizi online. Soprintendenza riceve richiesta via portale digitale, ha 20 giorni per rispondere (parere paesaggistico).

**Se Soprintendenza è non-digitale (ancora carte):** Procedimento rallenta (Soprintendenza non vede richiesta online, la riceve per PEC, demanda risposte lente). Comuni avanzati (Milano, Roma) hanno Soprintendenze digitalizzate (PNRR finanziate). Comuni piccoli ancora soffrono.

**Per TLC:** Se progetto paesaggistico richiede Soprintendenza lenta, negozia timeline lungo (90+ giorni). Se Soprintendenza è digitalizzata, timeline è standard (30-40 giorni).

## PNRR Investimenti Digitali (Missione 1.2)

### Progetti Tipici Finanziati

**Missione 1 (Digitalizzazione):** Sottomissione 1.2 "Digitalizzazione della PA e dei servizi pubblici". Progetti:
- **Cablaggio ultra-largo:** Fibra ottica fino a 100 Mbps. Budget: ~4 miliardi euro. Implementatore: operatori TLC privati con cofinanziamento pubblico.
- **5G Aree Rurali:** Copertura rete mobile in zone remote. Budget: ~700 milioni euro. Attuatore: RAN (rete nazionale 5G), operatori TLC co-investitori.
- **Cloud PA:** Migrazione PA verso cloud. Budget: ~1.2 miliardi euro. Implementatore: fornitori cloud (Aruba, TIM, Vodafone).
- **Cybersecurity:** Upgrade sicurezza PA. Budget: ~600 milioni euro. Implementatore: fornitori cybersecurity + system integrator.
- **SPID/IO:** Espansione identità digitale e app IO. Budget: ~300 milioni euro. Implementatore: PagoPA spa.

### Modalità Accesso PNRR

**Per ente locale (comune, regione):**
1. Scarica bando PNRR (Ministeri rilasciano bandi periodicamente).
2. Compila candidatura (progettazione, timeline, budget, cofinanziamento).
3. Invia a Struttura Missione PNRR (ente governativo che valuta).
4. Se approvato: ricevi grant (sovvenzione, non prestito). Se dinegato: no finanziamento.

**Per fornitore TLC (partner implementazione):**
1. Attendi ente locale che pubblica bando "gara servizi TLC PNRR".
2. Partecipa gara (regole D.Lgs. 36/2023 + vincoli PNRR).
3. Se aggiudicato: sei contraente implementazione per ente.

**Vincoli PNRR:**
- Rendicontazione ristretta (fatture, scontrini, ogni euro deve essere tracciato).
- Milestone obbligatori (es. "50% realizzazione entro giugno 2024" = data fissa, non negoziabile).
- Auditi frequenti (Guardia Finanza ogni 2-3 mesi per verificare spesa, antiriciclaggio).
- Green/Digital Criteria: Progetto deve rispettare standard ambientali (es. efficienza energetica per datacenter).

**Per TLC:** Se proponi progetto PNRR, preparati a:
- Documentazione estensiva (project plan, risk management, team CVs).
- Termini stringenti (milestone non posticipabili).
- Controlli rigorosi (GdF in cantiere, verifiche fatture).
- Reporting continuo (rendicontazione trimestrale + milestone finale).

## Checklist Digitalizzazione PA

- [ ] Verifica se ente ha SPID/CIE integrato nei portali (se no, è opportunità progetto TLC)
- [ ] Consulta roadmap PNRR ente per investimenti digitali (vedi PIAO)
- [ ] Se paesaggistico, verifica se Soprintendenza è integrata in SUAP digitale
- [ ] Ricerca dataset open data comune (indicatore maturità digitale ente)
- [ ] Se progetto è sensibile (dati personali, sanità), valuta compliance cybersecurity AgID
- [ ] Verifica modalità pagamento previste in contratto PA (PagoPA obbligatorio?)
- [ ] Valuta integrazione IO app (notifiche cittadini digitale)
- [ ] Se PNRR, scarica milestone contract (timeline non negoziabile)
- [ ] Prepara rendicontazione PNRR (fatture tracciabili, reporting mensile)
