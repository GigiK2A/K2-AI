---
name: relsta-unificata
description: |
  Skill unificata K2A per redigere Relazioni Statiche (RELSTA) di strutture
  porta-antenne TLC (pali poligonali, tubolari flangiati, tralicci) per tutti
  gli operatori italiani (Iliad, Cellnex, WindTre, Vodafone, INWIT). Sintesi
  di 9 RELSTA K2A con decision tree 11 rami: sito RL/RT, palo, pennone,
  mascheramento, sistema strutturale (mensola, stralli, puntoni, baggioli),
  fondazione (plinto, micropali, zavorrato, ancoraggi chimici), intervento
  (new site, upgrade, co-siting, innalzamento, rinforzo), esito OK o NV con
  progetto rinforzo (raddoppio nervature, RR-POLE, micropali, bulloneria,
  camicia/FRP, aggiunta stralli). Usa SEMPRE per "redigere RELSTA", "verifica
  statica palo TLC", "relazione statica antenna", "RELSTA nuova", "RELSTA con
  rinforzo", "palo NV progetto rinforzo", "RELSTA roof top", "RELSTA raw
  land", "RELSTA co-siting", "RELSTA con stralli", "RELSTA finto albero", o
  dati sito (codice, palo, antenne, fondazione) per generare il documento.
  Delega a verifica-statica-iliad-cellnex per FEM/SLU/SLE.
---

# RELSTA UNIFICATA — Skill Orchestratore K2A

**Versione:** 1.0 — 22/04/2026
**Autore:** K2A Srls — Ing. Luca Rossi
**Fonti:** 9 RELSTA K2A (Iliad/Cellnex/WindTre/Vodafone) + MASTER VERIFICA-PRT v10 + NTC 2018 + EC3/EC7 + CNR-DT 207/2008.

---

## 1. Missione della skill

Produrre una **Relazione Statica (RELSTA) completa e conforme** per qualsiasi
struttura porta-antenne TLC installata in Italia, scegliendo automaticamente
capitoli, formule, verifiche e sezioni di rinforzo in base alle caratteristiche
del sito e all'esito delle verifiche.

**Principio guida:** il documento si costruisce **come sintesi**, capitolo per
capitolo, attraversando un albero decisionale a 11 rami. Non esiste un singolo
template rigido: esiste un insieme di blocchi modulari che la skill compone.

---

## 2. Workflow operativo (alto livello)

```
Utente richiede nuova RELSTA
        │
        ▼
 ┌────────────────────────────┐
 │ STEP A — INTAKE            │  → raccolta dati sito (codice, operatore,
 │                            │    tipologia, palo, antenne, fondazione,
 │                            │    LC, intervento)
 └──────────┬─────────────────┘
            ▼
 ┌────────────────────────────┐
 │ STEP B — CLASSIFICAZIONE   │  → attraversamento decision tree,
 │                            │    output JSON di classificazione
 └──────────┬─────────────────┘
            ▼
 ┌────────────────────────────┐
 │ STEP C — CALCOLI           │  → delega a 9 skill VS esistenti
 │                            │    (azioni, sollecitazioni, fusto,
 │                            │    giunti, fondazione, SLE, fatica)
 └──────────┬─────────────────┘
            ▼
 ┌────────────────────────────┐
 │ STEP D — ESITO             │  → pivot: OK oppure NV
 └──────────┬─────────────────┘
            │
       ┌────┴────┐
       ▼         ▼
   OK        NV → rinforzo
       │         │
       │         ▼
       │    STEP D-bis — PROGETTO RINFORZO
       │    (scelta da catalogo rinforzi + ricalcolo)
       │         │
       └────┬────┘
            ▼
 ┌────────────────────────────┐
 │ STEP E — COMPOSIZIONE DOC  │  → scelta capitoli condizionali +
 │                            │    popolamento tabelle + output DOCX
 └────────────────────────────┘
```

**STEP A — INTAKE** usa `verifica-statica-iliad-cellnex:vs-input-dati` per la
raccolta dati. La nuova skill aggiunge **8 campi di classificazione** non
coperti dalla VS-skill:

