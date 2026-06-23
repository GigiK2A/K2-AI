"""Controlli di qualita condivisi da tutti i deliverable 8e.

Lo schema JSON verifica la forma, non la verita del contenuto. Questo modulo
aggiunge i gate che devono precedere e seguire ogni generazione vendibile:

* input minimi realmente presenti (mai campioni sintetici per far passare lo schema);
* metadati ricavati dagli input e data corrente;
* riconciliazione contabile FinanceBoost;
* rifiuto di placeholder, falsa precisione e numeri non tracciabili.

Tutto e deterministico e non chiama modelli.
"""
from __future__ import annotations

from copy import deepcopy
from datetime import date, datetime, timezone
import math
import re
from typing import Any, Iterable

from jsonschema import Draft202012Validator

from . import finance


GENERIC_NAMES = {"", "cliente", "azienda", "la tua azienda", "n/d", "-", "—"}


def _walk(v: Any) -> Iterable[Any]:
    if isinstance(v, dict):
        for x in v.values():
            yield from _walk(x)
    elif isinstance(v, list):
        for x in v:
            yield from _walk(x)
    else:
        yield v


def _num(v: Any) -> float | None:
    if isinstance(v, bool) or v is None:
        return None
    if isinstance(v, (int, float)) and math.isfinite(float(v)):
        return float(v)
    if isinstance(v, str):
        s = v.strip().replace("€", "").replace(" ", "")
        if not s:
            return None
        if "," in s:
            s = s.replace(".", "").replace(",", ".")
        try:
            n = float(s)
            return n if math.isfinite(n) else None
        except ValueError:
            return None
    return None


def display_name(inputs: dict) -> str | None:
    """Nome reale del soggetto, senza fallback cosmetici tipo ``Cliente``."""
    for key in ("ragione_sociale", "denominazione", "azienda", "nome", "client_name"):
        value = str(inputs.get(key) or "").strip()
        if value and value.lower() not in GENERIC_NAMES:
            return value
    # StrategyBoost usa una descrizione libera: accettala solo se breve e nominale.
    desc = str(inputs.get("descrizione_azienda") or "").strip()
    if desc and len(desc) <= 100:
        return desc
    return None


def validate_required_inputs(form_schema: dict, inputs: dict) -> list[str]:
    """Errori leggibili del form. Nessun valore viene inventato per sanarli."""
    if not form_schema:
        return []
    # ``ragione_sociale`` e un metadato trasversale aggiunto dal K-BOT e non e
    # ancora duplicato negli 11 form legacy. Valida il payload di dominio senza
    # farlo fallire come additionalProperty.
    props = form_schema.get("properties", {})
    domain_inputs = {k: v for k, v in inputs.items() if k in props}
    errors = sorted(Draft202012Validator(form_schema).iter_errors(domain_inputs), key=lambda e: list(e.path))
    out = []
    for err in errors[:20]:
        path = ".".join(str(p) for p in err.path) or "input"
        out.append(f"{path}: {err.message}")
    return out


def _close(a: float, b: float) -> bool:
    return abs(a - b) <= max(1.0, 0.005 * max(abs(a), abs(b), 1.0))


def _reclass_from_voci(row: dict) -> dict | None:
    """Se l'esercizio porta le VOCI grezze trascritte dal bilancio, le riclassifica
    deterministicamente (app/finance.py) e SOVRASCRIVE gli aggregati nel row: PN,
    EBITDA, EBIT, debiti finanziari, attivo/passivo corrente, passività verso terzi
    (al netto dei fondi ammortamento) e le componenti del PN. Cosi la riconciliazione
    qui sotto VALIDA numeri deterministici invece di fidarsi di stime dell'LLM, e lo
    stesso row alimenta Excel e indici. Le voci sono autoritative."""
    voci = row.get("voci")
    if not isinstance(voci, list) or not voci:
        return None
    rc = finance.reclassify_bilancio(voci, row.get("anno"))
    sp, ce = rc.get("sp", {}), rc.get("ce", {})
    mapped = {
        "ricavi": ce.get("ricavi"), "ebitda": ce.get("ebitda"),
        "reddito_operativo": ce.get("ebit"), "utile_netto": ce.get("utile_netto"),
        "imposte": ce.get("imposte"), "oneri_finanziari": ce.get("oneri_finanziari"),
        "ammortamenti_svalutazioni": ce.get("ammortamenti"),
        "totale_attivo": sp.get("totale_attivo"), "attivo_corrente": sp.get("attivo_corrente"),
        "passivo_corrente": sp.get("passivo_corrente"),
        "patrimonio_netto": sp.get("patrimonio_netto"),
        "debiti_finanziari": sp.get("debiti_finanziari"),
        "passivita_verso_terzi": sp.get("debiti_terzi"),
        "capitale_sociale": sp.get("capitale_sociale"),
        "riserve": sp.get("riserve"),
        "utili_portati_nuovo": sp.get("utili_portati_nuovo"),
        "risultato_esercizio": ce.get("utile_netto"),
    }
    for k, v in mapped.items():
        if v is not None:
            row[k] = v
    return rc


