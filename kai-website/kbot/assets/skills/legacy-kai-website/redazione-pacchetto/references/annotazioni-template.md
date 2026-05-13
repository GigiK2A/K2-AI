# Annotazioni nei Template — Classificazione Canonica

I template `.docx` iliad contengono annotazioni rosse/commentative destinate al compilatore. Ogni annotazione va classificata in due categorie e gestita con strategie diverse:

- **INLINE**: embedded in un paragrafo di testo valido → va **sostituita** con stringa vuota (o con il valore corretto)
- **STANDALONE**: costituisce l'intero paragrafo → va **cancellata** come intero paragrafo

**REGOLA D'ORO**: prima di mettere un marker in `annotation_markers`, APRIRE il template ed essere CERTI che l'annotazione NON sia inline in un paragrafo che deve restare. Se c'è il minimo dubbio, è sicuro metterlo in `replacements`.

---

## Catalogo Annotazioni — SCIA (doc 1)

| Annotazione | Tipo | Documento | Gestione |
|-------------|------|-----------|----------|
| `"; VERIFICARE CHE LA PROCURA SIA SEMPRE QUELLA DEL 04/2024"` | INLINE | SCIA | `replacements`: `""` |
| `", VERIFICARE CHE LA PROCURA SIA SEMPRE QUELLA DEL 04/2024"` | INLINE | Delega | `replacements`: `""` |
| `". VERIFICARE CHE LA PROCURA SIA SEMPRE QUELLA DEL 04/2024"` | INLINE | Atto d'obbligo | `replacements`: `"."` |
| `"; SOLO SE INFRASTRUTTURA DI PROPRIETA CELLNEX/PTI/INWIT ALTRIMENTI ELIMINARE"` | INLINE | SCIA | `replacements`: `""` (se sito Cellnex/PTI/INWIT; altrimenti cancellare il paragrafo) |
| `"; SOLO SE COMUNE DI ROMA ALTRIMENTI ELIMINARE"` | INLINE | SCIA | `replacements`: `""` (se Roma; altrimenti cancellare) |
| `"; SOLO SE PRESENTE 5G ALTRIMENTI ELIMINARE"` | INLINE | SCIA | `replacements`: `""` (se presente 5G; altrimenti cancellare) |
| `"NULLA OSTA DELLA PROPRIETA (SOLO SE INFRASTRUTTURA DI PROPRIETA CELLNEX/PTI/INWIT)"` | STANDALONE | SCIA allegati | Se sito Cellnex → mantenere il testo "Nulla Osta della proprietà"; altrimenti cancellare l'intero paragrafo |

---

## Catalogo Annotazioni — RT (doc 4)

| Annotazione | Tipo | Gestione |
|-------------|------|----------|
| `"CITARE TUTTI I VINCOLI PRESENTI E SPECIFICARE SE ININFLUNETI AI FINI DELL'INTERVENTO"` | STANDALONE | `annotation_markers`: cancellare |
| `"CITARE SOLO ULTIMA PREESISTENZA ILIAD – NO IDENTIFICATIVI MESSAGGIO PEC, SOLO PROTOCOLLI"` | STANDALONE | `annotation_markers`: cancellare |
| `"SE PRESENTI VINCOLI CITARE L'ULTIMO VINCOLO OTTENUTO IN TERMINI CRONOLOGICI"` | STANDALONE | `annotation_markers`: cancellare |
| `"SE ANCORA PRESENTE VINCOLO VAP IN BASE ALL"` | STANDALONE | `annotation_markers`: cancellare (sito senza VAP) |
| `" – SE PRESENTE NULLA OSTA VAP TRA LE PREESISTENZE"` | INLINE | `replacements`: `""` |
| `" O INFRASTRUTTURA SE PALO"` | INLINE | `replacements`: `""` (se Roof Top) / `"infrastruttura"` (se Raw Land) |
| `" VERIFICARE PRESENZA DI RRH O RFM E LORO POSIZIONE"` | INLINE | `replacements`: `""` |

---

## Catalogo Annotazioni — ASSEVERAZIONI (doc 6)

| Annotazione | Tipo | Gestione |
|-------------|------|----------|
| `"INSERIRE PRECISAZIONI RELAZIONE TECNICA"` | INLINE (rosso) | `replacements`: testo vero della relazione precisazioni (modifica radioelettrica + preesistenze + eventuale esclusione VAP) |
| `"CITARE TUTTI I VINCOLI PRESENTI"` | STANDALONE | `annotation_markers`: cancellare |
| Tutte le altre annotazioni identiche a RT | vedi RT | vedi RT |

---

## Catalogo Annotazioni — Atto d'obbligo (doc 10)

| Annotazione | Tipo | Gestione |
|-------------|------|----------|
| `". VERIFICARE CHE LA PROCURA SIA SEMPRE QUELLA DEL 04/2024"` | INLINE | `replacements`: `"."` |
| `"SOLO SE INFRASTRUTTURA CELLNEX/PTI/INWIT"` (in eventuali commi) | INLINE | caso per caso |

---

## Catalogo Annotazioni — Delega (doc 2)

| Annotazione | Tipo | Gestione |
|-------------|------|----------|
| `", VERIFICARE CHE LA PROCURA SIA SEMPRE QUELLA DEL 04/2024"` | INLINE | `replacements`: `""` |

---

## Catalogo Annotazioni — Impegno ARPA (doc 8) / Dich. Sostitutiva ALPHA24 (doc 9)

Generalmente **nessuna annotazione rossa**. Verificare per ogni sessione perché i template possono cambiare.

---

## Procedura Standard di Identificazione

Prima di ogni pacchetto, lanciare questo script diagnostico per trovare TUTTE le annotazioni rosse nei template caricati dall'utente:

```python
from docx import Document
from docx.oxml.ns import qn

def trova_annotazioni_rosse(path):
    doc = Document(path)
    result = []
    W_R = qn('w:r')
    W_COLOR = qn('w:color')
    for p in doc.element.body.iter(qn('w:p')):
        for r in p.iter(W_R):
            rpr = r.find(qn('w:rPr'))
            if rpr is None:
                continue
            col = rpr.find(W_COLOR)
            if col is not None and col.get(qn('w:val'), '').upper() in ('FF0000','C00000','CC0000'):
                text = ''.join(t.text or '' for t in r.iter(qn('w:t')))
                if text.strip():
                    result.append(text)
    return result

for name, path in [
    ("SCIA", "1...docx"),
    ("Delega", "2...docx"),
    ("RT", "4...docx"),
    ("ASSEV", "6...docx"),
    ("Atto", "10...docx"),
]:
    print(f"=== {name} ===")
    for a in trova_annotazioni_rosse(path):
        print(" -", repr(a[:120]))
```

Questo script va eseguito SEMPRE come prima cosa quando l'utente carica i template, così so quali annotazioni gestire in quella specifica revisione dei template.
