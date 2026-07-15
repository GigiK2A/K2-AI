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
import json
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
        "rimanenze": sp.get("rimanenze"),  # → Excel B10 + quick ratio (acid test) corretto
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


def prepare_inputs(skill: str, form_schema: dict, inputs: dict) -> tuple[dict, list[str], list[str], list[str]]:
    """Ritorna (prepared, identity_errors, content_errors, notes).

    identity_errors = manca il nome cliente (blocca SEMPRE: serve a intestare il
    documento). content_errors = campi obbligatori mancanti o bilancio non
    riconciliato: bloccano in FULL, ma in PARTIAL (report preliminare) diventano
    ipotesi etichettate anziché refuse."""
    prepared = deepcopy(inputs or {})
    notes: list[str] = []
    identity_errors = [] if display_name(prepared) else [
        "ragione_sociale: necessaria per personalizzare e identificare il report"
    ]
    if skill == "flusso-financeboost-pmi":
        prepared, finance_errors, notes = normalize_finance_inputs(prepared)
        # Il campo audit e interno e non fa parte dello schema form.
        schema_input = {k: v for k, v in prepared.items() if k != "_quality_audit"}
        content = validate_required_inputs(form_schema, schema_input) + finance_errors
        return prepared, identity_errors, content, notes
    return prepared, identity_errors, validate_required_inputs(form_schema, prepared), notes


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
    meta_props = props.get(key, {}).get("properties", {}) if key in props else {}
    if "servizio" in meta_props:
        meta["servizio"] = service
    # Data di generazione: popola il/i campo/i data che lo schema DICHIARA (varia per boost:
    # 'data' legacy, 'data_generazione' su cruscotto-direzionale, ...). Iniettare 'data' a
    # tappeto rompeva ControlBoost: il suo schema usa 'data_generazione' + additionalProperties
    # false → "'data' was unexpected" → validation_failed → REFUSE (vicolo cieco pagato).
    date_fields = [f for f in ("data", "data_generazione", "data_elaborazione", "data_documento",
                               "generated_at") if f in meta_props]
    if date_fields:
        for f in date_fields:
            meta[f] = now_iso() if f == "generated_at" else today_iso()
    elif props.get(key, {}).get("additionalProperties") is not False:
        # schema senza campo-data dichiarato ma che consente extra → compat render (legge meta.data)
        meta["data"] = today_iso()
    if "generated_at" in meta and "generated_at" not in date_fields:
        meta["generated_at"] = now_iso()
    return deliverable


# Template placeholder che il deep-gen a volte lascia NONOSTANTE il prompt che li vieta
# (es. '[città]' quando non conosce la sede): il gate CAGE li blocca come placeholder_leak
# (refuse reale in prod, job_f1d31380ff0d). Affidarsi al solo prompt non regge → qui li
# NEUTRALIZZIAMO deterministicamente PRIMA del gate: un dato mancante non deve far fallire la
# consegna. [nome]/[azienda] → cliente reale; date → mese/anno correnti; luoghi ignoti → neutro.
_SCRUB_SUBS: list[tuple] = [
    (re.compile(r"\[\s*(?:nome|azienda|ragione[\s_]*sociale|denominazione|cliente|committente|societ[aà])\s*\]", re.I), "{name}"),
    (re.compile(r"\[\s*(?:citt[aà]|comune|sede)\s*\]", re.I), "località non indicata"),
    (re.compile(r"\[\s*(?:regione|provincia|zona|area(?:\s+geografica)?|territorio)\s*\]", re.I), "area non indicata"),
    (re.compile(r"\[\s*indirizzo\s*\]", re.I), "indirizzo non indicato"),
    (re.compile(r"\[\s*(?:mese\s*/?\s*anno|data|periodo)\s*\]", re.I), "{myyyy}"),
    (re.compile(r"\[\s*anno\s*\]", re.I), "{yyyy}"),
    (re.compile(r"\[\s*(?:settore|mercato|comparto)\s*\]", re.I), "il settore di riferimento"),
    # Norma-segnaposto NON tra parentesi che l'LLM inventa quando non sa la norma reale
    # (es. settore energia: 'DM FER-X', 'FER-X', 'regolamento FER-X' — visto in prod su WebBoost).
    # Rispecchia _PLACEHOLDER_PATTERNS del gate → neutralizzazione onesta invece del block.
    (re.compile(r"\b(?:regolamento\s+FER-?X|D\.?\s*M\.?\s*FER\s*-?\s*X|FER\s*-\s*X)\b", re.I),
     "la normativa di settore applicabile"),
    # Marker INTERNI che non devono mai trapelare: se escono, neutralizza (non bloccare).
    (re.compile(r"\bSegnaposto deterministico\b", re.I), "dato non disponibile"),
    (re.compile(r"\boverride_locale\b", re.I), "fonte interna"),
    (re.compile(r"\bANTHROPIC_API_KEY\b", re.I), "configurazione interna"),
]
# Catch-all: qualunque parola MINUSCOLA (accentata) tra [] rimasta = segnaposto trapelato.
# Lowercase-only e senza cifre ⇒ NON tocca i marker legittimi maiuscoli ([IPOTESI]) né i ref ([1]).
_SCRUB_CATCHALL = re.compile(r"\[\s*[a-zàèéìòù][a-zàèéìòù _/]{1,30}\]")


