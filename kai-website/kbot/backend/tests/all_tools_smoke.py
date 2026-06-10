"""Smoke di TUTTI i tool compute esposti: costruisce un input campione dallo schema,
chiama il tool, e categorizza: OK (gira), INPUT (rifiuta sample = tool sano),
CRASH (eccezione di codice = possibile bug). Zero crediti."""
import sys, json, traceback
sys.path.insert(0,'.'); sys.path.insert(0,'vendor')
from pydantic import BaseModel, ValidationError
from app.api.compute import _REGISTRY

def sample(schema, defs):
    if "$ref" in schema:
        schema = defs.get(schema["$ref"].split("/")[-1], {})
    if "default" in schema: return schema["default"]
    if "enum" in schema: return schema["enum"][0]
    if "const" in schema: return schema["const"]
    t = schema.get("type")
    if isinstance(t,list): t=[x for x in t if x!="null"][0] if [x for x in t if x!="null"] else "string"
    if "anyOf" in schema or "oneOf" in schema:
        opts=[o for o in schema.get("anyOf",schema.get("oneOf",[])) if o.get("type")!="null"]
        return sample(opts[0], defs) if opts else None
    if t=="object":
        props=schema.get("properties",{}); req=set(schema.get("required",list(props)))
        return {k:sample(v,defs) for k,v in props.items() if k in req}
    if t=="array":
        it=schema.get("items",{"type":"number"}); n=max(1,schema.get("minItems",1))
        return [sample(it,defs) for _ in range(n)]
    if t in ("integer","number"):
        v=schema.get("minimum", schema.get("exclusiveMinimum",1) or 1); return (v+1) if t=="integer" else float(v)+1.0
    if t=="boolean": return False
    if t=="string":
        if schema.get("format")=="date": return "2025-01-01"
        return schema.get("examples",["x"])[0] if schema.get("examples") else "test"
    return None

from collections import Counter, defaultdict
cat=Counter(); crashes=[]
for tid, m in sorted(_REGISTRY.items()):
    model=m["input_model"]
    js=model.model_json_schema(); defs=js.get("$defs",{})
    try:
        inp=model(**sample(js, defs))
    except ValidationError:
        cat["INPUT(sano)"]+=1; continue
    except Exception as e:
        cat["SAMPLE-ERR"]+=1; continue
    try:
        m["fn"](inp); cat["OK"]+=1
    except (ValidationError, ValueError) as e:
        cat["INPUT(sano)"]+=1
    except Exception as e:
        cat["CRASH"]+=1; crashes.append((tid, f"{type(e).__name__}: {str(e)[:80]}"))
print("=== ESITO SMOKE 125 TOOL ===")
for k,v in cat.most_common(): print(f"  {v:3}  {k}")
print(f"\n=== CRASH (da indagare): {len(crashes)} ===")
for tid,err in crashes[:30]: print(f"  {tid:48} {err}")
