"""Layer 2 — Base Orchestrator (core comune alle tipologie).

Logica deterministica condivisa: validazione completezza, applicazione default
tipologici, costruzione pipeline di tool MCP, aggregazione flag/condizioni.
Le tipologie concrete (cabina industriale, terziario, ...) sottoclassano e
forniscono solo i DATI: CAMPI_CRITICI, DEFAULTS_TIPOLOGICI, PIPELINE_STANDARD.

NON invoca i tool (Layer 3). NON usa LLM. Schema A–E in input.
"""
from __future__ import annotations

import copy
from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Literal


class StatoValidazione(str, Enum):
    COMPLETO = "completo"
    INCOMPLETO_NON_CRITICO = "incompleto_non_critico"
    INCOMPLETO_CRITICO = "incompleto_critico"


@dataclass
class ValidazioneResult:
    status: StatoValidazione
    campi_mancanti_critici: list[str] = field(default_factory=list)
    campi_mancanti_non_critici: list[str] = field(default_factory=list)
    defaults_applicati: list[dict] = field(default_factory=list)
    review_richieste: list[dict] = field(default_factory=list)


@dataclass
class ToolPipelineStep:
    tool: str
    condizione_attivazione: str
    attivo: bool
    input_mappato: dict = field(default_factory=dict)
    iterazione: str | None = None
    note: list[str] = field(default_factory=list)


@dataclass
class OrchestrationResult:
    schema_input: dict
    schema_arricchito: dict
    validazione: ValidazioneResult
    pipeline: list[ToolPipelineStep]
    pipeline_attiva: list[ToolPipelineStep]
    mode: str
    warnings: list[str] = field(default_factory=list)


def _get(schema: dict, path: str) -> Any:
    """Naviga un path puntato (no indici) e ritorna il nodo, o None."""
    node: Any = schema
    for part in path.split("."):
        if not isinstance(node, dict) or part not in node:
            return None
        node = node[part]
    return node


def _campo_presente(schema: dict, path: str) -> bool:
    """True se il CampoBase esiste e non è RICHIESTO/vuoto."""
    node = _get(schema, path)
    if not isinstance(node, dict):
        return False
    return node.get("stato") != "RICHIESTO" and node.get("valore") not in (None, "", [])


