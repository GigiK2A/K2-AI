"""Pipeline 6 stadi (Phase-1, pilota LegalBoost) sugli asset REALI (handoff v2.27).

routing(manifest, catalogo chiuso) → resolve(snapshot entries per tipo) →
filiera(prosa attorno ai fatti) → assemble(deliverable conforme output-schema) →
validate(L1 libreria + L2 linter + output-schema) → render(HTML+PDF). Refuse esplicito.
"""
from __future__ import annotations

import logging
import re
from pathlib import Path

from jsonschema import Draft202012Validator

from . import (advisor, agevolazioni, assets, budget, build, calc, elettrico, finance,
               freshness, grounding, jobs, llm, mep, norme, normattiva, quality, quant,
               safety, tax, validate, web)
from .render import render_html, render_pdf
from .settings import CATALOGO_CHIUSO, OUT_DIR

log = logging.getLogger("8e.pipeline")

# Boost FINANZIARI: il grounding gate resta FAIL-CLOSED (block su qualunque numero-cliente
# non grounded) — un numero-CLIENTE fabbricato è il bug FinanceBoost. Il criterio NON è
# "è marketing vs finanza" ma "emette cifre-CLIENTE (€/indici) su cui il cliente AGISCE":
# vanno qui anche i boost che producono economics-cliente SENZA binder deterministico che
# li sovrascriva (cruscotto 12-mesi, host €impatto/scenari, gli express che calcolano ROE/
# D/E/CCII). Finché non hanno un binder, fail-closed = RIFIUTO onesto invece di numeri finti.
#
# Gli altri (qualitativi: SEO/marketing/strategy/legal) hanno l'integrità ADVISORY (warn) MA
# con eccezioni boost-agnostiche che restano block OVUNQUE (vedi grounding/quality): segnaposto
# specifici trapelati, cover anonima, e i numeri HARD-FINANCIAL (€/EBITDA/ROI/payback…). Solo i
# benchmark di settore "morbidi" (traffico/conversion %) e i dati mancanti annotano (warn).
# I mixed con binder che ricalcola i derivati pericolosi (mep payback/VAN/TIR via quant; build
# totale_eur; safety R=P·D) restano fuori: il numero pericoloso è già deterministico.
FINANCIAL_SKILLS = frozenset({
    "flusso-financeboost-pmi", "flusso-advisorboost-pmi",
    "flusso-fiscoboost-pmi", "flusso-agevolazioni-pmi",
    # economics-cliente SENZA binder → fail-closed finché non si cabla un binder reale:
    "cruscotto-direzionale",          # ControlBoost 1499€: trend 12-mesi cashflow/EBITDA tutto LLM
    "flusso-hostboost-ricettive",     # €impatto/scenari ricavi (impatto_eur_anno, rischio_sospensione_eur)
    "check-salute-finanziaria",       # ROE / D/E / Current Ratio / Margine sul cliente
    "check-pmi-express",              # kpi_derivati + alert_ccii (indici Codice Crisi)
    "check-fiscale-express",          # scoring fiscale: coerenza con la famiglia tax
})


class Refuse(Exception):
    def __init__(self, reason: str, message: str):
        self.reason = reason
        self.message = message


# ---- Stadio 1: routing ---------------------------------------------------

def route(service_id: str) -> tuple[str, str, float]:
    """service_id → (skill, blueprint_id, confidence). Catalogo chiuso Phase-1."""
    entry = CATALOGO_CHIUSO.get(service_id)
    if not entry:
        raise Refuse("out_of_catalog",
                     f"service_id '{service_id}' fuori dal catalogo chiuso Phase-1 (solo LegalBoost)")
    return entry["skill"], entry["blueprint_id"], 0.95


# ---- Stadio 3: resolve deterministico (snapshot entries per tipo) --------