| Campo | Valori ammessi | Usato per |
|---|---|---|
| `tipologia_sito` | `RL` \| `RT_pilastri` \| `RT_muratura` \| `RT_coperturaCA` \| `RT_shelter` | Ramo 1 |
| `tipologia_palo` | `poligonale` \| `tubolare_flangiato` \| `traliccio_3gambe` \| `traliccio_4gambe` | Ramo 2 |
| `pennone` | `dritto_circolare` \| `inclinato_portafari` \| `assente` | Ramo 3 |
| `mascheramento` | `nessuno` \| `finto_albero` \| `camino` \| `altro` | Ramo 4 |
| `sistema_strutturale` | `mensola` \| `mensola_stralli` \| `mensola_puntoni` \| `mensola_stralli_puntoni` \| `mensola_baggioli` | Ramo 5 |
| `intervento` | `new_site` \| `upgrade` \| `co_siting` \| `innalzamento` \| `rinforzo` | Ramo 7 |
| `tipologia_rinforzo` | `raddoppio_nervature` \| `RR_POLE` \| `micropali` \| `bulloneria` \| `camicia_FRP` \| `aggiunta_stralli` \| `NESSUNO` | Ramo 8 |
| `software` | `straus7` \| `pro_sap` \| `winstrand` | Ramo 9 |

Output STEP B: file `classificazione-sito.json` in `/sessions/<session>/relsta-work/`.

---

## 3. Mappa decisionale (sintesi, vedi `references/decision-tree.md`)

Ogni nuova RELSTA è identificata da una **tupla a 11 coordinate** (una per ramo).
I 9 casi K2A di riferimento sono:

| ID | RL/RT | Palo | Pennone | Sistema | Fondazione | Intervento | Esito | Software | LC | Fatica |
|---|---|---|---|---|---|---|---|---|---|---|
| RM00189 | RL | Poligonale 16L | Ø194 | Mensola | Platea+dado | Upgrade finto albero | OK | Straus7 | LC3 | Sì |
| LU55041 | RL | Flangiato 4T | assente | Mensola | Plinto+12 micropali | Rinforzo nervature | NV→OK | Straus7 | LC3 | Sì |
| LT032 | RT_shelter | Flangiato 5T | assente | Stralli+puntoni | Shelter zavorrato | Co-siting | OK | Straus7 | LC3 | Sì |
| PO008 | RL | Poligonale | n.d. | Mensola+RR-POLE | Plinto allargato | Rinforzo RR-POLE | NV→OK | PRO_SAP | LC3 | Sì |
| RM823 | RL | Poligonale 16L | Ø219.8 | Mensola | Plinto 5×5×0.75 | Co-siting + innalzamento | OK | **WinStrand** | LC3 | **No** |
| FI023/FI50137 | RL torre-faro | Poligonale 16L | **Inclinato** | Mensola | Platea+dado | Upgrade co-siting | OK | Straus7 | LC3 | Sì |
| SI53014 | RL | Poligonale 16L | Ø193.7 | Mensola | Plinto 4×4×2.5 | Prima config | OK | Straus7 | LC3 | Sì |
| LI57027 | RL | Poligonale 16L | Ø219.1 (sost.) | Mensola | Plinto 4.2×4.2+dado | Co-siting + sost. pennone | OK | Straus7 | LC3 | Sì |

**Dataset copre 8 varianti su ~35 teoriche.** Varianti non nel dataset ma che la
skill deve gestire (con template normativo senza esempio K2A):
RT pilastri c.a. isolati, RT muratura portante, RT copertura c.a. piena, RL con
solo stralli, RL solo puntoni, RL baggioli-zavorra, pali tralicciati 3/4 gambe.

**Per queste varianti:** la skill segnala all'utente *"Caso senza precedente
portfolio K2A — utilizzo template normativo; consigliata revisione peer"*.

---

## 4. File di riferimento (`references/`)