_BOOST_NAME_RX = re.compile(r"^[A-Z][A-Za-z]{2,}Boost$")


def _is_boost_name_leak(s: str, servizio: str) -> bool:
    """True se la stringa-foglia è ESATTAMENTE il nome di un boost/servizio (es.
    'FinanceBoost') — un placeholder trapelato dallo schema-example, MAI un
    contenuto legittimo (un'azione o un KPI non si chiamano 'FinanceBoost'). Solo
    match ESATTO sull'intero valore: una frase che *cita* il boost resta intatta."""
    t = (s or "").strip()
    return bool(t) and (t == servizio or bool(_BOOST_NAME_RX.match(t)))


# liste NARRATIVE: ogni item DEVE avere testo (azione, rischio, raccomandazione…).
# Un item senza testo dopo lo scrub (es. {priorita:1} rimasto quando 'azione' era il
# leak 'FinanceBoost' → svuotato) è degenere: nel PDF esce '· Piano azione / Priorita: 1'.
# NON tocchiamo le liste NON-narrative (serie numeriche/coordinate di grafici).
_NARRATIVE_LIST_KEYS = {
    "piano_azione", "azioni", "azioni_prioritarie", "azioni_consigliate", "top_azioni",
    "raccomandazioni", "rischi", "rischi_opportunita", "findings", "interventi",
}


def _has_text(v) -> bool:
    """True se c'è ALMENO una stringa non vuota (numeri/bool NON contano come testo)."""
    if isinstance(v, str):
        return bool(v.strip())
    if isinstance(v, dict):
        return any(_has_text(x) for x in v.values())
    if isinstance(v, list):
        return any(_has_text(x) for x in v)
    return False


def _compact_empties(v, key: str = ""):
    """Toglie dalle liste gli item diventati vuoti dopo lo scrub (stringa '' o dict
    tutto-vuoto). Nelle liste NARRATIVE toglie anche i dict SENZA testo (solo numeri):
    un bullet/azione senza testo nel PDF è peggio di assente."""
    if isinstance(v, list):
        out = [_compact_empties(x, key) for x in v]
        res = []
        for x in out:
            if x in (None, "", [], {}):
                continue
            if isinstance(x, dict) and all(y in (None, "", [], {}) for y in x.values()):
                continue
            if key in _NARRATIVE_LIST_KEYS and isinstance(x, dict) and not _has_text(x):
                continue  # item narrativo senza testo (es. {priorita:1}) → degenere
            res.append(x)
        return res
    if isinstance(v, dict):
        return {k: _compact_empties(x, k) for k, x in v.items()}
    return v


