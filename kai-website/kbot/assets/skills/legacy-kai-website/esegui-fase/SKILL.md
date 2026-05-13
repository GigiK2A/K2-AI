---
name: esegui-fase
description: >
  Orchestratore centrale cantieri TLC: esegue le fasi lavorative invocando le skill tecniche
  giuste (verifica PE, autorizzazioni, PSC, POS, sopralluoghi, prove, certificazioni, BEF).
  Usa SEMPRE per: "esegui fase", "lavora sulla fase", "verifica il PE", "controlla autorizzazioni",
  "redigi PSC", "verifica POS", "fai sopralluogo CSE", "genera SAL", "prove GC",
  "commissioning", "raccogli certificazioni", "fai il CFL", "prepara BEF",
  "cosa devo fare per questa fase", "prossimo step sito", "lavora sul sito",
  "avanza il cantiere", "esegui il prossimo passo".
tools:
  - Read
  - Write
  - Edit
  - Bash
  - Glob
  - Grep
---

# Esegui Fase — Orchestratore Cantieri TLC

Questa skill è il cuore del plugin: per ogni fase del processo cantiere, sa QUALE skill tecnica invocare e COSA farle fare. Non si limita a tracciare — esegue il lavoro.

## Flusso Operativo

### 1. Identifica sito e fase

Quando l'utente chiede di lavorare su un sito:

1. Leggi il tracker `tracker_cantieri_tlc.xlsx` dalla cartella di lavoro
2. Identifica il sito (per codice, o chiedi con `AskUserQuestion`)
3. Mostra lo stato corrente di tutte le fasi
4. Identifica la **prossima fase da eseguire** (prima fase non ancora "OK")
5. Chiedi conferma: "La prossima fase è **F[XX] — [Nome]**. Vuoi procedere?"

### 2. Esegui la fase

Leggi la matrice in `references/matrice-fase-skill.md` per la fase selezionata, poi:

1. **Spiega** all'utente cosa si farà e quali skill verranno coinvolte
2. **Chiedi i dati necessari** (documenti, informazioni specifiche)
3. **Invoca le skill tecniche** appropriate per eseguire il lavoro
4. **Genera gli output** previsti dalla matrice (documenti, checklist, report)
5. **Verifica** che tutto sia conforme prima di vidimare

### 3. Vidima e aggiorna tracker

Solo dopo che il lavoro è stato eseguito e verificato:
1. Aggiorna il tracker Excel con lo stato della fase
2. Se completata → scrivi la **DATA** (dd/mm/yyyy) nella cella (mai "OK")
3. Se ci sono problemi → segna `NC` con nota esplicativa nella colonna Y
4. Se il lavoro è parziale → segna `IN CORSO`
5. Ricalcola la % avanzamento con recalc.py

**REGOLA DATE:** Le fasi completate si vidimano SEMPRE con la data di esecuzione. Questo permette di ricostruire la timeline del cantiere.

---

## Mappatura Fasi → Skill Tecniche

### F00 — Chi Firma
- **Nessuna skill esterna** — decisione interna K2A
- Determina DL e CSE: Raw Land → Luca (Ing.); Roof Top → Jessica (Arch.)
- Genera tabella figure responsabili

### F01 — Ricezione e Verifica PE
- **Iliad →** invoca `iliad-progettazione-esecutiva:verifica-pe-terzi`
- **Cellnex →** invoca `cellnex-progettazione-esecutiva:verifica-progetto-terzi`
- **Generico →** invoca `verifica-pe-terzi`
- Genera checklist elaborati + lista NC

### F02 — Verifica Autorizzazioni
- **Urbanistica →** invoca `progettazione-architettonica` per verifica PRG/NTA e titoli
- **Vincoli →** invoca `architetto-beni-monumentali` per paesaggistica/Soprintendenza
- **Zona sismica →** invoca `progettista-strutturale` per deposito Genio Civile
- Genera tabella autorizzazioni con stato

### F03 — PSC e CME Sicurezza
- **PSC →** invoca `psc-coordinamento-sicurezza` per redazione o aggiornamento
- **Legale →** invoca `psc-legale:psc-legale` per verifica responsabilità
- **CME →** invoca `direzione-lavori` per verifica costi sicurezza
- Genera PSC firmato + CME verificata

### F04 — Ricezione e Verifica POS
- **POS →** invoca `cse-coordinatore-sicurezza` per verifica operativa
- Verifica coerenza POS ↔ PSC
- Se subappalti → verifica POS subappaltatori
- Genera POS approvato o lista NC

### F05 — Cronoprogramma
- **Pianificazione →** invoca `direzione-lavori` per approvazione
- Verifica milestones e coerenza con autorizzazioni
- Genera cronoprogramma approvato