| File | Contenuto | Quando leggerlo |
|---|---|---|
| `decision-tree.md` | Architettura completa 11 rami, matrice varianti | SEMPRE prima di classificare |
| `rinforzi-catalogo.md` | 6 tipologie rinforzo con formule e step di progetto | Solo se esito = NV |
| `formule-chiave.md` | α-factor flangia, Quatordio, Woehler, Miner, Brinch-Hansen | Durante verifica/progetto |
| `rt-varianti.md` | RT pilastri/muratura/c.a./shelter — ancoraggi, verifiche | Solo se `tipologia_sito` inizia con `RT_` |
| `stralli-puntoni.md` | Funi spiroidali, puntoni tubolari, pretensione, tensiometro | Solo se `sistema_strutturale` contiene `stralli` o `puntoni` |
| `mascheramento.md` | Finto albero, camino, camouflage — cp, A esposta, peso | Solo se `mascheramento` ≠ `nessuno` |
| `ante-post-operam.md` | Convenzione tabella sfruttamenti per upgrade/co-siting | Solo se `intervento` ∈ {upgrade, co_siting, innalzamento} |
| `software-modellazione.md` | Straus7 vs PRO_SAP vs WinStrand — setup FEM | Durante STEP C |
| `dataset-relsta-k2a.md` | Fact sheet dei 9 casi portfolio con parametri chiave | Come benchmark/confronto |

---

## 5. File template (`templates/`)

| File | Descrizione |
|---|---|
| `relsta-master.md` | Struttura-guida del documento con tutti i capitoli (fissi + condizionali) |
| `sezioni/01-premessa.md` | Capitolo 1 premessa e oggetto |
| `sezioni/02-RL-inquadramento.md` | Cap. 2 per Raw Land |
| `sezioni/02-RT-inquadramento.md` | Cap. 2 per Roof Top (con 4 sub-varianti) |
| `sezioni/04-palo-poligonale.md` | Cap. 4 per palo poligonale 16 lati |
| `sezioni/04-palo-flangiato.md` | Cap. 4 per palo tubolare multi-tronco flangiato |
| `sezioni/05-azioni-vento.md` | Cap. 5.1 vento CNR-DT 207/2008 |
| `sezioni/05-mascheramento-finto-albero.md` | Sezione aggiuntiva 5.1.bis (condizionale) |
| `sezioni/06-mensola-pura.md` | Cap. 6 modellazione a mensola |
| `sezioni/06-stralli-puntoni.md` | Cap. 6 modellazione con stralli e/o puntoni |
| `sezioni/09-verifiche-resistenza.md` | Cap. 9 verifiche SLU |
| `sezioni/10-fatica-woehler.md` | Cap. 10 verifica fatica (condizionale) |
| `sezioni/11-plinto-diretto.md` | Cap. 11 fondazione diretta |
| `sezioni/11-micropali.md` | Cap. 11 con micropali (condizionale) |
| `sezioni/11-shelter-zavorrato.md` | Cap. 11 RT su shelter (condizionale) |
| `sezioni/11-ancoraggi-chimici.md` | Cap. 11 per RT (condizionale) |
| `sezioni/12-rinforzo-raddoppio-nervature.md` | Cap. 12 rinforzo tipo 1 (condizionale) |
| `sezioni/12-rinforzo-RR-POLE.md` | Cap. 12 rinforzo tipo 2 (condizionale) |
| `sezioni/12-rinforzo-micropali.md` | Cap. 12 rinforzo tipo 3 (condizionale) |
| `sezioni/12-rinforzo-bulloneria.md` | Cap. 12 rinforzo tipo 4 (condizionale) |
| `sezioni/12-rinforzo-camicia-FRP.md` | Cap. 12 rinforzo tipo 5 (condizionale) |
| `sezioni/12-rinforzo-aggiunta-stralli.md` | Cap. 12 rinforzo tipo 6 (condizionale) |
| `sezioni/13-ante-post-operam.md` | Cap. 13 tabella confronto (condizionale) |
| `sezioni/14-asseverazione.md` | Cap. 14 asseverazione sicurezza statica |

---

## 6. Script calcolatori (`scripts/`)

