"""Debug test — resolve + L1 su TUTTI gli 11 boost (non solo LegalBoost).

Valida i path di resolve oltre il `normativo`: formula, input, benchmark.
Per ogni boost: carica blueprint + output-schema, risolve le chiavi dichiarate
dal manifest, verifica che nessun placeholder NON-benchmark resti irrisolto, e
che L1 (validate_blueprint) passi. I benchmark `da_strutturare` sono ammessi
non risolti (non bloccanti).
"""
from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from app import assets, validate, pipeline  # noqa: E402

# input form di esempio per i campi in_* (così il path input risolve)
SAMPLE_FORM = {
    "ragione_sociale": "Acme SRL", "settore": "manifatturiero", "regime": "ordinario",
    "bilanci": "{...}", "competitor": "X,Y", "url": "https://acme.it", "mese": "2026-05",
    "struttura": "hotel 40 camere", "edificio": "capannone", "intervento": "ristrutturazione",
    "cantiere": "cantiere edile",
}

# campo_form mancante nelle entry input → la resolve usa e.get("campo_form");
# passiamo un form generoso. Mappiamo anche i nomi chiave→form quando il
# campo_form non è presente.
BENCH_OK_UNRESOLVED = {"revpar_zona", "keyword_dataset"}  # da_strutturare noti


def main() -> int:
    man = assets.manifest()
    skills = sorted({v["skill"] for v in man.values()})
    print(f"Boost (skill) nel manifest: {len(skills)}")
    failures = []

    for skill in skills:
        bp = assets.load_blueprint(skill)
        keys = assets.placeholders_for(skill)
        if not bp:
            failures.append((skill, "blueprint mancante"))
            continue
        if not keys:
            print(f"  {skill:30} ⚠ nessuna chiave nel manifest placeholder")
            continue

        # resolve
        try:
            facts, citazioni = pipeline.resolve(skill, SAMPLE_FORM)
        except pipeline.Refuse as r:
            # accetta refuse solo se è un benchmark noto da_strutturare
            if r.reason == "unresolvable_placeholder" and any(b in r.message for b in BENCH_OK_UNRESOLVED):
                print(f"  {skill:30} ⚠ benchmark da_strutturare non risolto (atteso): {r.message}")
                facts, citazioni = {}, []
            else:
                failures.append((skill, f"resolve refuse: {r.reason} {r.message}"))
                continue

        # conta tipi risolti
        from app import assets as A
        snap = A.load_snapshot().get("entries", {})
        tipi = {}
        for k in keys:
            t = snap.get(k, {}).get("tipo", "MISSING")
            tipi[t] = tipi.get(t, 0) + 1

        # L1
        r1 = validate.l1(bp)
        l1_ok = r1["pass"]
        if not l1_ok:
            failures.append((skill, f"L1 FAIL: {r1.get('errors')}"))

        status = "OK" if l1_ok else "FAIL"
        print(f"  {skill:30} L1 {status} | chiavi {len(keys)} tipi {tipi} | citazioni {len(citazioni)}")

    print()
    if failures:
        print("FALLIMENTI:")
        for s, m in failures:
            print(f"  - {s}: {m}")
        return 1
    print("TUTTI GLI 11 BOOST: resolve + L1 OK ✅")
    return 0


if __name__ == "__main__":
    sys.exit(main())
