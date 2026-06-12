"""Layer 3 — Executor MCP (Tappa 3).

Invoca i tool MCP reali del principale per ogni step della pipeline Layer 2.
Aggrega gli output (per step / per linea / per dimensione asseverativa), gestisce
gli errori in 3 categorie e traccia tutto per l'asseverazione.

Deterministico (no LLM). Mantiene il pilastro safety-critical: per i tool che lo
supportano (i 5 cross-validated) propaga validate_runtime + with_kb_references +
dynamic_kb + validate_kb_values; per gli altri (Tappa 1) i flag non esistono e
vengono semplicemente non passati (filtro su model_fields).
"""
from __future__ import annotations

import time
import traceback
from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from typing import Any, Callable

from .input_mapper import mappa_input
from .orchestrator import OrchestrationResult, ToolPipelineStep

_PILASTRO = ("validate_runtime", "with_kb_references", "dynamic_kb", "validate_kb_values")


class StatoEsecuzioneStep(str, Enum):
    OK = "ok"
    FAILED_INPUT = "failed_input"
    FAILED_RUNTIME = "failed_runtime"
    DIVERGENCE_DETECTED = "divergence_detected"
    SKIPPED = "skipped"
    SKIPPED_PRECONDITION = "skipped_precondition"


@dataclass
class StepExecution:
    step_id: str
    tool: str
    iterazione: str | None
    stato: StatoEsecuzioneStep
    input_grezzo: dict
    input_validato: dict | None
    output: dict | None
    durata_ms: int
    timestamp: str
    cross_validation: dict | None = None
    kb_references: list[dict] = field(default_factory=list)
    kb_validation: list[dict] | None = None
    supporta_pilastro: bool = False
    error_type: str | None = None
    error_message: str | None = None
    error_traceback: str | None = None
    warnings: list[str] = field(default_factory=list)


@dataclass
class CalcoloLinea:
    linea_id: str
    descrizione: str
    dimensionamento_cavo: dict | None = None
    caduta_tensione: dict | None = None
    verifica_protezione: dict | None = None
    protezione_In: float | None = None  # da input verifica_protezione (non riemesso in output)
    coerente: bool = True
    warnings: list[str] = field(default_factory=list)


@dataclass
class DimensioniAsseverative:
    icc_calculations: list[dict] = field(default_factory=list)
    dimensionamento_linee: list[CalcoloLinea] = field(default_factory=list)
    dimensionamento_trafo: dict | None = None
    protezione_terra: dict | None = None
    guasto_terra_mt: dict | None = None
    rischio_fulmine: dict | None = None
    fv_specifico: dict | None = None
    selettivita: dict | None = None
    spd: dict | None = None
    ats_coordinamento: dict | None = None


@dataclass
class ExecutionResult:
    pipeline_steps: list[StepExecution]
    calcoli_linee: list[CalcoloLinea]
    dimensioni: DimensioniAsseverative
    n_step_ok: int = 0
    n_step_failed: int = 0
    n_step_divergent: int = 0
    n_step_skipped: int = 0
    warnings_globali: list[str] = field(default_factory=list)
    errors_globali: list[str] = field(default_factory=list)
    durata_totale_ms: int = 0
    timestamp_inizio: str = ""
    timestamp_fine: str = ""
    safety_critical_pieno: bool = True


