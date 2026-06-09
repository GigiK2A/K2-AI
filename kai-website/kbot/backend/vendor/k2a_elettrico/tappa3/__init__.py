"""Tappa 3 — Generatore di asseverazioni (Layer 1 + 2 + 3 + 4).

API alto livello end-to-end: input naturale → classifier (L1) → orchestrator (L2) →
executor tool MCP (L3) → composer DOCX (L4). Multi-tipologia (cabina industriale,
terziario) con pattern core+variants (ADR-019).
"""
from __future__ import annotations

from ._core.base_orchestrator import BaseOrchestrator, OrchestrationResult, StatoValidazione
from ._core.classifier import ClassificationError, ClassifierResult, TappaTreClassifier
from ._core.orchestrator import CabinaIndustrialeOrchestrator
from .tipologie.bt_commerciale import BtCommercialeOrchestrator
from .tipologie.bt_residenziale import BtResidenzialeOrchestrator
from .tipologie.cantiere_temporaneo import CantiereTemporaneoOrchestrator
from .tipologie.impianto_agricolo import ImpiantoAgricoloOrchestrator
from .tipologie.edificio_critico_sanitario import EdificioCriticoSanitarioOrchestrator
from .tipologie.cabina_mt_industriale_grande import CabinaMtIndustrialeGrandeOrchestrator
from .tipologie.datacenter import DatacenterOrchestrator
from .tipologie.cabina_terziario import CabinaTerziarioOrchestrator
from .tipologie.fv_bt import FvBtOrchestrator
from .tipologie.fv_mt import FvMtOrchestrator
from .tipologie.multisorgente_ats import MultisorgenteAtsOrchestrator

# Registro tipologie: nome → classe orchestrator (variante di BaseOrchestrator).
TIPOLOGIE = {
    "cabina_industriale": CabinaIndustrialeOrchestrator,
    "cabina_terziario": CabinaTerziarioOrchestrator,
    "bt_residenziale": BtResidenzialeOrchestrator,
    "bt_commerciale": BtCommercialeOrchestrator,
    "fv_bt": FvBtOrchestrator,
    "fv_mt": FvMtOrchestrator,
    "multisorgente_ats": MultisorgenteAtsOrchestrator,
    "cantiere_temporaneo": CantiereTemporaneoOrchestrator,
    "impianto_agricolo": ImpiantoAgricoloOrchestrator,
    "edificio_critico_sanitario": EdificioCriticoSanitarioOrchestrator,
    "cabina_mt_industriale_grande": CabinaMtIndustrialeGrandeOrchestrator,
    "datacenter": DatacenterOrchestrator,
}

__all__ = [
    "TappaTreClassifier", "ClassifierResult", "ClassificationError",
    "OrchestrationResult", "StatoValidazione", "TIPOLOGIE",
    "progetta_cabina_industriale", "progetta_cabina_terziario",
    "progetta_bt_residenziale", "progetta_bt_commerciale", "progetta_fv_bt",
    "progetta_fv_mt", "progetta_multisorgente_ats", "progetta_cantiere_temporaneo",
    "progetta_impianto_agricolo", "progetta_edificio_critico_sanitario",
    "progetta_cabina_mt_industriale_grande", "progetta_datacenter", "progetta_impianto",
]