class BaseOrchestrator:
    """Core generico. Le sottoclassi forniscono i tre attributi-dati seguenti."""

    CAMPI_CRITICI: list[str] = []
    DEFAULTS_TIPOLOGICI: dict[str, dict] = {}
    PIPELINE_STANDARD: list[dict] = []

    def __init__(self, mode: Literal["guided", "express", "validation"] = "validation"):
        self.mode = mode

    # --- entry point ---
    def esegui(self, schema_input: dict) -> OrchestrationResult:
        validazione = self.valida_completezza(schema_input)
        if validazione.status == StatoValidazione.INCOMPLETO_CRITICO and self.mode == "guided":
            return OrchestrationResult(
                schema_input=schema_input, schema_arricchito=schema_input,
                validazione=validazione, pipeline=[], pipeline_attiva=[], mode=self.mode,
                warnings=["Esecuzione bloccata: campi critici mancanti in modalità guided"])

        schema_arricchito, defaults = self.applica_defaults(schema_input)
        validazione.defaults_applicati = defaults
        validazione.review_richieste = self._raccogli_review(schema_arricchito)

        pipeline = self.costruisci_pipeline(schema_arricchito)
        pipeline_attiva = [s for s in pipeline if s.attivo]
        return OrchestrationResult(
            schema_input=schema_input, schema_arricchito=schema_arricchito,
            validazione=validazione, pipeline=pipeline, pipeline_attiva=pipeline_attiva,
            mode=self.mode)

    # --- validazione ---
    def valida_completezza(self, schema: dict) -> ValidazioneResult:
        richiesti = self._raccogli_per_stato(schema, "RICHIESTO")
        critici = [p for p in richiesti if p in self.CAMPI_CRITICI]
        for c in self.CAMPI_CRITICI:
            if not _campo_presente(schema, c) and c not in critici:
                critici.append(c)
        non_critici = [p for p in richiesti if p not in self.CAMPI_CRITICI]
        if critici:
            status = StatoValidazione.INCOMPLETO_CRITICO
        elif non_critici:
            status = StatoValidazione.INCOMPLETO_NON_CRITICO
        else:
            status = StatoValidazione.COMPLETO
        return ValidazioneResult(status=status, campi_mancanti_critici=sorted(set(critici)),
                                 campi_mancanti_non_critici=sorted(set(non_critici)))

    # --- defaults ---
    def applica_defaults(self, schema: dict) -> tuple[dict, list[dict]]:
        arr = copy.deepcopy(schema)
        applicati: list[dict] = []
        for path, dft in self.DEFAULTS_TIPOLOGICI.items():
            node = _get(arr, path)
            if isinstance(node, dict) and node.get("stato") == "RICHIESTO":
                node.update({"valore": dft["valore"], "stato": "DEFAULT",
                             "fonte": "norma" if dft.get("norma_ref") else "default_tipologico",
                             "norma_ref": dft.get("norma_ref"), "review_richiesta": True})
                applicati.append({"campo": path, "valore": dft["valore"],
                                  "norma_ref": dft.get("norma_ref")})
        return arr, applicati

    # --- pipeline ---
    def costruisci_pipeline(self, schema: dict) -> list[ToolPipelineStep]:
        flags = self._flags(schema)
        steps: list[ToolPipelineStep] = []
        for d in self.PIPELINE_STANDARD:
            cond = d["condizione"]
            attivo = True if cond == "sempre" else bool(flags.get(cond, False))
            steps.append(ToolPipelineStep(
                tool=d["tool"], condizione_attivazione=cond, attivo=attivo,
                input_mappato=self._mappa_input_tool(d["tool"], schema, d.get("iterazione")),
                iterazione=d.get("iterazione")))
        return steps

    @staticmethod
    def _flags(schema: dict) -> dict[str, bool]:
        sorgenti = _get(schema, "C_sorgenti_carichi.sorgenti_accessorie") or []
        trafi = _get(schema, "C_sorgenti_carichi.trasformatori") or []

        def _val(camp):
            return camp.get("valore", {}) if isinstance(camp, dict) else {}

        tipi = [_val(s).get("tipo") for s in sorgenti]
        ha_fv = "fotovoltaico" in tipi
        ha_ge = "gruppo_elettrogeno" in tipi
        ha_ats = any(_val(s).get("ats") for s in sorgenti)
        n_sorgenti = len(trafi) + len(sorgenti)
        return {"ha_fotovoltaico": ha_fv, "ha_ats": ha_ats, "ha_gruppo_elettrogeno": ha_ge,
                "ha_ats_e_ge": ha_ats and ha_ge, "multi_sorgente": n_sorgenti > 1}

    @staticmethod
    def _mappa_input_tool(tool: str, schema: dict, iterazione: str | None) -> dict:
        """Mapping di anteprima (NON eseguito): pochi parametri chiave dallo schema."""
        def v(path):
            n = _get(schema, path)
            return n.get("valore") if isinstance(n, dict) else None

        base = {"_preview": True, "_iterazione": iterazione}
        if tool == "dimensiona_trafo":
            base["P_kW"] = v("C_sorgenti_carichi.carico.P_kW")
            base["cosphi"] = v("C_sorgenti_carichi.carico.cosphi")
        elif tool in ("calcola_icc_cabina", "icc_bt_multisorgente"):
            base["Vn_MT_kV"] = v("B_allacciamento_sistema.tensione_MT_kV")
            base["Icc_MT_kA"] = v("B_allacciamento_sistema.Icc_MT_kA")
        elif tool == "verifica_terra":
            base["sistema"] = v("B_allacciamento_sistema.sistema_distribuzione_BT")
        elif tool == "valuta_rischio_fulmine":
            base["Nt_fulmini_km2_anno"] = v("A_anagrafica_contesto.Ng_fulmini_km2_anno")
        return base

    # --- helper walk ---
    @staticmethod
    def _raccogli_per_stato(schema: dict, stato: str) -> list[str]:
        out: list[str] = []

        def walk(obj, path=""):
            if isinstance(obj, dict):
                if "stato" in obj and "valore" in obj:
                    if obj.get("stato") == stato:
                        out.append(path)
                    return
                for k, val in obj.items():
                    walk(val, f"{path}.{k}" if path else k)
            elif isinstance(obj, list):
                for i, item in enumerate(obj):
                    walk(item, f"{path}[{i}]")

        walk(schema)
        return out

    def _raccogli_review(self, schema: dict) -> list[dict]:
        reviews: list[dict] = []

        def walk(obj, path=""):
            if isinstance(obj, dict):
                if "stato" in obj and "valore" in obj:
                    if obj.get("review_richiesta") and obj.get("stato") in ("DEFAULT", "RICHIESTO"):
                        reviews.append({"campo": path, "stato": obj.get("stato"),
                                        "norma_ref": obj.get("norma_ref")})
                    return
                for k, val in obj.items():
                    walk(val, f"{path}.{k}" if path else k)
            elif isinstance(obj, list):
                for i, item in enumerate(obj):
                    walk(item, f"{path}[{i}]")

        walk(schema)
        return reviews
