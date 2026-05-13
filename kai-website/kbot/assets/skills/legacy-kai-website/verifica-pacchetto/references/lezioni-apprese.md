# Lezioni Apprese — Redazione Pacchetti SCIA art. 45 iliad

> **QUESTO FILE È OBBLIGATORIO.** Va letto PRIMA di toccare qualsiasi template. Ogni voce è un errore realmente commesso in sessioni precedenti — non ripeterlo.

---

## L1 — Cancellazione accidentale della procura Longari

**Sintomo:** dopo la compilazione, il paragrafo con "Andrea Longari, Procuratore Speciale, giusta procura notarile…" sparisce da SCIA/Delega/Atto d'obbligo.

**Causa:** il template contiene annotazioni **inline** dentro frasi valide, tipo:
> "…procura notarile **, VERIFICARE CHE LA PROCURA SIA SEMPRE QUELLA DEL 04/2024** del 10/04/2024…"

Se uso `delete_paragraphs_by_markers` con `"VERIFICARE CHE LA PROCURA"` come marker, elimino l'INTERO paragrafo della procura.

**Regola canonica:**
- Le annotazioni **INLINE** (dentro un paragrafo che deve restare) vanno messe in `replacements` con stringa vuota, **MAI** in `annotation_markers`.
- Prima di aggiungere un marker, aprire il template e verificare se la stringa è inline o standalone. Vedi `annotazioni-template.md` per la classificazione canonica.

---

## L2 — Preesistenze sample nel template RT/ASSEV scambiate per dati reali

**Sintomo:** il pacchetto consegnato riporta `QF/2025/0126488 del 26/09/2025`, `19436.U del 20/03/2023` e un paragrafo VAP `NA/13029 del 12/06/2023` che non hanno nulla a che vedere con il sito reale.

**Causa:** il template `4.codice sito_nome sito_RT.docx` (tabella T3 R0 C1) e `6.ASSEVERAZIONI.docx` contengono già tre preesistenze sample REALISTICHE che vanno sempre sostituite. Non sono placeholder vuoti — sembrano dati veri.