def _default_registry() -> dict[str, tuple[Callable, type]]:
    from k2a_elettrico.cabina_mt import (DimensionaTrafoInput, IccCabinaMTInput,
                                          calcola_icc_cabina, dimensiona_trafo)
    from k2a_elettrico.caduta_v import CadutaVInput, caduta_tensione
    from k2a_elettrico.cavo import DimensionaCavoInput, dimensiona_cavo
    from k2a_elettrico.coordinamento_ats import (CoordinamentoATSInput,
                                                 coordinamento_ats_fv_generatore)
    from k2a_elettrico.icc_multisorgente import (IccMultisorgenteInput,
                                                 icc_bt_multisorgente)
    from k2a_elettrico.lps_fulmini import (ValutazioneRischioFulmineInput,
                                           valuta_rischio_fulmine)
    from k2a_elettrico.protezione import VerificaProtezioneInput, verifica_protezione
    from k2a_elettrico.selettivita_catena import (VerificaSelettivitaCatenaInput,
                                                  verifica_selettivita_catena)
    from k2a_elettrico.spd_coordinato import SpdCoordinatoInput, verifica_spd_coordinato
    from k2a_elettrico.spi_fv import SpiCei021Input, verifica_spi_cei_021
    from k2a_elettrico.protezioni_mt import (
        ProtezioneGeneraleMTInput, verifica_protezione_generale_mt,
        ProtezioneInterfacciaMTInput, verifica_protezione_interfaccia_mt)
    from k2a_elettrico.guasto_terra_mt import (
        CorrenteGuastoTerraMtInput, corrente_guasto_terra_mt)
    from k2a_elettrico.terra import (DispersoreTerraInput, VerificaTerraInput,
                                     dispersore_terra, verifica_terra)
    from k2a_elettrico.ups import UpsDimensionaInput, dimensiona_ups
    from k2a_elettrico.parallelo_trafi import ParalleloTrafiInput, parallelo_trafi_circolazione
    return {
        "dimensiona_trafo": (dimensiona_trafo, DimensionaTrafoInput),
        "calcola_icc_cabina": (calcola_icc_cabina, IccCabinaMTInput),
        "icc_bt_multisorgente": (icc_bt_multisorgente, IccMultisorgenteInput),
        "dimensiona_cavo": (dimensiona_cavo, DimensionaCavoInput),
        "caduta_tensione": (caduta_tensione, CadutaVInput),
        "verifica_protezione": (verifica_protezione, VerificaProtezioneInput),
        "coordinamento_atrs_fv_generatore": (coordinamento_ats_fv_generatore, CoordinamentoATSInput),
        "verifica_spi_cei_021": (verifica_spi_cei_021, SpiCei021Input),
        "verifica_protezione_generale_mt": (verifica_protezione_generale_mt, ProtezioneGeneraleMTInput),
        "verifica_protezione_interfaccia_mt": (verifica_protezione_interfaccia_mt, ProtezioneInterfacciaMTInput),
        "corrente_guasto_terra_mt": (corrente_guasto_terra_mt, CorrenteGuastoTerraMtInput),
        "verifica_selettivita_catena": (verifica_selettivita_catena, VerificaSelettivitaCatenaInput),
        "dispersore_terra": (dispersore_terra, DispersoreTerraInput),
        "verifica_terra": (verifica_terra, VerificaTerraInput),
        "valuta_rischio_fulmine": (valuta_rischio_fulmine, ValutazioneRischioFulmineInput),
        "verifica_spd_coordinato": (verifica_spd_coordinato, SpdCoordinatoInput),
        "dimensiona_ups": (dimensiona_ups, UpsDimensionaInput),
        "parallelo_trafi_circolazione": (parallelo_trafi_circolazione, ParalleloTrafiInput),
    }


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


