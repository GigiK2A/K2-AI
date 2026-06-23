"""Dimensionamento cavi BT — CEI-UNEL 35024/1 + CEI 64-8 art.433.1 + art.523.5 + art.521.8 (n_paralleli)."""
from __future__ import annotations
import json
from pathlib import Path
from typing import Literal
from pydantic import BaseModel, Field

_DATA = json.loads((Path(__file__).parent / "data" / "portate_cei_unel_35024.json").read_text())


class DimensionaCavoInput(BaseModel):
    Ib: float = Field(..., gt=0, description="Corrente d'impiego totale del circuito A")
    posa: Literal["B1", "B2", "C", "E", "F", "D1"] = "C"
    isolante: Literal["PVC", "EPR_XLPE"] = "PVC"
    materiale: Literal["Cu"] = "Cu"
    temp_ambiente: float = 30.0
    n_circuiti_raggruppati: int = Field(1, ge=1)
    n_paralleli: int = Field(
        1, ge=1, le=6,
        description="Conduttori in parallelo per fase (CEI 64-8 art.521.8). "
                    "Validità subordinata a stessa sezione, lunghezza, materiale, isolante, "
                    "tipo di posa, attestazione simmetrica. Oltre 6 paralleli si raccomanda "
                    "blindosbarra (CEI EN 61439-6).")
    In_protezione: float | None = None
    validate_runtime: bool = Field(False, description="Modalità C runtime (ADR-009): cross-validation inline.")
    with_kb_references: bool = Field(False, description="Tappa 2: include riferimenti normativi KB in riferimenti_kb.")
    dynamic_kb: bool = Field(False, description="Tappa 2 Fase 2: con with_kb_references, recupera i verbatim live dalla KB invece dello snapshot statico. Default False.")
    validate_kb_values: bool = Field(False, description="Tappa 2 Fase 2: con with_kb_references, valida i valori normativi del tool contro i verbatim KB (campo kb_validation). Default False.")


class DimensionaCavoOutput(BaseModel):
    sezione_minima_mm2: float                       # sezione SINGOLO conduttore
    Iz_corretta: float                              # Iz EFFETTIVA del circuito (n_par × Iz_singolo × k_par)
    fattore_temperatura_k1: float
    fattore_raggruppamento_k2: float
    # --- Campi n_paralleli (ADR-033, CEI 64-8 art.521.8 + art.523.5) ---
    n_paralleli: int = 1                            # numero conduttori in parallelo per fase
    Iz_singolo_A: float = 0.0                       # Iz del SINGOLO conduttore (Iz_30 × k1 × k2)
    Ib_per_cavo_A: float = 0.0                      # Ib / n_paralleli (assunzione parallelo bilanciato)
    fattore_paralleli_kpar: float = 1.0             # coefficiente correzione paralleli (CEI 64-8 §523.5: ~0.85)
    sezione_totale_mm2: float = 0.0                 # n_par × sezione_singola (informativa)
    notazione_display: str = ""                     # es. "4x240 mm² Cu EPR" per scrittura PE
    coordinamento_433_1: bool | None
    coordinamento_msg: str
    trace: dict
    cross_validation_eseguita: bool = False
    cross_validation_esito: str = "NON_ESEGUITA"
    cross_validation_delta_pct: dict = Field(default_factory=dict)
    cross_validation_note: list[str] = Field(default_factory=list)
    riferimenti_kb: list[dict] = Field(default_factory=list)
    kb_validation: list[dict] = Field(default_factory=list)


def _fattore_temp(t: float, isol: str) -> float:
    key = "fattori_correttivi_temperatura_aria_PVC" if isol == "PVC" else "fattori_correttivi_temperatura_aria_EPR"
    tbl = _DATA[key]
    ts = sorted(int(k) for k in tbl.keys())
    if t <= ts[0]: return float(tbl[str(ts[0])])
    if t >= ts[-1]: return float(tbl[str(ts[-1])])
    for i in range(len(ts) - 1):
        if ts[i] <= t <= ts[i + 1]:
            return tbl[str(ts[i])] + (tbl[str(ts[i + 1])] - tbl[str(ts[i])]) * (t - ts[i]) / (ts[i + 1] - ts[i])
    return 1.0


def _fattore_raggr(n: int) -> float:
    tbl = _DATA["fattori_correttivi_raggruppamento"]
    ks = sorted(int(k) for k in tbl.keys())
    if n <= ks[0]: return float(tbl[str(ks[0])])
    if n >= ks[-1]: return float(tbl[str(ks[-1])])
    for k in ks:
        if k >= n: return float(tbl[str(k)])
    return 1.0