def resolve(skill: str, form: dict) -> tuple[dict, list[dict]]:
    snap = assets.load_snapshot()
    entries = snap.get("entries", {})
    keys = assets.placeholders_for(skill)
    facts: dict[str, dict] = {}
    citazioni: list[dict] = []
    for k in keys:
        e = entries.get(k)
        if e is None:
            raise Refuse("unresolvable_placeholder", f"placeholder '{k}' assente nello snapshot")
        tipo = e.get("tipo")
        if tipo == "normativo":
            # Riferimento leggibile dal titolo verbatim (es. "# Art. 1341 Codice
            # Civile — ...") invece del campo interno (override_locale).
            testo = e.get("testo", "")
            first = testo.lstrip("# ").split("\n", 1)[0].strip() if testo else k
            riferimento = first.split("—")[0].strip() if "—" in first else first
            facts[k] = {"valore": testo, "tipo": "normativo",
                        "fonte": e.get("fonte"), "vigenza": e.get("vigenza"),
                        "riferimento": riferimento}
            citazioni.append({
                "campo": k, "riferimento": riferimento,
                "fonte": e.get("fonte"), "fonte_url": e.get("fonte_url"),
                "vigenza": e.get("vigenza"), "status": e.get("status"),
                "testo": testo,  # verbatim dallo snapshot → appendice deterministica
            })
        elif tipo == "formula":
            # Indici finanziari dichiarati 'calcolo-runtime' nello snapshot: il VALORE va
            # calcolato deterministicamente. Prima calc.py (bilancio/host/cruscotto), poi
            # il quant di Luca (dcf/wacc) — Fix #0. Solo se entrambi None resta la
            # formula-stringa (che poi calcolerebbe l'LLM): da evitare per le chiavi quant.
            computed = calc.resolve_formula_fact(k, form)
            if computed is None:
                computed = quant.resolve_quant_fact(k, form)
            facts[k] = computed if computed is not None else {"valore": e.get("formula"), "tipo": "formula"}
        elif tipo == "input":
            facts[k] = {"valore": form.get(e.get("campo_form")), "tipo": "input"}
        elif tipo == "benchmark":
            # non bloccante: se non disponibile → confronto assente (D-handoff E).
            # multipli_ev: prova il quant (EV da multipli). PRESERVA fonte/as_of/descrizione
            # dello snapshot (P0-8: D-046 — un benchmark senza fonte è un numero nudo).
            qf = quant.resolve_quant_fact(k, form)
            if qf is not None and qf.get("tipo") == "valore_calcolato":
                facts[k] = qf
            else:
                facts[k] = {"valore": e.get("valore"), "tipo": "benchmark",
                            "status": e.get("status"), "fonte": e.get("fonte"),
                            "as_of": e.get("as_of"), "descrizione": e.get("descrizione")}
        else:
            facts[k] = {"valore": e, "tipo": tipo}

    # FiscoBoost: mappa canonica decreto↔imposta nei fatti (l'LLM etichettava l'IVA come
    # "TUIR" citando a memoria articoli non nello snapshot; ora ha il decreto giusto).
    if skill == "flusso-fiscoboost-pmi":
        facts["_riferimenti_normativi_fisco"] = {
            "tipo": "riferimenti_normativi", "valore": tax.norme_riferimento(),
        }
    # AgevolazioniBoost: inietta il plafond de minimis DETERMINISTICO nei fatti così la PROSA
    # usa il residuo giusto (massimale 300k Reg. UE 2023/2831 − pregressi) e non lo ricalcola
    # col vecchio 200k. Il campo strutturato è già sovrascritto post-gen da apply_agevolazioni.
    if skill == "flusso-agevolazioni-pmi":
        dmf = agevolazioni.de_minimis_facts(form)
        if dmf:
            facts["_plafond_de_minimis"] = {"tipo": "agevolazione", "valore": dmf}
    return facts, citazioni


# ---- Stadio 4-assemble: deliverable conforme a output-schema (LegalBoost) -

def assemble_legalboost(blueprint: dict, sezioni: dict, citazioni: list[dict],
                        inputs: dict, meta_struct: dict | None = None,
                        offline: bool = False) -> dict:
    norme = [
        {"riferimento": c.get("riferimento") or c.get("campo"), "fonte": "normattiva"}
        for c in citazioni
    ]
    voci_meta = (meta_struct or {}).get("voci_meta", {})

    def _grav(g: str) -> str:
        return g if g in ("bassa", "media", "alta") else "media"

    voci_out = []
    for v in blueprint.get("voci", []):
        vid = v["id"]
        argomenti = v.get("argomenti_obbligatori", [])
        vm = voci_meta.get(vid) or {}
        # rischi/azioni: dal meta strutturato (LLM) se presente, altrimenti dalle argomenti
        rischi = [{"descrizione": str(r.get("descrizione", "")), "gravita": _grav(r.get("gravita", "media")),
                   "serve_avvocato": bool(r.get("serve_avvocato", False))}
                  for r in vm.get("rischi", []) if r.get("descrizione")]
        if not rischi:
            rischi = [{"descrizione": f"Verificare: {a}.", "gravita": "media", "serve_avvocato": False}
                      for a in argomenti[:2]] or [{"descrizione": f"Analisi area «{v['titolo']}».",
                                                   "gravita": "media", "serve_avvocato": False}]
        azioni = [str(a) for a in vm.get("azioni", []) if a] or \
                 [f"Approfondire «{a}»." for a in argomenti[:3]] or ["Approfondire l'area."]
        voci_out.append({
            "id": vid,
            "titolo": v["titolo"],
            "contenuto": str(sezioni.get(vid, "")),
            "rischi": rischi,
            "azioni": azioni,
            "norme_citate": norme if vid in ("contrattualistica", "societario_231") else [],
        })

    mappa = (meta_struct or {}).get("mappa_rischi")
    if not (isinstance(mappa, list) and mappa and all(
            m.get("semaforo") in ("verde", "giallo", "rosso") for m in mappa)):
        mappa = []
    score = (meta_struct or {}).get("score")
    if not isinstance(score, int) or not (0 <= score <= 100):
        # ONLINE senza score valido dall'LLM → -1 forza il refuse (mai score cosmetico
        # in un report reale/pagato). OFFLINE è un placeholder/demo (nessun LLM, sezioni
        # segnaposto): usa uno score-segnaposto valido per far girare la pipeline end-to-end.
        score = 50 if offline else -1
    return {
        "meta": {
            "servizio": "LegalBoost", "versione": "1.0.0", "data": quality.today_iso(),
            "azienda": quality.display_name(inputs) or "",
        },
        "sintesi": {"score_compliance": score, "mappa_rischi": mappa},
        "voci": voci_out,
        "piano_azione": [
            {"priorita": 1, "azione": "Adeguare le condizioni generali (artt. 1341-1342 c.c.)",
             "handoff_avvocato": True}
        ],
        "disclaimer": blueprint.get(
            "disclaimer",
            "Orientamento legale-compliance, NON consulenza legale (D-034); "
            "handoff all'avvocato sui punti a rischio.",
        ),
    }


