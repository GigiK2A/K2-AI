"""Deliverable readiness — la decisione deterministica "quali campi OBBLIGATORI del
boost mancano ancora?".

Radice del bug ricorrente: la chat (Haiku) decideva "ho tutto" su 4 campi generici,
cieca ai campi `required` del form del boost instradato (es. StrategyBoost esige
`competitor` + `obiettivo_strategico`). L'autofill omette il non-detto (giusto: niente
invenzioni) → il Gate 0 dell'8e fa fail-closed → l'utente vede un vicolo cieco generico.

Questo modulo è la SSOT condivisa da due punti:
- pre-flight di `/deliverables/auto`: se manca un required → 409 `needs_input` che NOMINA
  cosa serve, invece di spendere una generazione e farla rifiutare dall'8e;
- prompt della chat: dice al bot COSA deve ancora raccogliere prima di dichiararsi pronto.

Puro, niente import dell'app: testato standalone come services.py.
"""
from __future__ import annotations

from typing import Any

_EMPTY = (None, "", [], {})
_GENERIC_NAMES = {"", "cliente", "azienda", "la tua azienda", "n/d", "-", "—"}


def has_identity(inputs: dict | None) -> bool:
    """Vero se gli input contengono un nome-cliente USABILE. Mirror di 8e
    quality.display_name: il Gate 0 dell'8e lo esige per personalizzare il report, ma il
    pre-flight non lo controllava → un'identità mancante cadeva nel Gate 0 (errore generico)
    invece di essere nominata. Qui la riconosciamo per dirla tra i dati mancanti."""
    inputs = inputs or {}
    for k in ("ragione_sociale", "denominazione", "azienda", "nome", "client_name"):
        v = str(inputs.get(k) or "").strip()
        if v and v.lower() not in _GENERIC_NAMES:
            return True
    # StrategyBoost usa una descrizione libera: vale come identità solo se breve/nominale
    # (come 8e: una descrizione lunga NON è un nome).
    desc = str(inputs.get("descrizione_azienda") or "").strip()
    return bool(desc) and len(desc) <= 100


def _looks_numeric(s: str) -> bool:
    """Vero se la stringa è un numero, tollerando i separatori IT ('1.234.567', '1.234,56')
    e EN ('1,234.56', '1234.56'). Mirror leggero di autofill._as_num (readiness resta
    puro, niente import di autofill che dipende da settings)."""
    s = s.strip()
    if not s:
        return False
    has_dot, has_comma = "." in s, "," in s
    if has_dot and has_comma:
        s = s.replace(".", "").replace(",", ".") if s.rfind(",") > s.rfind(".") else s.replace(",", "")
    elif has_comma:
        s = s.replace(",", ".") if s.count(",") == 1 else s.replace(",", "")
    elif has_dot and s.count(".") > 1:
        s = s.replace(".", "")
    try:
        float(s)
        return True
    except Exception:
        return False


_IMPLAUSIBLE_TEXT = {"non lo so", "non so", "boh", "non saprei", "?", "n.d.", "n/d",
                     "nd", "non disponibile", "non ho", "non ce l'ho", "sconosciuto",
                     "da definire", "tbd", "-", "—", "non pervenuto", "non applicabile"}


def _campo_value_plausible(campo: dict, v: Any) -> bool:
    """Plausibilità di un valore per un CAMPO del form 8e (shape {id, tipo, enum, ...},
    diversa dal JSON-schema `prop` di `_value_plausible`). Lenient: vero salvo violazioni
    PALESI. Serve a bocciare i required 'presenti ma spazzatura' (es. fatturato='non lo so')
    che passavano il pre-flight, facevano pagare e venivano rifiutati a valle dall'8e.

    ATTENZIONE: 0 / 0.0 / False sono valori LEGITTIMI per numeri/booleani → mai scartati."""
    tipo = str(campo.get("tipo") or "").strip().lower()
    # Booleani: qualunque bool è valido (False incluso).
    if tipo == "boolean":
        return isinstance(v, bool) or str(v).strip().lower() in (
            "true", "false", "si", "sì", "no", "yes", "1", "0")
    # Numerici: 0 è legittimo. Boccia solo se NON convertibile a numero (testo libero).
    if tipo in ("integer", "number"):
        if isinstance(v, bool):
            return False  # un bool in un campo numerico è un errore di estrazione
        if isinstance(v, (int, float)):
            return True
        return _looks_numeric(str(v))
    # Enum: il valore deve essere tra quelli ammessi.
    enum = campo.get("enum")
    if isinstance(enum, (list, tuple)) and enum:
        if isinstance(v, list):
            return bool(v) and all(x in enum for x in v)
        return v in enum
    # Testo libero: boccia solo i non-valori palesi ('non lo so', '?', 'n/d').
    if isinstance(v, str):
        if v.strip().lower() in _IMPLAUSIBLE_TEXT:
            return False
    return True


