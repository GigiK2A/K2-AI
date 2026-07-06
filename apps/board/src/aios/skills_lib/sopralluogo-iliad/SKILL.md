---
name: sopralluogo-iliad
description: >
  Skill per la redazione automatica del Verbale di Sopralluogo (VdS) di co-location iliad
  su sito INWIT esistente. Genera il documento .docx finale partendo dal template master
  K2A e dalla cartella di commessa iliad. Usa SEMPRE questa skill quando l'utente dice
  "verbale di sopralluogo iliad", "VdS iliad", "verbale sopralluogo COLOC iliad",
  "compila VdS per il sito", "report sopralluogo iliad", "sopralluogo iliad COLOC",
  "sopralluogo co-location iliad", "VdS coloc iliad", "verbale ospitalità iliad",
  "verbale sopralluogo INWIT ospitata iliad", "fotomontaggio antenne iliad",
  "configurazione zona apparati iliad", "doppia soluzione adduzione iliad",
  "contatore autonomo vs sottolettura iliad".
metadata:
  version: "1.0.0"
  author: "Luca Rossi — K2A"
  riferimento: "Template VdS iliad COLOC K2A v.1 — derivato da prassi Circet/INWIT"
---

# Verbale di Sopralluogo iliad COLOC — Generazione automatica

## Cosa fa questa skill

Genera **un singolo file `.docx`** che è il Verbale di Sopralluogo iliad in co-location su sito INWIT, conforme al layout standard K2A (5 sezioni testo + 5 sezioni fotografiche).

**Input:** una cartella di commessa iliad/Circet (es. `…/GR58022_002_FOLLONICA CENTRO/1-SA/`).
**Output:** un `.docx` salvato nella stessa cartella `1-SA/` con naming:
`{COD_INWIT}_{NOME_SITO}-{COD_ILIAD}_{NomeCommerciale}_VDS.docx`.

## Template master

Sempre da:
```
{SKILL_DIR}/Template_VdS_iliad_COLOC_MASTER.docx
```

**Non rigenerare il documento da zero**: duplica il master e sostituisci solo i placeholder `{{...}}` e i 14 binari immagine.

## Struttura del verbale (immutabile)

Sezioni nel master:

| Sez. | Contenuto | Campi placeholder |
|------|-----------|-------------------|
| T0 | Anagrafica sito | `{{COD_INWIT}}`, `{{NOME_SITO}}`, `{{DATA_SOPRALLUOGO}}`, `{{COMUNE_PROV}}`, `{{INDIRIZZO}}` |
| T1 | Presenti al sopralluogo (2 righe) | `{{NOM_PROF}}`/`{{SOC_PROF}}`/`{{TEL_PROF}}` + `{{NOM_ALTRO}}`/`{{SOC_ALTRO}}`/`{{TEL_ALTRO}}` |
| IMPIANTO INWIT (P4-P8) | Stato di fatto del sito ospite | tipologia, apparati, `{{STRUTTURA}}`, `{{GESTORI}}`, `{{LEGITTIMITA}}` |
| OSPITALITÀ ILIAD (P10-P17) | Richiesta iliad | `{{COD_NOME_SRB_ILIAD}}`, `{{APPARATI_ILIAD}}`, `{{ANTENNE_ILIAD}}`, `{{PARABOLE_ILIAD}}`, `{{ALIMENTAZIONE}}`, `{{FO}}`, `{{NOTE_NB}}` |
| Sezione FOTO: Area Antenne | 1 slot — fotomontaggio iliad+settori | `{{GESTORE1_SETTORI}}`, `{{GESTORE2_SETTORI}}`, `{{GESTORE3_SETTORI}}`, `{{ILIAD_FOTOMONTAGGIO_DESC}}` |
| Sezione FOTO: Area Apparati ILIAD | 2 slot | `{{ILIAD_APPARATI_DESC}}` |
| Sezione FOTO: Adduzione A Contatore Autonomo | 1 slot | (didascalia fissa) |
| Sezione FOTO: Adduzione B Sottolettura | 2 slot | (didascalia fissa) |
| Sezione FOTO: Panoramiche | 8 slot (4 paragrafi × 2 foto) | (nessuna didascalia per singola) |

**Totale: 14 slot foto.** Non aggiungere paragrafi extra; non cambiare numero/posizione delle sezioni.

## Procedura operativa (vincolante)

### Step 1 — Skill di supporto

Invoca con `Skill`, nell'ordine, solo se non già attive:
1. `anthropic-skills:docx` — manipolazione DOCX
2. `iliad-progettazione-esecutiva:verifica-pe-terzi` — riscontro preesistenze (per `{{LEGITTIMITA}}`)
3. `anthropic-skills:nano-banana` — **solo se** l'utente richiede esplicitamente il fotomontaggio iliad generato (vedi Step 5)

### Step 2 — Discovery della cartella sito

