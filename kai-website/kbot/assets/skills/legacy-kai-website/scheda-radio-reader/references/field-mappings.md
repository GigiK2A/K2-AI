# Field Mappings — Scheda Radio iliad/TDC

Riferimento completo con pattern regex, varianti di layout e casi edge per l'estrazione campi.

## Pattern Regex Python

```python
import re

def extract_fields(text):
    """Estrae tutti i campi rilevanti da testo PDF Scheda Radio iliad/TDC."""
    results = {}

    # --- CODICE SITO ---
    # Pattern principale: 2 lettere + 5 cifre + _ + 3 cifre
    m = re.search(r'\b([A-Z]{2}\d{5}[_\s]?\d{3})\b', text)
    if m:
        results["codice_sito"] = m.group(1).replace(" ", "_")

    # --- NOME SITO ---
    # Cerca dopo etichette comuni
    m = re.search(
        r'(?:Nome\s+[Ss]ito|Site\s+Name|Nome\s+Localit[àa])[:\s]+([^\n\r]+)',
        text
    )
    if m:
        results["nome_sito"] = m.group(1).strip()
    else:
        # Fallback: riga dopo il codice sito
        codice = results.get("codice_sito", "")
        if codice:
            m = re.search(
                rf'{re.escape(codice)}[^\n]*\n([^\n]+)',
                text
            )
            if m:
                results["nome_sito"] = m.group(1).strip()

    # --- LATITUDINE ---
    m = re.search(
        r'(?:Lat(?:itudine)?|LAT|φ)[\.:\s°]*([34][0-9][.,]\d{4,8})',
        text, re.IGNORECASE
    )
    if m:
        results["latitudine"] = m.group(1).replace(",", ".")
    else:
        # DMS: 41°49'24.44"N
        m = re.search(r'(\d{1,2})°\s*(\d{1,2})[\'′]\s*(\d{1,2}(?:[.,]\d+)?)[\"″]\s*N', text)
        if m:
            d, mi, s = float(m.group(1)), float(m.group(2)), float(m.group(3).replace(",", "."))
            results["latitudine"] = f"{d + mi/60 + s/3600:.6f}"

    # --- LONGITUDINE ---
    m = re.search(
        r'(?:Lon(?:g(?:itudine)?)?|LON|λ)[\.:\s°]*([6-9]|1[0-8])[.,](\d{4,8})',
        text, re.IGNORECASE
    )
    if m:
        results["longitudine"] = m.group(1) + "." + m.group(2)
    else:
        # Decimale semplice
        m = re.search(
            r'(?:Lon(?:g(?:itudine)?)?|LON)[\.:\s°]*(\d{1,2}[.,]\d{4,8})',
            text, re.IGNORECASE
        )
        if m:
            results["longitudine"] = m.group(1).replace(",", ".")
        else:
            # DMS: 12°20'44.04"E
            m = re.search(r'(\d{1,2})°\s*(\d{1,2})[\'′]\s*(\d{1,2}(?:[.,]\d+)?)[\"″]\s*E', text)
            if m:
                d, mi, s = float(m.group(1)), float(m.group(2)), float(m.group(3).replace(",", "."))
                results["longitudine"] = f"{d + mi/60 + s/3600:.6f}"

    # --- PROVINCIA (sigla 2 lettere) ---
    m = re.search(
        r'(?:Provincia|Prov\.?)[:\s]+([A-Z]{2})\b',
        text, re.IGNORECASE
    )
    if m:
        results["provincia"] = m.group(1).upper()
    else:
        # Cerca tra parentesi dopo il comune
        m = re.search(r'\(([A-Z]{2})\)', text)
        if m:
            results["provincia"] = m.group(1).upper()

    # --- COMUNE ---
    m = re.search(
        r'(?:Comune|Municipality|City)[:\s]+([A-Za-zÀ-ú\s\']+?)(?:\n|\r|\(|,|$)',
        text, re.IGNORECASE
    )
    if m:
        results["comune"] = m.group(1).strip()

    # --- DATA SOPRALLUOGO ---
    # Formato gg/mm/aaaa o varianti
    m = re.search(
        r'(?:Data\s+(?:sopralluogo|visita|rilievo|del\s+sopralluogo)|Del)[:\s]+(\d{1,2}[/\-\.]\d{1,2}[/\-\.]\d{4})',
        text, re.IGNORECASE
    )
    if m:
        data = m.group(1).replace("-", "/").replace(".", "/")
        results["data"] = data
    else:
        # Data generica nel documento
        m = re.search(r'\b(\d{1,2})[/\-\.](\d{1,2})[/\-\.](\d{4})\b', text)
        if m:
            results["data"] = f"{m.group(1).zfill(2)}/{m.group(2).zfill(2)}/{m.group(3)}"

    # --- INDIRIZZO ---
    m = re.search(
        r'(?:Indirizzo|Via\b|Viale\b|Piazza\b|P\.za\b|Strada\b|Loc\.?\b|Localit[àa]\b)[:\s]*([^\n\r]{5,80})',
        text, re.IGNORECASE
    )
    if m:
        results["indirizzo"] = m.group(0).strip() if "Via" in m.group(0)[:5] else m.group(1).strip()

    # --- PRODUTTORE ANTENNA ---
    produttori_noti = ["Huawei", "Nokia", "Ericsson", "Kathrein", "CommScope", "RFS", "Andrew",
                       "Amphenol", "Cobham", "Rosenberger", "Powerwave"]
    m = re.search(
        r'(?:Produttore|Fornitore|Manufacturer|Vendor|Brand)[:\s]+([^\n\r]{2,40})',
        text, re.IGNORECASE
    )
    if m:
        val = m.group(1).strip()
        # Verifica se contiene un produttore noto
        for prod in produttori_noti:
            if prod.lower() in val.lower():
                results["produttore"] = prod
                break
        else:
            results["produttore"] = val.split()[0]  # Prima parola
    else:
        # Cerca direttamente il nome del produttore nel testo
        for prod in produttori_noti:
            if prod.lower() in text.lower():
                results["produttore"] = prod
                break

    # --- MODELLO ANTENNA ---
    m = re.search(
        r'(?:Modello|Tipo\s+[Aa]ntenna|Model|Part\s+[Nn]umber|P/N)[:\s]+([A-Z0-9\-\_\/]{4,30})',
        text, re.IGNORECASE
    )
    if m:
        results["modello"] = m.group(1).strip()

    # --- BASE ANTENNA (m) ---
    m = re.search(
        r'(?:Base\s+[Aa]ntenna|Base\s+ant\.?|H\s+base|Altezza\s+base|Quota\s+base)[:\s]+(\d{1,3}(?:[.,]\d{1,2})?)\s*m?',
        text, re.IGNORECASE
    )
    if m:
        results["base_antenna"] = m.group(1).replace(",", ".")

    # --- ALTEZZA CENTRO ELETTRICO (m) ---
    m = re.search(
        r'(?:Centro\s+[Ee]lettrico|H\s+el\.?|ACE|Altezza\s+CE|Centro\s+[Rr]adiante|H\s+centro)[:\s]+(\d{1,3}(?:[.,]\d{1,2})?)\s*m?',
        text, re.IGNORECASE
    )
    if m:
        results["h_elettrico"] = m.group(1).replace(",", ".")

    return results
```

