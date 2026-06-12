"""Verifica protezione AC — CEI 64-8 art.433.1 + 434.5.2 + CEI EN 61439-1 (Icw blindo).

v0.4: supporto I²t let-through realistico (database costruttori + override)
+ tipo_connessione (cavo / blindosbarra / sbarra_dedicata).
"""
from __future__ import annotations
import json
from pathlib import Path
from typing import Literal
from pydantic import BaseModel, Field

_DATA = json.loads((Path(__file__).parent / "data" / "portate_cei_unel_35024.json").read_text())
_I2T_DB = json.loads((Path(__file__).parent / "data" / "i2t_protezioni.json").read_text())


class VerificaProtezioneInput(BaseModel):
    Ib: float = Field(..., gt=0)
    In: float = Field(..., gt=0)
    Iz: float = Field(..., gt=0)
    sezione_mm2: float = Field(..., gt=0)
    materiale: Literal["Cu", "Al"] = "Cu"
    isolante: Literal["PVC", "EPR"] = "PVC"
    Icc_max_kA: float = Field(..., gt=0)
    tempo_intervento_max_s: float = 0.4
    I2_su_In_ratio: float = 1.45
    I2t_let_through_A2s: float | None = Field(
        default=None, ge=0,
        description="Energia let-through esplicita della protezione (A²·s) presa dalla "
                    "curva di limitazione del costruttore. Se fornita, override su Icc²·t "
                    "teorico. Tipico MCCB con limiting: 50k-3M A²·s per famiglie standard.")
    famiglia_protezione: str | None = Field(
        default=None,
        description="Chiave database I²t (es. 'ABB_Tmax_XT.MCCB_T3_250A_Icu36'). "
                    "Se fornita, lookup automatico di I2t_let_through_A2s dalla tabella interna. "
                    "Override comunque possibile via I2t_let_through_A2s diretto.")
    tipo_connessione: Literal["cavo", "blindosbarra", "sbarra_dedicata"] = Field(
        default="cavo",
        description="Tipo di connessione downstream alla protezione. "
                    "'cavo' = verifica k²S² standard. "
                    "'blindosbarra'/'sbarra_dedicata' = verifica Icw vs Icc.")
    Icw_blindo_kA: float | None = Field(
        default=None, ge=0,
        description="Icw 1s blindosbarra/sbarra dedicata (kA), obbligatorio se "
                    "tipo_connessione diverso da 'cavo'.")
    validate_runtime: bool = Field(False, description="Modalità C runtime (ADR-009): cross-validation inline.")
    with_kb_references: bool = Field(False, description="Tappa 2: include riferimenti normativi KB in riferimenti_kb.")
    dynamic_kb: bool = Field(False, description="Tappa 2 Fase 2: con with_kb_references, recupera i verbatim live dalla KB invece dello snapshot statico. Default False.")
    validate_kb_values: bool = Field(False, description="Tappa 2 Fase 2: con with_kb_references, valida i valori normativi del tool contro i verbatim KB (campo kb_validation). Default False.")


class VerificaProtezioneOutput(BaseModel):
    verifica_sovraccarico_433_1: bool
    verifica_sovraccarico_msg: str
    verifica_I2_45_Iz: bool
    verifica_I2t_434_5_2: bool
    verifica_I2t_msg: str
    k_costante: int
    I2t_ammissibile_A2s: float
    tempo_max_intervento_per_I2t_s: float
    conclusione_finale: bool
    I2t_passante_calcolato_A2s: float
    I2t_passante_fonte: str
    avvertenze: list[str]
    trace: dict
    cross_validation_eseguita: bool = False
    cross_validation_esito: str = "NON_ESEGUITA"
    cross_validation_delta_pct: dict = Field(default_factory=dict)
    cross_validation_note: list[str] = Field(default_factory=list)
    riferimenti_kb: list[dict] = Field(default_factory=list)
    kb_validation: list[dict] = Field(default_factory=list)


