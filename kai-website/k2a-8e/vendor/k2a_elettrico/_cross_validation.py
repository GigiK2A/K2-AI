"""Modulo di integrazione cross-validation runtime (modalità C — ADR-009).

Ogni tool safety-critical del principale, se chiamato con `validate=True`, invoca
il validator gemello (k2a-elettrico-validator) via import diretto, confronta gli
output entro soglia e include l'esito strutturato (`cross_validation_*`).

Default disabilitato (backward compatibility). Su divergenza: warning soft (no
raise) + flag DIVERGENTE. Tool senza gemello: NON_DISPONIBILE.

Import del validator robusto: se il pacchetto non è installato, si tenta un
fallback aggiungendo a sys.path il `src/` del repo affiancato.
"""
from __future__ import annotations

import sys
import warnings
from pathlib import Path
from typing import Any, Callable

SOGLIE_DELTA_PCT = {"numerico_stretto": 0.5, "numerico_kappa": 1.0}


class SkipCrossValidation(Exception):
    """Scenario non confrontabile cross-MCP (es. DB costruttori, modalità diversa)."""


def _ensure_validator() -> bool:
    """Garantisce l'importabilità del validator; fallback via sys.path."""
    try:
        import k2a_elettrico_validator  # noqa: F401
        return True
    except ImportError:
        cand = Path(__file__).resolve().parents[3] / "k2a-mcp-elettrico-validator" / "src"
        if cand.exists() and str(cand) not in sys.path:
            sys.path.insert(0, str(cand))
        try:
            import k2a_elettrico_validator  # noqa: F401
            return True
        except ImportError:
            return False


# --------------------------------------------------------------------------- #
# Esito strutturato
# --------------------------------------------------------------------------- #
class CrossValidationResult:
    def __init__(self) -> None:
        self.eseguita = False
        self.esito = "NON_ESEGUITA"  # CONVERGENTE/DIVERGENTE/ERRORE/NON_DISPONIBILE/NON_CONFRONTABILE
        self.delta_pct: dict[str, float] = {}
        self.note: list[str] = []

    def to_dict(self) -> dict:
        return {
            "cross_validation_eseguita": self.eseguita,
            "cross_validation_esito": self.esito,
            "cross_validation_delta_pct": self.delta_pct,
            "cross_validation_note": self.note,
        }


def _confronta(p: dict, v: dict, fields: dict[str, str], res: CrossValidationResult) -> bool:
    ok = True
    for nome, categoria in fields.items():
        pv, vv = p.get(nome), v.get(nome)
        if pv is None or vv is None:
            res.note.append(f"{nome}: None su un tool, skip")
            continue
        if categoria == "bool" or isinstance(pv, bool):
            if pv != vv:
                ok = False
                res.delta_pct[nome] = -1.0
                res.note.append(f"{nome}: BOOL DIVERGE p={pv} v={vv}")
            continue
        if categoria == "discreto":  # uguaglianza esatta (es. sezione)
            if pv != vv:
                ok = False
                res.delta_pct[nome] = -2.0
                res.note.append(f"{nome}: DISCRETO DIVERGE p={pv} v={vv}")
            continue
        delta = 0.0 if (abs(pv) < 1e-12 and abs(vv) < 1e-12) else (
            abs(pv - vv) / abs(pv) * 100 if abs(pv) >= 1e-12 else float("inf"))
        res.delta_pct[nome] = round(delta, 6)
        if delta > SOGLIE_DELTA_PCT.get(categoria, 0.5):
            ok = False
            res.note.append(f"{nome}: delta {delta:.4f}% > {SOGLIE_DELTA_PCT.get(categoria,0.5)}% (p={pv}, v={vv})")
    return ok


# --------------------------------------------------------------------------- #
# Mapping + normalizer per tool (principale -> validator)
# --------------------------------------------------------------------------- #
def _icc_map(inp):
    from k2a_elettrico_validator.tools.icc_bt_multisorgente_v import (
        IccMultisorgenteValidatorInput, TrasformatoreInput)
    un_mt_kv = inp.Vn_MT / 1000.0
    toll = inp.trafi[0].vcc_tolleranza_pct if inp.trafi else 0.0
    trs = [TrasformatoreInput(Sn_kVA=t.Sn_kVA, Un_MT_kV=un_mt_kv, Un_BT_V=inp.Vn_BT,
                              vcc_pct=t.vcc_pct, X_R_ratio=t.X_R_trafo) for t in inp.trafi]
    kw = dict(Un_BT_V=inp.Vn_BT, Un_MT_kV=un_mt_kv, Icc_MT_DSO_kA=inp.Icc_MT_kA,
              X_R_DSO=inp.X_R_rete, trasformatori=trs, vcc_tolleranza_pct=toll,
              R_a_caldo_factor=inp.R_a_caldo_factor)
    if inp.c_factor_override:
        kw["c_max"] = kw["c_min"] = inp.c_factor_override
    return IccMultisorgenteValidatorInput(**kw)