### F06 — Apertura Cantiere
- **Verbale →** invoca `direzione-lavori` per consegna area e GdL
- **Notifica →** invoca `psc-coordinamento-sicurezza` per Notifica Preliminare
- Genera verbale + NP + apertura GdL

### Sopralluogo Apertura Lavori (col O) — 1° obbligatorio
- **CSE →** invoca `cse-coordinatore-sicurezza`
- Verifica avvio cantiere, allestimento, DPI, cartello
- Genera verbale di coordinamento n. 1

### Sopralluogo Verifica in Cantiere (col P) — 2° obbligatorio
- **CSE →** invoca `cse-coordinatore-sicurezza`
- Verifica lavorazioni, interferenze, NC, prescrizioni
- Genera verbale di coordinamento n. 2+

### Sopralluogo Chiusura Lavori (col Q) — 3° obbligatorio
- **CSE →** invoca `cse-coordinatore-sicurezza`
- Verifica finale pre-chiusura, NC tutte chiuse
- Genera verbale di coordinamento finale

### Gestione Direzione Lavori (col R)
- **OdS, SAL, varianti →** invoca `direzione-lavori` per tutta la contabilità
- Genera OdS, SAL, perizia variante se necessaria
- Fase ciclica come F07

### F09 — Prove e Genio Civile
- **Strutturale →** invoca `progettista-strutturale` per prove, RSU, GC
- Verifica campioni cls, certificati acciaio
- Genera RSU firmata

### F10 — Commissioning
- **Elettrico →** invoca `impianti-elettrici` per verifica impianti e misure
- **Sicurezza →** invoca `cse-coordinatore-sicurezza` per sopralluogo finale
- Genera checklist commissioning + rapporto misure

### F11 — Certificazioni
- **DiCo →** invoca `impianti-elettrici` per verifica D.M. 37/2008
- **Agibilità →** invoca `agibilita` se necessaria (shelter abitabili, edifici)
- Raccoglie pacchetto certificazioni completo

### F12 — CFL
- **Fine lavori →** invoca `direzione-lavori` per CFL, verbale ultimazione, conto finale
- Verifica che F11 sia OK prima di procedere
- Genera CFL firmato

### F13 — BEF / Portale
- **Iliad →** invoca `iliad-progettazione-esecutiva:progetto-esecutivo-iliad` per checklist BEF
- **Cellnex →** invoca `cellnex-progettazione-esecutiva:verifica-progetto-terzi` per Form VS
- **Report CAR →** invoca `report-caratterizzazione-iliad:compila-report-car` se richiesto
- Genera BEF completo + email chiusura

---

## Regole di Sicurezza

### Prima di vidimare una fase come "OK", VERIFICA SEMPRE:

1. **Propedeuticità:** le fasi precedenti devono essere tutte OK o N/A
   - Non puoi fare F06 (Apertura) se F03 (PSC) è ancora NC
   - Non puoi fare F12 (CFL) se F11 (Certificazioni) non è OK

2. **Documenti prodotti:** ogni fase deve generare i suoi output previsti
   - F01 → checklist PE compilata
   - F03 → PSC firmato
   - F06 → verbale consegna firmato
   - F12 → CFL firmato

3. **Coerenza:** verifica che i documenti siano coerenti tra loro
   - Il PSC deve riferirsi al PE vigente
   - Il POS deve essere coerente con il PSC
   - Il CFL deve elencare tutte le certificazioni raccolte

### Se una verifica FALLISCE:
- Segna la fase come "NC" nel tracker
- Genera nota con descrizione del problema
- Suggerisci la skill da usare per risolvere
- Non procedere alle fasi successive

---

## Esempio d'Uso Completo

**Utente:** "Lavora sul sito MI00234_001"

**Plugin:**
1. Legge il tracker → sito MI00234_001, Iliad, Raw Land, DL: Luca
2. Stato: F00-F06 = OK, F07 = IN CORSO, F08-F13 = vuoto
3. Mostra: "Il sito è in fase F07 (Sopralluoghi CSE) — 50% avanzamento"
4. Chiede: "Vuoi registrare un nuovo sopralluogo CSE?"
5. Se sì → invoca `cse-coordinatore-sicurezza` per generare il verbale
6. Dopo → chiede se ci sono state NC da registrare
7. Aggiorna il tracker

**Utente:** "Verifica il PE del sito RM00126_003"

**Plugin:**
1. Identifica il sito → RM00126_003, Iliad, Roof Top
2. Riconosce → si tratta della fase F01 (Ricezione PE)
3. Invoca `iliad-progettazione-esecutiva:verifica-pe-terzi`
4. Genera checklist con esito
5. Se OK → chiede "Vuoi segnare F01 come completata?"
6. Aggiorna il tracker
