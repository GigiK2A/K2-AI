---
name: baseline-deposito-gc-tlc
description: Sub-skill di VerifyBoost TLC. Verifica e documenta il deposito al Genio Civile per siti TLC in zona sismica ≥2 (obbligatorio art. 93 DPR 380/2001). Estrae automaticamente file .p7m firmati digitalmente (CAdES) anche con wrapping doppio/triplo. Riconosce sistema PORTOS Toscana, MUDE Lombardia, MOSE Lazio, SUE-DSI Sicilia e altri. Si attiva quando l'orchestratore richiede la verifica GC, oppure quando l'utente dice "controlla il deposito Genio Civile", "verifica pratica sismica", "leggi i fascicoli depositati". Gestisce classificazioni "minore rilevanza" art. 94-bis con set ridotto di fascicoli e "rilevante" con set completo.
---








<!-- LEGAL-EVIDENCE-BLOCK-V7 -->
## Tools Normattiva + Giurisprudenza (CCost + CGUE + CEDU + CdS/TAR + Cassazione) — verifica obbligatoria

Hai 5 toolkit locali + 1 lookup live per consulenza legale evidence-based:
- **Normattiva** — ~42.000 norme italiane (DB FTS5)
- **Corte Costituzionale** — 22.258 pronunce + 46.154 massime (1956→2026)
- **Corte di Giustizia UE + Tribunale UE** — ~38.000 cause (2005→2026)
- **Corte EDU (Strasburgo)** — 10.000 casi contro l'Italia (2001→2026), con traduzioni ufficiali Min. Giustizia
- **Giustizia Amministrativa** — Consiglio di Stato + TAR + CGARS (2024→2025, in espansione)
- **Cassazione (LIVE pubblica)** — SentenzeWeb italgiure, accesso pubblico zero-setup (~188k civ + ~236k pen, testo integrale)

### Workflow obbligatorio

**A. Norme italiane**
```bash
python3 ~/normattiva_ai/tools/cita.py "<es. D.Lgs 81/2008>"
python3 ~/normattiva_ai/tools/rag_normattiva.py "<query>" --materia urbanistica_edilizia --limit 5
```

**B. Corte Costituzionale**
```bash
python3 ~/giurisprudenza_ai/tools/cross_norma_sentenza.py "art. 32 Cost." --limit 10
python3 ~/giurisprudenza_ai/tools/rag_giurisprudenza.py "<query>" --anno-da 2018
python3 ~/giurisprudenza_ai/tools/cita_sentenza.py "Corte cost. N/AAAA"
```

**C. CGUE (diritto UE / GDPR / appalti / antitrust / privacy / dogana)**
```bash
python3 ~/cgue_ai/tools/cross_norma_cgue.py "art. 101 TFUE" --limit 10
python3 ~/cgue_ai/tools/cross_norma_cgue.py "Reg. UE 679/2016"        # GDPR
python3 ~/cgue_ai/tools/rag_cgue.py "<query>" --anno-da 2018
python3 ~/cgue_ai/tools/cita_cgue.py "C-16/05"
```

**D. CEDU (diritti fondamentali / equo processo art. 6 / detenzione art. 3 / proprietà P1-1 / vita privata art. 8)**
```bash
python3 ~/cedu_ai/tools/cross_articolo_cedu.py "art. 6" --solo-importanti --limit 10
python3 ~/cedu_ai/tools/rag_cedu.py "<query>" --anno-da 2015
python3 ~/cedu_ai/tools/cita_cedu.py "63386/16"      # numero di ricorso
```

**E. Giustizia Amministrativa — CdS/TAR (appalti, edilizia, accesso atti, SCIA, silenzio, espropri, PA)**
```bash
python3 ~/gad_ai/tools/cross_norma_gad.py "D.Lgs 36/2023" --limit 10   # appalti
python3 ~/gad_ai/tools/cross_norma_gad.py "Legge 241/1990"             # procedimento
python3 ~/gad_ai/tools/rag_gad.py "<query>" --sede cds --anno-da 2024
```

**F. Cassazione (LIVE pubblica — civile/penale, legittimità) — zero setup**
```bash
# Verifica/recupera un precedente di Cassazione (SentenzeWeb pubblico, nessun login)
python3 ~/cassazione_ai/tools/cassazione_lookup.py --cit "Cass. civ. 12345/2023"
python3 ~/cassazione_ai/tools/cassazione_lookup.py --q "licenziamento giusta causa" --sezione civ --rows 5
python3 ~/cassazione_ai/tools/cassazione_lookup.py --cit "Cass. civ. 12345/2023" --full   # testo integrale
python3 ~/cassazione_ai/tools/check_cassazione.py --file <output.md>                        # verifica citazioni
```
Copre la finestra pubblica (~ultimi 5 anni + storico parziale). Se una citazione MANCA può essere fuori finestra; dillo, non inventare la massima.