Mappa con `Glob`/`Read` (questi pattern, in ordine di priorità):

| Fonte | Cosa estrarre |
|-------|---------------|
| `Valutazione_Preesistenze_*.docx` | coord WGS84, NCT (foglio/particella), struttura palo, cronologia, codici Inwit alternativi |
| `Scheda Rischi I*.pdf` | codice INWIT attivo + data ultima Scheda Rischi |
| `PREESISTENZE/*.pdf` (PRG ARC, VS, PE) | gestori presenti + loro settori |
| `SR + SP/` o `Scheda_Radio_iliad*.pdf` | n. antenne 4G/5G, lunghezze, BA, parabole, CP, RRH, settori desiderati iliad |
| `SOPRALLUOGO/FOTO/report/` | foto curate per il verbale (nomi convenzionali, vedi Step 4) |
| `SOPRALLUOGO/FOTO/<nome_sito>/` | panoramiche numerate del sito |
| Date EXIF/filename di `SOPRALLUOGO/FOTO/*` | data sopralluogo |

### Step 3 — Reperimento dati (regola ferrea)

Per ogni placeholder del template:
1. Cerca prima nei documenti di commessa (vedi tabella Step 2)
2. **Se manca, CHIEDI all'utente in lista puntata prima di generare il file**
3. Mai placeholder residui nel file finale (`{{...}}` deve essere tutto sostituito)

**Dati fondamentali da risolvere SEMPRE prima della generazione:**

- **Anagrafica sito**: cod Inwit, nome, comune+prov, indirizzo, data sopralluogo
- **Presenti**: almeno nome+società del professionista K2A
- **Struttura**: tipo palo (poligonale/tubolare/flangiato/traliccio) + altezza + pennone
- **Gestori esistenti**: lista (es. "VODAFONE + WINDTRE") **con i settori di ciascuno** (azimut)
- **Esito preesistenze → Legittimità**: una di queste tre forme:
   - "Conforme — preesistenze complete e verificate (VS DIVIGROUP/Calzavara/…)"
   - "Mancano preesistenze [terzo operatore / fondazione / VS] — non verificabile"
   - "Non Conforme — [motivo specifico]"
- **Apparati iliad** (da scheda radio): FCOB+MiniTD+ICA o variante, n. RRH, quota CG
- **Antenne iliad**: numero, lunghezza, BA + nota su isoquota con gestori esistenti
- **Parabole iliad**: numero, diametri, CP
- **Adduzione elettrica**: SEMPRE la doppia soluzione (A contatore autonomo / B sottolettura) — con indicazione preferita se nota
- **F.O.**: Presente / Non presente / Da verificare
- **Note N.B.**: vincoli specifici (sedime ferroviario, sismica, paesaggistici, ENAC/ENAV, archeologici), cronistoria palo solo se rilevante

Se l'utente dice "compila tutto, chiedimi solo lo stretto necessario" → considera anche un default ragionevole per i campi opzionali (es. `STRUTTURA_OSPITE` = "carpenteria apparati iliad — resto in quota già presente"), ma **non inventare mai gestori, settori, esiti preesistenze, scheda radio iliad**.

### Step 4 — Mappatura foto automatica

Cerca in `SOPRALLUOGO/FOTO/report/` per nome convenzionale:

| Slot # | Sezione | Pattern nome file (case-insensitive) |
|--------|---------|---------------------------------------|
| 1 | Area Antenne | `fotomontaggio*.*` OPPURE generato da nano-banana (vedi Step 5) OPPURE `antenne*iliad*` |
| 2 | Area Apparati ILIAD | `area*sito*iliad*` o `area*iliad*pianta*` (prima foto) |
| 3 | Area Apparati ILIAD | `area*iliad*pianta*` o `area*sito*iliad*` (seconda foto) |
| 4 | Adduzione A | `*contatori*autonom*` o `*fornitura*autonoma*` |
| 5 | Adduzione B | `*QE*sottolettura*` o `*pianta*sottolettura*` (pianta) |
| 6 | Adduzione B | `sottolettura*.jpg` o `QE_wind*` (foto QE) |
| 7-14 | Panoramiche | tutto il resto in `report/` + `follonica centro/` (o cartella `<nome_sito>/`) — fino a 8 foto |

Se mancano foto per gli slot 1-6: **CHIEDI all'utente** quale file usare o dichiara lo slot vuoto.
Se ci sono <8 panoramiche disponibili: **chiedi** o lascia gli slot vuoti (vedi gestione "panoramiche assenti" in Step 6).

### Step 5 — Fotomontaggio iliad (slot 1, opzionale)

