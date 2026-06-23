"""Layer 1 — LLM Classifier (Tappa 3).

Trasforma l'input naturale dell'utente in JSON conforme allo schema deterministico
della tipologia (sezioni A–E). NON contiene logica di calcolo, NON invoca tool MCP:
SOLO classificazione/estrazione.

LLM: gemini-2.5-flash via SDK **google-genai** (lo stesso usato da
`scripts/ocr_gemini.py` / `k2a_norme_tecniche.ocr`, coerente con Sessione 16).
La chiave è letta da GOOGLE_API_KEY/GEMINI_API_KEY (env) con fallback al `.env`
del repo norme-tecniche (come gli altri moduli K2A).

Mock-friendly: il client può essere iniettato (`client=`) per i test offline.
"""
from __future__ import annotations

import json
import os
from dataclasses import dataclass, field
from importlib import resources
from pathlib import Path

from jsonschema import Draft202012Validator

DEFAULT_MODEL = "gemini-2.5-flash"
_DEFAULT_NORME_ENV = "/Users/lucarossi/Code/k2a-mcp/k2a-mcp-norme-tecniche/.env"


class ClassificationError(Exception):
    """Errore irrecuperabile in classificazione LLM."""


def _resolve_ref(node: dict, defs: dict) -> dict:
    """Risolve un eventuale $ref locale (#/$defs/Nome)."""
    if isinstance(node, dict) and "$ref" in node:
        name = node["$ref"].split("/")[-1]
        return defs.get(name, {})
    return node if isinstance(node, dict) else {}


def _is_campobase(node: dict) -> bool:
    """Vero se lo schema (risolto) è un CampoBase: properties con valore+stato."""
    props = node.get("properties", {})
    return "valore" in props and "stato" in props


def _default_for_schema(node: dict, defs: dict):
    """Valore di default conforme per un campo required OMESSO dall'LLM.

    CampoBase → stub RICHIESTO; array → []; oggetto → ricorsione sui required;
    const → costante; scalari → default neutro per tipo. Permette di iniettare i
    campi obbligatori che il modello ha dimenticato, mantenendo il JSON conforme.
    """
    node = _resolve_ref(node, defs)
    if "const" in node:
        return node["const"]
    if _is_campobase(node):
        return {"valore": None, "stato": "RICHIESTO", "fonte": "default_generato",
                "norma_ref": None, "review_richiesta": True}
    t = node.get("type")
    if t == "array":
        return []
    if t == "object" or "properties" in node:
        props = node.get("properties", {})
        out = {}
        for k in node.get("required", []):
            if k in props:
                out[k] = _default_for_schema(props[k], defs)
        return out
    if t == "string":
        enum = node.get("enum")
        return enum[0] if enum else ""
    if t in ("number", "integer"):
        return 0
    if t == "boolean":
        return False
    return None


def _coerce_to_schema(value, node: dict, defs: dict):
    """Riconcilia l'output LLM verso lo schema PRIMA della validazione.

    Corregge i drift tipici del classificatore quando il prompt impone
    "ogni campo è un CampoBase" ma lo schema mescola CampoBase, array semplici
    e oggetti strutturali (es. ``asseverazione`` con ``const``):
    - applica i valori ``const`` (firmata=false, modalita="validation");
    - sciglie i CampoBase erroneamente avvolti attorno ad array/oggetti strutturali;
    - rimuove le proprietà non ammesse quando ``additionalProperties: false``.
    Deterministico, idempotente, testabile offline.
    """
    node = _resolve_ref(node, defs)
    if not node:
        return value
    if "const" in node:
        return node["const"]

    t = node.get("type")

    # CampoBase atteso: lascia se già conforme, altrimenti avvolge lo scalare.
    if _is_campobase(node):
        if isinstance(value, dict) and "valore" in value and "stato" in value:
            return value
        return {"valore": value, "stato": "DICHIARATO", "fonte": "utente",
                "norma_ref": None, "review_richiesta": False}

    # Array: scioglie un eventuale wrapper CampoBase attorno alla lista.
    if t == "array":
        if isinstance(value, dict) and "valore" in value:
            value = value.get("valore")
        if not isinstance(value, list):
            return []
        items = node.get("items")
        if not isinstance(items, dict):
            return value
        items_r = _resolve_ref(items, defs)
        required = items_r.get("required", [])
        coerced = []
        for v in value:
            # Scarta PRIMA della coercion gli item-spazzatura privi dei required
            # (es. verifiche generate dall'orchestrator, non dal classifier):
            # meglio lista vuota che item vuoti iniettati artificialmente.
            if required and not (isinstance(v, dict) and all(k in v for k in required)):
                continue
            coerced.append(_coerce_to_schema(v, items, defs))
        return coerced

    # Oggetto strutturale (non CampoBase).
    if t == "object" or "properties" in node:
        # wrapper CampoBase attorno a un oggetto strutturale → sciogli.
        if isinstance(value, dict) and "valore" in value and "stato" in value:
            inner = value.get("valore")
            value = inner if isinstance(inner, dict) else {}
        if not isinstance(value, dict):
            value = {}
        props = node.get("properties", {})
        required = node.get("required", [])
        out: dict = {}
        for k, sub in props.items():
            sub_r = _resolve_ref(sub, defs)
            if k in value:
                out[k] = _coerce_to_schema(value[k], sub, defs)
            elif "const" in sub_r:
                out[k] = sub_r["const"]
            elif k in required:
                # required OMESSO dall'LLM → inietta un default conforme.
                out[k] = _default_for_schema(sub, defs)
        # additionalProperties: false → scarta le chiavi inattese; altrimenti conserva.
        if node.get("additionalProperties", True) is not False:
            for k, v in value.items():
                if k not in out:
                    out[k] = v
        return out

    return value