**G. Verifica finale (prima del deliverable, su ogni file MD prodotto)**
```bash
python3 ~/normattiva_ai/tools/check_citazioni.py --file <output.md> --strict
python3 ~/giurisprudenza_ai/tools/check_sentenze.py --file <output.md> --strict
python3 ~/cgue_ai/tools/check_cgue.py --file <output.md> --strict
python3 ~/cedu_ai/tools/check_cedu.py --file <output.md> --strict
python3 ~/gad_ai/tools/check_gad.py --file <output.md> --strict
```

Knowledge pack norme: `~/normattiva_ai/knowledge_packs/urbanistica_edilizia/`

### ⚠️ Disclaimer obbligatorio (chiusura output)
> *Il presente documento ha finalità informative e di ricerca giuridica. **Non costituisce parere legale** né si sostituisce alla consulenza di un avvocato abilitato. Le citazioni normative e giurisprudenziali (italiane, UE, CEDU, amministrative, di legittimità) sono verificate sulle fonti ma l'utente è tenuto a verificarne il testo vigente sulle fonti ufficiali (normattiva.it, cortecostituzionale.it, eur-lex.europa.eu, hudoc.echr.coe.it, giustizia-amministrativa.it, italgiure.giustizia.it) prima di qualsiasi uso operativo. Il DB CEDU copre solo casi con Italia convenuta; CdS/TAR copre 2024-2025 (in espansione); la Cassazione è consultata live su SentenzeWeb pubblico (finestra ~5 anni + storico parziale).*

Se una norma/sentenza non risulta nei DB o nel lookup live: dillo, non inventare. Cause possibili: (a) non esiste, (b) abrogata, (c) non scaricata/sessione assente, (d) fonte non ancora coperta.
<!-- /LEGAL-EVIDENCE-BLOCK-V7 -->


# Baseline deposito Genio Civile TLC

Verifica completezza e regolarità del deposito al Genio Civile per siti TLC in zona sismica.

## Trigger di attivazione

- Chiamata dall'orchestratore VerifyBoost TLC (sempre se zona sismica ≥2)
- "Verifica deposito Genio Civile sito {codice}"
- "Controlla pratica sismica {codice}"
- "Leggi i fascicoli depositati"

## Regola hard-coded di attivazione obbligatoria

Se il sito ricade in **zona sismica 1, 2 o 3** (intero territorio Toscana, Liguria, Emilia-Romagna, gran parte Sud Italia), il deposito è obbligatorio art. 93 DPR 380/2001 + norma regionale.

**Mai assumere "non applicabile" su base tipologia (rooftop ≠ esenzione).** Anche siti rooftop con interventi "di minore rilevanza" art. 94-bis devono essere depositati - cambia solo il set di fascicoli richiesti.

## Pipeline operativa

### 1. Localizzazione del pacchetto deposito

Cerca nella cartella sito (passata da `discovery-cartella-sito-tlc`) file con pattern:

```bash
find <cartella_sito> -iname "*Deposito GC*" -o -iname "*PORTOS*" -o -iname "*Sismica*" -o -iname "*Vidimazione*"
```

Tipicamente troverai un archivio `.7z` da estrarre.

### 2. Estrazione p7m con wrapping multipli

Il pacchetto contiene tipicamente:
- 1 PDF protocollato (Avviso di Vidimazione)
- 1 ZIP "copiaConforme" che a sua volta contiene:
  - cartella ASSEVERAZIONI con 2-3 .pdf/.p7m
  - cartella AVVISI con vidimazione
  - 1 ZIP con fascicoli A0/A1/A2/.../A98 in formato .p7m doppio o triplo
- 2 ricevute IRIS (sistema regionale pagamenti)

Per estrarre i PDF dai .p7m firmati CAdES, usa **asn1crypto** (NON usare `openssl smime -verify` con `-noverify` perché spesso produce PDF corrotti):

```python
from asn1crypto import cms

def extract_pdf_from_p7m(path):
    with open(path, 'rb') as f:
        data = f.read()
    while True:
        try:
            ci = cms.ContentInfo.load(data)
            if ci['content_type'].native == 'signed_data':
                payload = ci['content']['encap_content_info']['content'].native
                if payload is None:
                    return None
                data = payload
                if data[:4] == b'%PDF' or data[:2] != b'0\x80' and data[0] != 0x30:
                    break
            else:
                break
        except Exception:
            break
    return data
```

Dettaglio completo in `references/estrazione-p7m-cades.md`.

### 3. Lettura Avviso di Vidimazione (documento chiave)

Il file `Avviso di Vidimazione.pdf` contiene:
- Numero progetto (es. 122597)
- Numero protocollo (es. AOOGRT/SISMICA/20220095422)
- Data vidimazione
- Norma di riferimento citata (art. 93 DPR 380/2001 + norma regionale)
- **Classificazione intervento** (di minore rilevanza / rilevante / non rilevante ai sensi art. 94-bis comma 1 DPR 380/2001)
- Lista completa dei fascicoli depositati con SHA256 di ognuno
- Sistema telematico utilizzato (PORTOS / MUDE / MOSE / SUE-DSI / etc.)
- Direttore Lavori nominato

### 4. Verifica completezza fascicoli per regione