def missing_required(campi: list[dict] | None, inputs: dict | None) -> list[dict]:
    """I campi del form marcati `obbligatorio` il cui valore è assente/vuoto O IMPLAUSIBILE.

    `campi` è la proiezione 8e di `/v1/form` ({id, obbligatorio, label, tipo, enum, ...});
    `inputs` è il dict auto-compilato dalla conversazione. Combacia col Gate 0 dell'8e
    (`validate_required_inputs`): un required assente = report non generabile. In più
    NOMINA i required presenti ma implausibili (es. fatturato='non lo so'), che il gate
    dell'8e rifiuterebbe DOPO il pagamento → qui evitiamo il vicolo cieco pagato."""
    inputs = inputs or {}
    out: list[dict] = []
    for c in campi or []:
        if not isinstance(c, dict) or not c.get("obbligatorio"):
            continue
        cid = c.get("id")
        if not cid:
            continue
        v = inputs.get(cid)
        if v in _EMPTY or not _campo_value_plausible(c, v):
            out.append(c)
    return out


def _label(campo: dict) -> str:
    return str(campo.get("label") or campo.get("descrizione") or campo.get("id") or "").strip()


def format_missing_labels(campi: list[dict] | None) -> str:
    """Etichette leggibili dei campi mancanti, per il messaggio all'utente."""
    return "; ".join(lbl for lbl in (_label(c) for c in (campi or [])) if lbl)


def _is_url(x: Any) -> bool:
    return isinstance(x, str) and x.strip().lower().startswith(("http://", "https://"))


def _value_plausible(prop: dict, v: Any) -> bool:
    """Lenient: vero salvo violazioni PALESI. Oggi copre i campi che vogliono URL
    (`format: uri`) ma ricevono testo libero — il caso reale: WebBoost `competitor`
    esige URL, ma la chat trova NOMI. Tutto il resto passa (non si scarta a caso)."""
    if not isinstance(prop, dict):
        return True
    types = prop.get("type")
    types = types if isinstance(types, list) else [types]
    if "array" in types and isinstance(v, list):
        items = prop.get("items") or {}
        if isinstance(items, dict) and items.get("format") == "uri":
            return all(_is_url(x) for x in v)
    if "string" in types and prop.get("format") == "uri":
        return _is_url(v)
    return True


def drop_invalid_optional(form_schema: dict | None, inputs: dict | None) -> tuple[dict, list[str]]:
    """Scarta dagli input i campi OPZIONALI il cui valore viola palesemente lo schema,
    così un dato auto-estratto sbagliato (es. competitor=nomi vs campo che vuole URL) non
    fa rifiutare la generazione dall'8e. I REQUIRED non si toccano MAI (li gestisce
    `missing_required`, che blocca con un messaggio leggibile). Ritorna (inputs, scartati).

    Self-adjusting: se l'8e allenta lo schema (competitor non più 'uri'), `_value_plausible`
    ritorna vero → il campo NON viene scartato → i valori fluiscono."""
    inputs = dict(inputs or {})
    if not isinstance(form_schema, dict):
        return inputs, []
    props = form_schema.get("properties") or {}
    required = set(form_schema.get("required") or [])
    dropped: list[str] = []
    for k, v in list(inputs.items()):
        if k in required or k not in props:
            continue
        prop = props[k]
        # Array a ENUM: l'autofill a volte inventa valori FUORI enum (es.
        # tratta_dati_personali=['anagrafe_cliente','email'] vs ammessi
        # ['clienti','dipendenti',...]) → l'8e rifiuta un campo OPZIONALE = vicolo cieco.
        # Sanitizza: tieni solo i valori ammessi; se resta vuoto, scarta il campo.
        items = prop.get("items") if isinstance(prop, dict) else None
        item_enum = items.get("enum") if isinstance(items, dict) else None
        if item_enum and isinstance(v, list):
            valid = [x for x in v if x in item_enum]
            if valid != v:
                if valid:
                    inputs[k] = valid
                else:
                    inputs.pop(k, None)
                    dropped.append(k)
                continue
        if not _value_plausible(prop, v):
            inputs.pop(k, None)
            dropped.append(k)
    return inputs, dropped