def _progetta(tipologia: str, input_naturale: str, mode: str = "validation",
              api_key: str | None = None, client=None, eseguire_pipeline: bool = True,
              componi_documento: bool = True, mode_documento: str = "draft",
              profilo_professionista: dict | None = None, output_dir: str = "output",
              narrator=None, genera_cad: bool = False) -> dict:
    """Core generico end-to-end per una tipologia (Layer 1→4)."""
    orchestrator_cls = TIPOLOGIE.get(tipologia)
    if orchestrator_cls is None:
        raise ValueError(f"Tipologia non supportata: {tipologia} (note: {list(TIPOLOGIE)})")

    classifier = TappaTreClassifier(tipologia=tipologia, api_key=api_key, client=client)
    cls = classifier.classifica(input_naturale)
    orch = orchestrator_cls(mode=mode).esegui(cls.schema_compilato)

    out = {
        "tipologia": tipologia,
        "classifier_result": {
            "confidence": cls.confidence, "campi_dichiarati": cls.campi_dichiarati,
            "campi_inferiti": cls.campi_inferiti, "note": cls.note_llm,
        },
        "orchestrator_result": {
            "status_validazione": orch.validazione.status.value,
            "campi_critici_mancanti": orch.validazione.campi_mancanti_critici,
            "review_richieste": orch.validazione.review_richieste,
            "pipeline_costruita_n_step": len(orch.pipeline),
            "pipeline_attiva_n_step": len(orch.pipeline_attiva),
            "tool_attivi": [s.tool for s in orch.pipeline_attiva],
        },
        "schema_arricchito": orch.schema_arricchito,
        "warnings": orch.warnings,
    }

    if eseguire_pipeline:
        from ._core.executor import ToolExecutor
        ex = ToolExecutor().esegui(orch)
        d = ex.dimensioni
        out["execution_result"] = {
            "n_step_ok": ex.n_step_ok, "n_step_failed": ex.n_step_failed,
            "n_step_divergent": ex.n_step_divergent, "n_step_skipped": ex.n_step_skipped,
            "safety_critical_pieno": ex.safety_critical_pieno,
            "durata_ms": ex.durata_totale_ms,
            "warnings_globali": ex.warnings_globali, "errors_globali": ex.errors_globali,
            "pipeline_steps": [{"step_id": s.step_id, "tool": s.tool,
                                "iterazione": s.iterazione, "stato": s.stato.value,
                                "durata_ms": s.durata_ms} for s in ex.pipeline_steps],
            "dimensioni": {
                "icc_n": len(d.icc_calculations), "linee_n": len(d.dimensionamento_linee),
                "ha_dimensionamento_trafo": d.dimensionamento_trafo is not None,
                "ha_protezione_terra": d.protezione_terra is not None,
                "ha_rischio_fulmine": d.rischio_fulmine is not None,
                "ha_fv": d.fv_specifico is not None,
                "ha_selettivita": d.selettivita is not None,
                "ha_ats": d.ats_coordinamento is not None,
            },
        }
        if componi_documento:
            from ._composer.composer import AsseverazioneComposer, carica_profilo
            cr = AsseverazioneComposer(
                ex, orch.schema_arricchito,
                profilo_professionista=profilo_professionista or carica_profilo(),
                mode=mode_documento, api_key=api_key, narrator=narrator,
                output_dir=output_dir, tipologia=tipologia, genera_cad=genera_cad).componi()
            out["composer_result"] = {
                "docx_path": cr.docx_path, "markdown_path": cr.markdown_path,
                "tracciabilita_path": cr.tracciabilita_path,
                "gemini_status": cr.gemini_status, "mode": cr.mode, "warnings": cr.warnings,
                "cad_paths": cr.cad_paths,
            }
    return out


def progetta_cabina_industriale(input_naturale: str, **kw) -> dict:
    """Pipeline end-to-end per cabina industriale."""
    return _progetta("cabina_industriale", input_naturale, **kw)


def progetta_cabina_terziario(input_naturale: str, **kw) -> dict:
    """Pipeline end-to-end per cabina terziario (uffici/retail/hotel)."""
    return _progetta("cabina_terziario", input_naturale, **kw)


def progetta_bt_residenziale(input_naturale: str, **kw) -> dict:
    """Pipeline end-to-end per impianto residenziale BT."""
    return _progetta("bt_residenziale", input_naturale, **kw)


def progetta_bt_commerciale(input_naturale: str, **kw) -> dict:
    """Pipeline end-to-end per impianto commerciale BT."""
    return _progetta("bt_commerciale", input_naturale, **kw)


def progetta_fv_bt(input_naturale: str, **kw) -> dict:
    """Pipeline end-to-end per impianto FV connesso in BT (CEI 0-21)."""
    return _progetta("fv_bt", input_naturale, **kw)


def progetta_fv_mt(input_naturale: str, **kw) -> dict:
    """Pipeline end-to-end per impianto FV connesso in MT (CEI 0-16)."""
    return _progetta("fv_mt", input_naturale, **kw)