## Varianti di Layout Documentale

### Layout Tipo A — Tabella strutturata (più comune)

```
+------------------+------------------+
| Codice Sito:     | RM00126_003      |
+------------------+------------------+
| Nome Sito:       | Acilia-MSP       |
+------------------+------------------+
| Comune:          | Roma (RM)        |
+------------------+------------------+
| Indirizzo:       | Via Eschilo, 54  |
+------------------+------------------+
| Latitudine:      | 41.823456        |
| Longitudine:     | 12.345678        |
+------------------+------------------+
```

### Layout Tipo B — Testo libero con label

```
SCHEDA RADIO - SOPRALLUOGO
Data: 15/03/2025

Sito: RM00126_003
Nome: Acilia-Monti San Paolo

Indirizzo: Via Eschilo, 54 - Roma (RM)
Lat: 41.823456 Lon: 12.345678

ANTENNA
Produttore: Huawei  Modello: APXVAAA4X4D65R
Base Antenna: 24.5 m   H. Elettrico: 27.5 m
```

### Layout Tipo C — PDF con tabelle complesse (pdfplumber table extraction)

Per layout con tabelle complesse, usare l'estrazione tabelle di pdfplumber:

```python
import pdfplumber

with pdfplumber.open(pdf_path) as pdf:
    for page in pdf.pages:
        tables = page.extract_tables()
        for table in tables:
            for row in table:
                # row è una lista di celle
                if row and any(r for r in row):
                    print(row)
```