Confronta i fascicoli depositati con `references/fascicoli-gc-per-regione.md`. Schema standard:

**Toscana (PORTOS) - intervento di minore rilevanza:**
- A0 - Schema Grafico Calcolo Contributi (anche valutazione forfettaria)
- A1 - Inquadramento generale
- A2 - Progetto architettonico
- A3 - Relazione Tecnica Generale
- A4 - Relazione sui Materiali
- A7-A8-A9 - Allegati di calcolo (relazione di calcolo strutturale può essere qui)
- A10 - Particolari Esecutivi
- A13 - Piano di Manutenzione
- A98 - Procura di invio (se delegato)

**Toscana (PORTOS) - intervento rilevante:**
Aggiunge anche A5 (relazione di calcolo strutturale dedicata), A6 (relazione geotecnica), A11 (piano controllo qualità), A12 (relazione geologica).

Vedi reference per Lombardia (MUDE), Lazio (MOSE), Sicilia (SUE-DSI), Veneto, Campania.

### 5. Verifica anomalie note

Pattern ricorrenti da rilevare:

**Pattern A - Triplicazione caricamento:** Spesso A07/A08/A09 sono lo **stesso file** caricato 3 volte sotto etichetta sbagliata "Relazione sui Materiali" mentre il contenuto è la Verifica Statica unica. Verifica con SHA256 confronto:
```python
import hashlib
md5_a07 = hashlib.md5(open(path_a07,'rb').read()).hexdigest()
md5_a08 = hashlib.md5(open(path_a08,'rb').read()).hexdigest()
md5_a09 = hashlib.md5(open(path_a09,'rb').read()).hexdigest()
if md5_a07 == md5_a08 == md5_a09:
    print("PATTERN A rilevato: caricamento triplicato")
```

**Pattern B - Etichetta errata fascicolo:** Verificare se il titolo dichiarato nel SHA256 corrisponde al contenuto effettivo (es. fascicolo etichettato "Relazione Materiali" che in realtà è "Verifica Statica IBS").

**Pattern C - Mancano A5/A6/A11/A12 in deposito "rilevante":** se l'intervento è classificato come rilevante ma mancano questi fascicoli, è una NC.

### 6. Verifica asseverazioni e ricevute IRIS

- 2-3 asseverazioni firmate digitalmente attestano la conformità del progetto a norme specifiche
- 2 ricevute IRIS attestano il pagamento dei contributi al GC

Se mancano: NC documentale.

## Output strutturato

```json
{
  "deposito_genio_civile": {
    "stato": "REGOLARE - VIDIMATO" | "REGOLARE - DA VIDIMARE" | "MANCANTE" | "INCOMPLETO",
    "ente": "Regione Toscana - Settore Sismica Sede di Firenze",
    "numero_progetto": "122597",
    "numero_protocollo": "AOOGRT/SISMICA/20220095422",
    "data_vidimazione": "2022-09-06",
    "norma_di_riferimento": "Art. 93 DPR 380/2001 + Art. 169 LRT 65/2014",
    "classificazione_intervento": "Di minore rilevanza ai sensi art. 94-bis comma 1 DPR 380/2001",
    "sistema_telematico": "PORTOS Regione Toscana",
    "direttore_lavori": "...",
    "fascicoli_depositati": [...],
    "asseverazioni": "n. ...",
    "ricevute_pagamento": "n. ...",
    "anomalie_formali_rilevate": [
      "A07/A08/A09 hanno SHA256 identico - caricamento triplicato sotto etichetta sbagliata",
      "Manca fascicolo A5 - relazione di calcolo strutturale dedicata (intervento classificato come rilevante)"
    ],
    "verdetto_gc": "VIDIMATO REGOLARE | VIDIMATO CON ANOMALIE FORMALI | NON VIDIMATO"
  }
}
```

## Lessons learned

- **Mai concludere "GC non applicabile" senza verificare la zona sismica.** Anche siti urbani in centro Firenze con torrino di vano scale richiedono il deposito.
- **Mai concludere "deposito mancante" se non hai cercato dentro `.7z` annidati.** Il pacchetto GC è quasi sempre in `.7z`.
- **Md5 dei fascicoli identici è red flag.** Indica caricamento triplicato sotto etichetta sbagliata - tipico bug del front-end PORTOS.
- **A02 architettonico depositato GC è quasi sempre identico al PE iliad/Cellnex.** Se diverso, significa che è stato fatto un PDM autorizzato diverso dal PE - segnalare come NC sostanziale.

## Riferimenti normativi

- DPR 6 giugno 2001, n. 380 art. 93 (preavviso scritto + deposito)
- DPR 6 giugno 2001, n. 380 art. 94-bis (classificazione interventi)
- LRT 10 novembre 2014, n. 65 art. 169 (Toscana)
- LR Lombardia 33/2015 (Lombardia)
- LR Lazio 31/2002 (Lazio)
- LR Sicilia 7/2003 (Sicilia)

Vedi `references/fascicoli-gc-per-regione.md` per i riferimenti completi per ogni regione.