Solo se l'utente richiede esplicitamente di generare il fotomontaggio iliad:
1. Identifica una foto del palo "pulita" (es. prospetto WindTre o foto in quota del palo nudo)
2. Invoca `anthropic-skills:nano-banana` con prompt strutturato:
   ```
   Sulla foto del palo esistente, aggiungi le antenne iliad alle quote richieste:
   - n.{N_ANT_4G} antenne 4G di lunghezza {L_ANT}m al baricentro {BA}m sui settori {AZIMUT_ILIAD}
   - n.{N_PARAB} parabole di diametro {D_PARAB}cm al centro pennone {CP}m
   - n. RRH a centro gruppo {CG}m
   Colore antenne: bianco standard. Mantieni proporzioni del palo, illuminazione coerente.
   ```
3. Salva il PNG generato in `SOPRALLUOGO/FOTO/report/fotomontaggio_iliad_<COD_ILIAD>.png` e usalo come slot 1.

Se l'utente NON richiede il fotomontaggio: lascia lo slot 1 con la foto "antenne iliad" originale, oppure chiedi quale foto usare.

### Step 6 — Sostituzione binari immagine (FORMATO CORRETTO)

⚠️ **IMPORTANTE — Errore frequente da evitare**: le foto vengono spesso "stirate" perché il template ha slot di aspect ratio fisso (cx, cy in EMU dichiarati nel drawing XML). Per evitare deformazioni:

1. **Leggi le dimensioni native** della foto Torresina/Follonica (PIL `img.size`)
2. **Leggi cx/cy** del drawing dello slot dal `word/document.xml` (regex su `wp:extent cx="..." cy="..."` E sul `pic:spPr/a:xfrm/a:ext`)
3. **Calcola aspect ratio** della foto originale e dello slot
4. Se differiscono di più del 5%, **NON limitarti a sostituire il binario**. Devi:
   - Padding bianco automatico per portare la foto all'aspect ratio dello slot (Pillow: `ImageOps.pad`), **OPPURE**
   - Aggiornare cx/cy nel drawing XML per matchare l'aspect della foto (preserva i pixel originali)
5. Salva la foto sempre con `optimize=True` e qualità 85 per JPEG (riduce dimensioni docx)
6. Risoluzione massima output: 1600px sul lato lungo (sufficiente per stampa A4)

Lo script `scripts/swap_photos.py` (vedi sezione Riferimenti) implementa questa logica con `ImageOps.pad`.

### Step 7 — Generazione del DOCX

1. **Duplica** il master template nella cartella `1-SA/` con il nome convenzionale
2. Apri con `python-docx` e sostituisci **solo i valori dei placeholder** `{{...}}` preservando stili
3. **Checkbox/spunte**: non presenti in questo template (è già "lineare")
4. **Date**: `gg/mm/aaaa`
5. **Coordinate**: come da fonte (`42°55'39,4"N — 10°45'18,1"E`)
6. Foto: vedi Step 6

### Step 8 — Verifica pre-consegna

Prima di restituire il file:
- Nessun `{{...}}` residuo (grep): se ne trovi, il file è incompleto, segnalalo all'utente
- Numero tabelle = 3, numero immagini ≥ 8 (slot panoramiche possono essere vuoti)
- Apri con `python-docx` e dump rapido per controllo
- Naming output rispettato

## Gestione "panoramiche assenti"

Se le 8 foto panoramiche non sono disponibili o l'utente preferisce gestirle a mano:
1. Lascia gli 8 slot panoramiche con le immagini placeholder del master (l'utente le sostituirà manualmente in Word)
2. Aggiungi una sola riga di nota all'inizio della sezione Panoramiche, in colore rosso:
   `[NOTA K2A — sostituire manualmente le panoramiche con foto da SOPRALLUOGO/FOTO/<nome_sito>/]`

Sempre meglio lasciare le foto del master che inserire foto sbagliate o stirate.

## Output

Solo il percorso assoluto del `.docx` generato + una tabella riassuntiva di:
- placeholder risolti (count)
- placeholder rimasti aperti (lista — se vuoto, "✓ tutti risolti")
- foto sostituite (slot # → file sorgente)
- foto non sostituite (slot # → motivo)

Niente PDF, niente note extra nel file.

## Stile linguistico interno al verbale

Sobrio, tecnico, conciso (come da forma definitiva utente K2A — Follonica Centro 07/05/2026). Frase tipo:
- "Da TR: n. 3 antenne iliad — altezza B.A. 27 mt circa isoquota tim"
- "FCOB + MiniTD + ICA (se contatore autonomo), 3 RRH A settore altezza 24 mt"
- "Mancano preesistenze terzo operatore – non verificabile"

Niente formule di compiacimento, niente emoji, niente promemoria inline rossi (l'unica eccezione è la nota per panoramiche da sostituire).

## Riferimenti

- `Template_VdS_iliad_COLOC_MASTER.docx` — template master con 14 slot foto e tutti i placeholder
- `scripts/swap_photos.py` — script Python per sostituzione foto con preservazione aspect ratio
- `references/checklist_dati.md` — checklist completa dei dati da chiedere all'utente quando non trovati
