# Patch per Luca — `build_catalog.py` perde abbonamenti/crediti

**Repo:** `inglucarossi73/k2a-skills` · **File:** `snapshot/build_catalog.py` · **Funzione:** `build()` (return finale).

## Problema
Il generatore legge `catalogo_documenti.json` (che contiene `abbonamenti`, `crediti`, `percorsi`, `mapping_tag_to_servizi`) ma nel dict di output emette **solo `services`**. Quindi il `catalog.json` generato ha `abbonamenti: []`/assenti → il consumer (kbot) vede solo pay-per-use e il layer abbonamenti/crediti resta morto.

## Fix (pass-through dalla fonte)
Nel `return` di `build()`, aggiungere 4 campi e bumpare la versione:

```diff
     return {
-        "catalog_version": "1.0.0",
+        "catalog_version": "1.1.0",
         "generated_at": os.environ.get("SNAPSHOT_TS", "BUILD_TS_PLACEHOLDER"),
         "fonte": "k2a-catalogo (catalogo_documenti.json)",
         "prezzo_minimo_eur": cat.get("prezzo_minimo_servizio_eur"),
         "n_services": len(services),
         "n_generabili_8e": n_8e,
         "services": services,
+        # Modello economico: PASS-THROUGH dalla fonte (prima venivano persi).
+        "abbonamenti": cat.get("abbonamenti", {}),
+        "crediti": cat.get("crediti", {}),
+        "percorsi": cat.get("percorsi", []),
+        "mapping_tag_to_servizi": cat.get("mapping_tag_to_servizi", {}),
     }
```

## Verificato
Rigenerato in locale: `catalog v1.1.0`, `n_services=81`, `generabili_8e=15` (invariati), e ora:
- `abbonamenti.piani` = free / pro / business
- `crediti` = 3 pacchetti, `valore_credito_eur=1`
- `percorsi`, `mapping_tag_to_servizi` presenti

## Cosa fare
1. Applica la patch a `snapshot/build_catalog.py`.
2. Rigenera: `python3 snapshot/build_catalog.py --catalogo <path catalogo_documenti.json> --out snapshot/catalog.json`.
3. Commit del nuovo `catalog.json` (v1.1.0).
4. Lato kbot: `scripts/sync_assets.sh` lo porta da noi e il layer pagamenti legge il modello reale.

> Non l'ho pushato io: la scrittura cross-repo è bloccata dal mio guardrail. Applica tu (1 minuto) o autorizzami a fare la PR.