def _lookup_database_i2t(famiglia: str, Icc_kA: float) -> tuple[float, str] | None:
    """Lookup I²t let-through dal database costruttori.

    Ritorna (A²s, fonte_str) se Icc dentro range caratterizzato; None se:
      - famiglia non trovata
      - Icc > Icc_max caratterizzato (fuori certificazione costruttore)
    Per Icc ≤ Icc_min usa minimo (lato sicuro: energia minima reale).
    """
    try:
        costruttore, modello = famiglia.split(".", 1)
        node = _I2T_DB[costruttore][modello]["I2t_letthrough_kA2s"]
    except (KeyError, ValueError):
        return None
    punti = sorted(
        (float(k), float(v) * 1e6)  # kA²s → A²s
        for k, v in node.items() if not k.startswith("_")
    )
    if not punti:
        return None
    Icc_min, Icc_max = punti[0][0], punti[-1][0]
    if Icc_kA <= Icc_min:
        return punti[0][1], f"let-through da database {famiglia} (Icc≤{Icc_min}kA, uso minimo)"
    if Icc_kA > Icc_max:
        # Fuori range caratterizzato: dispositivo non garantito.
        # Ritorna None → chiamante usa fallback teorico con avvertenza forte.
        return None
    for i in range(len(punti) - 1):
        k0, v0 = punti[i]
        k1, v1 = punti[i + 1]
        if k0 <= Icc_kA <= k1:
            v_interp = v0 + (v1 - v0) * (Icc_kA - k0) / (k1 - k0)
            return v_interp, f"let-through da database {famiglia} (interp. tra {k0}-{k1}kA)"
    return None