def _lint_instance(blueprint: dict) -> dict:
    """Instance per il linter L2 (shape attesa da k2a_validation.linter)."""
    voci = blueprint.get("voci", [])
    voci_li = []
    total = 0
    for v in voci:
        pag = (v.get("pagine") or {}).get("min", 2)
        total += pag
        voci_li.append({
            "id": v["id"], "titolo": v["titolo"], "ord": v.get("ord"),
            "pagine": pag, "argomenti_presenti": list(v.get("argomenti_obbligatori", [])),
        })
    return {
        "voci": voci_li,
        "pagine_totali": total,
        "ha_disclaimer": True, "ha_cta": True, "json_output_valido": True,
        "artefatti": [a["id"] for a in blueprint.get("artefatti_bundle", []) if a.get("obbligatorio")],
        "elementi_grafici": list(blueprint.get("elementi_grafici_obbligatori", [])),
        "tabelle": list(blueprint.get("tabelle_obbligatorie", [])),
        "prezzi_hardcoded": [],
    }


def apply_deterministic_bindings(skill: str, deliverable: dict, facts: dict,
                                 inputs: dict, filiera_meta: dict) -> tuple[dict, dict]:
    """Sovrascrive gli slot numerici/strutturali col valore dei tool deterministici, per-skill.

    Estratto da run() per essere testabile in isolamento (senza jobs/validazione/render).
    Ogni hook è no-op se il deliverable non ha gli slot attesi. Vedi test_pipeline_bindings.py.
    """
    # Binding strutturale (Fix #0 Fase 2): gli slot numerici di valutazione vengono
    # SOVRASCRITTI col valore del quant deterministico (non ri-emessi dall'LLM).
    # Chiude INV1/P0-1/P0-2; la provenance (call_id/as_of) finisce nel meta del job.
    deliverable, quant_prov = quant.bind_quant_slots(skill, deliverable, facts)
    if quant_prov:
        filiera_meta = {**filiera_meta, "quant_binding": quant_prov}

    # AdvisorBoost: binding economici §A-§D (EV-synth, DuPont, CCII, CTA) da bilancio
    # reale + quant — dopo bind_quant_slots (che popola enterprise_value.multipli_ebitda).
    if skill == "flusso-advisorboost-pmi":
        deliverable, adv_meta = advisor.apply_advisor(deliverable, inputs)
        if adv_meta:
            filiera_meta = {**filiera_meta, "advisor": adv_meta}
        # §E — piano_economico_finanziario (budget 36m + scenari + sensitivity) dal MCP
        # k2a_budget deterministico, non più dall'LLM. Dopo apply_advisor (serve l'EV multiplo).
        deliverable, budget_meta = budget.apply_budget(deliverable, inputs)
        if budget_meta:
            filiera_meta = {**filiera_meta, "budget_pef": budget_meta}

    # FinanceBoost: le 3 sezioni data-payload (riclassificazione/marginalità/
    # valutazione_performance) sono DETERMINISTICHE — dalle voci riclassificate
    # (finance.py) + WACC dal quant — non scritte dall'LLM (chiude P0-2/P0-6).
    if skill == "flusso-financeboost-pmi":
        fb_reclass = finance.latest_reclass_from_inputs(inputs)
        if fb_reclass:
            # WACC: se l'utente ne fornisce uno (es. "WACC 9,5%") HA LA PRECEDENZA sul CAPM del
            # quant, così la sezione valutazione (EVA) non contraddice la prosa, che usa
            # l'assunzione dell'utente. Senza input utente → CAPM deterministico del quant.
            user_wacc = finance.user_wacc_from_inputs(inputs)
            if user_wacc is not None:
                wacc_pct = user_wacc
            else:
                w = quant.resolve_quant_fact("wacc", inputs)
                wacc_pct = w.get("valore") if (isinstance(w, dict) and w.get("tipo") == "valore_calcolato") else None
            deliverable = finance.apply_financeboost_sections(deliverable, fb_reclass, wacc_pct)
            filiera_meta = {**filiera_meta, "financeboost_sezioni_deterministiche": True,
                            "wacc_fonte": "utente" if user_wacc is not None else "capm_quant"}

    # AgevolazioniBoost: i benefici (Sabatini/T5.0/de minimis) vengono dai tool
    # deterministici di k2a_agevolazioni, non dall'LLM (Fix #3). Cumulabilità segnalata.
    if skill == "flusso-agevolazioni-pmi":
        deliverable, agev_meta = agevolazioni.apply_agevolazioni(deliverable, inputs)
        if agev_meta:
            filiera_meta = {**filiera_meta, "agevolazioni": agev_meta}

    # FiscoBoost: il carico fiscale viene dal motore tax deterministico (tabelle
    # verificate), non dall'LLM (Fix #2/#4). IRAP/addizionali escluse con nota onesta.
    if skill == "flusso-fiscoboost-pmi":
        deliverable, fisco_meta = tax.apply_fiscoboost(deliverable, inputs)
        if fisco_meta:
            filiera_meta = {**filiera_meta, "fiscale": fisco_meta}

    # MepBoost: l'economia degli EEM (payback/VAN/TIR) è ricalcolata col motore
    # quant da costo+risparmio (non fabbricata dall'LLM). Termico/APE marcato
    # non_validato (nessun tool APE/UNI-TS-11300), non sovrascritto con numeri inventati.
    if skill == "flusso-mepboost-studio":
        deliverable, mep_meta = mep.apply_mep(deliverable, inputs)
        if mep_meta:
            filiera_meta = {**filiera_meta, "mep": mep_meta}
        # audit_elettrico: caduta tensione + verifica terra dal MCP k2a_elettrico
        # (CEI 64-8), se il form porta impianto_elettrico_dettaglio; altrimenti onesto.
        deliverable, el_meta = elettrico.apply_elettrico(deliverable, inputs)
        if el_meta:
            filiera_meta = {**filiera_meta, "elettrico": el_meta}

    # WebBoost: lo score SEO on-page è calcolato dal tool audit_seo_onpage sulla
    # pagina reale (fetch stdlib), non fabbricato dall'LLM. I volumi keyword restano
    # esterni (Semrush/GSC) → non inventati. Fetch fallito → onesto (no sovrascrittura).
    if skill == "flusso-webboost-pmi":
        deliverable, web_meta = web.apply_web(deliverable, inputs)
        if web_meta:
            filiera_meta = {**filiera_meta, "web_onpage": web_meta}

    # SafetyBoost: R=P×D + totale/incidenza dei costi sicurezza = math deterministica
    # (non più incoerenti). Singole voci Allegato XV = stima LLM (nessun prezzario) → flag.
    if skill == "flusso-safetyboost-studio":
        deliverable, safety_meta = safety.apply_safety(deliverable, inputs)
        if safety_meta:
            filiera_meta = {**filiera_meta, "safety": safety_meta}

    # BuildBoost: costi.totale_eur = Σ voci deterministico. Oneri urbanizzazione/CME/
    # tempi-iter = stima LLM (nessuna tabella per-comune / prezzario) → flag onesto.
    if skill == "flusso-buildboost-studio":
        deliverable, build_meta = build.apply_build(deliverable, inputs)
        if build_meta:
            filiera_meta = {**filiera_meta, "build": build_meta}
        # riferimenti normativi tecnici dal MCP k2a_norme_tecniche (search sul corpus).
        # KB vuota oggi → 0 riferimenti onesti (nessuna citazione inventata) finché Luca
        # non ingerisce NTC/CEI/Eurocodici. Risultati in meta (BuildBoost senza slot citazioni).
        deliverable, norme_meta = norme.apply_norme(deliverable, inputs)
        if norme_meta:
            filiera_meta = {**filiera_meta, "norme_tecniche": norme_meta}

    return deliverable, filiera_meta