def scrub_template_placeholders(deliverable: dict, inputs: dict) -> dict:
    """Neutralizza i segnaposto template trapelati dal LLM prima del gate/render. Deterministico."""
    name = display_name(inputs) or "l'azienda"
    myyyy = date.today().strftime("%m/%Y")
    yyyy = date.today().strftime("%Y")
    servizio = str((deliverable.get("meta") or deliverable.get("metadata") or {}).get("servizio") or "")

    def fix(s: str, boost_scrub: bool) -> str:
        # nome-boost trapelato come intero valore-foglia (es. 'FinanceBoost') → vuoto,
        # poi _compact_empties lo toglie da liste e il render salta i campi vuoti. MA
        # solo nel BODY: in meta/metadata 'FinanceBoost' è il valore CORRETTO di
        # `servizio` (spesso uno schema `const`) — svuotarlo fa fallire la validazione.
        if boost_scrub and _is_boost_name_leak(s, servizio):
            return ""
        for rx, tmpl in _SCRUB_SUBS:
            val = tmpl.format(name=name, myyyy=myyyy, yyyy=yyyy)
            s = rx.sub(lambda _m, _v=val: _v, s)        # lambda ⇒ replacement letterale (no backref)
        return _SCRUB_CATCHALL.sub(lambda _m: "dato non indicato", s)

    def walk(v, in_meta: bool = False):
        if isinstance(v, str):
            return fix(v, boost_scrub=not in_meta)
        if isinstance(v, dict):
            return {k: walk(x, in_meta or k in ("meta", "metadata")) for k, x in v.items()}
        if isinstance(v, list):
            return [walk(x, in_meta) for x in v]
        return v

    return _compact_empties(walk(deliverable))


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
# Marker di ASSUNZIONE ESPLICITA: un numero NON-grounded è ammesso se la frase lo etichetta
# onestamente come ipotesi/illustrazione (così un report qualitativo può includere cifre
# illustrative dichiarate). Riconosce i fraseggi onesti più naturali del modello — ma NON la
# parola debole 'stima'/'stimato' (una stima spacciata per quasi-fatto resta bloccata, vedi
# test_financial_strict_not_loosened_by_weak_estimate_word) né un numero NUDO.
_ASSUMPTION = re.compile(
    r"(?:assunzione|assuntiv\w*|ipotes\w*|ipotizz\w*|scenario\s+(?:illustrativo|assuntivo)|"
    r"illustrativ\w*|a\s+titolo|da\s+validare|da\s+confermare)", re.I)
# Numeri HARD-FINANCIAL: cifre-CLIENTE su cui si AGISCE economicamente (€, indici di
# bilancio, ROI/payback/VAN/TIR). Restano 'block' anche sui boost qualitativi
# (strict=False): un "€50k di impatto" o un "ROI del 250%" fabbricato è pericoloso in
# QUALSIASI report, non solo nei finanziari. I 'soft' (traffico/conversion %) sono
# benchmark di settore → declassabili a warn quando il boost non è finanziario.
# NB: le ALIQUOTE normative (IRES 24%, IRAP 3,9%, IVA 22%) NON sono qui: sono costanti
# pubbliche di legge (TUIR), non cifre-cliente fabbricate — su un boost qualitativo
# (es. orientamento fiscale del LegalBoost) sono warn, non block. Un IMPORTO in € resta
# comunque hard via il simbolo '€' (es. "imposta dovuta €5.000" → block).
_HARD_FINANCIAL = re.compile(
    r"(?:€|\beur\b|ebitda|utile|debit\w*|\bpfn\b|\bnfp\b|\broi\b|\broe\b|\bros\b|payback|"
    r"\bvan\b|\btir\b|margine|fatturat\w*|ricav\w*|cagr|"
    r"enterprise\s+value|valore\s+d'impresa|beneficio|risparmi\w*)", re.I)
# PROMESSA/GARANZIA: un numero-risultato GARANTITO al cliente ("ti garantiamo +40%") è
# una promessa fabbricata = liability, resta block ovunque. Distinta dal benchmark nudo
# ("+40% tipico del settore" → soft/warn): qui c'è il verbo di garanzia.
_PROMISE = re.compile(
    r"(?:garant\w*|assicuriam\w*|ti\s+assicur\w*|otterrai|raddoppi\w*|triplic\w*|moltiplic\w*)", re.I)
_UNCERTAIN_CLIENT_FACT = re.compile(
    r"(?:presumibilmente|probabilmente|ipotetic[oa]|si presume|verosimilmente).{0,100}"
    r"(?:dipendent|fatturat|cliente|contratt|registro|modello 231|social|seo|sito|process)", re.I | re.S
)


