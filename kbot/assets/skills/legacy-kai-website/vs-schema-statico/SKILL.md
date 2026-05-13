---
name: verifica-statica-iliad-cellnex:vs-schema-statico
description: Identifica e classifica lo schema statico di una struttura porta-antenne (palo RL o palina RT) prima del calcolo delle sollecitazioni. Attivala SEMPRE quando la struttura è un sito Roof Top (TC-RT o NS-RT), quando il fusto presenta staffe di ancoraggio, stralli, controventi o vincoli intermedi, oppure quando l'utente dice "strallato", "staffa", "cavi", "tiranti", "palina sul torrino", "palina ancorata", "baggioli", "palina reticolare", "schema non a mensola". Produce schema_statico.json con il tipo di schema e i parametri per il solver corretto (mensola analitica vs FEM multi-vincolo).
---

# vs-schema-statico — Classificazione schema statico strutturale

## Scopo

Prima del calcolo delle sollecitazioni (Passo 3), è necessario sapere **come è vincolata
la struttura**. Questo determina quale modello di calcolo usare:

| Schema | Modello | Skill di calcolo |
|--------|---------|-----------------|
| `mensola_pura` | Formula chiusa (mensola incastrata) | `vs-sollecitazioni` standard |
| `strallata_1_livello` | FEM 2D con molla a 1 quota | `vs-sollecitazioni` + `references/solver-multi-vincolo.md` |
| `strallata_2_livelli` | FEM 2D con molle a 2 quote | `vs-sollecitazioni` + `references/solver-multi-vincolo.md` |
| `controventata` | FEM 2D con aste diagonali | `vs-sollecitazioni` + `references/solver-multi-vincolo.md` |
| `reticolare` | FEM 3D o schema truss 2D | `vs-sollecitazioni` + `references/solver-multi-vincolo.md` |

**Regola fondamentale**: la mensola pura è SEMPRE conservativa sulle sollecitazioni
alla base, ma può essere NON conservativa sulle sollecitazioni **locali** ai nodi
di vincolo (stralli, staffe, baggioli), dove si concentrano le reazioni più elevate.
Quindi per strutture multi-vincolate il solver FEM è obbligatorio.

---

## Output atteso

`VS_<CODICE>/schema_statico.json`:

```json
{
  "tipo": "strallata_2_livelli",
  "descrizione": "Palina Ø114.3mm su copertura piana, staffa al torrino quota +4.5m, 2 ordini di stralli a quota +7.0m e +11.5m, sbalzo libero superiore 2.1m",
  "richiede_solver_fem": true,
  "schema_mensola_applicabile": false,
  "motivazione_schema_mensola_non_applicabile": "Presenza di stralli con rigidezza assiale non trascurabile. La mensola sovrastima M_base del 40-60% e non coglie il picco M_locale ai nodi strallo.",
  "vincoli_intermedi": [
    {
      "id": "V1",
      "tipo": "staffa_torrino",
      "quota_m": 4.5,
      "rigidezza_rotazionale_kNm_rad": null,
      "rigidezza_traslazionale_kN_m": 50000,
      "note": "Staffa metallica bullonata al torrino in cls — assume cerniera (traslaz. libera verticale, impedita orizzontale)"
    },
    {
      "id": "V2",
      "tipo": "strallo",
      "quota_m": 7.0,
      "angolo_deg": 45,
      "sezione_cavo_mm2": 78.5,
      "E_acciaio_MPa": 160000,
      "L_strallo_m": 5.0,
      "pretensione_kN": 8.0,
      "rigidezza_equivalente_kN_m": 2512,
      "note": "Cavo Ø10mm — rigidezza calcolata come EA/L=160000·78.5·1e-6/5.0"
    },
    {
      "id": "V3",
      "tipo": "strallo",
      "quota_m": 11.5,
      "angolo_deg": 40,
      "sezione_cavo_mm2": 78.5,
      "E_acciaio_MPa": 160000,
      "L_strallo_m": 7.2,
      "pretensione_kN": 6.0,
      "rigidezza_equivalente_kN_m": 1744,
      "note": "Cavo Ø10mm — rigidezza calcolata come EA/L"
    }
  ],
  "parametri_solver": {
    "n_nodi": 30,
    "passo_discretizzazione_m": 0.5,
    "condizioni_al_contorno": "incastro_base + molle_vincoli_intermedi",
    "modello": "frame_2D_euler_bernoulli"
  }
}
```

---

## Classificazione degli schemi

### TIPO A — mensola_pura

**Quando**: pali Raw Land (TC-RL, NS-RL) con fusto poligonale flangiato libero
e fondazione. Nessun vincolo intermedio. Anche paline RT semplici su copertura
senza staffe né stralli.

**Modello di calcolo**: formula chiusa — lo skill `vs-sollecitazioni` standard.

**Riconoscimento**:
- Tipologia sito = RL (Raw Land) → sempre mensola_pura salvo eccezioni
- Tipologia sito = RT, palina senza staffe né stralli visibili nelle foto → mensola_pura
- Documentazione preesistente non menziona vincoli intermedi

---

### TIPO B — strallata_1_livello

**Quando**: palina RT con un singolo ordine di cavi/stralli + attacco alla
struttura ospite (es. staffa al muro del torrino).

**Struttura tipica**: base ancorata su copertura (baggioli o flange bullonate) +
staffa di irrigidimento a un'altezza intermedia + sbalzo libero superiore.

**Modello**: FEM 2D con 1 molla traslazionale intermedia.