| Script | Funzione | Invocato da |
|---|---|---|
| `alpha_factor.py` | Calcolo α flangia bullonata (poli 4° grado) | Cap. 9 flange intermedie |
| `quatordio_kfs.py` | Piastra base senza nervature kfs=0.45+0.12·ρ | Cap. 9 piastra base |
| `bolt_combination.py` | Verifica trazione+taglio bulloni: [FV/FV,Rd]+[Ft/(1.4·Ft,Rd)] | Cap. 9 tirafondi/flange |
| `woehler_miner.py` | Fatica: curve S-N + danno cumulativo D=Σ(ni/Ni) | Cap. 10 fatica |
| `brinch_hansen.py` | Capacità portante con fattori inclinazione | Cap. 11 fondazione |
| `rinforzo_nervature.py` | Sfruttamento post-rinforzo con 2n nervature | Cap. 12 tipo 1 |
| `micropali_portanza.py` | Portanza laterale micropalo Ø220 L=8m | Cap. 12 tipo 3 |
| `classificazione.py` | Intake → JSON classificazione 11 rami | STEP B |

---

## 7. Regole di esecuzione (MANDATORIE)

### 7.1 Sequenza obbligatoria STEP A → E
Non generare il capitolo 12 (rinforzo) prima di aver completato tutte le
verifiche SLU (STEP C → D). Se durante STEP D risulta OK, **saltare** il
capitolo 12 e passare direttamente a STEP E.

### 7.2 Dati minimi per procedere
- Codice sito operatore (es. RM00189_012, FI50137_802)
- Coordinate geografiche
- Tipologia sito (RL/RT + sub-variante)
- Geometria palo completa (numero tronchi, Ø, t, L, acciaio)
- Presenza/assenza pennone
- Mascheramento
- Sistema strutturale (inclusi stralli/puntoni/baggioli)
- Fondazione (geometria + cls + armatura + eventuali micropali)
- LC (LC1/LC2/LC3)
- Elenco antenne/parabole ANTE-operam + POST-operam
- Tipo intervento

Se manca anche uno solo → **STOP e richiesta dati** all'utente.

### 7.3 Livello di conoscenza — scelta FC
- LC1 FC=1.35 → rilievo sommario, materiali stimati da normativa d'epoca
- LC2 FC=1.20 → rilievo strumentale + campionamento materiali
- LC3 FC=1.00 → disegni esecutivi originari + collaudo + relazione geologica

Il valore FC **riduce le resistenze di calcolo**: fyd,ridotta = fyd/FC.
Documentare in Cap. 3 quali documenti sono stati visionati.

### 7.4 Gestore = Iliad o Cellnex → fatica SEMPRE
Se H_totale ≥ 25 m OPPURE presenti parabole MW OPPURE operatore ∈ {Iliad,
Cellnex} → **fatica obbligatoria** (EN 1993-1-9, Woehler classe 80 per tubo-piastra,
classe 90 per saldatura longitudinale, γM,fat=1.35).

Se Wind Tre / Vodafone / altro su palo < 25 m e senza MW → fatica opzionale.

### 7.5 Ante/Post-operam obbligatoria per upgrade/co-siting/innalzamento
Produrre tabella Cap. 13 con riga per ogni elemento strutturale e colonna ANTE
% / POST %. Includere confronto FONDAZIONE sempre.

### 7.6 Rinforzo — vincolo "post-rinforzo deve essere OK"
Al termine del progetto di rinforzo, ricalcolare TUTTI gli sfruttamenti con
la nuova configurazione. Se anche uno solo > 1.00, iterare scelta rinforzo.

### 7.7 RT con stralli → prescrizione tensiometro
Per qualsiasi RELSTA con sistema `mensola_stralli` o `mensola_stralli_puntoni`,
inserire in Cap. 14 prescrizione obbligatoria: *"Il gestore è tenuto a
verificare la pretensione dei tiranti mediante tensiometro oleostatico con
cadenza almeno semestrale e a seguito di eventi meteorologici significativi
(vento > 80 km/h sostenuto, neve > 50 cm, sisma PGA > 0.05g locale)."*

### 7.8 Pennone inclinato → clausola di esclusione
Per `pennone = inclinato_portafari`, se non sono disponibili elaborati
esecutivi del pennone stesso (molto frequente nei casi torre-faro di stadi),
**dichiarare esplicitamente** in Cap. 4.5: *"La verifica del pennone
inclinato portafari è esclusa dalla presente relazione per carenza di dati
dimensionali e materici. Si demanda al gestore della torre la fornitura
degli elaborati costruttivi ai fini di una verifica successiva."*

