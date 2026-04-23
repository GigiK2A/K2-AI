# Convenzione ANTE/POST-OPERAM — RELSTA

Ogni verifica statica di un palo TLC esistente (TC = To Confirm) deve esplicitare **due configurazioni** e confrontarle: ANTE-OPERAM (stato attuale) e POST-OPERAM (stato di progetto, dopo intervento).

Questa convenzione è richiesta esplicitamente da iliad (LG VS v1.4 §6) e Cellnex (CNP_TS21_002).

---

## Definizioni

**ANTE-OPERAM:**
- Configurazione del palo come rilevato al sopralluogo
- Include tutte le antenne/apparati esistenti di tutti gli operatori co-sitanti (iliad + WindTre + Vodafone + Cellnex-others)
- Include mascheramenti esistenti
- Include rinforzi già installati
- Carichi sismici e vento calcolati con LC attuale (LC1 tipicamente se poche informazioni)

**POST-OPERAM:**
- Configurazione di progetto dopo l'intervento in corso
- Tipiche operazioni:
  - Aggiunta antenne nuovo operatore (co-siting)
  - Aggiunta/rimozione/sostituzione antenne operatore esistente
  - Installazione mascheramento
  - Installazione rinforzo strutturale
  - Installazione stralli/puntoni
- Rappresenta lo **stato futuro permanente** dopo l'intervento

---

## Tabella ante/post-operam obbligatoria

La RELSTA deve contenere una **tabella comparativa** dei parametri di verifica ANTE e POST:

### Schema tabella standard

| Parametro | ANTE-OPERAM | POST-OPERAM | Δ |
|---|---|---|---|
| **Geometria palo** | | | |
| Altezza palo fuori terra | H_ante | H_post | ΔH |
| Sopralzo pennone | n.a. | L_pennone | +L |
| **Antenne per operatore** | | | |
| Iliad: numero antenne | n_ante | n_post | Δn |
| Iliad: peso totale [kg] | W_ante | W_post | ΔW |
| Iliad: SEV totale [m²] | A_ante | A_post | ΔA |
| WindTre: numero | ... | ... | ... |
| Vodafone: numero | ... | ... | ... |
| **Parametri aerodinamici** | | | |
| Coefficiente c_p palo | 0.7 | 0.7 (o 1.0 se finto albero) | Δc_p |
| Area chioma [m²] | n.a. / A_ante | A_post | ΔA |
| **Azioni** | | | |
| Momento alla base SLU [kN·m] | M_ante | M_post | ΔM |
| Taglio alla base SLU [kN] | V_ante | V_post | ΔV |
| **Sfruttamenti sezioni critiche** | | | |
| Tronco 1 (base) η_VM | η_ante | η_post | Δη |
| Tronco 1 η_instab | η_ante | η_post | Δη |
| Flangia 1 η_bulloni | η_ante | η_post | Δη |
| Piastra di base η_flessione | η_ante | η_post | Δη |
| Fondazione α_ribaltamento | α_ante | α_post | Δα |
| **Esito complessivo** | OK / NO | OK / NO | — |

### Regole di compilazione

- **Tutti i valori numerici** devono essere effettivamente calcolati (NON scritti a mano da stime)
- Il Δ è puramente informativo (utile in caso di deliberato confronto impatto)
- Se la colonna POST ha valori peggiori di ANTE e **l'esito è OK**, il palo tollera bene l'intervento
- Se la colonna POST ha valori peggiori di ANTE e **l'esito è NO**, è necessario rinforzo

---

## Scenari ricorrenti

### Scenario A — Co-siting neutro

- Aggiunta di un nuovo operatore senza rimozione di altri
- ANTE: configurazione con 2-3 operatori esistenti, OK
- POST: configurazione con +1 operatore, deve rimanere OK
- Tipicamente richiede **rinforzo leggero** (R1 fasciatura, R2 nervature)

### Scenario B — Refarming (swap antenne)