@dataclass
class ClassifierResult:
    schema_compilato: dict
    confidence: float
    campi_dichiarati: list[str]
    campi_inferiti: list[str]
    note_llm: list[str] = field(default_factory=list)
    raw_response: str = ""


def _load_api_key() -> str | None:
    key = os.environ.get("GOOGLE_API_KEY") or os.environ.get("GEMINI_API_KEY")
    if key:
        return key
    env = Path(os.environ.get("K2A_NORME_ENV", _DEFAULT_NORME_ENV))
    if env.exists():
        for line in env.read_text().splitlines():
            if line.startswith(("GEMINI_API_KEY=", "GOOGLE_API_KEY=")):
                return line.split("=", 1)[1].strip()
    return None


SYSTEM_PROMPT_TEMPLATE = """Sei un classificatore esperto di progetti elettrici italiani.

Riceverai una descrizione in linguaggio naturale di un impianto elettrico. Estrai i
dati strutturati conformi al JSON Schema della tipologia.

REGOLE FONDAMENTALI:
1. Estrai SOLO ciò che l'utente ha esplicitamente dichiarato. NON inventare valori.
2. I campi-dato FOGLIA (quelli che nello schema hanno $ref a CampoBase) sono oggetti
   con: valore, stato, fonte, norma_ref, review_richiesta.
   - stato="DICHIARATO" (fonte="utente") se l'utente l'ha specificato;
   - stato="DEFAULT" (review_richiesta=true) per un default tipologico/geocoding/normativo;
   - stato="RICHIESTO" se il campo è critico ma mancante e senza default plausibile.
3. ATTENZIONE — NON tutto è un CampoBase. Rispetta ALLA LETTERA la struttura dello schema:
   - i campi di tipo "array" (es. liste di verifiche) sono ARRAY semplici, NON avvolgerli
     in {{valore, stato, ...}};
   - gli oggetti strutturali (es. "asseverazione") seguono le loro proprietà; i campi con
     "const" vanno copiati col valore costante (es. firmata=false, modalita="validation");
   - NON aggiungere proprietà che lo schema non prevede (gli oggetti con
     additionalProperties:false accettano SOLO le chiavi elencate).
4. NON eseguire calcoli ingegneristici: quelli sono compito dell'orchestrator.
5. Se un dato è ambiguo, marcalo "RICHIESTO" anziché indovinare.
6. Aggiungi "_metadata": {{"confidence": <0..1>, "note": ["..."]}}.
7. Rispondi SOLO con JSON valido conforme allo schema. Nessun testo introduttivo.

TIPOLOGIA TARGET: {tipologia}

SCHEMA (estratto):
{schema_json}

ESEMPIO DI OUTPUT BEN FORMATO (estratto):
{esempio_json}

Ora classifica il seguente input:
"""


