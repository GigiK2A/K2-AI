"""CAGE — il validatore che dà i denti al Grounding Contract (handoff Luca §2).

Layer di enforcement nel motore 8e: valida l'output del Boost PRIMA che esca,
facendo rispettare le 3 classi di claim del contratto (oggi solo istruzioni nelle
SKILL.md, niente le obbliga):

- C1  fatto-cliente verificabile (es. "il cliente non ha LinkedIn"): ammesso solo
      se viene dall'input, o tool-verificato+citato, o marcato [IPOTESI DA CONFERMARE].
      Mai un fatto-cliente nudo.
- C2  fatto esterno oggettivo (legge, dato di mercato): instradato a fonte grounded
      e CITATO, mai da memoria dell'LLM. Rigetta numeri/norme senza marker di citazione.
- C3  giudizio (punteggi, posizionamento, prioritizzazione): a bande/rubrica, MAI
      falsa precisione (no "0,75 / 0,35"); la prioritizzazione deve DIFFERENZIARE.

Ordine dei layer: FEED → ROUTE → FORMAT → CAGE (il CAGE è ULTIMO: su una pipeline
affamata produce solo buchi — prima si nutre, poi si ingabbia).

Deterministico, no LLM. Gira sul JSON generato. Findings con severità 'block'
(non si consegna) o 'warn' (si annota) + la 'classe' del contratto (C1/C2/C3).
"""
from __future__ import annotations

import re
from typing import Any, Iterable

from . import quality

# Segnaposto/template che NON devono MAI trapelare in un deliverable venduto.
_PLACEHOLDER_PATTERNS: list[tuple[str, str]] = [
    (r"\[\s*BOZZA\s+OFFLINE\s*\]", "bozza offline"),
    (r"\bSegnaposto deterministico\b", "testo di fallback interno"),
    (r"\boverride_locale\b", "identificatore interno della fonte"),
    (r"\bANTHROPIC_API_KEY\b", "configurazione interna"),
    (r"\[\s*citt[aà]\s*\]", "segnaposto [città]"),
    (r"\[\s*regione\s*\]", "segnaposto [regione]"),
    (r"\[\s*mese\s*/?\s*anno\s*\]", "segnaposto [mese/anno]"),
    (r"\bDM\s*FER\s*-?\s*X\b", "norma-segnaposto 'DM FER-X'"),
    (r"\bFER\s*-\s*X\b", "segnaposto 'FER-X'"),
    (r"\bregolamento\s+FER-?X\b", "segnaposto 'Regolamento FER-X'"),
    (r"\[[a-zàèéìòù ]{2,24}\]", "segnaposto generico [...]"),
]
# Marker DI SISTEMA tra parentesi quadre che NON sono template trapelati: il degrado
# offline (filiera senza API) produce '[BOZZA OFFLINE]' di proposito. Esenti dal block.
_PLACEHOLDER_EXEMPT = {"[bozza offline]"}
_COVER_GENERICA = {"", "cliente", "—", "-", "n/d", "azienda", "la tua azienda"}


def _walk_strings(v: Any) -> Iterable[str]:
    if isinstance(v, str):
        yield v
    elif isinstance(v, dict):
        for x in v.values():
            yield from _walk_strings(x)
    elif isinstance(v, list):
        for x in v:
            yield from _walk_strings(x)


def _collect_priorities(deliverable: dict) -> list[str]:
    """Raccoglie i valori di campi 'priorità/priorita/priority' nelle iniziative."""
    found: list[str] = []

    def rec(v: Any) -> None:
        if isinstance(v, dict):
            for k, val in v.items():
                if re.fullmatch(r"priorit[aà]|priority", str(k).strip().lower()) and isinstance(val, str) and val.strip():
                    found.append(val.strip())
                else:
                    rec(val)
        elif isinstance(v, list):
            for x in v:
                rec(x)

    rec(deliverable)
    return found


# C3 — coordinate di posizionamento a falsa precisione: chiavi tipo coordinata_x/y
# (o x/y, score_x/y) con un valore DECIMALE o frazionario 0-1 = numero inventato
# spacciato per misura. Le bande intere (0,1,2) sono un indice legittimo: si ignorano.
_COORD_KEY = re.compile(r"coordinata_[xy]|coord_[xy]|score_[xy]|punteggio_[xy]|[xy]")