def normalize_finance_inputs(inputs: dict) -> tuple[dict, list[str], list[str]]:
    """Riconcilia i bilanci senza scegliere arbitrariamente una definizione.

    Ritorna ``(input_normalizzato, errori_bloccanti, note_audit)``. Il patrimonio
    netto viene ricostruito dalle componenti o dall'identita patrimoniale; se un
    valore fornito contraddice la quadratura, il report viene bloccato.
    """
    out = deepcopy(inputs)
    errors: list[str] = []
    notes: list[str] = []
    rows = out.get("bilanci")
    if not isinstance(rows, list) or not rows:
        return out, ["bilanci: serve almeno un esercizio con SP e CE"], notes

    for i, row in enumerate(rows):
        if not isinstance(row, dict):
            errors.append(f"bilanci[{i}]: esercizio non strutturato")
            continue
        label = str(row.get("anno") or i + 1)
        # Se ci sono le voci grezze, riclassificale: popolano gli aggregati che la
        # riconciliazione qui sotto poi valida (doppia quadratura) e che alimentano Excel.
        rc = _reclass_from_voci(row)
        if rc is not None:
            notes.append(f"bilancio {label}: riclassificato da {len(row['voci'])} voci grezze del bilancio")
            quad = rc.get("quadratura") or {}
            if quad.get("ok") is False:
                errors.append(
                    f"bilancio {label}: le voci trascritte non quadrano "
                    f"(delta {quad.get('delta')}): trascrizione del bilancio da verificare"
                )
        components = [
            _num(row.get("capitale_sociale")),
            _num(row.get("riserve")),
            _num(row.get("utili_portati_nuovo")),
            _num(row.get("risultato_esercizio")),
        ]
        component_values = [v for v in components if v is not None]
        supplied_pn = _num(row.get("patrimonio_netto"))
        assets = _num(row.get("totale_attivo"))
        third_party = _num(row.get("passivita_verso_terzi"))
        printed_liabilities = _num(row.get("totale_passivita_prima_risultato"))
        if third_party is None and printed_liabilities is not None:
            pre_result_equity = sum(v for v in components[:3] if v is not None)
            if any(v is not None for v in components[:3]):
                third_party = printed_liabilities - pre_result_equity
                row["passivita_verso_terzi"] = round(third_party, 2)
                notes.append(
                    f"bilancio {label}: passivita verso terzi ricavate dal totale a 4 sezioni "
                    "al netto di capitale/riserve/utili portati"
                )
        derived: list[tuple[str, float]] = []
        if component_values:
            # Per usare la somma servono almeno capitale + risultato o una voce
            # aggregata esplicita; una componente isolata non e un PN completo.
            if len(component_values) >= 2:
                derived.append(("componenti PN", sum(component_values)))
        if assets is not None and third_party is not None:
            derived.append(("Attivo - passivita verso terzi", assets - third_party))

        candidates = ([('patrimonio_netto fornito', supplied_pn)] if supplied_pn is not None else []) + derived
        if candidates:
            derived_consensus = (
                len(derived) >= 2
                and all(_close(derived[0][1], value) for _, value in derived[1:])
            )
            if derived_consensus:
                chosen_name, chosen_value = derived[0]
                if supplied_pn is not None and not _close(supplied_pn, chosen_value):
                    notes.append(
                        f"bilancio {label}: PN fornito {supplied_pn:.2f} corretto a {chosen_value:.2f}; "
                        "due quadrature indipendenti concordano"
                    )
            else:
                base_name, base_value = candidates[0]
                for other_name, other_value in candidates[1:]:
                    if not _close(base_value, other_value):
                        errors.append(
                            f"bilancio {label}: patrimonio netto incoerente: {base_name}={base_value:.2f}, "
                            f"{other_name}={other_value:.2f}"
                        )
                chosen_name, chosen_value = derived[0] if derived else candidates[0]
            if not any(f"bilancio {label}: patrimonio netto incoerente" in e for e in errors):
                row["patrimonio_netto"] = round(chosen_value, 2)
                notes.append(f"bilancio {label}: PN={chosen_value:.2f} da {chosen_name}")
        else:
            errors.append(f"bilancio {label}: patrimonio netto non ricostruibile")

        pn = _num(row.get("patrimonio_netto"))
        if assets is not None and third_party is not None and pn is not None and not _close(assets, third_party + pn):
            errors.append(
                f"bilancio {label}: SP non quadra: attivo {assets:.2f} != passivita terzi + PN {third_party + pn:.2f}"
            )

        # EBITDA ricavabile dal conto economico quando tutte le componenti sono presenti.
        if _num(row.get("ebitda")) is None:
            net = _num(row.get("utile_netto"))
            taxes = _num(row.get("imposte"))
            fin = _num(row.get("oneri_finanziari"))
            da = _num(row.get("ammortamenti_svalutazioni"))
            if None not in (net, taxes, fin, da):
                row["ebitda"] = round(net + taxes + fin + da, 2)  # type: ignore[operator]
                notes.append(f"bilancio {label}: EBITDA stimato con bridge utile+imposte+OF+D&A")

        # Non confondere totale passivita di stampa con debiti finanziari.
        if row.get("debiti_finanziari") is None:
            bank = _num(row.get("debiti_bancari"))
            loans = _num(row.get("mutui_finanziamenti"))
            if bank is not None or loans is not None:
                row["debiti_finanziari"] = round((bank or 0) + (loans or 0), 2)
                notes.append(f"bilancio {label}: debiti finanziari ricostruiti da banche+mutui")

    out["_quality_audit"] = notes
    return out, errors, notes