**Riconoscimento**:
- Documentazione o foto mostrano un ordine di cavi/tiranti
- Relazione preesistente cita "strallo" o "staffa al torrino" o "staffa di contenimento"
- Geometria: H_libera_superiore / H_totale > 0.3 (sbalzo significativo)

---

### TIPO C — strallata_2_livelli

**Quando**: palina RT con due ordini di stralli o con staffa al torrino + un
ordine di cavi.

**Struttura tipica**: base ancorata su copertura + staffa al torrino (quota bassa) +
ordine stralli (quota alta) + sbalzo libero sommitale.

**Modello**: FEM 2D con 2 molle traslazionali a quote diverse.

**Riconoscimento**:
- Due ordini di cavi visibili nelle foto
- Relazione preesistente indica 2 livelli di vincolo
- Altezza totale palina > 15 m con base su copertura

---

### TIPO D — controventata

**Quando**: palo o palina con controventi a X, V, K tra il fusto e una struttura
adiacente (colonna del solaio, parete, altra palina).

**Modello**: FEM 2D con aste inclinate (truss element per controventi).

**Riconoscimento**:
- Foto mostrano profili diagonali imbullonati al fusto
- Schema a X o V con 2 diagonali che si incrociano

---

### TIPO E — reticolare

**Quando**: struttura porta-antenne in profili L/T/tubolari formante un reticolo
(traliccio autoportante o palina reticolare per RL).

**Modello**: FEM 3D o truss 2D per struttura simmetrica.

**Riconoscimento**:
- Struttura con n ≥ 4 profili longitudinali + diagonali di parete
- Traliccio autoportante triangolare o quadrangolare

---

## Sequenza di classificazione (obbligatoria)

### Step 1 — Prima domanda: RL o RT?

- Se TC-RL o NS-RL → `tipo = mensola_pura`, `richiede_solver_fem = false`
  - Eccezione: pali con stralli (rarissimo per RL) → vai a Step 2
- Se TC-RT o NS-RT → **vai a Step 2 obbligatoriamente**

### Step 2 — Raccolta informazioni per RT

Chiedi all'utente:

1. **Documentazione disponibile**: esiste una VS precedente? Un disegno costruttivo
   della palina? Foto del sopralluogo?
2. **Vincoli visibili**: sono presenti staffe di ancoraggio laterale? Cavi/stralli?
   Controventi diagonali?
3. **Geometria palina**: altezza totale, quota base su copertura, quota della
   staffa/strallo (se presente).
4. **Tipologia ancoraggio alla copertura**: piastra di base + baggioli in cls,
   flange bullonate alla struttura ospite, tirafondi nella soletta, o altro.

### Step 3 — Classificazione

Usa la tabella seguente per classificare:

| Vincoli rilevati | Tipo |
|-----------------|------|
| Nessuno | mensola_pura |
| 1 staffa OR 1 ordine stralli | strallata_1_livello |
| 2 staffe/stralli OR staffa+cavi | strallata_2_livelli |
| Diagonali/controventi | controventata |
| Struttura reticolare | reticolare |

### Step 4 — Raccolta parametri vincoli intermedi

Per ogni vincolo intermedio raccogli (obbligatorio se `richiede_solver_fem = true`):

**Staffa di contenimento (bordo muro/torrino)**:
- Quota dal basso (m)
- Tipo di connessione: morsetto scorrevole (→ traslazione libera verticale) o
  bullonato rigido (→ incastro parziale)
- Assume `rigidezza_traslazionale_kN_m = 50000` se non noto (parete cls)

**Strallo/cavo**:
- Quota di attacco sul fusto (m)
- Angolo rispetto all'orizzontale (deg)
- Diametro cavo (mm) → A = π·d²/4
- Lunghezza strallo (m) — misura dalla lunghezza geometrica
- Stima pretensione iniziale (kN) — se non nota usa 0 (conservativo)
- `k_strallo = E·A/L` (kN/m), con E = 160.000 MPa per trefolo acciaio

**Nota**: gli stralli lavorano solo a trazione. La rigidezza equivalente nella
direzione trasversale alla palina è `k_eff = k_strallo · sin²(θ)`.

### Step 5 — Avviso all'utente se richiede_solver_fem = true

Se il tipo non è mensola_pura, mostra questo messaggio:

> ⚠️ **Schema non a mensola pura rilevato** (`tipo = <tipo>`). Il calcolo delle
> sollecitazioni con formula chiusa (mensola incastrata) non è applicabile a questa
> struttura. La skill `vs-sollecitazioni` utilizzerà il solver FEM multi-vincolo
> (`references/solver-multi-vincolo.md`). Fornisci i parametri dei vincoli intermedi
> per procedere.

### Step 6 — Produzione output

Salva `VS_<CODICE>/schema_statico.json` con tutti i campi popolati.
Segnala all'orchestratore che può procedere con `vs-azioni-ambientali` (Passo 2).

---

## Template paline RT ricorrenti

Per le tipologie più comuni di paline RT, consulta
`references/tipologie-paline-rt.md` (skill `vs-template-paline-rt`) che contiene
schemi pre-configurati con geometrie tipiche e parametri di vincolo standard.

---

## Validazioni

1. Se `tipo != mensola_pura` e `vincoli_intermedi` è array vuoto → **FAIL**:
   obbligatorio specificare almeno 1 vincolo intermedio.
2. Se `tipo == strallata_*` e nessun strallo con `angolo_deg` specificato → **WARNING**:
   verifica che l'angolo sia plausibile (15°–60° è il range tipico).
3. Se `tipo == controventata` e nessun controvento con sezione dichiarata → **FAIL**.
4. `quota_m` dei vincoli deve essere nell'intervallo `[0, H_totale_palina]`.
