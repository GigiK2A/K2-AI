---
name: verifica-statica-iliad-cellnex:vs-template-paline-rt
description: Template library con tipologie ricorrenti di paline Roof Top per siti TLC (iliad, Cellnex, WindTre). Attivala quando la skill vs-schema-statico ha classificato la struttura come RT e l'utente non conosce i dettagli precisi della palina, quando si dice "palina sul tetto", "palina sul torrino", "palina con stralli", "palina reticolare RT", "tipologia standard palina", "pre-compila dati palina", "schema tipico RT", oppure quando il sopralluogo ha rivelato una tipologia identificabile tra quelle del catalogo. Produce un template pre-compilato di schema_statico.json da raffinare con i dati reali.
---

# vs-template-paline-rt — Catalogo tipologie paline Roof Top

Questo skill pre-compila i dati di schema per le 5 tipologie di palina RT più
diffuse sui siti iliad/Cellnex italiani, riducendo il rischio di omettere vincoli
critici.

**Uso**: confronta la descrizione e le foto del sopralluogo con le 5 tipologie.
Scegli quella più vicina e adatta i parametri dimensionali.

---

## TIPOLOGIA A — Palina su copertura piana senza vincoli (mensola pura)

**Descrizione**: palina tubolare Ø76÷168mm saldata o bullonata su flange a pavimento,
senza staffe laterali né stralli. Altezza tipica 3–8 m. Carico vento basso.

**Diffusione**: molto comune su terrazze condominiali, edifici bassi (2–5 piani).

**Pre-template schema_statico.json**:
```json
{
  "tipo": "mensola_pura",
  "descrizione": "Palina tubolare su flange a pavimento, senza vincoli intermedi",
  "richiede_solver_fem": false,
  "vincoli_intermedi": [],
  "parametri_solver": {
    "modello": "mensola_analitica"
  },
  "template_id": "RT-A",
  "dati_da_verificare": [
    "Diametro e spessore fusto",
    "Altezza totale",
    "Armatura baggioli/soletta",
    "Portata residua copertura (kPa)"
  ]
}
```

**Verifiche critiche**:
- Flange di base: dimensioni e bulloni (spesso M16 o M20 su piastra 200×200)
- Portata copertura residua sotto carico palina + antenne + neve
- Ancoraggio alla struttura ospite: tirafondi o chimica nella soletta

---

## TIPOLOGIA B — Palina su staffa a torrino (strallata 1 livello)

**Descrizione**: palina tubolare Ø88.9÷168mm con piastra di base sulla copertura
+ staffa metallica bullonata al muro perimetrale del torrino vano scala.
Altezza totale 5–12 m. Lo staffone laterale funziona da vincolo orizzontale
a quota bassa.

**Diffusione**: la tipologia più comune nei siti RT italiani. Quasi tutte le paline
iliad su condomini con torrino hanno questo schema.

**Pre-template schema_statico.json**:
```json
{
  "tipo": "strallata_1_livello",
  "descrizione": "Palina con staffa al torrino vano scala — vincolo orizzontale a quota bassa",
  "richiede_solver_fem": true,
  "schema_mensola_applicabile": false,
  "motivazione_schema_mensola_non_applicabile": "Staffa riduce drasticamente M_base ma concentra momento alla quota staffa",
  "vincoli_intermedi": [
    {
      "id": "V1",
      "tipo": "staffa_torrino",
      "quota_m": 3.5,
      "rigidezza_traslazionale_kN_m": 50000,
      "note": "[IPOTESI: quota staffa 3.5m — aggiornare con dato reale dal sopralluogo]"
    }
  ],
  "parametri_solver": {
    "n_nodi": 24,
    "passo_discretizzazione_m": 0.5,
    "condizioni_al_contorno": "incastro_base + molla_V1",
    "modello": "frame_2D_euler_bernoulli"
  },
  "template_id": "RT-B",
  "dati_da_verificare": [
    "Quota staffa dal piano copertura",
    "Tipo connessione staffa: morsetto scorrevole o bullonato rigido",
    "Spessore muro torrino (cls o laterizio → diversa rigidezza)",
    "Altezza sbalzo superiore sopra la staffa"
  ]
}
```

**Verifiche critiche**:
- Sezione della staffa metallica (profilo U o tubo quadro) + bulloni al torrino
- Il momento massimo si trova tipicamente alla quota della staffa, NON alla base
- Se staffa bullonata rigidamente → momento alla staffa = picco assoluto
- Se morsetto scorrevole → nodo cerniera, V1 k_traslazionale rimane ma k_rotazionale=0