def prepare_inputs(skill: str, form_schema: dict, inputs: dict) -> tuple[dict, list[str], list[str]]:
    prepared = deepcopy(inputs or {})
    notes: list[str] = []
    identity_errors = [] if display_name(prepared) else [
        "ragione_sociale: necessaria per personalizzare e identificare il report"
    ]
    if skill == "flusso-financeboost-pmi":
        prepared, finance_errors, notes = normalize_finance_inputs(prepared)
        # Il campo audit e interno e non fa parte dello schema form.
        schema_input = {k: v for k, v in prepared.items() if k != "_quality_audit"}
        return prepared, identity_errors + validate_required_inputs(form_schema, schema_input) + finance_errors, notes
    return prepared, identity_errors + validate_required_inputs(form_schema, prepared), notes


def today_iso() -> str:
    return date.today().isoformat()


def now_iso() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def ensure_metadata(deliverable: dict, output_schema: dict, inputs: dict, service: str) -> dict:
    """Imposta identita/data reali e aggiunge meta agli schemi legacy che lo consentono."""
    name = display_name(inputs) or ""
    props = output_schema.get("properties", {})
    key = "metadata" if "metadata" in props else "meta"
    if key not in props and output_schema.get("additionalProperties") is False:
        return deliverable
    meta = deliverable.setdefault(key, {})
    if not isinstance(meta, dict):
        meta = {}; deliverable[key] = meta
    # Copri le varianti usate dagli output-schema senza inventare il soggetto.
    for candidate in ("azienda", "cliente", "client_name", "committente"):
        if candidate in (props.get(key, {}).get("properties", {}) if key in props else {}) or candidate == "azienda":
            meta[candidate] = name
            break
    if "servizio" in (props.get(key, {}).get("properties", {}) if key in props else {}):
        meta["servizio"] = service
    if "data" in meta or key == "meta":
        meta["data"] = today_iso()
    if "generated_at" in meta:
        meta["generated_at"] = now_iso()
    return deliverable