def _proteggi_map(inp):
    from k2a_elettrico_validator.tools.verifica_protezione_v import VerificaProtezioneValidatorInput
    if inp.famiglia_protezione is not None and inp.I2t_let_through_A2s is None:
        raise SkipCrossValidation("DB costruttori (famiglia_protezione): validator usa solo formula")
    kw = dict(Ib_A=inp.Ib, In_A=inp.In, Iz_A=inp.Iz, sezione_mm2=inp.sezione_mm2,
              materiale=inp.materiale, isolante=inp.isolante, Icc_max_kA=inp.Icc_max_kA,
              tempo_intervento_max_s=inp.tempo_intervento_max_s, I2_su_In_ratio=inp.I2_su_In_ratio,
              tipo_connessione=inp.tipo_connessione)
    if inp.I2t_let_through_A2s is not None:
        kw["I2t_let_through_A2s"] = inp.I2t_let_through_A2s
    if inp.Icw_blindo_kA is not None:
        kw["Icw_blindo_kA"] = inp.Icw_blindo_kA
    return VerificaProtezioneValidatorInput(**kw)


def _cavo_map(inp):
    from k2a_elettrico_validator.tools.dimensiona_cavo_v import DimensionaCavoValidatorInput
    from k2a_elettrico.cavo import _DATA  # dato normativo condiviso (tabella portate)
    tab = _DATA[f"rame_{inp.isolante}"]
    portate = {float(s): r[inp.posa] for s, r in tab.items() if inp.posa in r}
    return DimensionaCavoValidatorInput(
        Ib_A=inp.Ib, portate_Iz30=portate, temp_ambiente_C=inp.temp_ambiente,
        isolante=inp.isolante, n_circuiti_raggruppati=inp.n_circuiti_raggruppati,
        n_paralleli=inp.n_paralleli,  # ADR-033
        In_protezione_A=inp.In_protezione)


def _caduta_map(inp):
    from k2a_elettrico_validator.tools.caduta_tensione_v import CadutaTensioneValidatorInput
    return CadutaTensioneValidatorInput(
        I_A=inp.I, L_m=inp.L, sezione_mm2=inp.sezione_mm2, cosfi=inp.cosfi,
        sistema=inp.sistema, Vn_V=inp.Vn, materiale=inp.materiale,
        temp_conduttore_C=inp.temp_conduttore)


def _fulmine_map(inp):
    from k2a_elettrico_validator.tools.valuta_rischio_fulmine_v import (
        ValutaRischioFulmineValidatorInput, LineaEntranteV)
    if inp.modalita != "completo_62305":
        raise SkipCrossValidation("validator copre solo modalità completo_62305")
    linee = [LineaEntranteV(tipo=l.tipo, Lc_m=l.Lc_m, posa=l.posa, Ct=l.Ct,
                            Al_m2_override=l.Al_m2_override, Ai_m2_override=l.Ai_m2_override)
             for l in inp.linee_entranti]
    kw = dict(Nt_fulmini_km2_anno=inp.Nt_fulmini_km2_anno, L_m=inp.L_m, W_m=inp.W_m, H_m=inp.H_m,
              Cd_posizione=inp.Cd_posizione, Ce_ambiente=inp.Ce_ambiente,
              R_tollerabile=inp.R_tollerabile, LPS_classe=inp.LPS_classe, SPD_livello=inp.SPD_livello,
              misure_antincendio=inp.misure_antincendio, rischio_incendio=inp.rischio_incendio,
              pericolo_speciale=inp.pericolo_speciale, misure_contatto_passo=inp.misure_contatto_passo,
              nz_su_nt=inp.nz_su_nt, tz_su_8760=inp.tz_su_8760, linee_entranti=linee)
    if inp.destinazione is not None:
        kw["destinazione"] = inp.destinazione
    if inp.pavimento_tipo is not None:
        kw["pavimento_tipo"] = inp.pavimento_tipo
    if inp.Ad_override_m2 is not None:
        kw["Ad_override_m2"] = inp.Ad_override_m2
    # passa LA/LB/LU/LV solo se override esplicito (i flag privati del sentinel)
    for f in ("LA", "LB", "LU", "LV"):
        if getattr(inp, f"_{f}_explicit", False):
            kw[f] = getattr(inp, f)
    return ValutaRischioFulmineValidatorInput(**kw)