## Casi Edge

| Caso | Soluzione |
|------|-----------|
| PDF scansionato (solo immagine) | Usare OCR: `pip install pytesseract` |
| Coordinate in formato DMS | Convertire con formula: `D + M/60 + S/3600` |
| Più settori antenna (α/β/γ) | Usare i dati del settore α (primo) o quello specificato dall'utente |
| Data mancante | Usare la data di creazione del PDF (`pdf.metadata`) |
| Codice sito diverso (es. WIND, VODA) | Adattare regex: `[A-Z]{2,4}\d{4,6}[_\-]?\d{2,3}` |
| Province con accento (es. VB = Verbano) | Mappa di lookup sigle province italiane |

## Mappa Province Italiane (sigle)

```python
PROVINCE_IT = {
    "AG": "Agrigento", "AL": "Alessandria", "AN": "Ancona", "AO": "Aosta",
    "AR": "Arezzo", "AP": "Ascoli Piceno", "AT": "Asti", "AV": "Avellino",
    "BA": "Bari", "BT": "Barletta-Andria-Trani", "BL": "Belluno", "BN": "Benevento",
    "BG": "Bergamo", "BI": "Biella", "BO": "Bologna", "BZ": "Bolzano",
    "BS": "Brescia", "BR": "Brindisi", "CA": "Cagliari", "CL": "Caltanissetta",
    "CB": "Campobasso", "CE": "Caserta", "CT": "Catania", "CZ": "Catanzaro",
    "CH": "Chieti", "CO": "Como", "CS": "Cosenza", "CR": "Cremona",
    "KR": "Crotone", "CN": "Cuneo", "EN": "Enna", "FM": "Fermo",
    "FE": "Ferrara", "FI": "Firenze", "FG": "Foggia", "FC": "Forlì-Cesena",
    "FR": "Frosinone", "GE": "Genova", "GO": "Gorizia", "GR": "Grosseto",
    "IM": "Imperia", "IS": "Isernia", "AQ": "L'Aquila", "SP": "La Spezia",
    "LT": "Latina", "LE": "Lecce", "LC": "Lecco", "LI": "Livorno",
    "LO": "Lodi", "LU": "Lucca", "MC": "Macerata", "MN": "Mantova",
    "MS": "Massa-Carrara", "MT": "Matera", "ME": "Messina", "MI": "Milano",
    "MO": "Modena", "MB": "Monza e Brianza", "NA": "Napoli", "NO": "Novara",
    "NU": "Nuoro", "OR": "Oristano", "PD": "Padova", "PA": "Palermo",
    "PR": "Parma", "PV": "Pavia", "PG": "Perugia", "PU": "Pesaro e Urbino",
    "PE": "Pescara", "PC": "Piacenza", "PI": "Pisa", "PT": "Pistoia",
    "PN": "Pordenone", "PZ": "Potenza", "PO": "Prato", "RG": "Ragusa",
    "RA": "Ravenna", "RC": "Reggio Calabria", "RE": "Reggio Emilia",
    "RI": "Rieti", "RN": "Rimini", "RM": "Roma", "RO": "Rovigo",
    "SA": "Salerno", "SS": "Sassari", "SV": "Savona", "SI": "Siena",
    "SR": "Siracusa", "SO": "Sondrio", "SU": "Sud Sardegna", "TA": "Taranto",
    "TE": "Teramo", "TR": "Terni", "TO": "Torino", "TP": "Trapani",
    "TN": "Trento", "TV": "Treviso", "TS": "Trieste", "UD": "Udine",
    "VA": "Varese", "VE": "Venezia", "VB": "Verbano-Cusio-Ossola",
    "VC": "Vercelli", "VR": "Verona", "VV": "Vibo Valentia", "VI": "Vicenza",
    "VT": "Viterbo"
}
```
