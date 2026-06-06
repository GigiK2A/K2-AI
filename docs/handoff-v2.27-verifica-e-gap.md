# Handoff v2.27 (Luca → Luigi) — verifica e gap

**Data**: 2026-06-04 · **Da**: Luigi + Claude operativo · **Zip**: `consegna-luigi-v2.27.zip`

## Esito: asset SOLIDI, ownership chiarita, 3 gap nei tooling

Il `CONSEGNA_LUIGI.md` chiude la decisione ownership: **"l'8e di produzione lo
costruisce Luigi"** (riga 37) + "Cosa costruisci tu: K-BOT + 8e runtime" (riga 39).
→ Il mio engine `kai-website/k2a-8e/` diventa **IL motore** (non più candidato). Luca
consegna gli **asset** (blueprint, snapshot, validazione, catalog); Luigi costruisce
e deploya il **runtime**.

## Cosa ho verificato (PASS)

| Check | Esito |
|---|---|
| 12 blueprint vs meta-schema (L1, libreria reale) | **12/12 PASS** |
| snapshot grounding | v1.0.0, 57 entries (23 normativo verbatim, 20 formula, 10 input, 4 benchmark) |
| catalog.json | 76 servizi, 15 generabili 8e, prezzo_min 19€ |
| Engine end-to-end su asset reali (LegalBoost, offline) | **PASS** — L1+L2+output-schema PASS, PDF 4064 bytes, 3 citazioni verbatim (override_locale) |

## Cosa ho integrato nell'engine

- Vendorizzati in `kai-website/k2a-8e/`: `k2a_validation/` (lib L1/L2 reale), `blueprints/` (12), `grounding/grounding-snapshot.json`, `catalog/catalog.json`, `blueprints/manifest.json`.
- Riscritto engine sui formati reali: `assets.py` (manifest+blueprint+snapshot), `validate.py` (delega a `k2a_validation`), `pipeline.py` (resolve da snapshot per tipo: normativo verbatim / formula / input / benchmark; assemble deliverable conforme a output-schema; L1+L2+output-schema), `render.py`.
- Catalogo chiuso Phase-1 = solo LegalBoost (4 service_id legali dal manifest); altri → `out_of_catalog`.

## 3 GAP nell'handoff (da Luca)

### GAP-1 — `snapshot/build_snapshot.py` MANCANTE (bloccante per resolve multi-boost)
Lo zip non lo contiene. Conteneva la funzione `manifest()` = **mapping
placeholder→boost** (quali chiavi snapshot consuma ogni boost). Le `entries` dello
snapshot NON dichiarano il boost di appartenenza (nessun campo `boost`); solo
`coverage.gaps` cita il boost per le 4 chiavi benchmark mancanti.
- **Conseguenza**: `resolver_stub.py` crasha (`FileNotFoundError`); l'engine non sa
  quali fatti risolvere per i boost diversi da LegalBoost.
- **Workaround**: `grounding/boost_placeholders.json` INTERIM, seedato solo per
  LegalBoost con le 3 chiavi note (`cc_1341`, `cc_1342`, `dlgs231_25septies`).
- **Serve da Luca**: `build_snapshot.py` o il manifest placeholder→boost completo
  (15 service_id / 12 boost).

### GAP-2 — `interfaccia-kbot-8e.md` MANCANTE
Confermato dal file `interfaccia-kbot-8e.MANCANTE.txt` nello zip (Luca non l'ha
trovato su disco). **Non bloccante**: la membrana canonica esiste già lato Luigi in
`docs/interfaccia-kbot-8e.md` (la includo io). Allinearsi su quella.

### GAP-3 — `check_parity.py` path/glob errati (cosmetico)
Default `--blueprints ../blueprints` + glob `*.boost.blueprint.json` non matchano il
layout consegnato (`blueprints/<skill>/blueprint.json`) → stampa `0/0 PASS`. Con path
corretto: **12/12 PASS**. Fix banale (una riga), i blueprint sono a posto.

## Residuo dichiarato da Luca (non bloccante)
4 dataset benchmark `da_strutturare` (coverage 53/57): `benchmark_settore`,
`multipli_ev`, `revpar_zona`, `keyword_dataset`. In arrivo snapshot v2.28. I
deliverable si generano comunque (benchmark non-bloccante in resolve).

## Prossimi passi
1. **Luca**: mandare `build_snapshot.py` / manifest placeholder→boost (sblocca GAP-1).
2. **Luigi**: con ANTHROPIC_API_KEY → filiera Sonnet reale (oggi offline template); il verbatim normativo entra nella prosa.
3. **Luigi**: sostituire `kbot/backend/app/data/catalog.json` (interim) con il catalog reale di Luca + overlay `tag_pillar_sito` (scenario C).
4. **Luigi**: client 8e nel K-BOT (`engine.py`) + endpoint deliverables; swap mock→engine reale.
5. **Gate pre-vendita**: snapshot reale conferma articoli `da confermare` (override Cod.Civ.).
