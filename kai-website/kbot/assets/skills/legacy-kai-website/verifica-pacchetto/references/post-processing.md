# Post-Processing — Procedure Tecniche per la Pulizia Finale dei `.docx`

Dopo le sostituzioni di testo con `replace_in_doc` e le cancellazioni con `delete_paragraphs_by_markers`, restano alcune operazioni "di basso livello" che richiedono XML/zipfile. Questo file le cataloga in ordine di esecuzione.

**Ordine canonico per ogni `.docx` generato:**
1. `replace_in_doc` (sostituzioni di testo)
2. `delete_paragraphs_by_markers` (cancellazioni standalone)
3. Cancellazioni mirate di paragrafi dentro celle specifiche (aeroporti, VAP)
4. **Red Color Stripping** ← obbligatorio per RT e ASSEV
5. `doc.save(dst)`
6. **Sostituzione Foto Sito** via zipfile ← obbligatorio per RT
7. Verifica finale con `Document(dst)` e sanity-check

---

## 1. Red Color Stripping

Dopo aver sostituito annotazioni rosse, il testo di sostituzione eredita il colore rosso del run originale. Vanno ripuliti tutti i `<w:color>` rossi.

```python
from docx.oxml.ns import qn

def strip_red_color(doc):
    W_COLOR = qn('w:color')
    W_R = qn('w:r')
    W_RPR = qn('w:rPr')
    W_VAL = qn('w:val')
    red_values = {'FF0000', 'C00000', 'CC0000', 'EA2C2C'}

    for r in doc.element.body.iter(W_R):
        rpr = r.find(W_RPR)
        if rpr is None:
            continue
        col = rpr.find(W_COLOR)
        if col is not None:
            val = col.get(W_VAL, '').upper()
            if val in red_values:
                rpr.remove(col)

# Uso:
strip_red_color(doc)
doc.save(dst)
```

**Applicare SEMPRE a:** `edit_rt.py`, `edit_asseverazioni.py`.
**Opzionale ma consigliato per:** `edit_scia.py`, `edit_atto.py`.

---

## 2. Cancellazione Paragrafi in Celle Specifiche (Aeroporti)

Il metodo `delete_paragraphs_by_markers` opera sul body del documento. Per paragrafi dentro celle di tabella specifiche serve un'iterazione diretta sulla cella.

```python
def _remove_para(p):
    el = p._element
    parent = el.getparent()
    if parent is not None:
        parent.remove(el)

# RT: tabella T3 R0 C0 (labels) e C1 (valori)
t3 = doc.tables[3]
c0 = t3.rows[0].cells[0]
c1 = t3.rows[0].cells[1]

# Rimuovi labels Fiumicino + Urbe
labels_to_remove = [
    "Leonardo Da Vinci",         # Fiumicino
    "Carta degli ostacoli di Aeroporto Roma Urbe",  # Urbe
]
for p in list(c0.paragraphs):
    if any(m in p.text for m in labels_to_remove):
        _remove_para(p)

# Rimuovi i 2 valori corrispondenti
for p in list(c1.paragraphs):
    if "non è soggetta a limitazioni" in p.text:
        _remove_para(p)
```

**Per ASSEVERAZIONI** è la tabella `t1` invece di `t3`. Stesso schema.

**Adattare l'indice tabella** se il template cambia: lanciare una diagnostica preliminare per localizzare la tabella PRG/PTPR.

---

## 3. Rimozione VAP (se sito senza VAP)

```python
vap_markers = [
    "V.A.P. – ininfluente",
    "V.A.P. - ininfluente",
    "Dipartimento Ciclo dei Rifiuti",
]
# Nelle celle PRG/PTPR:
for cell in [c0, c1]:
    for p in list(cell.paragraphs):
        if any(m in p.text for m in vap_markers):
            _remove_para(p)

# Negli allegati SCIA (se il template li ha):
from docx_tools import delete_paragraphs_by_markers
delete_paragraphs_by_markers(doc, [
    "Parere favorevole del Dipartimento Ciclo dei Rifiuti",
])
```

---

## 4. Sostituzione Foto Sito (RT)

Il template RT incorpora 2 immagini sample in `word/media/image1.jpeg` e `word/media/image2.jpeg`. Vanno sostituite con la foto reale del sito dopo `doc.save(dst)`.

