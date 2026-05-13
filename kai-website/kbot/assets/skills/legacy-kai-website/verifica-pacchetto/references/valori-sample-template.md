# Valori "Sample" nei Template — Lista Canonica delle Sostituzioni

I template iliad contengono valori sample **realistici** (non placeholder vuoti) che sembrano dati veri ma appartengono a siti campione. Vanno sostituiti in OGNI pacchetto, anche quando sembrano plausibili per il sito corrente.

**Il rischio è consegnare un pacchetto che mescola dati reali con dati sample.** Già capitato.

---

## Template RT (doc 4) — Tabella T3 R0 C1

### PRG / PTPR

| Valore sample nel template | Quando sostituire |
|---------------------------|-------------------|
| `"Città storica: Tessuti di espansione otto-novecentesca ad isolato – T4"` | SEMPRE se il sito non è in T4 Città storica — verificare PRG su WebGIS Roma |

### ENAC Ciampino

| Valore sample | Quando sostituire |
|---------------|-------------------|
| `"Area non interessata da limitazione e non interferente con la superficie di inviluppo"` | Se il sito rientra in una superficie di limitazione ENAC Ciampino → sostituire con `"Area interessata da limitazione e non interferente con la superficie di inviluppo"` |

### Preesistenze (SCIA / ARPA / VAP)

Il template riporta 3 preesistenze sample. **Vanno sempre verificate e sostituite** con i dati reali del sito:

| Valore sample | Sostituzione |
|---------------|-------------|
| `"in data 24/09/2025 e assunta al prot. n. QF/2025/0126488 del 26/09/2025"` | data invio SCIA reale + protocollo + data DPU reali |
| `"24/09/2025"` | data trasmissione SCIA reale (può comparire separato) |
| `"QF/2025/0126488 del 26/09/2025"` | protocollo + data DPU reali |
| `"19436.U del 20/03/2023"` | protocollo + data parere ARPA reali |
| `"NA/13029 del 12/06/2023"` | protocollo + data parere VAP reali (o **cancellare la riga** se sito senza VAP) |

### Fotografia sito

Il template incorpora due copie della stessa foto sample (`word/media/image1.jpeg` e `word/media/image2.jpeg`) di un sito di esempio. **SEMPRE** da sostituire con la foto reale del sito fornita dall'utente. Vedi `post-processing.md` § "Sostituzione Foto Sito".

### Aeroporti (C0 labels + C1 valori)

Il template elenca 3 aeroporti (Ciampino + Fiumicino + Urbe). Tenere SOLO il reference del sito identificato dal PDM. Vedi `lezioni-apprese.md` § L4.

---

## Template ASSEVERAZIONI (doc 6) — Tabella T1 R0 C1

Stessi valori sample del template RT (PRG/ENAC/Aeroporti). In più:

### Relazione precisazioni (C0 P31)

| Valore sample | Sostituzione |
|---------------|-------------|
| `"INSERIRE PRECISAZIONI RELAZIONE TECNICA"` (rosso) | Testo reale della relazione: tipo di intervento (modifica radioelettrica), preesistenze (SCIA prot. + ARPA prot.), conformità PRG/PTPR, eventuale esclusione VAP ex art. 5 co. 5 Delibera 78/2024 |

---

## Template SCIA (doc 1)

### Dati legale rappresentante iliad

| Valore sample | Sostituzione |
|---------------|-------------|
| `"procura del 04/2024"` | Verificare validità procura Longari al momento della sessione. Se ancora in corso → lasciare invariato. Se cambiata → aggiornare data procura. |
| `"assunta al prot. n. ... del ..."` | Protocollo SCIA preesistente se modifica, altrimenti cancellare |

---

## Template Delega (doc 2), Atto d'obbligo (doc 10)

Generalmente non contengono sample numerici ma solo annotazioni. Vedi `annotazioni-template.md`.

---

## Template Dich. Sostitutiva ALPHA24 (doc 9)

| Valore sample | Sostituzione |
|---------------|-------------|
| Reference site placeholder (es. `"RMXXXXX_YYY"`) | Valore reale dalla Scheda Radio alla voce `"Reference Site alpha24 5G"` |

