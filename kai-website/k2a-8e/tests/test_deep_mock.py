"""Esercita generate_deliverable_deep END-TO-END con un client Anthropic FINTO
(zero crediti). Verifica il percorso nuovo per-sezione che offline non gira mai:
parse risposta, validazione sotto-schema, refuse su sezione required invalida,
validazione finale dell'intero deliverable, su TUTTI gli output-schema generici.

Il fake client legge il nome sezione dal prompt, costruisce un campione conforme
al sotto-schema e lo restituisce come JSON → simula un Sonnet "bravo". Un secondo
fake restituisce spazzatura per provare il refuse.
"""
from __future__ import annotations

import json
import re
import sys
import types
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from jsonschema import Draft202012Validator  # noqa: E402

from app import assets, llm  # noqa: E402


def _pattern_value(pat: str) -> str:
    """Valore minimo che soddisfa i pattern usati negli schemi (P.IVA, YYYY-MM…)."""
    table = {
        r"^\d{11}$": "12345678901",
        r"^\d{4}-\d{2}$": "2026-06",
        r"^\d{4}-\d{2}-\d{2}$": "2026-06-08",
    }
    if pat in table:
        return table[pat]
    # fallback: solo cifre se il pattern è di sole \d, altrimenti testo
    return "0000000000" if "\\d" in pat else "esempio"


def sample(schema: dict, root: dict | None = None):
    """Campione conforme al (sotto)schema: risolve $ref, rispetta type/enum/pattern/min/max."""
    root = root or schema
    if "$ref" in schema:
        ref = schema["$ref"]
        if ref.startswith("#/$defs/"):
            schema = root.get("$defs", {}).get(ref.split("/")[-1], {})
    t = schema.get("type")
    if isinstance(t, list):
        t = t[0]
    if "enum" in schema:
        return schema["enum"][0]
    if t == "object":
        props = schema.get("properties", {})
        return {k: sample(v, root) for k, v in props.items()}
    if t == "array":
        it = schema.get("items", {"type": "string"})
        n = 2
        if "minItems" in schema:
            n = max(n, schema["minItems"])
        if "maxItems" in schema:
            n = min(n, schema["maxItems"])
        return [sample(it, root) for _ in range(n)]
    if t in ("integer", "number"):
        v = 62
        if "minimum" in schema:
            v = max(v, schema["minimum"])
        if "maximum" in schema:
            v = min(v, schema["maximum"])
        return v
    if t == "boolean":
        return True
    if t == "string":
        if "pattern" in schema:
            return _pattern_value(schema["pattern"])
        s = "Analisi approfondita di esempio per la sezione, su misura per il cliente."
        if "maxLength" in schema:
            s = s[: schema["maxLength"]]
        if "minLength" in schema and len(s) < schema["minLength"]:
            s = s + "x" * (schema["minLength"] - len(s))
        return s
    return "n/d"


class _Block:
    def __init__(self, text):
        self.type = "text"
        self.text = text


class _Usage:
    input_tokens = 100
    output_tokens = 800
    cache_read_input_tokens = 0


class _Resp:
    def __init__(self, text):
        self.content = [_Block(text)]
        self.usage = _Usage()
        self.stop_reason = "end_turn"


def _section_name(user: str) -> str:
    m = re.search(r"sezione «([^»]+)»", user)
    return m.group(1) if m else ""


def _install_fake(make_text):
    """Inietta un modulo 'anthropic' finto. make_text(name, sub)->str."""
    fake = types.ModuleType("anthropic")

    class _Stream:
        def __init__(self, resp):
            self._r = resp

        def __enter__(self):
            return self

        def __exit__(self, *a):
            return False

        def get_final_message(self):
            return self._r

    class _Messages:
        def _resp_for(self, kw):
            user = kw["messages"][0]["content"]
            name = _section_name(user)
            sub = fake._SCHEMA["properties"].get(name, {})
            return _Resp(make_text(name, sub))

        def create(self, **kw):
            return self._resp_for(kw)

        def stream(self, **kw):
            return _Stream(self._resp_for(kw))

    class _Anthropic:
        def __init__(self, api_key=None):
            self.messages = _Messages()

    fake.Anthropic = _Anthropic
    fake._SCHEMA = None
    sys.modules["anthropic"] = fake
    return fake