def grounded_numbers(inputs: dict, facts: dict, citations: list | None = None) -> set[float]:
    nums: set[float] = set()
    for value in list(_walk(inputs)) + list(_walk(facts)) + list(_walk(citations or [])):
        n = _num(value)
        if n is not None:
            nums.add(round(n, 4))
        if isinstance(value, str):
            for raw in re.findall(r"(?<![\w])-?\d+(?:[.,]\d+)?", value):
                embedded = _num(raw)
                if embedded is not None:
                    nums.add(round(embedded, 4))
    return nums


_NUMBER = re.compile(r"(?<![\w])(-?\d+(?:[.,]\d+)?)\s*(%|€|eur|x\b)?", re.I)
_QUANT_CONTEXT = re.compile(
    r"(?:€|\beur\b|%|margine|ricav|ebitda|utile|debito|costo|risparm|roi|roe|ros|"
    r"payback|fatturato|conversion|traffico|nfp|pfn|cagr|impatto|beneficio)", re.I
)
_ASSUMPTION = re.compile(r"(?:assunzione|ipotesi esplicita|scenario illustrativo|da validare)", re.I)
_UNCERTAIN_CLIENT_FACT = re.compile(
    r"(?:presumibilmente|probabilmente|ipotetic[oa]|si presume|verosimilmente).{0,100}"
    r"(?:dipendent|fatturat|cliente|contratt|registro|modello 231|social|seo|sito|process)", re.I | re.S
)


def unsupported_number_findings(deliverable: dict, inputs: dict, facts: dict,
                                citations: list | None = None, strict: bool = True) -> list[dict]:
    """Trova falsa precisione economica non presente negli input/fact.

    Percentuali/valute nuove sono ammesse solo se dichiarate come assunzioni
    esplicite. Non blocca date, numerazione di passi o durate operative.

    strict=True (boost FINANZIARI): severità 'block' — un numero-cliente fabbricato è
    pericoloso (il bug FinanceBoost originale). strict=False (boost QUALITATIVI: SEO/
    marketing/strategy): severità 'warn' — i benchmark di settore (CTR, traffico %) sono
    conoscenza di dominio citata, non numeri-cliente inventati: si annotano, non bloccano
    un deliverable pagato (i numeri-cliente critici dei finanziari restano comunque bound
    deterministicamente dai binder).
    """
    known = grounded_numbers(inputs, facts, citations)
    findings: list[dict] = []
    for value in _walk(deliverable):
        if not isinstance(value, str) or not _QUANT_CONTEXT.search(value):
            continue
        for match in _NUMBER.finditer(value):
            suffix = (match.group(2) or "").lower()
            if not suffix and not re.search(r"(?:ricav|ebitda|utile|debito|fatturat|nfp|pfn).{0,20}" + re.escape(match.group(1)), value, re.I):
                continue
            n = _num(match.group(1))
            if n is None or round(n, 4) in known:
                continue
            # percentuali derivate possono essere presenti nei formula-fact; se
            # non lo sono, devono apparire come assunzione verificabile.
            if _ASSUMPTION.search(value):
                continue
            excerpt = re.sub(r"\s+", " ", value).strip()[:180]
            findings.append({
                "code": "numero_non_grounded", "severity": "block" if strict else "warn",
                "dettaglio": f"numero {match.group(0).strip()} non presente in input/fact e non marcato come assunzione: {excerpt}",
            })
    # dedup compatto
    seen, out = set(), []
    for f in findings:
        key = f["dettaglio"]
        if key not in seen:
            seen.add(key); out.append(f)
    return out[:20]


def uncertain_fact_findings(deliverable: dict, strict: bool = True) -> list[dict]:
    full = "\n".join(str(v) for v in _walk(deliverable) if isinstance(v, str))
    return [{
        "code": "fatto_cliente_ipotetico", "severity": "block" if strict else "warn",
        "dettaglio": "un dato controllabile del cliente e stato sostituito da una supposizione; va raccolto o dichiarato non disponibile",
    }] if _UNCERTAIN_CLIENT_FACT.search(full) else []