class TappaTreClassifier:
    """Classificatore LLM per le tipologie Tappa 3 (MVP: cabina_industriale)."""

    def __init__(self, tipologia: str = "cabina_industriale",
                 model_name: str = DEFAULT_MODEL, api_key: str | None = None,
                 client=None):
        self.tipologia = tipologia
        self.model_name = model_name

        try:
            schema_text = (resources.files("k2a_elettrico.tappa3.schemas")
                           .joinpath(f"{tipologia}.json").read_text(encoding="utf-8"))
        except (FileNotFoundError, ModuleNotFoundError) as e:
            raise FileNotFoundError(
                f"Schema non trovato per tipologia '{tipologia}'") from e
        self.schema = json.loads(schema_text)
        self.validator = Draft202012Validator(self.schema)

        if client is not None:
            self._client = client  # iniezione per test offline
        else:
            key = api_key or _load_api_key()
            if not key:
                raise RuntimeError(
                    "GOOGLE_API_KEY/GEMINI_API_KEY non configurata (env o .env norme-tecniche).")
            from google import genai  # import lazy
            self._client = genai.Client(api_key=key)

    def classifica(self, input_naturale: str, esempio_json: dict | None = None,
                   max_retries: int = 2) -> ClassifierResult:
        if esempio_json is None:
            esempio_json = self._esempio_default()

        prompt = SYSTEM_PROMPT_TEMPLATE.format(
            tipologia=self.tipologia,
            schema_json=json.dumps(self.schema, ensure_ascii=False)[:8000],
            esempio_json=json.dumps(esempio_json or {}, ensure_ascii=False)[:4000],
        )
        full_prompt = prompt + "\n\n" + input_naturale

        last_error: Exception | None = None
        for attempt in range(max_retries + 1):
            try:
                resp = self._client.models.generate_content(
                    model=self.model_name, contents=full_prompt)
                raw = (getattr(resp, "text", None) or "").strip()
                raw = self._strip_fences(raw)
                schema_compilato = json.loads(raw)

                # Normalizzazione deterministica verso lo schema (drift prompt-vs-schema).
                schema_compilato = self._normalizza(schema_compilato)

                errors = list(self.validator.iter_errors(schema_compilato))
                if errors:
                    msgs = [f"{list(e.path)}: {e.message}" for e in errors[:5]]
                    raise ValueError("JSON non conforme allo schema:\n" + "\n".join(msgs))

                meta = schema_compilato.get("_metadata", {})
                return ClassifierResult(
                    schema_compilato=schema_compilato,
                    confidence=float(meta.get("confidence", 0.85)),
                    campi_dichiarati=self._estrai_campi_per_stato(schema_compilato, "DICHIARATO"),
                    campi_inferiti=self._estrai_campi_per_stato(schema_compilato, "DEFAULT"),
                    note_llm=list(meta.get("note", [])),
                    raw_response=raw,
                )
            except (json.JSONDecodeError, ValueError) as e:
                last_error = e
                if attempt < max_retries:
                    full_prompt += (f"\n\nTENTATIVO {attempt+1} FALLITO: {e}\n"
                                    "Correggi e restituisci SOLO JSON conforme.")
                    continue
                raise ClassificationError(
                    f"Classificazione fallita dopo {max_retries+1} tentativi: {e}") from e
        raise ClassificationError(str(last_error))  # pragma: no cover

    def _normalizza(self, obj: dict) -> dict:
        """Applica `_coerce_to_schema` al top-level preservando `_metadata`."""
        if not isinstance(obj, dict):
            return obj
        defs = self.schema.get("$defs", {})
        meta = obj.get("_metadata")
        coerced = _coerce_to_schema(obj, self.schema, defs)
        if not isinstance(coerced, dict):
            return obj
        if meta is not None and "_metadata" not in coerced:
            coerced["_metadata"] = meta
        return coerced

    @staticmethod
    def _strip_fences(text: str) -> str:
        t = text.strip()
        if t.startswith("```"):
            lines = t.split("\n")
            t = "\n".join(lines[1:-1]) if len(lines) > 2 else t
            if t.lstrip().lower().startswith("json"):
                t = t.lstrip()[4:].lstrip()
        return t.strip()

    def _esempio_default(self) -> dict | None:
        candidates = [
            Path(__file__).resolve().parents[4] / "docs" / "tappa3" / "esempio_cabina_rossi.json",
            Path(__file__).resolve().parents[2] / "tests" / "tappa3" / "fixtures" / "esempio_cabina_rossi.json",
        ]
        for p in candidates:
            if p.exists():
                return json.loads(p.read_text(encoding="utf-8"))
        return None

    @staticmethod
    def _estrai_campi_per_stato(schema_compilato: dict, stato: str) -> list[str]:
        paths: list[str] = []

        def walk(obj, path=""):
            if isinstance(obj, dict):
                if "stato" in obj and "valore" in obj:  # è un CampoBase: foglia
                    if obj.get("stato") == stato:
                        paths.append(path)
                    return
                for k, v in obj.items():
                    walk(v, f"{path}.{k}" if path else k)
            elif isinstance(obj, list):
                for i, item in enumerate(obj):
                    walk(item, f"{path}[{i}]")

        walk(schema_compilato)
        return paths
