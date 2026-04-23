# Output Schema K-BOT: TEASER + ANALISI COMPLETA

Questo documento definisce il formato tecnico dei payload JSON generati dalla skill base.

## 1) TEASER (gratuito)

Campi obbligatori:
- `settore`: slug settore (deve essere uno dei valori in `SECTOR_BUNDLES`)
- `skill_attive`: array di stringhe (skill realmente caricate)
- `segnali`: array di 3-5 elementi
- `hook_pdf`: stringa di 1-2 righe

Vincoli `segnali[]`:
- `priorita`: `critica | rilevante | da_monitorare`
- `titolo`: max 8 parole
- `sintesi`: 2 righe, con causa + impatto
- `anteprima_analisi`: termina sempre con `...`

## 2) ANALISI COMPLETA (PDF 19 euro)

Campi obbligatori:
- `meta.settore`
- `meta.skill_attive`
- `meta.data_generazione` (ISO 8601)
- `meta.versione_modello`
- `executive_summary`
- `sezioni` (min 4: analisi_verticale, automazione, benchmark, roadmap)
- `automazioni_consigliate` (3-6 voci)
- `prossimo_passo`

## 3) Tipi supportati per `elementi_visivi[].dati`

- `tabella`: `{ "colonne": [], "righe": [[]] }`
- `grafico_barre`: `{ "labels": [], "valori": [], "unita": "" }`
- `gauge`: `{ "valore": 0-100, "label": "", "soglie": {"verde": 70, "giallo": 40} }`
- `lista_prioritizzata`: `{ "elementi": [{"testo": "", "priorita": "alta|media|bassa"}] }`
- `schema_flusso`: `{ "nodi": [{"id": "", "label": ""}], "archi": [{"da": "", "a": ""}] }`

## 4) Esempi per settore

### Commercialista (estratto)
- Segnale critica: scadenziario frammentato e riconciliazioni manuali
- Automazione prioritaria: riconciliazione movimenti + reminder scadenze

### Studio ingegneria (estratto)
- Segnale rilevante: redazione relazioni tecniche disallineata tra commesse
- Automazione prioritaria: compilazione assistita elaborati + controllo coerenza

### Manifatturiero (estratto)
- Segnale critica: dati qualità dispersi tra fogli e sistemi
- Automazione prioritaria: raccolta KPI produzione e non conformità su flusso unico
