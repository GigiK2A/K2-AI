#!/usr/bin/env bash
# Sincronizza gli asset del motore 8e da inglucarossi73/k2a-skills (fonte di verità).
# Sostituisce la copia manuale dello zip. Richiede accesso gh al repo privato.
#
# Uso:
#   scripts/sync_assets.sh            # clona shallow in /tmp e copia
#   K2A_SKILLS_DIR=/path scripts/sync_assets.sh   # usa un clone locale esistente
#
# Aggiorna: blueprints/, grounding/grounding-snapshot.json, catalog/catalog.json,
#           k2a_validation/, grounding/boost_placeholders.json (da build_snapshot.manifest()).
set -euo pipefail

HERE="$(cd "$(dirname "$0")/.." && pwd)"
SRC="${K2A_SKILLS_DIR:-}"

if [[ -z "$SRC" ]]; then
  TMP="$(mktemp -d)"
  echo "→ clono k2a-skills (shallow) in $TMP"
  gh repo clone inglucarossi73/k2a-skills "$TMP/k2a-skills" -- --depth 1 >/dev/null 2>&1
  SRC="$TMP/k2a-skills"
fi

echo "→ sorgente: $SRC"
[[ -f "$SRC/snapshot/grounding-snapshot.json" ]] || { echo "ERRORE: snapshot non trovato"; exit 1; }

# 1) snapshot + catalog
cp "$SRC/snapshot/grounding-snapshot.json" "$HERE/grounding/grounding-snapshot.json"
cp "$SRC/snapshot/catalog.json"            "$HERE/catalog/catalog.json"

# 2) blueprints + libreria validazione (dal pacchetto handoff)
rsync -a --delete "$SRC/handoff-8e/blueprints/"     "$HERE/blueprints/"
rsync -a --delete "$SRC/handoff-8e/k2a_validation/" "$HERE/k2a_validation/"

# 3) manifest placeholder→boost (da build_snapshot.manifest())
python3 - "$SRC" "$HERE" <<'PY'
import importlib.util, json, sys
src, here = sys.argv[1], sys.argv[2]
spec = importlib.util.spec_from_file_location("bs", f"{src}/snapshot/build_snapshot.py")
bs = importlib.util.module_from_spec(spec); spec.loader.exec_module(bs)
from collections import defaultdict
byb = defaultdict(list)
for e in bs.manifest():
    byb[e["boost"]].append(e["key"])
out = {"_nota": "Generato da sync_assets.sh (k2a-skills/snapshot/build_snapshot.py manifest()).",
       "_fonte": "inglucarossi73/k2a-skills"}
for b in sorted(byb):
    out[b] = sorted(byb[b])
json.dump(out, open(f"{here}/grounding/boost_placeholders.json", "w"), ensure_ascii=False, indent=2)
print(f"  boost_placeholders: {len(byb)} boost")
PY

# 4) pulizia AppleDouble
find "$HERE/blueprints" "$HERE/k2a_validation" -name "._*" -delete 2>/dev/null || true

echo "→ verifiche:"
python3 -c "import json; d=json.load(open('$HERE/grounding/grounding-snapshot.json')); print('  snapshot:', d['snapshot_version'], d['coverage']['resolved'],'/',d['coverage']['declared'])"
python3 -c "import json; d=json.load(open('$HERE/catalog/catalog.json')); print('  catalog:', d['catalog_version'], d['n_services'],'servizi')"
echo "✓ sync completato. Esegui 'tests/smoke_test.py' per validare."