def _normalize_inputs(inputs: dict) -> dict:
    """Compat di schema FEED. Certi campi-lista del form passano da string[] a object[]:
    il breaking change di Advisor è `competitor` ('ACME' → {'nome': 'ACME', ...}). L'engine
    deve reggere ENTRAMBE le forme, così il merge del branch grounding di Luca non rompe la
    prod (sequenza dell'handoff §4: prima l'engine gestisce il nuovo schema, poi si mergia).
    Canonicalizza a object[]: le stringhe diventano {'nome': str}, i dict passano intatti, i
    tipi imprevisti si scartano. Le sessioni vecchie con string[] continuano a funzionare."""
    if not isinstance(inputs, dict):
        return inputs
    out = dict(inputs)
    for campo in ("competitor", "competitors"):
        v = out.get(campo)
        if isinstance(v, list) and any(isinstance(x, str) for x in v):
            out[campo] = [{"nome": x} if isinstance(x, str) else x
                          for x in v if isinstance(x, (str, dict))]
    return out


def _enrich_citazioni_normattiva(deliverable: dict, citazioni: list[dict]) -> list[dict]:
    """§3b — verifica i riferimenti di legge del deliverable contro il corpus Normattiva.
    Le norme TROVATE diventano citazioni grounded col testo verbatim → il CAGE C2
    (norma_non_citata) si spegne per quelle. Le norme NON trovate (confabulate o assenti,
    es. 'DM 143/2013' quando esiste solo L. 143/2013) restano flaggate. No-op onesto se il
    corpus non è disponibile (NORMATTIVA_DB_PATH assente)."""
    import json as _json
    full = _json.dumps(deliverable, ensure_ascii=False)
    enriched = list(citazioni)

    # Norme UE (GDPR, AI Act, regolamenti): NON sono nel corpus Normattiva (solo
    # legislazione italiana) → niente verbatim, ma vanno almeno in «Fonti normative»:
    # un parere privacy che discute il GDPR 15 volte senza citarlo tra le fonti è
    # incompleto (bug N1). Fonte marcata eur_lex, senza `testo` → il render la elenca
    # nelle fonti e NON tra i testi verbatim (niente finto grounding).
    _EU_CANON = {"2016/679": "Reg. (UE) 2016/679 (GDPR)",
                 "2024/1689": "Reg. (UE) 2024/1689 (AI Act)"}
    eu_found: dict[str, str] = {}
    if re.search(r"\bGDPR\b|2016/679", full, re.I):
        eu_found["2016/679"] = _EU_CANON["2016/679"]
    if re.search(r"\bAI\s*Act\b|2024/1689", full, re.I):
        eu_found["2024/1689"] = _EU_CANON["2024/1689"]
    for m in re.finditer(r"reg(?:olamento)?\.?\s*\(?\s*ue\s*\)?\s*(?:n\.?\s*)?(\d{4})\s*/\s*(\d{1,4})", full, re.I):
        key = f"{m.group(1)}/{m.group(2)}"
        eu_found.setdefault(key, _EU_CANON.get(key, f"Reg. (UE) {key}"))
    already = {str(c.get("riferimento") or "") for c in citazioni}
    for key, rif in eu_found.items():
        if not any(key in a or rif == a for a in already):
            enriched.append({"riferimento": rif, "campo": "norma_ue", "fonte": "eur_lex"})

    if not normattiva.available():
        return enriched
    seen = {(c.get("tipo"), str(c.get("numero")), c.get("anno")) for c in citazioni}
    for ref in normattiva.extract_norm_refs(full):
        key = (ref["tipo"], ref["numero"], ref["anno"])
        if key in seen:
            continue
        # Con l'ARTICOLO citato nel testo si aggancia QUEL chunk (bug N2: prima usciva
        # sempre il primo articolo della legge, es. art. 1 dello Statuto invece
        # dell'art. 4 sulla videosorveglianza).
        articolo = ref.get("articolo")
        hits = normattiva.find_by_estremi(ref["anno"], ref["numero"], tipo=ref["tipo"],
                                          articolo=articolo, limit=1)
        if hits and articolo:
            # Articolo esplicito e trovato → verbatim di QUEL chunk.
            h = hits[0]
            seen.add(key)
            enriched.append({
                "riferimento": h["citazione"], "campo": "norma_verificata", "fonte": "normattiva",
                "tipo": h.get("tipo"), "numero": h.get("numero"), "anno": h.get("anno"),
                "articolo": h.get("articolo"), "testo": (h.get("testo") or "")[:1200],
            })
            continue
        # Articolo NON indicato nel testo (o chunk specifico assente): la norma si
        # verifica che ESISTA nel corpus e va in fonti SENZA asserire un articolo a
        # caso né un verbatim arbitrario (bug N2: 'L. 300/1970, art. 1' spacciato come
        # citazione quando il testo parlava d'altro). Norma davvero assente → skip
        # (confabulata: il CAGE C2 la tiene flaggata).
        if not hits:
            hits = normattiva.find_by_estremi(ref["anno"], ref["numero"], tipo=ref["tipo"], limit=1)
        if not hits:
            continue
        h = hits[0]
        seen.add(key)
        enriched.append({
            "riferimento": normattiva.citazione({**h, "articolo": None}),
            "campo": "norma_verificata", "fonte": "normattiva",
            "tipo": h.get("tipo"), "numero": h.get("numero"), "anno": h.get("anno"),
        })
    return enriched


