# Script Python per generazione DOCX

## Istruzioni per Claude

Per generare il report, usa questo script Python come base. Adattalo con i dati raccolti dall'utente.

**Prerequisiti:** `pip install python-docx --break-system-packages -q`

---

## Script base (da adattare)

```python
from docx import Document
from docx.shared import Pt, RGBColor, Inches, Cm
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.enum.style import WD_STYLE_TYPE
import datetime

def crea_report_car(dati):
    """
    dati = dict con chiavi:
      - tipo_struttura: "muratura" | "cemento_armato"
      - codice_sito: es. "RM00177_015"
      - nome_sito: es. "Mandrione"
      - indirizzo: es. "Via Ciro da Urbino, 37"
      - comune: es. "Roma"
      - provincia: es. "RM"
      - data_report: es. "2025-09-16"
      - progettista: "luca_rossi" | "jessica_romanelli"
      - cliente: "Circet" | "Site" | "Sirti"
      - destinazione_uso: es. "Condominio residenziale"
      - descrizione_edificio: testo libero
      - strumentazione: lista, es. ["Termocamera Flir E8", "Laser Scanner GEOSLAM", ...]
      - fasi: lista delle fasi eseguite
      - testo_fasi: dict {nome_fase: testo_risultati}
      - pilastri: lista di dict (solo per C.A.) [{id, dim_a, dim_b, metodo, note}]
      - conclusioni: testo libero
    """
    doc = Document()

    # ---- Impostazioni pagina ----
    section = doc.sections[0]
    section.page_width = Cm(21)
    section.page_height = Cm(29.7)
    section.left_margin = Cm(2.5)
    section.right_margin = Cm(2.5)
    section.top_margin = Cm(2.5)
    section.bottom_margin = Cm(2.5)

    # ---- COPERTINA ----
    # Titolo principale
    titolo = doc.add_paragraph()
    titolo.alignment = WD_ALIGN_PARAGRAPH.CENTER
    run = titolo.add_run("REPORT STRUTTURALE")
    run.bold = True
    run.font.size = Pt(20)

    doc.add_paragraph()  # spazio

    # Sottotitolo
    sottotitolo = doc.add_paragraph()
    sottotitolo.alignment = WD_ALIGN_PARAGRAPH.CENTER
    run2 = sottotitolo.add_run(
        "Progetto di realizzazione di impianto tecnologico di radiotelecomunicazioni\n"
        "per telefonia cellulare a servizio della rete del Gestore Iliad Italia S.p.A."
    )
    run2.font.size = Pt(11)

    doc.add_paragraph()  # spazio

    # Tabella dati sito (copertina)
    table = doc.add_table(rows=6, cols=2)
    table.style = 'Table Grid'
    campi_copertina = [
        ("Codice Sito", dati['codice_sito']),
        ("Nome Sito", dati['nome_sito']),
        ("Indirizzo", dati['indirizzo']),
        ("Comune", dati['comune']),
        ("Provincia", dati['provincia']),
        ("Data documento", dati['data_report']),
    ]
    for i, (campo, valore) in enumerate(campi_copertina):
        table.rows[i].cells[0].text = campo
        table.rows[i].cells[1].text = valore
        table.rows[i].cells[0].paragraphs[0].runs[0].bold = True

    doc.add_page_break()

    # ---- SEZIONE 1: Informazioni di Base ----
    doc.add_heading("Informazioni di Base", level=1)
    doc.add_paragraph(f"Nome del Sito: {dati['codice_sito']} - {dati['nome_sito']}")
    doc.add_paragraph(f"Ubicazione: {dati['indirizzo']} - {dati['comune']} ({dati['provincia']})")
    doc.add_paragraph(f"Data Report: {dati['data_report']}")

    # Testo progettista
    testi_progettisti = {
        "luca_rossi": (
            "Il sottoscritto Ing. Luca Rossi, iscritto all'Ordine degli Ingegneri della provincia "
            "di Perugia al num. A2212 e domiciliato per la carica presso K2A Srls in Via Alessandro "
            "Manzoni n°84 Perugia (PG), in qualità di tecnico incaricato dalla Società Iliad S.p.A., "
            "dopo aver preso visione dei luoghi relaziona quanto segue."
        ),
        "jessica_romanelli": (
            "La sottoscritta Ing. Jessica Romanelli, iscritta all'Ordine degli Ingegneri della "
            "provincia di Perugia al num. A3537 e domiciliata per la carica presso K2A Srls in Via "
            "Alessandro Manzoni n°84 Perugia (PG), in qualità di tecnico incaricato dalla Società "
            "Iliad S.p.A., dopo aver preso visione dei luoghi relaziona quanto segue."
        ),
    }
    doc.add_paragraph(testi_progettisti[dati['progettista']])

    # ---- SEZIONE 2: Situazione Attuale ----
    doc.add_heading("Situazione Attuale", level=1)
    doc.add_heading("Descrizione", level=3)
    doc.add_paragraph(dati['descrizione_edificio'])

    # ---- SEZIONE 3: Modalità caratterizzazione ----
    doc.add_heading("Modalità di esecuzione della caratterizzazione", level=1)
    doc.add_paragraph("L'attività di caratterizzazione è stata svolta nelle seguenti fasi:")
    for fase in dati['fasi']:
        p = doc.add_paragraph(style='List Bullet')
        p.add_run(fase)

    # Dettaglio fasi
    for nome_fase, testo_fase in dati.get('testo_fasi', {}).items():
        doc.add_heading(nome_fase, level=2)
        doc.add_paragraph(testo_fase)
        # Segnaposto foto
        doc.add_paragraph(f"[Foto {nome_fase} — da inserire]").italic = True

    # ---- SEZIONE PILASTRI (solo C.A.) ----
    if dati['tipo_struttura'] == 'cemento_armato' and dati.get('pilastri'):
        doc.add_heading("Pilastri Rilevati", level=1)
        for i, pilastro in enumerate(dati['pilastri'], start=1):
            pid = pilastro.get('id', f'P{i}')
            dim_a = pilastro.get('dim_a', 'N.D.')
            dim_b = pilastro.get('dim_b', 'N.D.')
            dim_str = f"{dim_a}x{dim_b}" if dim_a != 'N.D.' else 'N.D.'
            doc.add_heading(f"Pilastro: {pid} (Dim: {dim_str})", level=2)

            if dim_a == 'N.D.':
                doc.add_paragraph(
                    f"Non è stato possibile rilevare le dimensioni del pilastro {pid} in quanto "
                    f"{pilastro.get('note', 'non accessibile durante il sopralluogo')}."
                )
            else:
                metodo = pilastro.get('metodo', 'rilievo laser scanner')
                doc.add_paragraph(
                    f"Le dimensioni del pilastro {pid} sono state estrapolate tramite {metodo}. "
                    f"{pilastro.get('note', '')}"
                )
            doc.add_paragraph(f"[Foto Pilastro {pid} — da inserire]").italic = True

    # ---- SEZIONE Strumentazione ----
    doc.add_heading("Strumentazione utilizzata", level=1)
    for strumento in dati['strumentazione']:
        p = doc.add_paragraph(style='List Bullet')
        p.add_run(strumento)

    # ---- SEZIONE Conclusioni ----
    doc.add_heading("Conclusioni", level=1)
    doc.add_paragraph(dati['conclusioni'])

    # Firma
    doc.add_paragraph()
    doc.add_paragraph()
    firma_testi = {
        "luca_rossi": "Ing. Luca Rossi\nOrdine Ingegneri Perugia n° A2212\nK2A Srls",
        "jessica_romanelli": "Ing. Jessica Romanelli\nOrdine Ingegneri Perugia n° A3537\nK2A Srls",
    }
    p_firma = doc.add_paragraph(firma_testi[dati['progettista']])
    p_firma.alignment = WD_ALIGN_PARAGRAPH.RIGHT

    return doc


# ---- ESEMPIO DI UTILIZZO ----
if __name__ == "__main__":
    dati_esempio = {
        "tipo_struttura": "cemento_armato",
        "codice_sito": "RM00177_015",
        "nome_sito": "Mandrione",
        "indirizzo": "Via Ciro da Urbino, 37",
        "comune": "Roma",
        "provincia": "RM",
        "data_report": "2025-09-16",
        "progettista": "luca_rossi",
        "cliente": "Circet",
        "destinazione_uso": "Condominio residenziale",
        "descrizione_edificio": (
            "L'edificio oggetto del Rilievo è situato in via Ciro da Urbino 37. "
            "L'edificio ha una struttura portante intelaiata di Cemento Armato "
            "costituito da travi e pilastri."
        ),
        "strumentazione": [
            "Termocamera Flir E8",
            "DISTO D510",
            "Fotocamera 360° Insta360 X",
            "Pacometro",
            "Laser Scanner GEOSLAM",
        ],
        "fasi": [
            "Verifica visiva dei luoghi e identificazione delle strutture portanti",
            "Rilievo della pianta dei luoghi tramite Laser Scanner",
            "Identificazione dei componenti strutturali non visibili tramite Termocamera",
            "Verifica Pacometrica degli elementi identificati",
            "Verifica tramite prova semi-distruttiva della consistenza dell'elemento strutturale",
        ],
        "testo_fasi": {
            "Verifica visiva": "In fase preliminare, è stata condotta una verifica visiva...",
            "Laser Scanner": "Il rilievo tridimensionale condotto mediante Laser Scanner...",
            "Termocamera": "L'indagine termografica è stata condotta per l'identificazione...",
            "Pacometro": "A seguito dell'individuazione preliminare di elementi potenzialmente strutturali...",
            "Saggi semi-distruttivi": "A integrazione delle verifiche preliminari...",
        },
        "pilastri": [
            {"id": "P1", "dim_a": "25", "dim_b": "25", "metodo": "rilievo laser scanner", "note": ""},
            {"id": "P2", "dim_a": "25", "dim_b": "25", "metodo": "rilievo laser scanner", "note": ""},
            {"id": "P3", "dim_a": "N.D.", "dim_b": "N.D.", "metodo": "", "note": "Non accessibile"},
        ],
        "conclusioni": "In conclusione l'idea progettuale è quella di realizzare un'infrastruttura distribuita...",
    }

    doc = crea_report_car(dati_esempio)
    output_path = "/sessions/serene-zen-johnson/mnt/REPORT CARATTERIZZIONE/PILASTRI/RM00177_015_REPORT_CAR.docx"
    doc.save(output_path)
    print(f"Report salvato: {output_path}")
```

---

## Note per Claude durante la generazione

1. **Installa la libreria** prima di tutto: `pip install python-docx --break-system-packages -q`
2. **Adatta lo script** con i dati reali raccolti dall'utente (non usare l'esempio sopra direttamente)
3. **Percorso di salvataggio:**
   - Muratura → `/sessions/serene-zen-johnson/mnt/REPORT CARATTERIZZIONE/MURATURA/[CODICE]_REPORT_CAR.docx`
   - C.A. → `/sessions/serene-zen-johnson/mnt/REPORT CARATTERIZZIONE/PILASTRI/[CODICE]_REPORT_CAR.docx`
4. **Nome file:** sempre nel formato `[CODICE_SITO]_REPORT_CAR.docx` (es. `FI50135_006_REPORT_CAR.docx`)
5. **Dopo il salvataggio**, presenta il link `computer://` al file
