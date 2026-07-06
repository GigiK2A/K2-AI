# Matrice Fase → Skill → Azione Concreta

Questa matrice definisce, per ogni fase del processo cantiere, QUALI skill invocare e COSA fargli fare.

## F00 — Chi Firma

**Skill da usare:** nessuna (decisione interna K2A)
**Azione:**
- Determina DL e CSE in base al tipo sito
- Raw Land → Luca (Ing.); Roof Top → Jessica (Arch.)
- Produci tabella figure con ruoli e firme
**Output:** Tabella figure responsabili compilata

---

## F01 — Ricezione e Verifica PE

**Skill da usare:**
- `iliad-progettazione-esecutiva:verifica-pe-terzi` → per siti Iliad
- `cellnex-progettazione-esecutiva:verifica-progetto-terzi` → per siti Cellnex
- `verifica-pe-terzi` → verifica generica PE

**Azione:**
1. Carica i file del PE dalla cartella del sito
2. Invoca la skill di verifica PE specifica per l'operatore
3. Genera la checklist elaborati con esito (presente/mancante/NC)
4. Se ci sono NC → genera lista NC con riferimenti

**Output:** Checklist PE compilata + lista NC (se presenti)
**Condizione OK:** Checklist completa, zero NC aperte

---

## F02 — Verifica Autorizzazioni

**Skill da usare:**
- `progettazione-architettonica` → verifica urbanistica PRG/NTA, titoli abilitativi
- `architetto-beni-monumentali` → se sito in area vincolata (paesaggistico, monumentale, centro storico)
- `progettista-strutturale` → se zona sismica, verifica deposito Genio Civile

**Azione:**
1. Chiedi all'utente quali autorizzazioni sono state richieste
2. Verifica con `progettazione-architettonica` se i titoli sono coerenti con il tipo intervento
3. Se area vincolata → invoca `architetto-beni-monumentali` per verifica autorizzazione paesaggistica
4. Se zona sismica → invoca `progettista-strutturale` per verifica deposito GC
5. Compila tabella autorizzazioni con stato e scadenze

**Output:** Tabella autorizzazioni (ottenuta / pendente / mancante / scaduta)
**Condizione OK:** Tutte le autorizzazioni necessarie ottenute e in corso di validità

---

## F03 — PSC e CME Sicurezza

**Skill da usare:**
- `psc-coordinamento-sicurezza` → redazione o aggiornamento PSC completo
- `psc-legale:psc-legale` → verifica aspetti legali e responsabilità CSP/CSE
- `direzione-lavori` → verifica CME e coerenza costi sicurezza

**Azione:**
1. Verifica se esiste già un PSC per il sito
2. Se NO → invoca `psc-coordinamento-sicurezza` per redigerlo da zero
3. Se SÌ → verifica che sia aggiornato rispetto al PE corrente
4. Verifica che la CME contenga i costi sicurezza separati e coerenti con il PSC
5. Opzionale: invoca `psc-legale:psc-legale` per check legale

**Output:** PSC redatto/aggiornato + CME verificata
**Condizione OK:** PSC firmato dal CSP, CME con costi sicurezza coerenti

---

## F04 — Ricezione e Verifica POS

**Skill da usare:**
- `cse-coordinatore-sicurezza` → verifica operativa POS dell'impresa

**Azione:**
1. Richiedi il POS dell'impresa esecutrice
2. Invoca `cse-coordinatore-sicurezza` per verificare conformità all'Allegato XV D.Lgs. 81/2008
3. Verifica coerenza POS ↔ PSC
4. Se subappalti RSA/ASA → verifica POS subappaltatori
5. Se NC → genera richiesta integrazione scritta

**Output:** POS approvato o lista NC per integrazione
**Condizione OK:** POS conforme e approvato dal CSE

---

## F05 — Cronoprogramma

**Skill da usare:**
- `direzione-lavori` → approvazione cronoprogramma e verifica coerenza

**Azione:**
1. Ricevi cronoprogramma dall'impresa
2. Verifica coerenza con tempistiche autorizzazioni e contratto
3. Identifica milestones critiche (getto fondazione, montaggio palo, commissioning)
4. Approva con firma DL

**Output:** Cronoprogramma approvato
**Condizione OK:** Cronoprogramma firmato DL + Impresa

---

## F06 — Apertura Cantiere

**Skill da usare:**
- `direzione-lavori` → verbale consegna area, apertura Giornale dei Lavori
- `psc-coordinamento-sicurezza` → notifica preliminare ASL/DTL

**Azione:**
1. Genera verbale di consegna area (template in `apertura-cantiere/references/`)
2. Verifica invio notifica preliminare
3. Verifica allestimento cartello di cantiere
4. Apri Giornale dei Lavori con `direzione-lavori`
5. Comunica al cliente (Iliad/Cellnex) l'inizio lavori

**Output:** Verbale firmato, NP protocollata, GdL aperto
**Condizione OK:** Verbale + NP + cartello + GdL tutti completati

---

## Sopralluogo Apertura Lavori (col O) — 1° obbligatorio

**Skill da usare:**
- `cse-coordinatore-sicurezza` → sopralluogo e verbale

**Azione:**
1. Invoca `cse-coordinatore-sicurezza` per verifica cantiere all'avvio
2. Verifica: cantiere allestito secondo PSC, cartello presente, recinzione ok, DPI
3. Genera verbale di coordinamento n. 1