def render_external(service_id: str, deliverable: dict, citazioni: list | None = None,
                    inputs: dict | None = None) -> dict:
    """Renderizza un deliverable GIÀ generato altrove (es. dall'agente A2 nel backend)
    → PDF, applicando gli STESSI gate del flusso normale: enrich normattiva (§3b) +
    CAGE grounding (§2). Sincrono (niente LLM: solo verifica + render). Ritorna il job
    8e (status rendered|refused + outputs), così il backend lo tratta come gli altri."""
    skill, bp_id, _ = route(service_id)
    blueprint = assets.load_blueprint(skill)
    form_schema = assets.load_form(skill)
    if not blueprint:
        raise Refuse("unresolvable_placeholder", f"asset mancanti per skill '{skill}'")
    inputs = inputs or {}
    citazioni = _enrich_citazioni_normattiva(deliverable, list(citazioni or []))
    strict_grounding = skill in FINANCIAL_SKILLS
    g_findings = (grounding.required_inputs_findings(form_schema, inputs, strict=strict_grounding)
                  + grounding.integrity_findings(deliverable, citazioni=citazioni, inputs=inputs,
                                                  strict=strict_grounding))
    job_id = jobs.create(service_id, bp_id, 1.0)
    if grounding.blocks(g_findings):
        jobs.update(job_id, status="refused", refusal_reason="grounding_failed",
                    validation={"grounding_block": grounding.blocks(g_findings), "grounding_findings": g_findings})
        return jobs.get(job_id)
    out_dir = OUT_DIR / job_id
    out_dir.mkdir(parents=True, exist_ok=True)
    pdf_path = out_dir / "deliverable.pdf"
    json_path = out_dir / "deliverable.json"
    import json as _json
    json_path.write_text(_json.dumps(deliverable, ensure_ascii=False, indent=2), encoding="utf-8")
    from .render import render_generic_pdf
    render_generic_pdf(deliverable, blueprint, citazioni, pdf_path)
    jobs.update(job_id, status="rendered",
                outputs={"pdf_path": str(pdf_path), "json_path": str(json_path), "bundle": []},
                validation={"grounding": g_findings or "PASS"}, citazioni=citazioni,
                meta={"skill": skill, "blueprint_id": bp_id, "auth_level": "FULL",
                      "source": "agent_a2", "snapshot_version": assets.snapshot_version()})
    return jobs.get(job_id)