# Coefficiente correzione cavi in parallelo a contatto (CEI 64-8 §523.5).
# Conservativo per posa aerea in canale/passerella, conduttori a contatto
# attestati in modo simmetrico. Per cavi separati in passerella distanziati,
# valori più alti (≥ 0.90) possono essere usati con motivazione.
_KPAR_PARALLELI: dict[int, float] = {
    1: 1.00,
    2: 0.90,
    3: 0.88,
    4: 0.85,
    5: 0.82,
    6: 0.80,
}


def dimensiona_cavo(inp: DimensionaCavoInput) -> DimensionaCavoOutput:
    """Dimensionamento cavo con supporto cavi in parallelo (CEI 64-8 §521.8).

    Logica n_paralleli (ADR-033):
      1) Ogni cavo singolo trasporta Ib/n_par (parallelo bilanciato).
      2) Sezione minima del SINGOLO cavo: Iz_singolo × k1 × k2 ≥ Ib_per_cavo.
      3) Iz totale del circuito: Iz_singolo × n_par × k_par
         con k_par = coefficiente correzione paralleli (CEI 64-8 §523.5).
      4) Coordinamento 433.1: Ib ≤ In ≤ Iz_totale.
      5) Notazione: "n_par × S mm² Cu/Al EPR/PVC" pronta per CSA/PE.
    """
    tbl = _DATA[f"rame_{inp.isolante}"]
    k1 = _fattore_temp(inp.temp_ambiente, inp.isolante)
    k2 = _fattore_raggr(inp.n_circuiti_raggruppati)
    k_par = _KPAR_PARALLELI[inp.n_paralleli]

    # Parallelo bilanciato: ogni cavo trasporta Ib/n_par
    Ib_per_cavo = inp.Ib / inp.n_paralleli

    # Vincolo singolo cavo: Iz_singolo × k1 × k2 ≥ Ib_per_cavo (portata)
    # Vincolo coordinamento: Iz_totale ≥ In_protezione (se fornita)
    # Quindi Iz_singolo ≥ max(Ib_per_cavo, In_protezione / (n_par × k_par))
    Iz_singolo_min = Ib_per_cavo
    if inp.In_protezione:
        Iz_singolo_min_coord = inp.In_protezione / (inp.n_paralleli * k_par)
        Iz_singolo_min = max(Iz_singolo_min, Iz_singolo_min_coord)

    # Cerco sezione minima del SINGOLO conduttore che soddisfi entrambi i vincoli
    sez_ok, Iz_singolo = None, 0.0
    for sez_str, riga in tbl.items():
        Iz_eff_singolo = riga[inp.posa] * k1 * k2
        if Iz_eff_singolo >= Iz_singolo_min:
            sez_ok, Iz_singolo = float(sez_str), Iz_eff_singolo
            break

    # Vincolo principale Ib_per_cavo: se nessuna sezione lo soddisfa → eccezione (errore reale)
    # Vincolo coordinamento: se non soddisfatto, uso sezione max e segnalo KO
    if sez_ok is None:
        if Ib_per_cavo > Iz_singolo_min * 0.99:
            # Il vincolo bloccante è Ib (portata) — errore di dimensionamento
            raise ValueError(
                f"Nessuna sezione soddisfa Ib_per_cavo={Ib_per_cavo:.1f}A "
                f"(Ib={inp.Ib}A / n_paralleli={inp.n_paralleli}). "
                f"Aumentare n_paralleli o cambiare posa.")
        # Vincolo bloccante è il coordinamento: uso la sezione max disponibile,
        # il coordinamento riporterà KO
        sez_max_str = max(tbl.keys(), key=float)
        sez_ok = float(sez_max_str)
        Iz_singolo = tbl[sez_max_str][inp.posa] * k1 * k2

    # Iz totale del circuito (n_par cavi in parallelo, derating k_par)
    Iz_totale = Iz_singolo * inp.n_paralleli * k_par

    # Notazione display per scrittura PE/CSA
    isol_str = "EPR" if inp.isolante == "EPR_XLPE" else "PVC"
    sez_disp = int(sez_ok) if sez_ok == int(sez_ok) else sez_ok
    notazione = (f"{inp.n_paralleli}x{sez_disp} mm² Cu {isol_str}"
                 if inp.n_paralleli > 1 else f"{sez_disp} mm² Cu {isol_str}")

    coord, msg = None, "In_protezione non fornita."
    if inp.In_protezione:
        # Coordinamento 433.1 sulla Iz totale del circuito
        coord = inp.Ib <= inp.In_protezione <= Iz_totale
        if coord:
            par_info = f" [{inp.n_paralleli}x{sez_disp}mm²]" if inp.n_paralleli > 1 else ""
            msg = (f"OK 433.1: Ib={inp.Ib} ≤ In={inp.In_protezione} ≤ "
                   f"Iz_tot={Iz_totale:.1f}A{par_info}")
        elif inp.In_protezione < inp.Ib:
            msg = f"KO: In={inp.In_protezione} < Ib={inp.Ib}A"
        else:
            msg = f"KO: In={inp.In_protezione} > Iz_tot={Iz_totale:.1f}A"

    _out = DimensionaCavoOutput(
        sezione_minima_mm2=sez_ok,
        Iz_corretta=round(Iz_totale, 2),
        fattore_temperatura_k1=round(k1, 3),
        fattore_raggruppamento_k2=round(k2, 3),
        n_paralleli=inp.n_paralleli,
        Iz_singolo_A=round(Iz_singolo, 2),
        Ib_per_cavo_A=round(Ib_per_cavo, 2),
        fattore_paralleli_kpar=k_par,
        sezione_totale_mm2=round(sez_ok * inp.n_paralleli, 2),
        notazione_display=notazione,
        coordinamento_433_1=coord,
        coordinamento_msg=msg,
        trace={
            "norma": "CEI-UNEL 35024/1 + CEI 64-8 art.433.1 + art.521.8 + art.523.5",
            "formula_Iz_singolo": "Iz_singolo = Iz_30°C × k1(T) × k2(n_raggr)",
            "formula_Iz_totale": "Iz_totale = Iz_singolo × n_paralleli × k_par",
            "k_par_range": "1: 1.00, 2: 0.90, 3: 0.88, 4: 0.85, 5: 0.82, 6: 0.80 (CEI 64-8 §523.5 conservativo)",
            "vincoli_paralleli_521_8": (
                "Per n_paralleli > 1: stessa sezione, lunghezza, materiale, "
                "isolante, tipo di posa, attestazione simmetrica obbligatorie. "
                "Verifica I²t per CIASCUN cavo singolo: I²t_singolo ≤ K²·S² "
                "con Icc_per_cavo = Icc_totale / n_paralleli (parallelo bilanciato)."),
        },
    )
    from ._cross_validation import finalize
    return finalize(inp, _out, "dimensiona_cavo", {"In_protezione_fornita": inp.In_protezione is not None})