**Output:** Verbale sopralluogo apertura firmato
**Vidimazione:** data del sopralluogo

---

## Sopralluogo Verifica in Cantiere (col P) — 2° obbligatorio

**Skill da usare:**
- `cse-coordinatore-sicurezza` → sopralluogo e verbale

**Azione:**
1. Invoca `cse-coordinatore-sicurezza` per verifica durante i lavori
2. Verifica: lavorazioni conformi al PSC, interferenze, prescrizioni precedenti
3. Gestisci NC: classificazione (critica/grave/lieve), sospensione se necessario
4. Genera verbale di coordinamento n. 2+

**Output:** Verbale sopralluogo verifica firmato, registro NC aggiornato
**Vidimazione:** data del sopralluogo

---

## Sopralluogo Chiusura Lavori (col Q) — 3° obbligatorio

**Skill da usare:**
- `cse-coordinatore-sicurezza` → sopralluogo finale e verbale

**Azione:**
1. Invoca `cse-coordinatore-sicurezza` per verifica pre-chiusura
2. Verifica: opere completate, nessuna NC residua, smobilitazione ordinata
3. Genera verbale di coordinamento finale

**Output:** Verbale sopralluogo chiusura firmato, NC tutte chiuse
**Vidimazione:** data del sopralluogo

---

## F08 — Gestione DL

**Skill da usare:**
- `direzione-lavori` → ordini di servizio, SAL, contabilità, varianti

**Azione:**
1. Gestisci ordini di servizio con `direzione-lavori`
2. Compila SAL periodici (mensile o a milestone)
3. Se variante necessaria → redigi perizia di variante
4. Aggiorna documentazione fotografica avanzamento

**Output:** OdS emessi, SAL compilati, eventuale perizia variante
**Condizione OK:** SAL aggiornato, nessun OdS inevaso

---

## F09 — Prove e Genio Civile

**Skill da usare:**
- `progettista-strutturale` → prove materiali, RSU, deposito GC, collaudo statico

**Azione:**
1. Verifica campionatura cls (provini, etichette, date prove)
2. Verifica certificati acciaio (marcatura CE, numero colata)
3. Verifica deposito ante-operam al Genio Civile (se zona sismica)
4. Redigi RSU (Relazione a Struttura Ultimata) con `progettista-strutturale`
5. Se richiesto → coordina collaudo statico con collaudatore terzo

**Output:** Prove ok, RSU firmata, GC completato
**Condizione OK:** Prove positive, RSU firmata, deposito GC regolare

---

## F10 — Commissioning

**Skill da usare:**
- `impianti-elettrici` → verifica impianto elettrico e di terra
- `cse-coordinatore-sicurezza` → sopralluogo finale sicurezza

**Azione:**
1. Verifica misure impianto di terra (resistenza ≤ 10 Ω)
2. Verifica impianto elettrico (isolamento, protezioni, Icc) con `impianti-elettrici`
3. Verifica funzionamento apparati (alimentazione, allarmi)
4. Sopralluogo finale CSE con `cse-coordinatore-sicurezza`

**Output:** Checklist commissioning firmata, rapporto misure
**Condizione OK:** Tutte le misure conformi, checklist firmata

---

## F11 — Certificazioni

**Skill da usare:**
- `impianti-elettrici` → verifica dichiarazioni conformità D.M. 37/2008
- `agibilita` → se necessaria (non per TLC puro, ma per shelter abitabili o edifici)

**Azione:**
1. Raccogli tutte le DiCo dall'impresa (elettrico, condizionamento, LPS)
2. Verifica completezza con `impianti-elettrici` (modulo ministeriale, allegati)
3. Raccogli certificati materiali (prove cls, acciaio)
4. Raccogli RSU e collaudo statico (da F09)
5. Se edificio con agibilità → invoca `agibilita`

**Output:** Pacchetto certificazioni completo
**Condizione OK:** Tutte le DiCo ricevute e conformi

---

## F12 — CFL (Certificato Fine Lavori)

**Skill da usare:**
- `direzione-lavori` → dichiarazione fine lavori, verbale ultimazione, conto finale

**Azione:**
1. Redigi CFL con template (dichiarazione DL)
2. Redigi verbale ultimazione lavori
3. Conto finale e certificato di pagamento finale con `direzione-lavori`
4. Verifica che tutte le certificazioni (F11) siano allegate

**Output:** CFL firmato, verbale ultimazione, conto finale
**Condizione OK:** CFL firmato dal DL

---

## F13 — BEF / Portale Cliente

**Skill da usare:**
- `iliad-progettazione-esecutiva:progetto-esecutivo-iliad` → per verifica completezza BEF Iliad
- `cellnex-progettazione-esecutiva:verifica-progetto-terzi` → per verifica completezza BEF Cellnex
- `report-caratterizzazione-iliad:compila-report-car` → se richiesto report CAR

**Azione:**
1. Compila checklist BEF specifica per operatore
2. Verifica che tutti i documenti delle fasi precedenti siano presenti
3. Genera email/PEC di chiusura al PM cliente
4. Se Iliad → usa `iliad-progettazione-esecutiva` per verifica documentale
5. Se Cellnex → usa `cellnex-progettazione-esecutiva` per Form VS e checklist

**Output:** BEF completo caricato su portale, email chiusura inviata
**Condizione OK:** BEF caricato, conferma ricezione dal cliente