**Regola canonica:** in ogni sessione, per RT/ASSEV, sostituire ESPLICITAMENTE queste stringhe (vedi `valori-sample-template.md` per l'elenco completo):
- `"24/09/2025"` → data invio SCIA preesistente reale
- `"QF/2025/0126488 del 26/09/2025"` → protocollo SCIA preesistente reale
- `"19436.U del 20/03/2023"` → protocollo ARPA preesistente reale
- **VAP**: se il sito non ha VAP (caso frequente: T3 Città consolidata fuori Rete Ecologica), cancellare sia la riga dei vincoli `V.A.P. – ininfluente…` sia la preesistenza `Parere favorevole del Dipartimento Ciclo dei Rifiuti…`

**Come evitarlo:** tenere in `edit_rt.py` e `edit_asseverazioni.py` la lista di replacements per queste sample, anche quando il sito sembra identico. È a costo zero mantenerle.

---

## L3 — PRG T4 (Città storica) nel template ma sito in T3 (Città consolidata)

**Sintomo:** la RT recita `Città storica: Tessuti di espansione otto-novecentesca ad isolato – T4` anche se il sito è in periferia (es. Tuscolana, Tiburtina, ecc.).

**Causa:** il template ha come PRG sample "T4 Città storica", ma le tavole del PRG variano per zona. Roma ha tipicamente:
- Centro storico → T1/T2/T3 Città storica
- Fascia intermedia ottocentesca → T4 Città storica
- Periferia novecentesca (Tuscolana, Prenestina, ecc.) → T3 Città consolidata "Tessuti di espansione novecentesca a tipologia edilizia libera"
- Zone di espansione → Città da ristrutturare, Agro Romano, ecc.

**Regola canonica:** SEMPRE verificare il PRG su WebGIS Roma (vedi `regolamento-roma.md`) e sostituire il testo sample `"Città storica: Tessuti di espansione otto-novecentesca ad isolato – T4"` con il testo corretto prima di salvare.

---

## L4 — Aeroporti di riferimento: tenere SOLO quello pertinente dal PDM

**Sintomo:** la RT elenca Ciampino + Fiumicino + Urbe con tre righe diverse nelle tabelle T3 (RT) e T1 (ASSEV). L'utente chiede di tenerne solo uno.

**Regola canonica:**
1. Aprire il PDM (Piano Di Misura) del sito (`COMUNE/RMXXXXX_XXX_PDM_*.pdf`) ed estrarre il testo con `pdftotext -layout`.
2. Cercare quale aeroporto è citato nelle tavole 7.x del PDM: quello è il **reference**.
3. Nella RT (tabella 3, riga 0, celle 0 e 1) e nell'ASSEV (tabella 1, riga 0, celle 0 e 1):
   - Cancellare i paragrafi con `"Leonardo Da Vinci"` e `"Carta degli ostacoli di Aeroporto Roma Urbe"` in C0 (labels)
   - Cancellare i 2 paragrafi `"L'area in oggetto non è soggetta a limitazioni;"` in C1 (valori Fiumicino + Urbe)
   - Lasciare solo la riga Ciampino con il valore corretto per il sito (vedi L5)
4. Euristiche geografiche (SOLO come sanity-check, mai come fonte primaria — leggere sempre il PDM):
   - Roma Sud/Sud-Est (Tuscolana, Appia, Casilina, Prenestina) → **Ciampino "G.B. Pastine"**
   - Roma Ovest/Sud-Ovest (Portuense, Aurelia, Magliana) → **Fiumicino "Leonardo Da Vinci"**
   - Centro/Nord (Flaminio, Salario, Tiburtina bassa) → **Roma Urbe**

---

## L5 — ENAC Ciampino: `Area interessata` vs `Area non interessata`

**Sintomo:** il template ha "Area **non** interessata da limitazione e non interferente con la superficie di inviluppo" ma il sito rientra in una superficie di limitazione ENAC.

**Regola canonica:** leggere dal PDM/verifica ENAC. I due testi canonici sono:
- `"Area non interessata da limitazione e non interferente con la superficie di inviluppo"` — fuori da qualunque superficie di limitazione
- `"Area interessata da limitazione e non interferente con la superficie di inviluppo"` — dentro una superficie di limitazione ma senza interferenza

Una volta scelto, deve essere coerente tra RT e ASSEV.

---

## L6 — Foto del sito nel template è quella di un altro cantiere

**Sintomo:** la RT consegnata ha la documentazione fotografica con l'immagine di default del template (un altro Roof Top).

**Causa:** il template `4.codice sito_nome sito_RT.docx` incorpora in `word/media/image1.jpeg` e `word/media/image2.jpeg` due immagini di un sito campione. `python-docx` non le tocca nelle sostituzioni di testo.

**Regola canonica:** dopo `doc.save(dst)`, sostituire le immagini via zipfile. Vedi `post-processing.md` § "Sostituzione Foto Sito".

**Come sapere quali immagini sostituire:** listare `word/media/` e cercare i file `.jpeg` > 100KB (le icone sono < 20KB). In caso di dubbio, chiedere all'utente di confermare la foto corretta PRIMA di consegnare.

---

## L7 — Red color di annotazioni rimane anche dopo la sostituzione testuale

**Sintomo:** dopo aver sostituito un'annotazione rossa `"INSERIRE PRECISAZIONI RELAZIONE TECNICA"` con il testo corretto, il testo nuovo resta rosso perché eredita il `<w:color w:val="FF0000"/>` del run originale.

**Regola canonica:** dopo tutte le sostituzioni di testo, fare uno sweep XML-level per rimuovere tutti i `<w:color>` rossi. Codice in `post-processing.md` § "Red Color Stripping".

---

## L8 — Alpha24 reference site: NON è il codice sito stesso per default

**Sintomo:** la dichiarazione ALPHA24 riporta un reference site errato (es. placeholder della sessione precedente).

**Regola canonica:** il reference site alpha24 è scritto ESPLICITAMENTE nella Scheda Radio sotto la voce `"Reference Site alpha24 5G: XXXXX"`. Va estratto da lì caso per caso. A volte è il sito stesso (self-reference), a volte è un sito vicino. **Non inventare, non copiare dalla sessione precedente.**

---

## L9 — Progettista vs Direttore dei Lavori: due figure distinte

**Sintomo:** in un documento compaiono entrambi i nomi (Rossi + Romanelli) perché il template ha due occorrenze diverse da valorizzare.

**Regola canonica:** all'inizio della sessione, chiedere all'utente:
- Chi è il **Progettista** (firma RT, Asseverazioni, dichiarazioni tecniche)?
- Chi è il **DL** (se diverso)?

Tipicamente per K2A: Ing. Jessica Romanelli è progettista, Ing. Luca Rossi è DL (ma non dare per scontato). Vedi `dati-sito.md` per i dati anagrafici completi.

La RT e le Asseverazioni portano il nome del **progettista**. L'Atto d'obbligo porta il nome del **Legale rappresentante iliad (Longari)**. La Dichiarazione ALPHA24 porta il nome del **progettista**.

---

## L10 — VAP: verificare applicabilità art. 5 co. 5 Delibera 78/2024 PRIMA di lasciare riferimenti VAP

**Sintomo:** la RT/ASSEV cita il VAP come preesistenza o vincolo anche se il sito non è tra le zone art. 5 co. 5.

**Regola canonica:**
1. Verificare il PRG Tav. 4_XX (Rete Ecologica) e le altre zone elencate in `regolamento-roma.md` (Aree verde privato della Città consolidata, Ambiti strategici, Agro Romano, Servizi).
2. Se il sito **NON** rientra → cancellare OGNI riferimento VAP:
   - Riga `V.A.P. – ininfluente ai fini dell'intervento;` nei vincoli
   - Preesistenza `Parere favorevole del Dipartimento Ciclo dei Rifiuti...`
   - Allegato VAP nella SCIA (se presente)
   - Nella relazione precisazioni ASSEV: scrivere che "non è richiesta la VAP ai sensi dell'art. 5 co. 5 della Delibera 78/2024"
3. Se il sito **rientra** → mantenere tutti i riferimenti e verificare che la preesistenza VAP sia presente.

---

## L11 — Alternative inline "edificio O INFRASTRUTTURA SE PALO"

**Sintomo:** il template ha frasi tipo `"il palo O INFRASTRUTTURA SE PALO è ancorato…"` perché pensato per coprire sia edifici che pali. In output rimane il frammento `O INFRASTRUTTURA SE PALO`.

**Regola canonica:** queste alternative sono annotazioni INLINE da risolvere sostituendo con la versione corretta per il caso del sito. Vedi `annotazioni-template.md` per l'elenco completo.

---

## L12 — Perdita di memoria tra sessioni (meta-lezione)

**Sintomo:** ogni nuova sessione ri-scopre gli stessi bug, perché il modello non ha memoria persistente tra sessioni.

**Regola canonica:** ogni volta che emergono un nuovo pattern o un nuovo errore, AGGIORNARE questo file con una nuova voce L-next. Se ricevi feedback dell'utente del tipo "hai dimenticato X", "ti avevo detto Y", "l'avevamo già risolto Z" → quello è un segnale che il file va esteso. Non dire "scusa" e basta: apri il file e aggiungi la voce.

---

## L13 — Asseverazioni derivano dalla Relazione Tecnica (ORDINE VINCOLANTE)

**Sintomo:** le Asseverazioni contengono precisazioni generiche, disallineate rispetto alla Relazione Tecnica; oppure Asseverazioni compilate per prime con dati che poi cambiano quando viene finalizzata la RT → incoerenze tra i due documenti.

**Causa:** il documento `6.ASSEVERAZIONI.docx` è concepito come **derivato** della Relazione Tecnica. La cella "relazione precisazioni" (C0 P31) e i dati PRG/PTPR/ENAC/vincoli devono essere **gli stessi** che compaiono nella RT. Se si compilano le Asseverazioni prima della RT, c'è il rischio concreto di:
- scrivere precisazioni generiche (placeholder, valori sample del template)
- disallinearle rispetto al testo finale della RT
- dover rifare il lavoro quando la RT viene poi aggiornata

**Regola canonica (ORDINE DI REDAZIONE BLOCCANTE):**

1. **PRIMA** → redigere e finalizzare `4.RT.docx` (Relazione Tecnica) completa:
   - PRG/PTPR/vincoli verificati da WebGIS Roma
   - Preesistenze SCIA/ARPA/VAP aggiornate con protocolli reali
   - ENAC verificato dalle tavole PDM
   - Descrizione intervento, tipo modifica, apparati
   - Foto sito sostituite
   - Red stripping eseguito
   - Sanity-check passato

2. **POI e SOLO POI** → redigere `6.ASSEVERAZIONI.docx` **derivando esplicitamente da RT**:
   - Leggere il testo finale della RT (`docx2txt` o `Document()` + iter paragrafi)
   - Copiare/derivare i dati PRG/PTPR/ENAC/vincoli dalla RT (non da altre fonti)
   - Nella cella "relazione precisazioni" inserire un **riassunto coerente** del testo RT: tipo intervento, preesistenze citate in RT, conformità urbanistica dichiarata in RT, eventuale esclusione VAP ex art. 5 co. 5 Delib. 78/2024 (se già motivata in RT)
   - Stesse stringhe di PRG/ENAC → se la RT dice "T3 Città consolidata" allora l'ASSEV deve dire identicamente "T3 Città consolidata"

3. **Implementazione pratica:** lo script `edit_asseverazioni.py` DEVE leggere `4.RT.docx` dall'output e estrarne i valori canonici prima di compilare l'ASSEV. In alternativa, il dizionario `SITO` deve essere la singola fonte di verità per entrambi gli script, e `edit_asseverazioni.py` non deve mai essere eseguito prima di `edit_rt.py`.

4. **Ordine di esecuzione nel flusso di redazione:**
   ```
   edit_scia.py  →  edit_delega.py  →  edit_rt.py  →  edit_asseverazioni.py  →  edit_atto.py  →  edit_alpha24.py  →  edit_arpa.py
                                         ↑              ↑
                                         |              | DEVE leggere l'output di edit_rt.py
                                         |              | e/o usare lo stesso dizionario SITO
                                         |
                                         | DEVE essere completato PRIMA di edit_asseverazioni.py
   ```

5. **Sanity-check dedicato:** dopo aver generato entrambi i documenti, confrontare i valori chiave:
   - PRG (stringa RT) == PRG (stringa ASSEV)
   - PTPR (stringa RT) == PTPR (stringa ASSEV)
   - ENAC Ciampino area interessata/non → identica
   - Elenco vincoli → identico
   - Preesistenze SCIA/ARPA/VAP → identiche
   
   Se c'è anche una sola discrepanza → NON consegnare il pacchetto, tornare al flusso.

---

## L14 — Permit Coordinator sbagliato in SCIA, DICH. SOSTITUTIVA, Atto d'obbligo

**Sintomo:** i documenti riportano un Permit Coordinator diverso da quello corretto. Il dato cambia nel tempo (prima era uno, ora è un altro — attualmente Bellussi).

**Causa:** il template contiene un Permit Coordinator sample o obsoleto. Lo script non ha sostituito il valore con quello corretto, oppure ha usato un valore preso da un'altra fonte che non era aggiornata.

**Regola canonica:**
1. Il Permit Coordinator **DEVE** essere letto dalla **preesistenza** (pacchetto precedente dello stesso sito o pacchetto recente dello stesso comune/zona). La preesistenza contiene il valore che il committente iliad ha validato l'ultima volta.
2. Se non c'è preesistenza → chiedere esplicitamente all'utente: "Quale Permit Coordinator indicare? (es. Bellussi, altro)"
3. Il Permit Coordinator compare in: **doc 1 (SCIA)**, **doc 9 (DICH. SOSTITUTIVA α24)**, **doc 10 (Atto d'obbligo)** — verificare che sia identico in tutti e tre.
4. Aggiungere il campo `permit_coordinator` (nome, telefono, email) al dizionario `SITO` e usarlo come fonte unica per tutti gli script.
5. Aggiungere alla domande obbligatorie: "Permit Coordinator da preesistenza: [nome, telefono, email]?"

---

## L15 — Codice reversale mancante nella SCIA

**Sintomo:** nella SCIA art. 45 manca il "codice reversale" (codice del pagamento dei diritti).

**Causa:** il codice reversale è un dato procedurale che non compare in nessun template e non è generabile automaticamente — deve essere fornito dall'utente o dalla preesistenza.

**Regola canonica:**
1. Chiedere SEMPRE in Fase 0-QUATER (domande obbligatorie): "Codice reversale per la SCIA (dal pagamento dei diritti di segreteria)?"
2. Se l'utente non lo ha ancora → segnare `[DA COMPILARE — richiede: codice reversale pagamento]` nel punto corretto della SCIA
3. Aggiungere il campo `codice_reversale` al dizionario `SITO`
4. Il codice reversale va inserito nella SCIA nel punto dove si dichiara l'avvenuto pagamento

---

## L16 — Foto deformata nella RT (copertina e ultima pagina)

**Sintomo:** la foto del sito nella RT è deformata (aspect ratio sbagliato) — risulta stirata o compressa.

**Causa:** quando si sostituisce un'immagine nel `.docx` via zipfile, la nuova immagine ha dimensioni pixel diverse dall'originale ma il `<wp:extent>` e `<a:ext>` nel XML mantengono le dimensioni dell'immagine originale. Se le proporzioni non coincidono → immagine deformata.

**Regola canonica:**
1. Dopo la sostituzione via zipfile di `word/media/image1.jpeg` e `image2.jpeg`, **leggere le dimensioni pixel della nuova immagine** (es. con PIL/Pillow: `Image.open(path).size`)
2. Calcolare l'aspect ratio della nuova immagine: `ar = width / height`
3. Nel `word/document.xml`, cercare i tag `<wp:extent cx="..." cy="..."/>` e `<a:ext cx="..." cy="..."/>` associati all'immagine
4. Mantenere una delle due dimensioni (es. `cx` larghezza) e ricalcolare l'altra: `cy_new = cx / ar`
5. Le unità sono EMU (English Metric Units): 1 cm = 360000 EMU, 1 inch = 914400 EMU
6. **Alternativa semplice**: ridimensionare la nuova immagine alle stesse dimensioni pixel dell'immagine originale PRIMA di iniettarla nel zip (con `Image.resize()` di Pillow)
7. **Test visivo**: dopo la sostituzione, aprire il `.docx` e verificare che la foto non sia deformata — aggiungere questo step al sanity-check in `post-processing.md`

---

## L17 — Proprietà infrastruttura sbagliata nella RT ("SITE" invece di "Cellnex")

**Sintomo:** nella tabella "1. Dati identificativi dell'immobile" della RT, il campo proprietà riporta "SITE S.p.A." (o altro valore sample) invece del proprietario reale (es. "Cellnex Italia S.p.A.").

**Causa:** il template RT ha un valore sample per la proprietà dell'infrastruttura. Se lo script non lo sostituisce esplicitamente, rimane il valore errato.

**Regola canonica:**
1. Il proprietario dell'infrastruttura va letto dalla **preesistenza** (campo che indica chi possiede il palo/edificio/terreno)
2. Valori comuni: `Cellnex Italia S.p.A.`, `SITE S.p.A.`, proprietà privata (nome condominio/proprietario), proprietà comunale
3. Aggiungere il campo `proprieta_infrastruttura` al dizionario `SITO` — è un dato OBBLIGATORIO
4. Nella `valori-sample-template.md` aggiungere il valore sample del template per la proprietà (identificarlo dalla diagnostica template Fase 0-TER)
5. Nelle domande obbligatorie: "Proprietario infrastruttura (da preesistenza): [nome]?"

---

## L18 — Codici tavole PRG nella RT non corrispondono alla cartografia PDF

**Sintomo:** nella sezione cartografia della RT, i codici delle tavole PRG (es. "Tav. 3_18") non corrispondono a quelli della cartografia effettivamente allegata come PDF.

**Causa:** il template contiene codici tavola sample (es. `Tav. 3_18` per la zona tipo del template). Se il sito è in un'altra zona di Roma, le tavole PRG hanno numeri diversi (es. `Tav. 3_12`, `Tav. 3_22`, ecc.). Lo script ha lasciato i codici del template senza aggiornarli.

**Regola canonica:**
1. In Fase 0 (ricerche web), quando si verifica il PRG su WebGIS Roma, annotare ANCHE il numero specifico della tavola (es. `Tav. 3_12 — Sistemi e regole — Zona Tuscolana`)
2. Se l'utente fornisce i PDF degli stralci cartografici (es. `Stralcio_PRG_Tav3.pdf`), leggere dal nome del file o dal contenuto il numero esatto della tavola
3. Il campo `tavola_prg` (e analogamente `tavola_ptpr_a`, `tavola_ptpr_b`, `tavola_ptpr_c`) va aggiunto al dizionario `SITO`
4. Cercare e sostituire nel template TUTTI i riferimenti a tavole sample con quelli reali
5. **Validazione**: confrontare i codici tavola nel testo della RT con i nomi dei file PDF allegati — se non corrispondono → NC BLOCCANTE

---

## L19 — Didascalia PRG "Sistemi e regole" con testo sample del template

**Sintomo:** nella sezione cartografia PRG della RT, la didascalia sotto lo stralcio riporta un testo generico o relativo a un'altra zona (es. "Città storica: Tessuti di espansione otto-novecentesca ad isolato – T4" per un sito in periferia novecentesca T3).

**Causa:** collegato a L3 — il template ha una didascalia PRG sample che va SEMPRE aggiornata. Ma qui il problema è più specifico: non basta sostituire "T4" con "T3" nel corpo testo — bisogna aggiornare anche la **didascalia** sotto lo stralcio cartografico, che è un testo separato.

**Regola canonica:**
1. La didascalia PRG **deve riportare esattamente la destinazione urbanistica del sito** come risulta dalla verifica WebGIS Roma
2. Formato canonica: `"Stralcio P.R.G. — Tav. [X]_[Y] — Sistemi e regole: [zona/tessuto esatto]"`
3. Cercare nel template TUTTE le occorrenze della didascalia sample e sostituirle
4. Le didascalie possono essere in paragrafi sotto le immagini O dentro le tabelle — cercare in entrambi i contesti

---

## L20 — Zona sismica non aggiornata nella RT

**Sintomo:** la RT riporta una zona sismica errata (es. "Zona 2" quando Roma è classificata diversamente).

**Causa:** il template ha un valore sample di zona sismica che non viene aggiornato.

**Regola canonica:**
1. La zona sismica di Roma è **Zona 2B** (ai sensi dell'OPCM 3274/2003 e s.m.i. — Regione Lazio DGR 387/2009). Nota: alcuni comuni della provincia di Roma possono essere Zona 2A o Zona 3.
2. Verificare SEMPRE la classificazione sismica:
   - Sorgente primaria: PE (relazione strutturale)
   - Sorgente secondaria: preesistenza
   - Sorgente di fallback: database classificazione sismica Protezione Civile / Regione Lazio
3. Aggiungere `zona_sismica` al dizionario `SITO` — obbligatorio
4. Cercare e sostituire nel template il valore sample (identificarlo in Fase 0-TER)

---

## L21 — Sezione "Descrizione dell'area di intervento" non aggiornata nella RT

**Sintomo:** la sezione 2 della RT ("Descrizione dell'area di intervento") contiene un testo generico/sample che non descrive l'area reale del sito.

**Causa:** il template contiene una descrizione d'area tipo per la zona campione. Se il sito è in un'altra zona, la descrizione deve essere personalizzata.

**Regola canonica:**
1. La descrizione dell'area **deve essere specifica** per il sito in esame. Deve menzionare:
   - Il quartiere/zona reale (es. "quartiere Tuscolano", "zona Tiburtina")
   - Il contesto edilizio reale (es. "edifici residenziali a 5-7 piani degli anni '60–'70")
   - Il tipo di infrastruttura (es. "palo/traliccio Raw Land in area recintata" oppure "copertura edificio Roof Top")
   - Eventuali elementi rilevanti (vicinanza strade importanti, ferrovia, parchi, ecc.)
2. Fonti per la descrizione:
   - Google Maps / Street View (ricerca web in Fase 0)
   - PE (progetto architettonico) — la relazione descrive il contesto
   - Preesistenza — la RT precedente aveva già una descrizione
   - Foto del sito fornite dall'utente
3. NON lasciare mai la descrizione sample del template. Se non si hanno informazioni → scrivere una descrizione basata sull'indirizzo + zona PRG e segnare `⚠️ descrizione da verificare in sopralluogo`

---

## L22 — Tabella parabole non compilata nella RT

**Sintomo:** la tabella delle parabole/antenne paraboliche nella RT è vuota o contiene i dati sample.

**Causa:** la tabella parabole richiede dati specifici dalla Scheda Radio o dal PE — diametro, azimuth, tilt, frequenza, altezza centro antenna. Se non vengono estratti e inseriti, la tabella rimane vuota.

**Regola canonica:**
1. La tabella parabole va compilata con i dati dalla **Scheda Radio** (sezione parabole/ponti radio) o dal **FILETX.xlsx** (sezione ponti radio/microwave)
2. Se il sito NON ha parabole → la tabella va comunque gestita:
   - Se il template ha una tabella vuota con intestazioni → lasciarla con una nota "Nessuna parabola prevista nell'intervento"
   - Se il template ha righe sample → eliminare le righe sample
3. Se il sito HA parabole → compilare TUTTE le righe con: diametro, frequenza, azimuth, tilt, altezza centro fase
4. Aggiungere alla Fase 0-QUATER: "Il sito ha parabole/ponti radio? Se sì, fornire i dati (o la scheda radio con la sezione parabole)"
5. Questo dato NON è derivabile dalla preesistenza (le parabole cambiano con gli interventi) — serve sempre la Scheda Radio aggiornata

---

## Quando incontri un problema NON previsto in questo file

1. **Fermati.** Non tentare di indovinare.
2. Chiedi all'utente con una **domanda diretta**: quale valore usare, quale ramo scegliere.
3. Dopo aver risolto, **aggiungi** una nuova voce (L-next) così la prossima sessione non ripete l'errore.