### 7.9 Finto albero → cp = 1.0 e area chioma
Per `mascheramento = finto_albero`:
- cp,palo = **1.0** (invece di 0.7)
- A,chioma forfait = **24 m²** alla quota baricentrica (o valore dichiarato dal produttore)
- Peso chioma = **200 kg/m²** di superficie (o valore certificato produttore)

### 7.10 Software WinStrand → annotazione ereditarietà
Se `software = winstrand`, annotare in Cap. 6.1: *"La modellazione è stata
condotta con WinStrand (ENEXSYS Srl) per continuità con il progetto ereditato
dal gestore precedente. I risultati sono stati validati per confronto con
modello semplificato analitico."*

---

## 8. Delega alle skill esistenti

La skill `relsta-unificata` **non ri-implementa** i calcoli strutturali. Delega:

| Calcolo | Skill delegata | Input | Output |
|---|---|---|---|
| Intake dati | `vs-input-dati` | utente | `input_dati.json` |
| Azioni ambientali | `vs-azioni-ambientali` | input_dati | `azioni.json` |
| Sollecitazioni | `vs-sollecitazioni` | azioni + schema | `sollecitazioni.json` |
| Schema statico | `vs-schema-statico` | input (solo RT) | `schema_statico.json` |
| Template palina RT | `vs-template-paline-rt` | (solo RT) | pre-compilato |
| Verifiche fusto | `vs-verifiche-fusto` | sollecitazioni | `verifiche_fusto.json` |
| Verifiche giunti | `vs-verifiche-giunti` | sollecitazioni | `verifiche_giunti.json` |
| Verifiche fondazione | `vs-verifiche-fondazione` | sollecitazioni | `verifiche_fondazione.json` |
| Verifiche SLE | `vs-verifiche-sle` | sollecitazioni | `verifiche_sle.json` |
| Verifiche fatica | `vs-verifiche-fatica` | azioni + geometria | `verifiche_fatica.json` |
| Redazione documento | `vs-redazione-documento` | tutti i JSON | `RELSTA.docx` |

La nuova skill **aggiunge** a questa pipeline:

- Classificazione 11 rami (`classificazione-sito.json`)
- Progetto rinforzo (`progetto_rinforzo.json` + ricalcolo iterativo)
- Sezioni condizionali (RT varianti, stralli/puntoni, mascheramento, ante/post, co-siting)
- Composizione finale DOCX con tutte le sezioni assemblate

---

## 9. Output finale

**File di output principale**:
`/sessions/<session>/mnt/RELSTA/output/RELSTA_<codice_sito>_<data>.docx`

**File di output accessori**:
- `classificazione-sito.json` — classificazione 11 rami
- `verifiche-*.json` — output delle VS-skills
- `progetto_rinforzo.json` (se NV)
- `scheda-sintesi-A4.pdf` (se operatore = Cellnex)
- `unifilare-palo.dwg` (se palo flangiato multi-tronco)
- `XLSX-capacity-check.xlsx` (tabella ante/post per Cellnex)

---

## 10. Checklist anti-omissione (GATE FINALE)

Prima di emettere il documento, verificare che:

- [ ] Classificazione sito completa su 11 rami (file JSON esistente e valido)
- [ ] Per RT: schema statico classificato (mensola / stralli / puntoni / misto)
- [ ] Per palo flangiato: tutte le flange intermedie verificate con α-factor
- [ ] Per palo H > 25m o Iliad/Cellnex: fatica eseguita (Woehler + Miner)
- [ ] Sopralzo pennone POST: confronto con geometria ANTE esplicito
- [ ] Combinazione ghiaccio per siti con parabole MW in zona neve
- [ ] Tabella ANTE/POST operam completa (se intervento ∈ {upgrade, co-siting, innalzamento})
- [ ] Per stralli: prescrizione tensiometro presente in Cap. 14
- [ ] Per finto albero: cp = 1.0 e A chioma esplicitati
- [ ] Per WinStrand: nota ereditarietà in Cap. 6.1
- [ ] Validazione indipendente (modello semplificato) presente in Cap. 6 o App.
- [ ] Asseverazione firmata da Ing. abilitato iscritto ad Albo