---

## TIPOLOGIA C — Palina strallata con 2 ordini di cavi

**Descrizione**: palina tubolare Ø114.3÷219.1mm con 2 set di stralli a trefolo
d'acciaio Ø8÷12mm, tesi con tensori. Altezza totale 8–18 m.
Spesso su edifici industriali, capannoni o palazzine con terrazza ampia.

**Diffusione**: meno comune nel residenziale, più frequente in RT industriali.
Tipica nei siti NS-RT iliad dove l'altezza richiesta supera i 10 m.

**Pre-template schema_statico.json**:
```json
{
  "tipo": "strallata_2_livelli",
  "descrizione": "Palina con 2 ordini di stralli a trefolo — altezza elevata",
  "richiede_solver_fem": true,
  "schema_mensola_applicabile": false,
  "motivazione_schema_mensola_non_applicabile": "2 livelli di vincolo con redistribuzione complessa del momento. M_base ≪ M_locale ai nodi cavo.",
  "vincoli_intermedi": [
    {
      "id": "V1",
      "tipo": "strallo",
      "quota_m": 5.0,
      "angolo_deg": 45,
      "sezione_cavo_mm2": 78.5,
      "E_acciaio_MPa": 160000,
      "L_strallo_m": 5.0,
      "pretensione_kN": 8.0,
      "rigidezza_equivalente_kN_m": 2512,
      "note": "[IPOTESI: quota e angolo da verificare con rilievo]"
    },
    {
      "id": "V2",
      "tipo": "strallo",
      "quota_m": 10.0,
      "angolo_deg": 40,
      "sezione_cavo_mm2": 78.5,
      "E_acciaio_MPa": 160000,
      "L_strallo_m": 7.5,
      "pretensione_kN": 6.0,
      "rigidezza_equivalente_kN_m": 1675,
      "note": "[IPOTESI: quota e angolo da verificare con rilievo]"
    }
  ],
  "parametri_solver": {
    "n_nodi": 32,
    "passo_discretizzazione_m": 0.5,
    "condizioni_al_contorno": "incastro_base + molle_V1_V2",
    "modello": "frame_2D_euler_bernoulli"
  },
  "template_id": "RT-C",
  "dati_da_verificare": [
    "Quota, angolo e diametro di ciascun strallo",
    "Lunghezza strallo fino al punto di ancoraggio sulla copertura",
    "Presenza e entità della pretensione",
    "Sezione bullone di attacco strallo al fusto (spesso M16 con occhiello saldato)"
  ]
}
```

**Verifiche critiche**:
- Verifica bulloni attacco strallo al fusto (sforzo assiale = T_strallo / sin(θ))
- Verifica tensori e capocorda (componente non strutturale ma critica)
- Stralli lavorano solo a trazione: con vento in direzione opposta allo strallo,
  il cavo si scarica e la struttura si comporta come mensola parziale → verificare
  entrambe le direzioni vento

---

## TIPOLOGIA D — Palina reticolare compatta

**Descrizione**: struttura in profilati tubolari quadri o circolari formante
un reticolo a sezione quadrata o triangolare. Altezza 6–20 m.
Comune nei siti NS-RL per altezze contenute o NS-RT per carichi elevati.

**Diffusione**: meno frequente delle paline tubolari, ma presente in zone
ad alta densità di operatori (colocation) dove serve superficie installativa.

**Pre-template schema_statico.json**:
```json
{
  "tipo": "reticolare",
  "descrizione": "Struttura reticolare a sezione quadrata — profili tubolari",
  "richiede_solver_fem": true,
  "schema_mensola_applicabile": false,
  "motivazione_schema_mensola_non_applicabile": "Struttura reticolare con inerzia composta — la mensola semplice sottostima EI e sovrastima le deformazioni",
  "vincoli_intermedi": [],
  "geometria_reticolo": {
    "sezione_trasversale_lato_mm": 400,
    "n_correnti": 4,
    "n_diagonali_per_pannello": 2,
    "passo_pannello_m": 1.5,
    "profilo_corrente": "SHS 80x80x4",
    "profilo_diagonale": "SHS 40x40x3"
  },
  "parametri_solver": {
    "n_nodi_per_corrente": 12,
    "modello": "truss_2D_frame_equivalente",
    "EI_equivalente_note": "Calcolare I_eq = n_correnti * A_corrente * (d/2)^2 con d = lato sezione"
  },
  "template_id": "RT-D",
  "dati_da_verificare": [
    "Sezione correnti longitudinali",
    "Sezione e schema diagonali",
    "Connessioni: saldate o bullonate",
    "Piastra di base e ancoraggi"
  ]
}
```