def unsupported_number_findings(deliverable: dict, inputs: dict, facts: dict,
                                citations: list | None = None, strict: bool = True) -> list[dict]:
    """Trova falsa precisione economica non presente negli input/fact.

    Percentuali/valute nuove sono ammesse solo se dichiarate come assunzioni
    esplicite. Non blocca date, numerazione di passi o durate operative.

    strict=True (boost FINANZIARI): severità 'block' su QUALUNQUE numero non grounded — un
    numero-cliente fabbricato è pericoloso (il bug FinanceBoost originale). strict=False
    (boost QUALITATIVI: SEO/marketing/strategy): la severità dipende dalla NATURA del numero,
    non dal boost — un benchmark di settore morbido (CTR, traffico, conversion %) si annota
    (warn), ma un numero HARD-FINANCIAL (€/EBITDA/ROI/payback…) o una promessa GARANTITA
    ("ti garantiamo +40%") resta 'block' OVUNQUE: fabbricare una cifra-cliente su cui si agisce
    economicamente è liability in qualsiasi report. (I numeri-cliente dei finanziari restano
    comunque bound deterministicamente dai binder dove esistono.)
    """
    known = grounded_numbers(inputs, facts, citations)
    findings: list[dict] = []
    for value in _walk(deliverable):
        if not isinstance(value, str) or not _QUANT_CONTEXT.search(value):
            continue
        for match in _NUMBER.finditer(value):
            suffix = (match.group(2) or "").lower()
            # Salta se il numero è privo di contesto finanziario (date, step, ID, ecc.).
            # Eccezione: se il simbolo valutario/termine hard è PRIMA del numero (es. "€40000")
            # o il termine è nel value (post-posizione "40000 EBITDA") → non saltare.
            # Pre-positioned currency "€40000": controlla solo i 5 char prima del match.
            pre_window = value[max(0, match.start() - 5):match.start()]
            pre_currency = bool(re.search(r"(?:€|eur)\s*$", pre_window, re.I))
            if not suffix and not pre_currency and not re.search(
                    r"(?:ricav|ebitda|utile|debito|fatturat|nfp|pfn).{0,20}" + re.escape(match.group(1)), value, re.I):
                continue
            n = _num(match.group(1))
            if n is None:
                continue
            # Match grounding tollerante al formato IT delle migliaia: "850.000" è parsato
            # 850.0 da _num (nessuna virgola → il '.' resta decimale) ma può valere 850000
            # (= input fatturato). Prova ENTRAMBE le letture: se UNA combacia con un numero
            # grounded, il valore è coperto → niente falso positivo su un numero d'input.
            cand = {round(n, 4)}
            tok = match.group(1)
            if re.fullmatch(r"-?\d{1,3}(?:\.\d{3})+", tok):
                cand.add(round(float(tok.replace(".", "")), 4))
            if cand & known:
                continue
            # percentuali derivate possono essere presenti nei formula-fact; se
            # non lo sono, devono apparire come assunzione verificabile.
            if _ASSUMPTION.search(value):
                continue
            excerpt = re.sub(r"\s+", " ", value).strip()[:180]
            # Hard-financial (€/indici/ROI…) o promessa garantita → block ANCHE sui
            # qualitativi. Controlla ±80 char intorno al numero (NON l'intera stringa:
            # "risparmio energetico" in un'altra frase non trasforma "82%" in financial).
            ctx_start = max(0, match.start() - 80)
            ctx_end = min(len(value), match.end() + 80)
            near = value[ctx_start:ctx_end]
            hard = suffix in ("€", "eur") or bool(_HARD_FINANCIAL.search(near)) or bool(_PROMISE.search(near))
            findings.append({
                "code": "numero_non_grounded", "severity": "block" if (strict or hard) else "warn",
                "dettaglio": f"numero {match.group(0).strip()} non presente in input/fact e non marcato come assunzione: {excerpt}",
            })
    # dedup compatto
    seen, out = set(), []
    for f in findings:
        key = f["dettaglio"]
        if key not in seen:
            seen.add(key); out.append(f)
    return out[:20]


# Framing esplicito richiesto dall'owner (QA 8 lug): i numeri-target non ancorati NON
# devono leggersi come KPI quasi-definitivi → tag "SCENARIO ASSUNTIVO". Contiene ancora
# "ipotesi da confermare" così _ASSUMPTION (gate) continua a esentarli.
_NUM_SCRUB_MARK = " (SCENARIO ASSUNTIVO — ipotesi da confermare)"