def main() -> int:
    llm.ANTHROPIC_API_KEY = "test-fake-key"  # attiva il ramo "online"

    man = assets.manifest()
    skills = sorted({v["skill"] for v in man.values()})
    generic = [s for s in skills if s not in llm.__dict__.get("VOCI_SHAPE_SKILLS", set())]
    # VOCI_SHAPE_SKILLS vive in settings; deep gira sui generici (tutti tranne LegalBoost)
    from app.settings import VOCI_SHAPE_SKILLS
    generic = [s for s in skills if s not in VOCI_SHAPE_SKILLS]

    bp_stub = {"pacchetto": {"nome_commerciale": "Boost K2-AI"}}
    facts = {"f1": {"tipo": "normativo", "valore": "Art. 13 GDPR", "fonte": "normattiva", "vigenza": "2026"}}
    inputs = {"ragione_sociale": "Acme S.r.l.", "settore": "manifatturiero", "dipendenti": 18}

    # --- 1) HAPPY PATH: fake bravo → deliverable conforme, assembly=deep ---
    fake = _install_fake(lambda name, sub: json.dumps(sample(sub, fake._SCHEMA), ensure_ascii=False))
    ok, fail = 0, []
    for skill in generic:
        osch = assets.load_output_schema(skill)
        if not osch:
            fail.append((skill, "no output-schema"))
            continue
        fake._SCHEMA = osch
        result, meta = llm.generate_deliverable_deep(osch, bp_stub, facts, inputs)
        if result is None:
            fail.append((skill, f"refuse inatteso: {meta}"))
            continue
        errs = list(Draft202012Validator(osch).iter_errors(result))
        if errs:
            fail.append((skill, f"output non conforme: {errs[0].message[:80]}"))
            continue
        if meta.get("assembly") != "deep":
            fail.append((skill, f"assembly={meta.get('assembly')}"))
            continue
        ok += 1
        print(f"  {skill:34} OK  sezioni={meta.get('sezioni')} tok={meta.get('output_tokens')}")

    print(f"\nDEEP happy-path: {ok}/{len(generic)} conformi")

    # --- 2) NO-DEAD-END: fake che rompe una sezione required → NON deve dare vicolo cieco.
    # Contratto (vedi llm.generate_deliverable_deep, righe ~570-583): una sezione required
    # non valida NON rifiuta più a questo livello — viene messa a placeholder schema-valido
    # e MARCATA in `meta["degraded_sections"]` (report preliminare), e il refuse vero vive
    # A VALLE (gate grounding/quality della pipeline, rafforzato per legale/fisco e numeri
    # hard-financial). Il fallimento da evitare è la consegna PULITA di spazzatura NON
    # marcata: qui verifichiamo che ogni sezione garbage sia o rifiutata (result None) o
    # segnalata come degradata.
    degrade_ok = 0
    degrade_tot = 0
    fake2 = _install_fake(lambda name, sub: "questo non è JSON conforme {{{")
    for skill in generic:
        osch = assets.load_output_schema(skill)
        if not osch:
            continue
        req = osch.get("required", list(osch.get("properties", {})))
        # serve almeno una sezione required che NON sia meta/metadata
        req_non_meta = [r for r in req if r not in ("meta", "metadata")]
        if not req_non_meta:
            continue
        degrade_tot += 1
        fake2._SCHEMA = osch
        result, meta = llm.generate_deliverable_deep(osch, bp_stub, facts, inputs)
        degraded = set((meta or {}).get("degraded_sections") or [])
        # Corretto: o rifiuta (result None), o consegna un preliminare con ALMENO una
        # sezione marcata degradata. Le sezioni deterministiche (binder/meta) restano
        # valide anche con LLM garbage: legittimo, non è un dead-end. Il fallimento da
        # evitare è la consegna PULITA con degraded_sections vuoto = garbage non marcata.
        if result is None or degraded:
            degrade_ok += 1
        else:
            print(f"  NO-DEAD-END FAIL {skill}: consegnato senza marcare alcuna sezione degradata")

    print(f"NO-DEAD-END su sezione invalida: {degrade_ok}/{degrade_tot} gestiti correttamente")

    # --- 3) meta compilato deterministico senza LLM ---
    osch = assets.load_output_schema(generic[0])
    meta_ok = True
    if "meta" in osch.get("properties", {}) or "metadata" in osch.get("properties", {}):
        # reinstalla il fake "bravo" (il refuse-loop ha lasciato installato fake2)
        fake = _install_fake(lambda name, sub: json.dumps(sample(sub, fake._SCHEMA), ensure_ascii=False))
        fake._SCHEMA = osch
        result, _ = llm.generate_deliverable_deep(osch, bp_stub, facts, inputs)
        if result is None:
            meta_ok = False
            print(f"meta deterministico ({generic[0]}): refuse inatteso")
        else:
            mkey = "meta" if "meta" in osch["properties"] else "metadata"
            blob = json.dumps(result.get(mkey, {}), ensure_ascii=False)
            meta_ok = bool("Acme" in blob or result.get(mkey))
            print(f"meta deterministico ({generic[0]}): {result.get(mkey)}")

    bad = bool(fail) or degrade_ok != degrade_tot or ok != len(generic) or not meta_ok
    if fail:
        print("\nFALLIMENTI happy-path:")
        for s, e in fail:
            print("  -", s, e)
    print("\n" + ("DEEP-MOCK TEST PASS" if not bad else "DEEP-MOCK TEST FAIL"))
    return 1 if bad else 0


if __name__ == "__main__":
    sys.exit(main())