CONFIG: dict[str, dict] = {
    "icc_bt_multisorgente": {
        "func": ("icc_bt_multisorgente_v", "icc_bt_multisorgente_v"),
        "map": _icc_map,
        "norm_p": lambda o: {"Ik3max_kA": o.Ik3max_kA, "Ik3min_kA": o.Ik3min_kA, "Ip": o.Ipk_kA, "kappa": o.kappa},
        "norm_v": lambda o: {"Ik3max_kA": o.Ik3max_kA, "Ik3min_kA": o.Ik3min_kA, "Ip": o.Ip_kA, "kappa": o.kappa},
        "fields": {"Ik3max_kA": "numerico_stretto", "Ik3min_kA": "numerico_stretto",
                   "Ip": "numerico_stretto", "kappa": "numerico_kappa"},
    },
    "verifica_protezione": {
        "func": ("verifica_protezione_v", "verifica_protezione_v"),
        "map": _proteggi_map,
        "norm_p": lambda o: {"sovr": o.verifica_sovraccarico_433_1, "i2_45": o.verifica_I2_45_Iz,
                             "i2t": o.verifica_I2t_434_5_2, "concl": o.conclusione_finale,
                             "I2t_amm": o.I2t_ammissibile_A2s, "I2t_pass": o.I2t_passante_calcolato_A2s},
        "norm_v": lambda o: {"sovr": o.verifica_sovraccarico_433_1, "i2_45": o.verifica_I2_45_Iz,
                             "i2t": o.verifica_I2t_434_5_2, "concl": o.conclusione_finale,
                             "I2t_amm": o.I2t_ammissibile_A2s, "I2t_pass": o.I2t_passante_A2s},
        "fields": {"sovr": "bool", "i2_45": "bool", "i2t": "bool", "concl": "bool",
                   "I2t_amm": "numerico_stretto", "I2t_pass": "numerico_stretto"},
    },
    "dimensiona_cavo": {
        "func": ("dimensiona_cavo_v", "dimensiona_cavo_v"),
        "map": _cavo_map,
        "norm_p": lambda o: {"sez": o.sezione_minima_mm2, "Iz": o.Iz_corretta,
                             "k1": o.fattore_temperatura_k1, "k2": o.fattore_raggruppamento_k2,
                             "coord": o.coordinamento_433_1,
                             "n_par": o.n_paralleli, "kpar": o.fattore_paralleli_kpar,
                             "Iz_sing": o.Iz_singolo_A},
        "norm_v": lambda o: {"sez": o.sezione_minima_mm2, "Iz": o.Iz_corretta_A,
                             "k1": o.fattore_k1, "k2": o.fattore_k2, "coord": o.coordinamento_433_1,
                             "n_par": o.n_paralleli, "kpar": o.fattore_kpar,
                             "Iz_sing": o.Iz_singolo_A or 0.0},
        "fields": {"sez": "discreto", "Iz": "numerico_stretto", "k1": "numerico_stretto",
                   "k2": "numerico_stretto", "coord": "bool",
                   "n_par": "discreto", "kpar": "numerico_stretto", "Iz_sing": "numerico_stretto"},
    },
    "caduta_tensione": {
        "func": ("caduta_tensione_v", "caduta_tensione_v"),
        "map": _caduta_map,
        "norm_p": lambda o: {"dV": o.delta_V_volt, "dVpc": o.delta_V_percento,
                             "R": o.R_unitario_ohm_per_km, "X": o.X_unitario_ohm_per_km, "ver": o.verifica_CEI_525},
        "norm_v": lambda o: {"dV": o.delta_V_volt, "dVpc": o.delta_V_percento,
                             "R": o.R_unitario_ohm_per_km, "X": o.X_unitario_ohm_per_km, "ver": o.verifica_CEI_525},
        "fields": {"dV": "numerico_stretto", "dVpc": "numerico_stretto", "R": "numerico_stretto",
                   "X": "numerico_stretto", "ver": "bool"},
    },
    "valuta_rischio_fulmine": {
        "func": ("valuta_rischio_fulmine_v", "valuta_rischio_fulmine_v"),
        "map": _fulmine_map,
        "norm_p": lambda o: {"RA": o.stadio_3_finale_LPS_SPD.RA, "RB": o.stadio_3_finale_LPS_SPD.RB,
                             "RU": o.stadio_3_finale_LPS_SPD.RU, "RV": o.stadio_3_finale_LPS_SPD.RV,
                             "R1_fin": o.R1_finale, "R1_ini": o.R1_iniziale, "conf": o.conforme_finale},
        "norm_v": lambda o: {"RA": o.stadio_3_finale.RA, "RB": o.stadio_3_finale.RB,
                             "RU": o.stadio_3_finale.RU, "RV": o.stadio_3_finale.RV,
                             "R1_fin": o.R1_finale, "R1_ini": o.R1_iniziale, "conf": o.conforme},
        "fields": {"RA": "numerico_stretto", "RB": "numerico_stretto", "RU": "numerico_stretto",
                   "RV": "numerico_stretto", "R1_fin": "numerico_stretto", "R1_ini": "numerico_stretto",
                   "conf": "bool"},
    },
}