def _value_has_blocking_number(value: str, known: set) -> bool:
    """True se `value` contiene un numero che unsupported_number_findings BLOCCHEREBBE
    (stessa identica logica di rilevazione): contesto economico, non grounded, non gia'
    marcato come ipotesi. Usato dallo scrub deterministico pre-gate."""
    if not _QUANT_CONTEXT.search(value) or _ASSUMPTION.search(value):
        return False
    for m in _NUMBER.finditer(value):
        suffix = (m.group(2) or "").lower()
        pre_window = value[max(0, m.start() - 5):m.start()]
        pre_currency = bool(re.search(r"(?:€|eur)\s*$", pre_window, re.I))
        if not suffix and not pre_currency and not re.search(
                r"(?:ricav|ebitda|utile|debito|fatturat|nfp|pfn).{0,20}" + re.escape(m.group(1)), value, re.I):
            continue
        n = _num(m.group(1))
        if n is None:
            continue
        cand = {round(n, 4)}
        tok = m.group(1)
        if re.fullmatch(r"-?\d{1,3}(?:\.\d{3})+", tok):
            cand.add(round(float(tok.replace(".", "")), 4))
        if cand & known:
            continue
        return True
    return False


def scrub_ungrounded_numbers(deliverable: dict, inputs: dict, facts: dict,
                             citations: list | None = None, *, strict: bool = False) -> dict:
    """Marca i numeri non-grounded in contesto economico come illustrativi PRIMA del gate.

    Scelta-utente resa deterministica: i boost QUALITATIVI possono contenere numeri
    illustrativi SE etichettati onestamente. Il modello a volte scrive un importo non
    presente in input/fact senza marcarlo → il gate lo bloccherebbe (numero_non_grounded)
    e il report fallisce. Qui si appende un marker '(ipotesi da confermare)' alla frase
    che contiene il numero: e' onesto (quel numero NON e' verificato) e il gate poi lo
    esenta (via _ASSUMPTION). Il backstop resta: cio' che era grounded resta tale.

    strict=True (boost FINANZIARI): NO-OP. Le loro cifre vanno bound/grounded davvero
    (un'etichetta non basta), quindi il gate deve continuare a bloccarle."""
    if strict:
        return deliverable
    known = grounded_numbers(inputs, facts, citations)
    out = deepcopy(deliverable)

    def walk(v):
        if isinstance(v, dict):
            return {k: walk(x) for k, x in v.items()}
        if isinstance(v, list):
            return [walk(x) for x in v]
        if isinstance(v, str) and _value_has_blocking_number(v, known):
            return v + _NUM_SCRUB_MARK
        return v

    return walk(out)


# Audit 1d (15 lug 2026): sui boost FINANZIARI l'etichetta non basta — il lettore prende
# decisioni di cassa su quelle righe. MEGLIO NESSUN NUMERO CHE UN NUMERO SBAGLIATO.
_ND_MARK = " [valore non verificato rimosso: N/D — da confermare col cliente]"


def _neutralize_value(value: str, known: set) -> str:
    """Sostituisce con 'N/D' i numeri economici non-grounded di `value` (stessa logica di
    rilevazione di _value_has_blocking_number, applicata numero per numero: quelli
    grounded restano)."""
    if not _QUANT_CONTEXT.search(value) or _ASSUMPTION.search(value):
        return value
    spans = []
    for m in _NUMBER.finditer(value):
        suffix = (m.group(2) or "").lower()
        pre_window = value[max(0, m.start() - 5):m.start()]
        pre_currency = bool(re.search(r"(?:€|eur)\s*$", pre_window, re.I))
        if not suffix and not pre_currency and not re.search(
                r"(?:ricav|ebitda|utile|debito|fatturat|nfp|pfn).{0,20}" + re.escape(m.group(1)), value, re.I):
            continue
        n = _num(m.group(1))
        if n is None:
            continue
        cand = {round(n, 4)}
        tok = m.group(1)
        if re.fullmatch(r"-?\d{1,3}(?:\.\d{3})+", tok):
            cand.add(round(float(tok.replace(".", "")), 4))
        if cand & known:
            continue
        spans.append((m.start(), m.end()))
    if not spans:
        return value
    out = value
    for s, e in reversed(spans):
        out = out[:s] + "N/D" + out[e:]
    return out + _ND_MARK