def _collect_coords(v: Any, out: list[tuple[str, Any]]) -> None:
    if isinstance(v, dict):
        for k, val in v.items():
            if _COORD_KEY.fullmatch(str(k).strip().lower()) and isinstance(val, (int, float)) \
                    and not isinstance(val, bool):
                f = float(val)
                if f != int(f) or 0 < f < 1:   # decimale, o frazione 0-1: falsa precisione
                    out.append((str(k), val))
            else:
                _collect_coords(val, out)
    elif isinstance(v, list):
        for x in v:
            _collect_coords(x, out)


# C1 — fatto-cliente verificabile (presenza/assenza di un canale del cliente).
# Ammesso solo se viene dall'input o è marcato [IPOTESI]; mai asserito nudo.
_C1_CANALI = ("linkedin", "google business", "google my business", "sito web", "sito",
              "seo", "instagram", "facebook", "newsletter", "blog", "youtube", "tiktok")
_C1_PATTERNS = (
    # canale → verbo-di-assenza ("LinkedIn assente", "sito non ottimizzato")
    re.compile(
        r"(?:linkedin|google\s+(?:my\s+)?business|sito(?:\s+web)?|seo|instagram|facebook|newsletter|blog|youtube|tiktok)"
        r"[^.\n]{0,45}?"
        r"(?:assente|assenti|mancante|inesistente|non\s+(?:è\s+)?presente|non\s+presidiat\w*|"
        r"non\s+ottimizzat\w*|non\s+(?:lo\s+|la\s+)?(?:ha|hanno|usa|usano|gestisc\w+)|"
        r"dormiente|inattiv\w*|fermo|trascurat\w*|priv[oa])",
        re.I),
    # verbo-di-assenza → canale ("assenza di LinkedIn", "non ha un profilo Instagram")
    re.compile(
        r"(?:assenza|mancanza|priv[oa]|senza|non\s+(?:ha|hanno|dispone|dispongono|presidia|gestisce))"
        r"[^.\n]{0,30}?"
        r"(?:profilo\s+)?(?:linkedin|google\s+(?:my\s+)?business|sito(?:\s+web)?|seo|instagram|facebook|newsletter|blog|youtube|tiktok)",
        re.I),
)

# C2 — riferimento normativo (DM/DL/DPR/D.Lgs/L. n/anno). Se è nel testo ma non tra le
# citazioni grounded = norma da memoria (es. "DM 143/2013" sui minimi tariffari, ABOLITI
# dal DL 1/2012). Estremo tipico: prefisso-token + numero + (/|-) + anno.
_C2_NORMA = re.compile(
    r"\b(d\.?\s?m\.?|d\.?\s?l\.?|d\.?\s?p\.?r\.?|d\.?\s?lgs\.?|legge|l\.)\s*(?:n\.?\s*)?(\d{1,4})\s*[/\-]\s*(\d{2,4})",
    re.I)