def verifica_protezione(inp: VerificaProtezioneInput) -> VerificaProtezioneOutput:
    avvertenze: list[str] = []

    # === Sovraccarico (sempre verificato) ===
    cond1 = inp.Ib <= inp.In <= inp.Iz
    if cond1:
        msg1 = f"OK 433.1: Ib={inp.Ib} ≤ In={inp.In} ≤ Iz={inp.Iz}A"
    elif inp.In < inp.Ib:
        msg1 = f"KO: In={inp.In} < Ib={inp.Ib}A"
    else:
        msg1 = f"KO: In={inp.In} > Iz={inp.Iz}A"
    I2 = inp.I2_su_In_ratio * inp.In
    cond_I2 = I2 <= 1.45 * inp.Iz

    # === Caso blindosbarra / sbarra dedicata: verifica Icw vs Icc ===
    if inp.tipo_connessione in ("blindosbarra", "sbarra_dedicata"):
        if inp.Icw_blindo_kA is None:
            raise ValueError(f"tipo_connessione={inp.tipo_connessione} richiede Icw_blindo_kA")
        cond_blindo = inp.Icc_max_kA <= inp.Icw_blindo_kA
        avvertenze.append(
            "Verifica k²S² non applicabile per blindo/sbarra: verificato Icw vs Icc 1s."
        )
        msg_I2t = (
            f"OK: Icc={inp.Icc_max_kA}kA ≤ Icw_blindo={inp.Icw_blindo_kA}kA (CEI EN 61439-1)"
            if cond_blindo else
            f"KO: Icc={inp.Icc_max_kA}kA > Icw_blindo={inp.Icw_blindo_kA}kA"
        )
        _out = VerificaProtezioneOutput(
            verifica_sovraccarico_433_1=cond1, verifica_sovraccarico_msg=msg1,
            verifica_I2_45_Iz=cond_I2,
            verifica_I2t_434_5_2=cond_blindo, verifica_I2t_msg=msg_I2t,
            k_costante=0, I2t_ammissibile_A2s=0.0,
            tempo_max_intervento_per_I2t_s=0.0,
            conclusione_finale=cond1 and cond_I2 and cond_blindo,
            I2t_passante_calcolato_A2s=0.0,
            I2t_passante_fonte=f"verifica Icw (tipo_connessione={inp.tipo_connessione})",
            avvertenze=avvertenze,
            trace={
                "norma": "CEI EN 61439-1 (verifica Icw blindo/sbarra)",
                "modello": f"{inp.tipo_connessione}",
            },
        )
        from ._cross_validation import finalize
        return finalize(inp, _out, "verifica_protezione", {"tipo_connessione": inp.tipo_connessione})

    # === Caso cavo: k²S² standard con I²t passante realistico ===
    k = _DATA["k_costanti_I2t"][f"{inp.materiale}_{inp.isolante}"]
    I2t_amm = (k * inp.sezione_mm2) ** 2
    Icc_A = inp.Icc_max_kA * 1000

    # Determinazione I²t passante (priorità: override > database > teorico)
    if inp.I2t_let_through_A2s is not None:
        I2t_pass = inp.I2t_let_through_A2s
        fonte = "let-through override utente"
    elif inp.famiglia_protezione is not None:
        lookup = _lookup_database_i2t(inp.famiglia_protezione, inp.Icc_max_kA)
        if lookup is not None:
            I2t_pass, fonte = lookup
        else:
            # Distingui causa del None: famiglia inesistente vs Icc fuori range
            try:
                costruttore, modello = inp.famiglia_protezione.split(".", 1)
                famiglia_esiste = (
                    costruttore in _I2T_DB and modello in _I2T_DB[costruttore]
                )
            except ValueError:
                famiglia_esiste = False

            I2t_pass = Icc_A ** 2 * inp.tempo_intervento_max_s
            if not famiglia_esiste:
                fonte = "Icc²·t teorico (famiglia non trovata in DB)"
                avvertenze.append(
                    f"Famiglia '{inp.famiglia_protezione}' non trovata in database."
                )
            else:
                fonte = "Icc²·t teorico (Icc fuori range caratterizzato)"
                avvertenze.append(
                    f"ATTENZIONE: la famiglia '{inp.famiglia_protezione}' "
                    f"non è caratterizzata per Icc={inp.Icc_max_kA} kA. "
                    f"Verificare scelta protezione: potrebbe essere sottodimensionata. "
                    f"Usato modello Icc²·t teorico (conservativo)."
                )
    else:
        I2t_pass = Icc_A ** 2 * inp.tempo_intervento_max_s
        fonte = "Icc²·t teorico"
        if inp.Icc_max_kA > 10:
            avvertenze.append(
                "Modello conservativo: considerare curva let-through "
                "costruttore per MCCB con Icc > 10 kA (può ridurre I²t passante "
                "di 1-2 ordini di grandezza)."
            )

    cond_I2t = I2t_pass <= I2t_amm
    t_max = I2t_amm / (Icc_A ** 2)
    msg_I2t = (
        f"OK: I²t passante={I2t_pass:.0f} A²s ≤ k²S²={I2t_amm:.0f} A²s"
        if cond_I2t else
        f"KO: I²t passante={I2t_pass:.0f} A²s > k²S²={I2t_amm:.0f} A²s"
    )

    _out = VerificaProtezioneOutput(
        verifica_sovraccarico_433_1=cond1, verifica_sovraccarico_msg=msg1,
        verifica_I2_45_Iz=cond_I2,
        verifica_I2t_434_5_2=cond_I2t, verifica_I2t_msg=msg_I2t,
        k_costante=k, I2t_ammissibile_A2s=round(I2t_amm, 1),
        tempo_max_intervento_per_I2t_s=round(t_max, 5),
        conclusione_finale=cond1 and cond_I2 and cond_I2t,
        I2t_passante_calcolato_A2s=round(I2t_pass, 2),
        I2t_passante_fonte=fonte,
        avvertenze=avvertenze,
        trace={
            "norma": "CEI 64-8 art.433.1 + 434.5.2",
            "k_source": "tab.43A",
            "modello_I2t": fonte,
        },
    )
    from ._cross_validation import finalize
    return finalize(inp, _out, "verifica_protezione", {"tipo_connessione": inp.tipo_connessione})
