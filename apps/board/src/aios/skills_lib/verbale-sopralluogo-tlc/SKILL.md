---
name: verbale-sopralluogo-tlc
description: Genera il Verbale di Sopralluogo congiunto DL+CSE per cantieri TLC (iliad/Cellnex) duplicando il template master DOCX e compilando solo i campi. USA quando l'utente scrive "verbale sopralluogo", "verbale DL CSE", "sopralluogo cantiere TLC", o cita un sito iliad/Cellnex con richiesta di verbale.
---

# Verbale di Sopralluogo DL + CSE — Cantieri TLC

Genera UN file `.docx` che è copia byte-per-byte del template master, con i soli valori sostituiti. **Non rigenerare il documento da zero**: il layout (tabelle, larghezze celle, stili, griglie foto, font Calibri, bordi) deve restare identico al master.

## Template master (fonte autoritativa del layout)

```
/Users/lucarossi/Documents/Claude/Projects/Direzine lavori e coordinamento sicureza telecomunicazioni/Templates/Template_Verbale_Sopralluogo_MASTER.docx
```

Cartella di output (stesso livello del template):
```
/Users/lucarossi/Documents/Claude/Projects/Direzine lavori e coordinamento sicureza telecomunicazioni/
```

Nome file output: `Verbale_sopralluogo_<CODICE_SITO>_<NOME_SITO>.docx`.

## Procedura operativa (vincolante)

### Step 1 — Skill di supporto
Invoca con `Skill`, nell'ordine, solo se non già attive:
1. `anthropic-skills:docx` — manipolazione del DOCX preservando stili.
2. `anthropic-skills:direzione-lavori` — contenuto §7 (conformità PE, SAL).
3. `anthropic-skills:cse-coordinatore-sicurezza` — contenuto §8 (documentazione, DPI, interferenze).
4. `anthropic-skills:consulente-sicurezza-lavoro` — D.Lgs. 81/2008 per checklist.
5. `gestione-cantiere-tlc:esegui-fase` — coerenza fase lavorativa TLC.
6. **Verifica progettuale (entrambe se applicabili):**
   - `anthropic-skills:progettista-strutturale` + `verifica-statica-iliad-cellnex:vs-orchestratore` — riscontro struttura realizzata vs progetto/VS.
   - `iliad-progettazione-esecutiva:verifica-pe-terzi` (committente iliad) **oppure** `cellnex-progettazione-esecutiva:verifica-progetto-terzi` (proprietà Cellnex) — confronto sistematico con tavole PE.
   - `verifyboost-tlc:matrice-scostamenti-tlc` — struttura la §7.3 con classificazione *Lieve / Sostanziale / Bloccante*.
7. **Profilo legale:**
   - `psc-legale:psc-legale` — **obbligatoria**: formula §9 (prescrizioni/ordini di servizio) in modo opponibile.
   - `anthropic-skills:diritto-urbanistica-edilizia` — se una difformità impatta il titolo abilitativo (necessità di variante S.C.I.A./CILA/PdC).
   - `anthropic-skills:diritto-italiano` — inquadramento generale responsabilità DL/CSE.

Se una skill non è disponibile, segnalalo e procedi con le rimanenti.

### Step 2 — Reperimento dati (regola ferrea)

NON inventare e NON precompilare nomi/società/professionisti. Per ogni campo:
1. **Cerca nei documenti di progetto** presenti nella cartella sito o forniti dall'utente (PE, PSC, Verifica Statica, Notifica Preliminare, POS, S.C.I.A./CILA, frontespizi, timbri). Usa Read/Glob/Grep.
2. Se manca, **chiedi all'utente** in lista puntata prima di generare il file.
3. Mai placeholder tipo "Ing. ___" o "Società XYZ" nel file finale.

Campi obbligatori:
- Codice sito + nome + indirizzo + comune/provincia
- Dati catastali (foglio, particella) e coordinate geografiche
- Proprietà infrastruttura (tower company)
- Committente (società + referente + sede)
- Titolo abilitativo (tipo, protocollo, data, ente)
- Data, ora, numero verbale
- Descrizione intervento, lavorazioni puntuali, importo
- Struttura portante (tipo + altezza) + estremi Verifica Statica
- Date inizio/fine lavori
- Progettista, DL, RdL, CSP, CSE (nome, ordine, n. iscrizione, CF, recapiti)
- Imprese: ragione sociale, datore di lavoro, sede, P.IVA
- Lavoratori: nome, impresa, qualifica, matricola, assunzione, sede
- Mezzi: tipo, targa, impresa
- Difformità progettuali rilevate (per §7.3) o conferma assenza
- NC / documenti mancanti (per `☐` in §8.1)

### Step 3 — Generazione del DOCX

1. **Duplica** il template master nella cartella di output con il nome file convenzionale.
2. Apri il DOCX duplicato (via libreria python-docx o equivalente nella skill `docx`) e **sostituisci solo i valori delle celle**, lasciando intatti: numero e ordine sezioni, larghezze colonne, stili paragrafo, font, bordi, dimensioni delle celle immagine dell'Allegato A, didascalie come testo modificabile.
3. **Checkbox**: `☑` se conformità verificata; `☐` + nota "Da verificare"/"In attesa" se documento o voce mancante.
4. Date `gg/mm/aaaa`; coordinate `Lat. xx.xxxxxx N – Long. xx.xxxxxx E`.
5. §7.3 (matrice difformità): se nessuna, una sola riga *"Nessuna difformità rilevata – cantiere conforme al PE e alla VS"*. Altrimenti una riga per difformità con colonne: # | Elemento (rif. tavola/relazione) | Previsione di progetto | Stato rilevato | Classificazione | Azione + termine.
6. §8.3: includere sempre i rischi standard — lavori in quota >2 m, linee AT adiacenti, impianto in tensione, caduta materiali, vento >45 km/h, interferenza viabilità.
7. §9: ogni prescrizione formulata secondo schema `psc-legale` — riferimento normativo, fatto contestato, prescrizione, termine, conseguenze inadempimento. Se §7.3 contiene difformità *Sostanziali* o *Bloccanti*, generare automaticamente in §9 la prescrizione corrispondente e, se impatta titolo abilitativo, richiamare l'obbligo di variante.

### Step 4 — Verifica pre-consegna

Prima di restituire il file:
- Numero e titoli sezioni identici al master (1–11 + Allegato A con A.1–A.5).
- Nessun campo placeholder.
- Stili e tabelle integri (apri il file con `unzip -p <file> word/document.xml | head` per controllo rapido se in dubbio).

## Output

Solo il percorso assoluto del `.docx` generato. Niente PDF, niente allegati extra, niente commento fuori dal file.

## Stile linguistico interno al verbale

Sobrio, tecnico, impersonale ("si attesta", "si è verificato", "si prescrive"). Nessuna formula di compiacimento, nessun emoji.