def integrity_findings(deliverable: dict, *, citazioni: list | None = None,
                       inputs: dict | None = None, facts: dict | None = None,
                       strict: bool = True) -> list[dict]:
    citazioni = citazioni or []
    findings: list[dict] = []
    full = "\n".join(_walk_strings(deliverable))

    # 1. SEGNAPOSTO TRAPELATI → block (output rotto/non professionale). I marker di
    #    sistema (es. '[BOZZA OFFLINE]') sono esenti: non sono template trapelati.
    for pat, desc in _PLACEHOLDER_PATTERNS:
        for m in re.finditer(pat, full, re.I):
            if m.group(0).strip().lower() in _PLACEHOLDER_EXEMPT:
                continue
            findings.append({"code": "placeholder_leak", "severity": "block",
                             "dettaglio": f"{desc}: \"{m.group(0)}\""})
            break   # un finding per pattern basta

    # 2. COVER non personalizzata → warn
    meta = deliverable.get("meta") or deliverable.get("metadata") or {}
    cliente = str(meta.get("cliente") or meta.get("azienda") or meta.get("client_name") or "").strip()
    if cliente.lower() in _COVER_GENERICA:
        findings.append({"code": "cover_non_personalizzata", "severity": "block",
                         "dettaglio": f"meta.cliente generico ('{cliente or 'vuoto'}') invece del nome reale"})

    # ── C2 · NUMERI ESTERNI (target normativi/UE/mercato) asseriti senza essere tra
    #    le citazioni grounded → warn. È il 'FER al 72%' inventato del report Strategy.
    grounded = " ".join(_walk_strings(citazioni))
    grounded_low = grounded.lower()
    grounded_nums = set(re.findall(r"\d+(?:[.,]\d+)?", grounded))
    for m in re.finditer(
        r"(?:target|obiettiv\w*|UE|europ\w*|direttiv\w*|regolament\w*|RED\s*III|PNIEC|FER)[^.]{0,70}?(\d{1,3}(?:[.,]\d+)?)\s*%",
        full, re.I):
        num = m.group(1)
        if num not in grounded_nums:
            findings.append({"code": "numero_esterno_non_grounded", "classe": "C2", "severity": "warn",
                             "dettaglio": f"'{num}%' asserito come fatto normativo/di mercato senza citazione grounded"})

    # ── C2 · NORMA citata a memoria: un estremo di legge (DM/DL/DPR/D.Lgs/L. n/anno)
    #    presente nel testo ma assente dalle citazioni grounded = recall non verificato.
    #    È la 'tariffe minime ex DM 143/2013' del report Strategy (minimi ABOLITI dal
    #    DL 1/2012): l'LLM cita una norma a memoria, per giunta superata.
    for m in _C2_NORMA.finditer(full):
        ref = re.sub(r"\s+", " ", m.group(0)).strip()
        num = m.group(2)
        if num not in grounded_nums and ref.lower() not in grounded_low:
            findings.append({"code": "norma_non_citata", "classe": "C2", "severity": "warn",
                             "dettaglio": f"riferimento normativo '{ref}' asserito senza citazione grounded "
                                          f"(rischio norma da recall / superata, es. minimi tariffari aboliti dal DL 1/2012)"})

    # ── C3 · COORDINATE a falsa precisione: la mappa di posizionamento con
    #    coordinata_x=0,75 / coordinata_y=0,35 — decimali inventati spacciati per
    #    misura. Il render le converte già in bande (non trapelano nel PDF): qui le
    #    si flagga alla fonte (warn: l'artefatto è mitigato, l'audit resta).
    coords: list[tuple[str, Any]] = []
    _collect_coords(deliverable, coords)
    if coords:
        esempio = ", ".join(f"{k}={v}" for k, v in coords[:3])
        findings.append({"code": "coordinate_falsa_precisione", "classe": "C3", "severity": "warn",
                         "dettaglio": f"posizionamento a falsa precisione ({esempio}"
                                      f"{'…' if len(coords) > 3 else ''}, {len(coords)} valori decimali): "
                                      f"il giudizio va a bande/rubrica, non a coordinate inventate"})

    # ── C1 · FATTO-CLIENTE verificabile asserito nudo (senza fonte né [IPOTESI]).
    #    È il 'LinkedIn assente' del report Strategy: affermazione su un canale del
    #    cliente che NON è nell'input e NON è marcata [IPOTESI] → fatto confabulato.
    input_text = " ".join(_walk_strings(inputs or {})).lower()
    for pat in _C1_PATTERNS:
        for m in pat.finditer(full):
            frase = m.group(0)
            low = frase.lower()
            canale = next((c for c in _C1_CANALI if c in low), "canale")
            ctx = full[max(0, m.start() - 60): m.end() + 24].lower()
            if canale in input_text or "ipotesi" in ctx or "da confermare" in ctx or "da verificare" in ctx:
                continue
            findings.append({"code": "fatto_cliente_non_verificato", "classe": "C1", "severity": "warn",
                             "dettaglio": f"fatto-cliente verificabile asserito senza fonte né [IPOTESI]: "
                                          f"\"{frase.strip()[:72]}\" (canale '{canale}' non nei dati d'ingresso)"})

    # 3b. DEPTH-vs-DATA → warn: deliverable ricco su input scarni = la RADICE del
    #     generico (16 pagine sicure su 4 fatti + 'non ho dati'). Non blocca, ma
    #     segnala che l'analisi è probabilmente archetipo, non QUESTO cliente.
    sostanziali = sum(1 for v in _walk_strings(inputs or {}) if len(str(v).strip()) >= 3)
    if inputs is not None and sostanziali < 5 and len(full) > 4000:
        findings.append({"code": "input_povero", "severity": "block",
                         "dettaglio": f"deliverable ricco (~{len(full)} caratteri) su soli {sostanziali} dati "
                                      f"cliente sostanziali: rischio analisi generica/archetipo, non specifica"})

    # 3c. Falsa precisione economica e fatti cliente ipotetici. Questi controlli
    # sono condivisi da Finance, Strategy, Legal, Web, MEP, Safety, Host ecc.
    findings.extend(quality.unsupported_number_findings(
        deliverable, inputs or {}, facts or {}, citazioni, strict=strict,
    ))
    findings.extend(quality.uncertain_fact_findings(deliverable, strict=strict))

    # ── C3 · PRIORITÀ indifferenziate → warn (la 'lettura prioritizzata' è vuota)
    prios = _collect_priorities(deliverable)
    if len(prios) >= 3 and len({p.lower() for p in prios}) == 1:
        findings.append({"code": "priorita_indifferenziate", "classe": "C3", "severity": "warn",
                         "dettaglio": f"tutte le {len(prios)} iniziative hanno priorità '{prios[0]}': "
                                      f"il documento promette priorità ma non le differenzia"})

    # Boost QUALITATIVI (strict=False): l'integrità è ADVISORY — segnaposto/cover/numeri
    # non-grounded sono benchmark di settore o dati mancanti, non numeri-CLIENTE fabbricati:
    # si annotano (warn), NON bloccano un deliverable pagato. I boost FINANZIARI (strict=True)
    # restano fail-closed (il bug FinanceBoost). required_inputs_findings resta block a parte.
    if not strict:
        for f in findings:
            if f.get("severity") == "block":
                f["severity"] = "warn"
    # dedup (stesso code+dettaglio)
    seen, uniq = set(), []
    for f in findings:
        key = (f["code"], f["dettaglio"])
        if key not in seen:
            seen.add(key)
            uniq.append(f)
    return uniq