**Verifiche critiche**:
- Inerzia equivalente della sezione composta (non quella del singolo corrente)
- Diagonali di parete: verifica a compressione con instabilità (λ̄ critica)
- Connessioni corrente-diagonale: saldature d'angolo o bulloni a taglio

---

## TIPOLOGIA E — Palina su cassero metallico (scaffolding RT)

**Descrizione**: palina tubolare montata su un telaio/cassero metallico
autoportante posato sulla copertura (tipologia usata quando non si può
forare la copertura). Il cassero stesso ha 4 piedi appoggiati e zavorrati.

**Diffusione**: specifica di siti dove il condominio nega i tirafondi nella
soletta (contratto di locazione). Illecito edilizio in alcuni comuni.

**Pre-template schema_statico.json**:
```json
{
  "tipo": "mensola_pura",
  "descrizione": "Palina su telaio zavorrato — nessun ancoraggio strutturale alla copertura",
  "richiede_solver_fem": false,
  "vincoli_intermedi": [],
  "note_speciali": "La stabilità dipende dalla zavorra. Verificare peso zavorra vs. azione ribaltante vento. Spesso INSUFFICIENTE per antenne massive MIMO (>40kg).",
  "parametri_solver": {
    "modello": "mensola_analitica_con_verifica_ribaltamento_telaio"
  },
  "template_id": "RT-E",
  "dati_da_verificare": [
    "Peso totale zavorra (blocchi calcestruzzo su piedi telaio)",
    "Schema telaio: larghezza interasse piedi (braccio resistente)",
    "Altezza palina sopra il telaio",
    "Condizione contrattuale: ancoraggio consentito?"
  ],
  "verifiche_aggiuntive": [
    "M_ribaltante = Fx_vento_max * (H_palina + H_telaio)",
    "M_stabilizzante = P_zavorra * B_piedi/2",
    "Coefficiente sicurezza ribaltamento = M_stabilizzante / M_ribaltante >= 1.5",
    "Se CS < 1.5 → NON IDONEO indipendentemente dalla verifica del fusto"
  ]
}
```

**Verifiche critiche**:
- La verifica principale è il ribaltamento del telaio, non la resistenza della palina
- Zavorra spesso insufficiente per vento forte (zona vento ≥ 4)
- Documentare contratto di locazione: il vincolo può impedire il miglioramento

---

## Come usare i template

### Passo 1 — Selezione tipologia

Descrivi all'utente le 5 tipologie e chiedi di indicare quale corrisponde
al sito da verificare. Se ha foto del sopralluogo, usale per classificare.

### Passo 2 — Pre-compilazione

Copia il template corrispondente in `VS_<CODICE>/schema_statico.json`.

### Passo 3 — Verifica e aggiornamento

Sostituisci tutti i valori con `[IPOTESI: ...]` con i dati reali del sopralluogo.
Se alcuni dati non sono disponibili, mantieni l'IPOTESI documentandola.

### Passo 4 — Handoff alla skill vs-schema-statico

Segnala allo skill `vs-schema-statico` che il template è pre-compilato e
che va eseguita solo la validazione finale (Step 4-6 della sua sequenza).

---

## Note su casi limite

### Palina con staffa scorrevole (morsetto a coda di rondine)
- Il morsetto consente spostamento verticale libero ma blocca quello orizzontale
- Modellare come cerniera (rotazione libera, traslazione orizzontale bloccata)
- `k_rotazionale = 0`, `k_traslazionale_x = 50000 kN/m`

### Palina con 3 ordini di stralli (raro)
- Usare tipologia C e aggiungere un terzo nodo vincolo
- Il modello FEM regge naturalmente N vincoli

### Palina doppia (due paline affiancate con traverse di collegamento)
- La rigidezza complessiva è superiore alla singola palina
- In mancanza di solver 3D: trattare la coppia come una struttura singola
  con I_eq = 2·I_singola + A·d²/2 (teorema Huygens)