def progetta_multisorgente_ats(input_naturale: str, **kw) -> dict:
    """Pipeline end-to-end per impianto multisorgente con ATS."""
    return _progetta("multisorgente_ats", input_naturale, **kw)


def progetta_cantiere_temporaneo(input_naturale: str, **kw) -> dict:
    """Pipeline end-to-end per impianto di cantiere temporaneo (CEI 64-8 sez.706)."""
    return _progetta("cantiere_temporaneo", input_naturale, **kw)


def progetta_impianto_agricolo(input_naturale: str, **kw) -> dict:
    """Pipeline end-to-end per impianto agricolo/zootecnico (CEI 64-8 sez.705)."""
    return _progetta("impianto_agricolo", input_naturale, **kw)


def progetta_edificio_critico_sanitario(input_naturale: str, **kw) -> dict:
    """Pipeline end-to-end per edificio sanitario / locali ad uso medico (CEI 64-8 sez.710)."""
    return _progetta("edificio_critico_sanitario", input_naturale, **kw)


def _rileva_tipologia(testo: str) -> str:
    """Euristica semplice (Fase 1) per il dispatcher: keyword → tipologia.
    Ordine: i casi più specifici prima dei più generici."""
    t = testo.lower()
    if any(k in t for k in ("ospedal", "casa di cura", "rsa", "clinica", "ambulatorio",
                            "day hospital", "uso medico", "sala operatoria", "sanitar")):
        return "edificio_critico_sanitario"
    if any(k in t for k in ("datacenter", "data center", "server room", "sala server",
                            "ced ", "rack server")):
        return "datacenter"
    if any(k in t for k in ("ats", "gruppo elettrogeno", "continuità", "critic")):
        return "multisorgente_ats"
    if any(k in t for k in ("agricol", "allevamento", "stalla", "zootecnic", "serra",
                            "mungitura", "azienda agricola", "bovini", "fienile")):
        return "impianto_agricolo"
    fv_kw = any(k in t for k in ("fotovoltaic", "impianto fv", " fv ", "parco fv", "moduli", "inverter"))
    if fv_kw and any(k in t for k in ("mt", "media tensione", "0-16", "0/16",
                                       "utente attivo", "cabina di consegna", "elevatore")):
        return "fv_mt"
    if fv_kw and "cabina" not in t:
        return "fv_bt"
    if any(k in t for k in ("cantiere", "demolizione", "edile temporane", "asc ",
                            "gru a torre", "betoniera")):
        return "cantiere_temporaneo"
    if any(k in t for k in ("condominio", "condominiale", "appartament", "residenzial",
                            "unità abitative", "palazzina", "casa singola")):
        return "bt_residenziale"
    if any(k in t for k in ("negozio", "negozi", "ristorante", "bar", "retail",
                            "attività commerciale", "esercizio commerciale")):
        return "bt_commerciale"
    if any(k in t for k in ("uffici", "ufficio", "hotel", "albergo", "ricettiv",
                            "direzional", "terziario")):
        return "cabina_terziario"
    if any(k in t for k in ("acciaieria", "fonderia", "metallurgic", "industria pesante",
                            "trasformatori in parallelo", "trafi in parallelo", "grande potenza",
                            "ridondanza n+1", "forni a induzione")):
        return "cabina_mt_industriale_grande"
    return "cabina_industriale"


def progetta_cabina_mt_industriale_grande(input_naturale: str, **kw) -> dict:
    """Pipeline end-to-end per cabina MT/BT industriale grande potenza (multi-trafo)."""
    return _progetta("cabina_mt_industriale_grande", input_naturale, **kw)


def progetta_datacenter(input_naturale: str, **kw) -> dict:
    """Pipeline end-to-end per datacenter/server room (categoria dimostrativa, EN 50600 non in KB)."""
    return _progetta("datacenter", input_naturale, **kw)


def progetta_impianto(input_naturale: str, tipologia: str | None = None, **kw) -> dict:
    """Dispatcher: se `tipologia` è None la rileva con euristica su keyword (Fase 1)."""
    tip = tipologia or _rileva_tipologia(input_naturale)
    return _progetta(tip, input_naturale, **kw)