def neutralize_ungrounded_numbers(deliverable: dict, inputs: dict, facts: dict,
                                  citations: list | None = None) -> dict:
    """Boost FINANZIARI, numeri hard non-grounded: NON etichetta — RIMUOVE (→ N/D).

    Complementare a scrub_ungrounded_numbers (che sui financial è NO-OP): quando il gate
    trova valori inventati e la policy no-vicolo-cieco impone comunque la consegna, qui
    il numero sparisce e resta il buco ONESTO. Il report esce preliminare, mai una cifra
    fabbricata presentata come scenario."""
    known = grounded_numbers(inputs, facts, citations)
    out = deepcopy(deliverable)

    def walk(v):
        if isinstance(v, dict):
            return {k: walk(x) for k, x in v.items()}
        if isinstance(v, list):
            return [walk(x) for x in v]
        if isinstance(v, str):
            return _neutralize_value(v, known)
        return v

    return walk(out)


# ── Sanitizer valori implausibili (bug prod 8 lug 2026: 'Impatto: 2024.0') ─────────
# L'LLM a volte fa trapelare un ANNO in un campo numerico percent-like (impatto,
# probabilità, scostamento). Regola precisa (zero falsi positivi su 'impatto 2000€'):
# il valore è un intero che coincide con un anno NOTO al job (anni bilancio negli input
# o anno corrente ±1) dentro una chiave percent-like → la voce è corrotta e si scarta.
_PERCENTLIKE_KEY = re.compile(
    r"(^|_)(impatto|probabilita|percentuale|scostamento(_percentuale)?|peso)($|_)")


def _known_years(inputs: dict) -> set[int]:
    years = {datetime.now().year - 1, datetime.now().year, datetime.now().year + 1}
    blob = json.dumps(inputs or {}, ensure_ascii=False, default=str)
    for m in re.finditer(r"\b(19\d{2}|20\d{2})\b", blob):
        years.add(int(m.group(1)))
    return years


def sanitize_implausible_numbers(deliverable: dict, inputs: dict) -> tuple[dict, int]:
    """Rimuove i valori anno-trapelato dai campi percent-like, per QUALSIASI boost.
    Se il campo corrotto sta in un elemento di lista, l'elemento viene eliminato
    (schema-safe); altrimenti il valore diventa None. Ritorna (deliverable, n_rimossi)."""
    if not isinstance(deliverable, dict):
        return deliverable, 0
    years = _known_years(inputs)
    removed = 0

    def _is_year_leak(k, v):
        lk = str(k).lower()
        if re.search(r"eur|euro|importo|valore|anno", lk):
            return False               # campi monetari/anno legittimi: mai toccati
        return (_PERCENTLIKE_KEY.search(lk)
                and isinstance(v, (int, float)) and not isinstance(v, bool)
                and float(v) == int(v) and int(v) in years)

    def walk(v):
        nonlocal removed
        if isinstance(v, dict):
            out = {}
            for k, x in v.items():
                if _is_year_leak(k, x):
                    removed += 1
                    out[k] = None
                else:
                    out[k] = walk(x)
            return out
        if isinstance(v, list):
            kept = []
            for item in v:
                if isinstance(item, dict) and any(_is_year_leak(k, x) for k, x in item.items()):
                    removed += 1        # elemento corrotto → via (schema-safe sulle array)
                    continue
                kept.append(walk(item))
            return kept
        return v

    return walk(deepcopy(deliverable)), removed


def uncertain_fact_findings(deliverable: dict, strict: bool = True) -> list[dict]:
    full = "\n".join(str(v) for v in _walk(deliverable) if isinstance(v, str))
    return [{
        "code": "fatto_cliente_ipotetico", "severity": "block" if strict else "warn",
        "dettaglio": "un dato controllabile del cliente e stato sostituito da una supposizione; va raccolto o dichiarato non disponibile",
    }] if _UNCERTAIN_CLIENT_FACT.search(full) else []