**ATTENZIONE L8**: il reference alpha24 NON è per default il codice sito stesso. A volte è un sito vicino. Leggere SEMPRE dalla scheda radio.

---

## Template Impegno ARPA (doc 8)

| Valore sample | Sostituzione |
|---------------|-------------|
| Tariffa ARPA (es. `"€ 150,00"`) | Verificare tariffario ARPA Lazio aggiornato (Fase 0 ricerca web) |
| IBAN/dati bancari | Verificare validità per l'anno in corso |

---

## Lista Replacements Canonica per `edit_rt.py` / `edit_asseverazioni.py`

```python
replacements += [
    # PRG default
    ("Città storica: Tessuti di espansione otto-novecentesca ad isolato – T4",
     f"{SITO['prg_sistemi_regole']}"),

    # ENAC Ciampino
    ("Area non interessata da limitazione e non interferente con la superficie di inviluppo",
     SITO["enac_ciampino"]),

    # Preesistenze SCIA
    ("in data 24/09/2025 e assunta al prot. n. QF/2025/0126488 del 26/09/2025",
     f"in data {SITO['pree_scia_data_invio']} e assunta al prot. n. {SITO['pree_scia_prot_dpu']} del {SITO['pree_scia_data_dpu']}"),
    ("QF/2025/0126488 del 26/09/2025",
     f"{SITO['pree_scia_prot_dpu']} del {SITO['pree_scia_data_dpu']}"),
    ("24/09/2025", SITO['pree_scia_data_invio']),

    # Preesistenza ARPA
    ("19436.U del 20/03/2023",
     f"{SITO['pree_arpa_prot']} del {SITO['pree_arpa_data']}"),

    # Preesistenza VAP (solo se sito ha VAP)
    # ("NA/13029 del 12/06/2023",
    #  f"{SITO['pree_vap_prot']} del {SITO['pree_vap_data']}"),
]
```

    # Proprietà infrastruttura (L17)
    ("SITE S.p.A.",  # valore sample tipico — identificare il reale in Fase 0-TER
     SITO['proprieta_infrastruttura']),

    # Zona sismica (L20)
    # Il valore sample va identificato in Fase 0-TER, es.:
    # ("Zona 3", SITO['zona_sismica']),

    # Codici tavole PRG (L18)
    # Il valore sample va identificato in Fase 0-TER, es.:
    # ("Tav. 3_18", f"Tav. {SITO['tavola_prg']}"),

    # Permit Coordinator (L14)
    # Il valore sample va identificato in Fase 0-TER, es.:
    # ("NOME PERMIT SAMPLE", SITO['permit_coordinator_nome']),
    # ("permit@sample.it", SITO['permit_coordinator_email']),
    # ("0612345678", SITO['permit_coordinator_tel']),
]
```

**Queste replacements vanno mantenute ANCHE quando sembrano non applicabili.** Se la stringa sample non esiste nel template corrente, la replace è no-op e non fa danno.

---

## Nuovi campi nel dizionario `SITO` (v0.4.0 — L14-L22)

Oltre ai campi già documentati sopra, il dizionario `SITO` deve includere:

| Campo | Sorgente | Obbligatorio | Lezione |
|-------|----------|--------------|---------|
| `permit_coordinator_nome` | Preesistenza | SI | L14 |
| `permit_coordinator_tel` | Preesistenza | SI | L14 |
| `permit_coordinator_email` | Preesistenza | SI | L14 |
| `codice_reversale` | Utente | SI (o [DA COMPILARE]) | L15 |
| `proprieta_infrastruttura` | Preesistenza | SI | L17 |
| `tavola_prg` | WebGIS Roma / PDF stralci | SI | L18 |
| `tavola_ptpr_a` | WebGIS Roma / PDF stralci | SI | L18 |
| `tavola_ptpr_b` | WebGIS Roma / PDF stralci | se applicabile | L18 |
| `tavola_ptpr_c` | WebGIS Roma / PDF stralci | se applicabile | L18 |
| `didascalia_prg` | WebGIS Roma | SI | L19 |
| `zona_sismica` | PE / Preesistenza / Regione Lazio | SI | L20 |
| `descrizione_area_intervento` | Street View / PE / Preesistenza | SI | L21 |
| `parabole` | Scheda Radio / FILETX | se presenti | L22 |