# Campi che servono al TEMPLATE (intestazione/personalizzazione del PDF), non alla
# diagnosi: mai trasformarli in barriera consulenziale (eval: "confusione tra dati di
# template e dati di consulenza" — la richiesta di ragione sociale a diagnosi quasi
# completa faceva percepire un questionario burocratico).
_TEMPLATE_FIELD_IDS = frozenset({"ragione_sociale", "forma_giuridica", "descrizione_azienda"})


def required_fields_hint(campi: list[dict] | None, boost_label: str | None = None,
                         consulenza_ricca: bool = False) -> str:
    """Istruzione per il system prompt della chat sui campi che il boost instradato esige.

    DATI DI CONSULENZA vs DATI DI TEMPLATE: i campi diagnostici si chiedono solo se
    pertinenti al caso; quelli di template (intestazione) in UNA sola domanda leggera in
    coda. Un campo mancante NON blocca il summary: il motore produce comunque un report
    PRELIMINARE con stime dichiarate (auth_level PARTIAL in /deliverables/auto).

    `consulenza_ricca` (bug routing 18 lug): quando la consulenza ha già prodotto una
    diagnosi/analisi, ESSA è la fonte del report — NON si chiedono i campi di analisi del
    template solo perché il form li prevede (era: crisi organizzativa → StrategyBoost →
    «mi servono competitor, anno fondazione…»). Ciò che manca si ricava dalla conversazione
    o si dichiara come assunzione. `boost_label` NON viene mai mostrato all'utente (i nomi
    interni dei boost non devono trapelare in chat)."""
    obbligatori = [c for c in (campi or []) if isinstance(c, dict) and c.get("obbligatorio") and c.get("id")]
    if not obbligatori:
        return ""
    diag = [c for c in obbligatori if c["id"] not in _TEMPLATE_FIELD_IDS]
    tmpl = [c for c in obbligatori if c["id"] in _TEMPLATE_FIELD_IDS]
    # NB: mai «boost_label» nel testo — il nome interno del report non va all'utente.
    parts = ["\nCAMPI DEL DOCUMENTO:"]
    intestazione = (
        "- Per INTESTARE il PDF serve solo il nome dell'azienda (e la forma giuridica se "
        "emerge): chiedilo in UNA domanda leggera poco prima del summary, MAI come requisito "
        "che interrompe la consulenza."
    )
    if consulenza_ricca:
        # la consulenza È la fonte: nessuna richiesta di campi di analisi del template.
        parts.append(
            "- La consulenza svolta è la FONTE del report: NON chiedere all'utente campi di "
            "analisi solo perché il template li prevede (competitor, obiettivi, dati di "
            "settore, anno fondazione, clienti target…). Ciò che manca si ricava dalla "
            "conversazione o si dichiara come assunzione nel report (che esce PRELIMINARE): è "
            "il comportamento corretto. Il report è la naturale prosecuzione della consulenza."
        )
        if tmpl:
            parts.append(intestazione)
        return "\n".join(parts) + "\n"
    if diag:
        voci = "; ".join(f"{c['id']} ({_label(c)})" if _label(c) and _label(c) != c["id"] else str(c["id"])
                         for c in diag)
        parts.append(
            f"- DATI DI ANALISI: {voci}. Chiedili SOLO se pertinenti al caso concreto e se non già "
            "deducibili dalla conversazione — mai come modulo. Se l'utente non li ha o non sono "
            "pertinenti, NON insistere e NON bloccare: emetti comunque il summary (il documento "
            "uscirà come PRELIMINARE con stime dichiarate, ed è il comportamento corretto)."
        )
    if tmpl:
        parts.append(intestazione)
    return "\n".join(parts) + "\n"