class ToolExecutor:
    """Esecutore Layer 3. Pilastro safety-critical attivo by default."""

    def __init__(self, validate_runtime: bool = True, with_kb_references: bool = True,
                 dynamic_kb: bool = True, validate_kb_values: bool = True,
                 continue_on_error: bool = True, registry: dict | None = None):
        self.flags = {"validate_runtime": validate_runtime,
                      "with_kb_references": with_kb_references,
                      "dynamic_kb": dynamic_kb, "validate_kb_values": validate_kb_values}
        self.continue_on_error = continue_on_error
        self.registry = registry if registry is not None else _default_registry()

    def esegui(self, orchestration: OrchestrationResult) -> ExecutionResult:
        ts_inizio = _now()
        start = time.time()
        schema = orchestration.schema_arricchito
        steps: list[StepExecution] = []

        for idx, step in enumerate(orchestration.pipeline):
            step_id = self._step_id(idx, step)
            if not step.attivo:
                steps.append(self._skip(step_id, step, StatoEsecuzioneStep.SKIPPED))
                continue
            ex = self._esegui_step(step_id, step, schema)
            steps.append(ex)
            if (not self.continue_on_error and ex.stato in
                    (StatoEsecuzioneStep.FAILED_INPUT, StatoEsecuzioneStep.FAILED_RUNTIME)):
                break

        linee = self._aggrega_per_linea(steps)
        dimensioni = self._aggrega_per_dimensione(steps, linee)

        ok = [s for s in steps if s.stato == StatoEsecuzioneStep.OK]
        div = [s for s in steps if s.stato == StatoEsecuzioneStep.DIVERGENCE_DETECTED]
        failed = [s for s in steps if s.stato in
                  (StatoEsecuzioneStep.FAILED_INPUT, StatoEsecuzioneStep.FAILED_RUNTIME)]
        skipped = [s for s in steps if s.stato in
                   (StatoEsecuzioneStep.SKIPPED, StatoEsecuzioneStep.SKIPPED_PRECONDITION)]

        # safety_critical_pieno: ogni step (ok/divergent) che SUPPORTA il pilastro
        # deve aver prodotto cross_validation (eseguita).
        pilastro_steps = [s for s in (ok + div) if s.supporta_pilastro]
        sc_pieno = all(
            (s.cross_validation or {}).get("cross_validation_eseguita") for s in pilastro_steps
        ) if pilastro_steps else True

        return ExecutionResult(
            pipeline_steps=steps, calcoli_linee=linee, dimensioni=dimensioni,
            n_step_ok=len(ok), n_step_failed=len(failed), n_step_divergent=len(div),
            n_step_skipped=len(skipped),
            warnings_globali=[f"[{s.step_id}] {w}" for s in steps for w in s.warnings],
            errors_globali=[f"[{s.step_id}] {s.error_type}: {s.error_message}"
                            for s in steps if s.error_message],
            durata_totale_ms=int((time.time() - start) * 1000),
            timestamp_inizio=ts_inizio, timestamp_fine=_now(),
            safety_critical_pieno=sc_pieno)

    # --- single step ---
    def _esegui_step(self, step_id: str, step: ToolPipelineStep, schema: dict) -> StepExecution:
        start = time.time()
        ts = _now()
        if step.tool not in self.registry:
            return StepExecution(step_id, step.tool, step.iterazione,
                                 StatoEsecuzioneStep.FAILED_INPUT, {}, None, None,
                                 int((time.time() - start) * 1000), ts,
                                 error_type="ToolNotFound",
                                 error_message=f"Tool '{step.tool}' non nel registry")
        fn, InputClass = self.registry[step.tool]
        campi = set(InputClass.model_fields.keys())
        supporta_pilastro = all(f in campi for f in _PILASTRO)

        grezzo = mappa_input(step.tool, schema, step.iterazione)
        payload = {**grezzo, **{k: v for k, v in self.flags.items() if k in campi}}
        payload = {k: v for k, v in payload.items() if k in campi}

        try:
            inp = InputClass(**payload)
        except Exception as e:  # noqa: BLE001 — Pydantic validation
            return StepExecution(step_id, step.tool, step.iterazione,
                                 StatoEsecuzioneStep.FAILED_INPUT, grezzo, None, None,
                                 int((time.time() - start) * 1000), ts,
                                 supporta_pilastro=supporta_pilastro,
                                 error_type=type(e).__name__, error_message=str(e)[:300])
        try:
            out = fn(inp).model_dump()
        except Exception as e:  # noqa: BLE001 — runtime
            return StepExecution(step_id, step.tool, step.iterazione,
                                 StatoEsecuzioneStep.FAILED_RUNTIME, grezzo,
                                 inp.model_dump(), None,
                                 int((time.time() - start) * 1000), ts,
                                 supporta_pilastro=supporta_pilastro,
                                 error_type=type(e).__name__, error_message=str(e)[:300],
                                 error_traceback=traceback.format_exc())

        cv = {k: out[k] for k in out if k.startswith("cross_validation")}
        esito = str(cv.get("cross_validation_esito", "")).upper()
        divergente = "DIVERG" in esito
        warnings = [f"Cross-validation divergente: {esito}"] if divergente else []
        return StepExecution(
            step_id, step.tool, step.iterazione,
            StatoEsecuzioneStep.DIVERGENCE_DETECTED if divergente else StatoEsecuzioneStep.OK,
            grezzo, inp.model_dump(), out, int((time.time() - start) * 1000), ts,
            cross_validation=cv or None, kb_references=out.get("riferimenti_kb", []),
            kb_validation=out.get("kb_validation"), supporta_pilastro=supporta_pilastro,
            warnings=warnings)

    @staticmethod
    def _step_id(idx: int, step: ToolPipelineStep) -> str:
        base = f"step{idx:02d}_{step.tool}"
        return f"{base}_{step.iterazione}" if step.iterazione else base

    @staticmethod
    def _skip(step_id: str, step: ToolPipelineStep, stato: StatoEsecuzioneStep) -> StepExecution:
        return StepExecution(step_id, step.tool, step.iterazione, stato,
                             step.input_mappato, None, None, 0, _now())

    # --- aggregazioni ---
    def _aggrega_per_linea(self, steps: list[StepExecution]) -> list[CalcoloLinea]:
        per: dict[str, CalcoloLinea] = {}
        for s in steps:
            if s.iterazione is None or s.stato not in (StatoEsecuzioneStep.OK,
                                                       StatoEsecuzioneStep.DIVERGENCE_DETECTED):
                continue
            linea = per.setdefault(s.iterazione, CalcoloLinea(s.iterazione, s.iterazione))
            if s.tool == "dimensiona_cavo":
                linea.dimensionamento_cavo = s.output
            elif s.tool == "caduta_tensione":
                linea.caduta_tensione = s.output
            elif s.tool == "verifica_protezione":
                linea.verifica_protezione = s.output
                if s.input_validato:
                    linea.protezione_In = s.input_validato.get("In")
        for linea in per.values():
            linea.coerente = self._coerenza(linea)
        return list(per.values())

    @staticmethod
    def _coerenza(linea: CalcoloLinea) -> bool:
        dim = linea.dimensionamento_cavo or {}
        ver = linea.verifica_protezione or {}
        s_dim = dim.get("sezione_minima_mm2") or dim.get("sezione_scelta_mmq")
        s_ver = ver.get("sezione_mm2") or ver.get("sezione_verificata_mmq")
        if s_dim and s_ver and abs(float(s_dim) - float(s_ver)) > 1e-6:
            linea.warnings.append(f"Incoerenza sezione: dim={s_dim} vs verifica={s_ver}")
            return False
        return True

    @staticmethod
    def _aggrega_per_dimensione(steps: list[StepExecution],
                                linee: list[CalcoloLinea]) -> DimensioniAsseverative:
        dim = DimensioniAsseverative(dimensionamento_linee=linee)
        for s in steps:
            if s.stato not in (StatoEsecuzioneStep.OK, StatoEsecuzioneStep.DIVERGENCE_DETECTED):
                continue
            t = s.tool
            if "icc" in t:
                dim.icc_calculations.append(s.output)
            elif t == "dimensiona_trafo":
                dim.dimensionamento_trafo = s.output
            elif t == "dispersore_terra" or t == "verifica_terra":
                dim.protezione_terra = s.output
            elif t == "corrente_guasto_terra_mt":
                dim.guasto_terra_mt = s.output
            elif t == "valuta_rischio_fulmine":
                dim.rischio_fulmine = s.output
            elif t == "verifica_spi_cei_021":
                dim.fv_specifico = s.output
            elif t == "verifica_selettivita_catena":
                dim.selettivita = s.output
            elif t == "verifica_spd_coordinato":
                dim.spd = s.output
            elif "atrs" in t or "ats" in t:
                dim.ats_coordinamento = s.output
        return dim