# ---- Helper pubblico: Iz per sezione installata --------------------------

PosaType = Literal["B1", "B2", "C", "D1", "E", "F"]


def iz_per_sezione(
    sezione_mm2: float,
    materiale: Literal["Cu", "Al"] = "Cu",
    isolante: Literal["PVC", "EPR", "XLPE", "EPR_XLPE"] = "PVC",
    posa: PosaType = "C",
    k1_temperatura: float = 1.0,
    k2_raggruppamento: float = 1.0,
) -> float:
    """Ritorna Iz [A] della sezione installata, considerando posa e derating.

    Lookup tabella CEI-UNEL 35024-1 ed. 2021. Iz_30°C tabellare × k1 × k2.

    Esempi:
        >>> iz_per_sezione(16, "Cu", "EPR_XLPE", "D1")
        95.0
        >>> iz_per_sezione(2.5, "Cu", "PVC", "B1")
        21.0
        >>> iz_per_sezione(10, "Cu", "PVC", "C", k1_temperatura=0.87)  # T=40°C
        49.59

    Solleva ValueError se sezione non in tabella.
    Solleva NotImplementedError se materiale=Al (non popolato in v0.3).
    """
    if materiale == "Al":
        raise NotImplementedError("Tabella Al non popolata in v0.3 (solo Cu).")
    isolante_key = "EPR_XLPE" if isolante in ("EPR", "XLPE", "EPR_XLPE") else "PVC"
    table_key = f"rame_{isolante_key}"
    if table_key not in _DATA:
        raise ValueError(f"Combinazione non supportata: {materiale}/{isolante}")
    tbl = _DATA[table_key]
    # Chiavi JSON: "1.5", "2.5", "4", "6", "10", "16", ...
    sez_key = str(int(sezione_mm2)) if sezione_mm2 == int(sezione_mm2) else str(sezione_mm2)
    if sez_key not in tbl:
        raise ValueError(
            f"Sezione {sezione_mm2}mm² non in tabella. "
            f"Disponibili: {sorted(tbl.keys(), key=float)}"
        )
    if posa not in tbl[sez_key]:
        raise ValueError(f"Posa '{posa}' non disponibile per sezione {sezione_mm2}mm².")
    Iz_30 = tbl[sez_key][posa]
    return round(Iz_30 * k1_temperatura * k2_raggruppamento, 2)