**Se uno qualunque è NO → bloccare output e ritornare a step mancante.**

---

## 11. Riferimenti normativi (elenco cumulato)

- **NTC 2018** — DM 17/01/2018, struttura generale SLU/SLE
- **Circ. 7/2019** — istruzioni applicative NTC 2018
- **EN 1993-1-1** — Eurocodice 3 acciaio, regole generali
- **EN 1993-1-8** — giunti bullonati e saldati
- **EN 1993-1-9** — fatica acciaio, curve Woehler
- **EN 1997-1** — Eurocodice 7 geotecnica
- **CNR-DT 207/2008** — azioni del vento sulle costruzioni
- **UNI EN ISO 1461** — zincatura a caldo
- **EOTA TR029** — progetto ancoraggi chimici
- **CNP_TS21_002** — Cellnex verifica strutture esistenti
- **LG Iliad VS v1.4** — linee guida verifica statica Iliad Italia

---

## 12. Esempi di invocazione

### 12.1 Nuova RELSTA raw land poligonale co-siting (caso tipo SI53014)
```
Utente: "Mi serve RELSTA sito SI53014_003, co-siting Iliad, palo poligonale 16
lati due tronchi H=24m+pennone 3m Ø193.7, plinto 4x4x2.5, LC3, antenne nuove
Kathrein 80010681 n°3 + parabola 0.6m"

→ Skill esegue:
  STEP A: raccolta dati mancanti (acciaio, Rck cls, dati antenne dettagliati)
  STEP B: tupla = (RL, poligonale, dritto_circolare, nessuno, mensola,
          plinto_diretto, co_siting, NESSUNO, straus7, LC3, presente)
  STEP C: delega a 9 VS-skills
  STEP D: esito OK
  STEP E: capitoli 1-11, 13 (ante/post), 14, Allegati A/B
```

### 12.2 RELSTA flangiato con rinforzo nervature (caso LU55041)
```
Utente: "RELSTA LU55041, palo tubolare flangiato 4 tronchi H=33m, nessun
pennone, NV sulle flange intermedie (α = 132.7% e 121.0%), vogliamo rinforzo
raddoppio nervature"

→ Skill esegue:
  STEP B: tupla = (RL, tubolare_flangiato, assente, nessuno, mensola,
          plinto_diretto, rinforzo, raddoppio_nervature, straus7, LC3, presente)
  STEP C: calcolo flange con formula α (poli 4° grado)
  STEP D: NV confermato
  STEP D-bis: progetto raddoppio nervature (2n nervature sfasate 360°/4n)
  Ricalcolo: sfruttamento post-rinforzo → OK (target 68-70%)
  STEP E: capitoli 1-11, 12 (rinforzo), 13, 14, App.
  → Se fondazione anche NV: aggiungere micropali Ø220 L=8m (capitolo 12 esteso)
```

### 12.3 RELSTA roof top con stralli+puntoni (caso LT032)
```
Utente: "RELSTA LT032, RT su shelter metallico zavorrato, palo flangiato 5
tronchi H=23.5m con 4 stralli TECI Ø18 pretensione 1000kg + 2 puntoni Ø139.7×7.8
ancorati a +11.2m, co-siting Iliad"

→ Skill esegue:
  STEP B: tupla = (RT_shelter, tubolare_flangiato, assente, nessuno,
          mensola_stralli_puntoni, shelter_zavorrato, co_siting, NESSUNO,
          straus7, LC3, presente)
  STEP C: delega a VS-skills + uso references/stralli-puntoni.md
          - Modellazione FEM con truss solo-trazione per stralli
          - Truss compressione con verifica instabilità EC3-1-1 per puntoni
          - Verifica shelter a ribaltamento/scorrimento
          - Verifica zavorre a ribaltamento
  STEP E: capitoli 1-11, 13, 14 + prescrizione tensiometro
          (Cap. 6 esteso con stralli+puntoni, Cap. 11 sostituito da shelter)
```

---

**Fine SKILL.md** — per dettagli operativi consultare `references/` e `templates/`.