def _load_validator_func(modname: str, funcname: str) -> Callable:
    mod = __import__(f"k2a_elettrico_validator.tools.{modname}", fromlist=[funcname])
    return getattr(mod, funcname)


def cv_hook(inp: Any, out: Any, tool_name: str) -> Any:
    """Hook modalità C: arricchisce `out` con la cross-validation se inp.validate=True.

    Da chiamare prima del return di ogni tool: `return cv_hook(inp, out, "nome")`.
    """
    if getattr(inp, "validate_runtime", False):
        return out.model_copy(update=cross_validate_tool(tool_name, out, inp).to_dict())
    return out


def finalize(inp: Any, out: Any, tool_name: str, kb_context: dict | None = None) -> Any:
    """Tail unico dei tool: arricchisce con riferimenti KB (Tappa 2) e poi con la
    cross-validation runtime (modalità C, validate_runtime).

    KB references (Tappa 2):
      - `with_kb_references=True` → popola `riferimenti_kb`
      - `dynamic_kb=True` → verbatim live dalla KB (Fase 2) invece dello snapshot
      - `validate_kb_values=True` → popola `kb_validation` (convergenza valori
        normativi hardcoded vs verbatim KB; Fase 2)
    """
    if getattr(inp, "with_kb_references", False):
        from ._kb_references import build_kb_references
        out = out.model_copy(update={"riferimenti_kb": build_kb_references(
            tool_name, kb_context, dynamic_kb=getattr(inp, "dynamic_kb", False))})
    if getattr(inp, "validate_kb_values", False):
        from ._kb_validation import valida_valori_tool
        out = out.model_copy(update={"kb_validation": valida_valori_tool(tool_name)})
    return cv_hook(inp, out, tool_name)


def cross_validate_tool(tool_name: str, principale_output: Any, input_principale: Any) -> CrossValidationResult:
    """Entry point: esegue la cross-validation runtime per un tool."""
    res = CrossValidationResult()
    cfg = CONFIG.get(tool_name)
    if cfg is None:
        res.esito = "NON_DISPONIBILE"
        res.note.append(f"Tool '{tool_name}' senza validator gemello: cross-validation non disponibile.")
        return res

    if not _ensure_validator():
        res.esito = "ERRORE"
        res.note.append("Pacchetto k2a-elettrico-validator non importabile (assente e fallback path fallito).")
        warnings.warn(f"Cross-validation {tool_name}: validator non importabile", UserWarning, stacklevel=3)
        return res

    try:
        vfunc = _load_validator_func(*cfg["func"])
        vin = cfg["map"](input_principale)
        vout = vfunc(vin)
        p = cfg["norm_p"](principale_output)
        v = cfg["norm_v"](vout)
        convergente = _confronta(p, v, cfg["fields"], res)
        res.eseguita = True
        res.esito = "CONVERGENTE" if convergente else "DIVERGENTE"
        if not convergente:
            warnings.warn(
                f"Cross-validation runtime DIVERGENTE per {tool_name}: vedi cross_validation_note",
                UserWarning, stacklevel=3)
    except SkipCrossValidation as e:
        res.esito = "NON_CONFRONTABILE"
        res.note.append(str(e))
    except Exception as e:  # noqa: BLE001
        res.esito = "ERRORE"
        res.note.append(f"Eccezione durante cross-validation: {e}")
        warnings.warn(f"Cross-validation runtime ERRORE per {tool_name}: {e}", UserWarning, stacklevel=3)
    return res