- Sostituzione antenne esistenti con antenne di nuova generazione (spesso più grandi/pesanti per 5G)
- ANTE: configurazione originaria
- POST: configurazione refreshed
- Tipicamente **Δ peso = +20-40 kg**, **Δ SEV = +1-3 m²** per operatore

### Scenario C — Rinforzo con aumento mascheramento

- Aggiunta mascheramento finto albero + nuove antenne
- ANTE: palo nudo con antenne originarie
- POST: palo mascherato con antenne di progetto + CHIOMA (impatto aerodinamico)
- Tipicamente richiede **doppio rinforzo**: strutturale + verifica portanza fondazione

### Scenario D — Dismissione parziale

- Rimozione di un operatore dal palo (cessazione contratto)
- ANTE: configurazione congestionata
- POST: configurazione snellita
- Ideale dal punto di vista strutturale — nessun rinforzo necessario
- CRITICO solo in caso di rilascio di ancoraggi strallo / puntoni (da verificare)

### Scenario E — Rinforzo con installazione struttura ibrida

- Introduzione stralli / puntoni / baggioli
- ANTE: palo come pura mensola
- POST: palo multi-vincolato
- **Cambia schema statico** → modello FEM da rifare completamente
- Tipicamente tipico per interventi RT

---

## Criticità ricorrenti nel confronto ANTE/POST

1. **Mancanza dati ANTE**: se il palo non ha documentazione originaria, l'analisi ANTE è una **ricostruzione** (spesso approssimata) che richiede Livello di Conoscenza LC1 (FC = 1.35)
2. **Divergenza rilievo-documentazione**: la documentazione dice 24 antenne, il rilievo ne trova 28 — usare sempre il RILIEVO come dato principale
3. **Variazione azione sismica**: se il sito ha aggiornato la microzonazione sismica, POST può essere più gravoso anche senza modifiche fisiche al palo
4. **Aggiornamento norma**: se è uscita una norma più severa fra ANTE (esistente) e POST (progetto), la verifica POST può risultare più sfavorevole

---

## Prescrizioni in RELSTA

**Testo standard da includere:**

> "La presente verifica statica confronta la configurazione ANTE-OPERAM (stato di fatto rilevato al sopralluogo del [DATA]) con la configurazione POST-OPERAM (stato di progetto dopo l'installazione delle modifiche descritte al § X). Entrambe le configurazioni sono state calcolate con analisi strutturale completa (azioni ambientali, combinazioni SLU/SLE, verifiche EN 1993), applicando al palo esistente il Fattore di Confidenza FC = 1.20 (Livello di Conoscenza LC2) giustificato dalla disponibilità della documentazione originaria + prove di carico / indagini in sito."

**Tabella comparativa:** deve comparire obbligatoriamente nel cap. 8 o equivalente del template RELSTA.

---

## Verifiche di fatica ANTE/POST

La verifica a fatica (Woehler + Palmgren-Miner) richiede **distinzione fra ANTE e POST:**
- ANTE: danno accumulato fino al momento dell'intervento (stimato dalla storia del sito)
- POST: danno residuo + nuovo ciclico di progetto per la vita utile residua

**Vita utile residua tipica:**
- Palo esistente integrato con rinforzo: 30 anni da progetto (vita utile "rinforzo = nuova")
- Palo esistente in buono stato senza rinforzo: vita residua = 50 anni - età attuale

---

## File tracciabilità

Per ogni RELSTA produrre (nell'archivio di progetto):
1. **Tabella ANTE/POST** esportata come XLSX separato (allegato)
2. **Due modelli FEM** ANTE e POST archiviati (per eventuali future verifiche)
3. **Foto ANTE (sopralluogo)** e foto POST (a intervento completato)

Questo consente di rifare velocemente la verifica se in futuro arriva un nuovo operatore/refarming.

---

*La distinzione ANTE/POST è una scelta metodologica fondamentale che rende la RELSTA **rintracciabile e riutilizzabile** nelle successive iterazioni di vita del sito.*