### Step 1 — Diagnostica: quali immagini sostituire?

```python
import zipfile
with zipfile.ZipFile(template_path) as z:
    for n in z.namelist():
        if n.startswith('word/media/'):
            print(n, z.getinfo(n).file_size)
```

Regola pratica:
- File `.jpeg` > 100KB → probabilmente foto sito (da sostituire)
- File < 20KB → icone/loghi (NON sostituire)
- File ~80KB → logo K2A o logo iliad (NON sostituire — **verificare aprendo il file**)

In caso di dubbio, estrarre il file e visionarlo prima di decidere.

### Step 2 — Sostituzione via zipfile

```python
import zipfile, os

def replace_docx_media(docx_path, mapping):
    """mapping: {'word/media/image1.jpeg': b'<bytes>', ...}"""
    tmp = docx_path + ".tmp"
    with zipfile.ZipFile(docx_path, "r") as zin:
        with zipfile.ZipFile(tmp, "w", zipfile.ZIP_DEFLATED) as zout:
            for item in zin.infolist():
                data = zin.read(item.filename)
                if item.filename in mapping:
                    data = mapping[item.filename]
                zout.writestr(item, data)
    os.replace(tmp, docx_path)

# Uso:
with open("/path/to/foto_reale.jpeg", "rb") as f:
    photo_bytes = f.read()

replace_docx_media(dst, {
    "word/media/image1.jpeg": photo_bytes,
    "word/media/image2.jpeg": photo_bytes,
})
```

### Step 3 — Verifica post-sostituzione

```python
import zipfile
with zipfile.ZipFile(dst) as z:
    for n in z.namelist():
        if n.startswith('word/media/'):
            print(n, z.getinfo(n).file_size)
```

Le dimensioni dei file `image1.jpeg` e `image2.jpeg` dovrebbero ora corrispondere a quella del file sorgente.

**ATTENZIONE**: la sostituzione byte-per-byte mantiene il nome del file ma il dimensionamento nell'XML (width/height) NON viene aggiornato. Se l'immagine reale ha un aspect ratio molto diverso, visualmente può risultare stirata. In quel caso serve approccio alternativo con python-docx + `add_picture`, ma si perde la formattazione del template.

---

## 5. Sanity-Check Finale

Dopo `doc.save(dst)` (e dopo sostituzione immagini), eseguire uno script di verifica che:

```python
from docx import Document
d = Document(dst)
full_text = '\n'.join(p.text for p in d.paragraphs)
for t in d.tables:
    for row in t.rows:
        for cell in row.cells:
            full_text += '\n' + cell.text

# Check no residual annotations
BAD_MARKERS = [
    "VERIFICARE CHE",
    "SOLO SE",
    "INSERIRE ",
    "CITARE ",
    "SE PRESENTE",
    "SE ANCORA PRESENTE",
    "DA VERIFICARE",
]
found = [m for m in BAD_MARKERS if m in full_text]
if found:
    print(f"⚠️  {dst}: annotations residue:", found)
else:
    print(f"✅ {dst}: no residual annotations")

# Check no sample preesistenze
SAMPLE_DATA = [
    "QF/2025/0126488",
    "19436.U del 20/03/2023",
    "NA/13029 del 12/06/2023",
    "24/09/2025",  # data sample
    "T4",  # PRG sample (possibile falso positivo — verificare contesto)
]
for s in SAMPLE_DATA:
    if s in full_text:
        print(f"⚠️  {dst}: sample data found:", s)

# Check Longari procura è presente (SCIA, Delega, Atto)
if "Longari" in dst.lower() or "scia" in dst.lower() or "delega" in dst.lower() or "atto" in dst.lower():
    assert "Longari" in full_text, f"❌ {dst}: Longari procura MISSING!"
```

**Questo check va eseguito automaticamente** come ultimo step di ogni `edit_*.py`.

---

## 6. Template Files Fissi (iliad e K2A)

Certi valori sono **invariabili** per tutti i pacchetti iliad e non vanno mai modificati:

- Ragione sociale: `Iliad Italia S.p.A.`
- Sede legale: `Via Benigno Crespi 19, 20159 Milano`
- CF/P.IVA: verificare in `dati-sito.md`
- Procuratore: `Andrea Longari` (procura del 10/04/2024)

Se un template riporta questi con errori → segnalare all'utente prima di modificare.