def required_inputs_findings(form_schema: dict | None, inputs: dict | None) -> list[dict]:
    """FEED-completeness (C1) — i campi 'required' del form.json del blueprint che NON
    sono arrivati negli input estratti dalla conversazione.

    Il form.json è la SSOT di cosa serve al boost. Oggi il suo `required` è solo
    ADVISORY: proietta in /v1/form → l'autofill ci mette '(OBBLIGATORIO)' nel prompt,
    ma se la chat non conteneva quel dato il campo viene omesso e la generazione parte
    LO STESSO su dati parziali — la radice del report-archetipo. Qui si rende il
    `required` un segnale vero: i fatti-cliente indispensabili mancanti diventano un
    finding C1 (le chiavi degli input combaciano con gli id del form, niente falsi
    positivi). Severità warn, come il resto del CAGE (vedi nota nel modulo)."""
    if not form_schema or inputs is None:
        return []
    required = form_schema.get("required")
    if not isinstance(required, list):
        return []
    props = form_schema.get("properties") if isinstance(form_schema.get("properties"), dict) else {}
    findings: list[dict] = []
    for name in required:
        if inputs.get(name) in (None, "", [], {}):
            desc = ((props or {}).get(name) or {}).get("description") or name
            findings.append({"code": "campo_obbligatorio_mancante", "classe": "C1", "severity": "warn",
                             "dettaglio": f"campo obbligatorio del form '{name}' assente dagli input estratti "
                                          f"(il boost lo dichiara indispensabile: {str(desc)[:80]})"})
    return findings


def blocks(findings: list[dict]) -> list[dict]:
    return [f for f in findings if f.get("severity") == "block"]