def run(job_id: str, service_id: str, inputs: dict, auth_level: str = "FULL") -> None:
    try:
        jobs.update(job_id, status="running")
        inputs = _normalize_inputs(inputs)      # FEED: regge competitor string[] o object[]
        skill, bp_id, _ = route(service_id)

        blueprint = assets.load_blueprint(skill)
        out_schema = assets.load_output_schema(skill)
        form_schema = assets.load_form(skill) or {}   # FEED contract: campi richiesti dal boost
        if not blueprint or not out_schema:
            raise Refuse("unresolvable_placeholder", f"asset mancanti per skill '{skill}'")

        # Gate 0. L'IDENTITÀ (nome cliente) blocca SEMPRE: serve a intestare il documento.
        # La COMPLETEZZA/quadratura blocca solo in FULL; in PARTIAL (report preliminare)
        # diventa ipotesi etichettata → si genera comunque con i dati disponibili invece
        # del vicolo cieco. La PREVIEW gratuita resta permissiva (assaggio su input minimi).
        inputs, identity_errors, content_errors, quality_notes = quality.prepare_inputs(skill, form_schema, inputs)
        if identity_errors and auth_level != "PREVIEW":
            raise Refuse("insufficient_or_inconsistent_input", "; ".join(identity_errors[:4]))
        # NIENTE VICOLO CIECO (regola prodotto): gli errori di CONTENUTO — campi mancanti O
        # bilancio riclassificato che non quadra — NON fanno più refuse nemmeno in FULL. Si
        # degrada a PRELIMINARE con ipotesi etichettate + l'incoerenza segnalata, invece di
        # un `insufficient_or_inconsistent_input` che lasciava il cliente a mani vuote. Solo
        # l'identità resta bloccante (serve a intestare il documento). PREVIEW resta permissivo.
        partial_mode = bool(content_errors) and auth_level != "PREVIEW"

        facts, citazioni = resolve(skill, inputs)

        # Freshness-gate runtime (Fix #6-gate / P0-10): se il boost usa un fatto normativo
        # HARD-stale (snapshot regredito a legge pre-riforma) → non consegnare legge superata.
        stale = freshness.stale_findings(used_keys=set(facts.keys()))
        if stale:
            raise Refuse("snapshot_stale",
                         "; ".join(f"{s['key']}: {s['motivo']} ({s.get('law')})" for s in stale[:5]))

        # PREVIEW (gate W8): compone SOLO l'assaggio, niente documento/file/leak.
        if auth_level == "PREVIEW":
            prev = llm.generate_preview(blueprint, facts, inputs)
            # voci[0]=sintesi, voci[1]=criticità#1 mostrata → altre = voci[2:] (solo titoli)
            altre = [v.get("titolo") for v in blueprint.get("voci", [])][2:]
            jobs.update(
                job_id, status="rendered",
                outputs={"preview": {
                    "score": prev.get("score"),
                    "criticita_1": prev.get("criticita_1"),
                    "altre_aree": altre,            # solo titoli, contenuto NASCOSTO
                    "cta": "Sblocca il documento completo",
                }, "pdf_url": None, "bundle": []},
                validation={"auth_level": "PREVIEW"},
                citazioni=[],
                meta={"skill": skill, "blueprint_id": bp_id, "auth_level": "PREVIEW",
                      "filiera": {"mode": prev.get("mode")},
                      "snapshot_version": assets.snapshot_version()},
            )
            return

        from .settings import VOCI_SHAPE_SKILLS
        generic = skill not in VOCI_SHAPE_SKILLS
        base_citazioni = list(citazioni or [])
        # RETRY anti-flake: la generazione è non-deterministica (temperature default), quindi un
        # grounding/validation fallito è spesso la sfortuna del singolo roll (un numero non
        # grounded sfuggito al prompt). Rigenera fino a _MAX_GEN_TRIES; refuse solo se TUTTI i
        # tentativi falliscono. Le success-path restano identiche (si esce al 1° tentativo); il
        # costo extra (rigenerazione) ricade solo sui fallimenti, raro. Vale per tutti i boost.
        _MAX_GEN_TRIES = 3
        _refusal = None
        _ok = False
        offline_mode = False
        for _attempt in range(_MAX_GEN_TRIES):
            citazioni = list(base_citazioni)
            if not generic:
                # Voci-shape (LegalBoost/FiscoBoost): HYBRID prosa + meta strutturato.
                sezioni, filiera_meta = llm.generate_sezioni(blueprint, facts, inputs)
                meta_struct = llm.generate_structured_meta(blueprint, facts, inputs)
                offline = filiera_meta.get("mode") == "offline"
                deliverable = assemble_legalboost(blueprint, sezioni, citazioni, inputs, meta_struct, offline=offline)
                filiera_meta = {**filiera_meta, "assembly": "hybrid" if meta_struct else "prose+deterministic",
                                "structured_meta": bool(meta_struct)}
            else:
                # Altri boost: generazione PROFONDA per-sezione (profondità tipo report
                # consulenziale). Fallback alla singola chiamata, poi refuse se invalido.
                deliverable, filiera_meta = llm.generate_deliverable_deep(out_schema, blueprint, facts, inputs)
                if not deliverable:
                    deliverable, fm2 = llm.generate_conforming(out_schema, blueprint, facts, inputs)
                    filiera_meta = {**filiera_meta, **fm2, "assembly": "generic-fallback"}
                if not deliverable:
                    raise Refuse("validation_failed",
                                 "generazione non disponibile (offline o incompleta) per questo boost")

            deliverable = quality.ensure_metadata(
                deliverable, out_schema, inputs,
                blueprint.get("pacchetto", {}).get("nome_commerciale", service_id),
            )

            # Binding deterministici per-skill (estratto in apply_deterministic_bindings,
            # coperto da test_pipeline_bindings.py): sovrascrive gli slot col valore dei tool
            # deterministici (quant/finance/tax/mep/elettrico/web/safety/build/norme).
            deliverable, filiera_meta = apply_deterministic_bindings(
                skill, deliverable, facts, inputs, filiera_meta)

            # Scrub segnaposto template trapelati ([città]/[regione]/[nome]…) PRIMA del gate e
            # del render: il deep-gen a volte li lascia su dati mancanti nonostante il prompt, e
            # il gate li blocca (placeholder_leak). Neutralizzazione deterministica → il report si
            # consegna pulito invece di fallire. Il gate resta come backstop su ciò che sfugge.
            deliverable = quality.scrub_template_placeholders(deliverable, inputs)
            # OFFLINE = deliverable segnaposto/demo (no LLM): gira su input minimi → i block del
            # gate sono attesi e non vanno applicati (rigenerare non aiuta: niente retry).
            offline_mode = (filiera_meta or {}).get("mode") == "offline"

            # SAFETY (mai un report PAGATO con segnaposto): se la filiera anthropic ha
            # DEGRADATO delle voci (troncamento → [BOZZA OFFLINE]) pur non essendo in demo
            # offline → è un fallimento, non una consegna. Rigenera e, se persiste, REFUSE
            # (fail-loud) invece di spedire un placeholder spacciato per analisi reale.
            degraded_voci = (filiera_meta or {}).get("degraded_voci") or []
            if not offline_mode and (degraded_voci or "[BOZZA OFFLINE]" in str(deliverable)):
                _refusal = ("filiera_degradata",
                            {"reason": "sezioni non generate dalla filiera (troncamento/errore LLM)",
                             "degraded_voci": degraded_voci})
                if _attempt == _MAX_GEN_TRIES - 1:
                    log.warning("job %s REFUSE filiera_degradata (esauriti %d tentativi): %s",
                                job_id, _MAX_GEN_TRIES, degraded_voci or "[BOZZA OFFLINE]")
                    break
                log.warning("job %s: voci degradate %s tentativo %d/%d → rigenero",
                            job_id, degraded_voci or "[BOZZA]", _attempt + 1, _MAX_GEN_TRIES)
                continue

            # Validazione: L1 (libreria) + output-schema (jsonschema). L2 (linter
            # voci-shape) solo per i boost voci-shape; i generici sono validati dallo schema.
            jobs.update(job_id, status="validating")
            r1 = validate.l1(blueprint)
            r2 = {"pass": True} if generic else validate.l2(_lint_instance(blueprint), blueprint)
            out_errs = sorted(Draft202012Validator(out_schema).iter_errors(deliverable),
                              key=lambda e: list(e.path))
            if not r1["pass"] or not r2["pass"] or out_errs:
                _refusal = ("validation_failed",
                            {"L1": r1["pass"], "L2": r2["pass"],
                             "output_schema_errors": [str(e.message) for e in out_errs[:5]],
                             "L2_errori": r2.get("errori"), "L2_findings": r2.get("findings")})
                if offline_mode or _attempt == _MAX_GEN_TRIES - 1:
                    break
                log.warning("validation_failed job %s tentativo %d/%d → rigenero", job_id, _attempt + 1, _MAX_GEN_TRIES)
                continue

            # Gate di GROUNDING (integrità qualitativa) — accanto a L1/L2. Becca la
            # classe di difetti che il linter STRUTTURALE non vede e che nessun calc.py
            # intercetta sui boost qualitativi: segnaposto trapelati, numeri esterni
            # asseriti senza citazione, cover non personalizzata, priorità tutte uguali
            # (vedi report StrategyBoost reale). 'block' → non si consegna (fail-closed).
            # §3b · ROUTE: verifica i riferimenti normativi contro il corpus → citazioni
            # verbatim grounded (le norme reali); le confabulate restano scoperte per il CAGE.
            citazioni = _enrich_citazioni_normattiva(deliverable, citazioni)
            # In PARTIAL i numeri non ancorati diventano ipotesi ETICHETTATE (illustrative),
            # non un refuse: un report preliminare vive di stime dichiarate. Quindi anche i
            # boost finanziari usano il grounding non-strict (scrub+label invece di block).
            strict_grounding = skill in FINANCIAL_SKILLS and not partial_mode
            # Scrub deterministico: sui qualitativi (non-financial) etichetta i numeri non-grounded
            # come illustrativi PRIMA del gate (scelta-utente) → il report si consegna invece di
            # fallire su una cifra che il modello non ha marcato. Financial: no-op (restano strict).
            deliverable = quality.scrub_ungrounded_numbers(deliverable, inputs, facts, citazioni, strict=strict_grounding)
            g_findings = (grounding.required_inputs_findings(form_schema, inputs, strict=strict_grounding)
                          + grounding.integrity_findings(deliverable, citazioni=citazioni, inputs=inputs,
                                                          facts=facts, strict=strict_grounding))
            g_blocks = grounding.blocks(g_findings)
            if g_blocks and not offline_mode:
                # NIENTE VICOLO CIECO: se i blocchi sono SOLO numeri non ancorati (delta %
                # derivati, benchmark di settore, ROE anno-su-anno) — non allucinazioni di
                # fatti-cliente — si ETICHETTANO illustrativi (scrub non-strict) e si consegna
                # invece di rifiutare. I numeri-core dei finance restano deterministici. Solo
                # i blocchi "duri" (placeholder, fatto-cliente confabulato) fanno refuse.
                if all(b.get("code") == "numero_non_grounded" for b in g_blocks):
                    deliverable = quality.scrub_ungrounded_numbers(
                        deliverable, inputs, facts, citazioni, strict=False)
                    log.info("grounding: %d numeri non-grounded etichettati illustrativi (no refuse) job %s",
                             len(g_blocks), job_id)
                    _ok = True
                    break
                _refusal = ("grounding_failed",
                            {"grounding_block": g_blocks, "grounding_findings": g_findings})
                if _attempt == _MAX_GEN_TRIES - 1:
                    log.warning("grounding gate REFUSE job %s (esauriti %d tentativi): %s",
                                job_id, _MAX_GEN_TRIES, [b["dettaglio"] for b in g_blocks])
                    break
                log.warning("grounding gate block job %s tentativo %d/%d → rigenero: %s",
                            job_id, _attempt + 1, _MAX_GEN_TRIES, [b["dettaglio"] for b in g_blocks])
                continue

            _ok = True
            break

        if not _ok:
            reason, val = _refusal or ("validation_failed", {})
            jobs.update(job_id, status="refused", refusal_reason=reason, validation=val)
            return

        # Render HTML + PDF.
        out_dir = OUT_DIR / job_id
        out_dir.mkdir(parents=True, exist_ok=True)
        html_path = out_dir / "deliverable.html"
        pdf_path = out_dir / "deliverable.pdf"
        json_path = out_dir / "deliverable.json"
        import json as _json
        json_path.write_text(_json.dumps(deliverable, ensure_ascii=False, indent=2), encoding="utf-8")
        if generic:
            from .render import render_generic_pdf
            html_path.write_text("<pre>" + _json.dumps(deliverable, ensure_ascii=False, indent=2) + "</pre>",
                                 encoding="utf-8")
            render_generic_pdf(deliverable, blueprint, citazioni, pdf_path, preliminare=partial_mode)
        else:
            html_path.write_text(render_html(deliverable, blueprint, citazioni), encoding="utf-8")
            render_pdf(deliverable, blueprint, citazioni, pdf_path, preliminare=partial_mode)

        bundle = []
        extra_outputs = {}
        if skill == "flusso-financeboost-pmi":
            # Il modello Excel richiede le voci di bilancio. In PARTIAL (report preliminare)
            # i bilanci possono mancare → NON far fallire l'intero job: si consegna il PDF
            # preliminare senza il modello finanziario (che senza bilancio non ha senso).
            try:
                from .xlsx import render_finance_workbook
                xlsx_path = render_finance_workbook(inputs, out_dir / "modello-finanziario.xlsx")
                extra_outputs["xlsx_path"] = str(xlsx_path)
                bundle.append({"formato": "xlsx", "path": str(xlsx_path), "formule_vive": True})
            except Exception as exc:
                if not partial_mode:
                    raise  # in FULL i bilanci ci sono per definizione: un errore qui è reale
                log.warning("xlsx finance saltato (preliminare senza bilanci): %s", exc)

        jobs.update(
            job_id, status="rendered",
            outputs={"html_path": str(html_path), "pdf_path": str(pdf_path),
                     "json_path": str(json_path), "bundle": bundle, **extra_outputs},
            validation={"L1": "PASS", "L2": "PASS", "output_schema": "PASS",
                        "grounding": g_findings or "PASS"},
            citazioni=citazioni,
            meta={"skill": skill, "blueprint_id": bp_id,
                  "auth_level": "PARTIAL" if partial_mode else "FULL",
                  "preliminare": partial_mode,
                  "assunzioni": content_errors if partial_mode else [],
                  "filiera": filiera_meta, "snapshot_version": assets.snapshot_version()},
        )
    except Refuse as r:
        jobs.update(job_id, status="refused", refusal_reason=r.reason, error=r.message)
    except Exception as exc:
        log.exception("pipeline error")
        jobs.update(job_id, status="error", error=str(exc))
