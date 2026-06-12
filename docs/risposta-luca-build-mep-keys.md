# Per Luca — chiavi Build/MEP + Build flaggato Salva-Casa + nota snapshot Fisco

Confermo la tua correzione (Build ≠ MEP). Ti do le chiavi e ho già esteso il gate.

## 1. Le 4 chiavi MEP — confermate, stabili
`dm37_5`, `dm37_6`, `dm37_7`, `dm37_15` = **D.M. 37/2008 art. 5 / 6 / 7 / 15**
(Progettazione impianti · Realizzazione e installazione · Dichiarazione di conformità · Sanzioni).
- fonte `override_locale`, vigenza **2008-03-27**.
- D.M. 37/2008 non riformato → **stabile**. QA di fatto chiusa (gate hard OK su `dm37_7`). Confermo i 4 keys come da tua ipotesi.

## 2. Le 4 chiavi Build — e hai ragione, è QA vera
`dpr380_3`, `dpr380_10`, `dpr380_22`, `dpr380_24` = **DPR 380/2001 art. 3 / 10 / 22 / 24**
(Definizioni interventi · Permesso di costruire · SCIA · Agibilità).
- fonte `akn_bulk_xml`, vigenza "consolidato (KB normattiva)".
- **Verificato sul verbatim**: NESSUN marker Salva-Casa (`69/2024`, `105/2024`, `36-bis` tutti assenti). E art.3 (definizioni) e art.24 (agibilità) sono proprio tra quelli toccati dal D.L.69/2024. → **il verbatim Build può essere pre-riforma**, esattamente il caso "groundato ≠ vigente".
- → **passo a te per QA via MCP** contro la KB: art. 3, 10, 22, 24 DPR 380.

## 3. Freshness-gate esteso (il tuo reminder) — fatto
Ho aggiunto Build e MEP a `freshness_rules.json`:
- `dpr380_3` e `dpr380_24` → **SOFT warn** ("nessuna evidenza Salva-Casa, QA via MCP pendente"). Non bloccano il pilota, ma restano segnalati finché non confermi/rinfreschi.
- `dm37_7` → hard OK (stabile).
- Gate ora 8/10 + 2 soft (Build). In CI.

Quando rinfreschi Build post-Salva-Casa, i marker compaiono e i due soft si chiudono da soli.

**Sul reminder "confrontare la data CONSOLIDATED dell'MCP"**: giusto, è l'evoluzione del gate. Offline non ho l'MCP, quindi oggi uso i marker testuali. Quando il subprocess MCP è stabile, aggiungiamo il confronto data-consolidamento per-entry (te lo cablo: mi serve solo il campo `CONSOLIDATED/AAAAMMGG` che l'MCP espone, da scrivere nello snapshot in fase di build).

## 4. ⚠️ Nota importante sul Fisco — possibile disallineamento snapshot
Tu dici ancora "tuir_11 e ravvedimento_13 erano stale → refresh PRIMA". Ma **nello snapshot committato che leggo io sono GIÀ current**:
- `tuir_11`: `a) fino a 28.000, 23%; b) … ((33%)); c) oltre 50.000, 43%` (L.199/2025).
- `ravvedimento_13`: ha b-bis…b-quater + footer "AGGIORNAMENTO (30) D.Lgs. 14 giugno 2024, n. 87 … dal 1° settembre 2024".

Quindi o il tuo ambiente di build ha uno **snapshot più vecchio** del committato, o ne esistono **due copie**. Prima di qualsiasi refresh, **riconciliamo quale snapshot è canonico** (quello in `kai-website/k2a-8e/grounding/grounding-snapshot.json`, version + generated_at): non vorrei che rinfreschi su una copia vecchia mentre quella in repo è già a posto. Mandami `snapshot_version` + `generated_at` del tuo, confronto coi miei.

## Net
- **MEP**: chiuso (stabile).
- **Build**: 4 keys passate, QA via MCP a te (gate lo tiene segnalato).
- **Fisco**: verifica quale snapshot è canonico prima di rinfrescare — il mio è già current.
- **MCP instabile**: ok, non tocca il pilota (runtime risolve da snapshot statico).
- **Pilota Legal+Fisco+Safety**: confermato pronto.
