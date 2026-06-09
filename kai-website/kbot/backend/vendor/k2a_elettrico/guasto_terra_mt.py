"""Corrente di guasto monofase a terra in reti MT (Ig) — CEI 0-16 §5.2.1.7.

Nasce dal finding Redbox: la verifica di terra MT assumeva Ig=50 A hardcoded. Questo
tool calcola Ig in modo metodologicamente solido, con 3 modalità a firmabilità esplicita,
e (opzionale) chiude la catena Ig → U_E = R_terra·Ig.

Modalità:
  - dati_dso_dichiarati  → usa Ig comunicata dal DSO (FIRMABILE; CEI 0-16 §5.2.1.7)
  - neutro_isolato_puro  → formula empirica CEI 0-16 §5.2.1.7: Ig = U·(0,003·L_aerea + 0,2·L_cavo) [FIRMABILE]
  - stima_letteratura    → contributo capacitivo C0 utente + stima rete DSO [NON FIRMABILE, indicativo]

NOTE §13 (verificate in KB CEI 0-16):
  - La formula empirica è in §5.2.1.7 (NON §A.4, inesistente in CEI 0-16:2025-04).
  - §8.5.12.3.2: la 51N si tara al 140% di Ig comunicata dal DSO, "tipicamente 70 A a 20 kV
    e 56 A a 15 kV" su reti a neutro compensato → Ig DSO ≈ 50/40 A (valida l'assunto Redbox).
  - Non esiste validator gemello né un tool MCP `verifica_terra_cabina` MT (la catena U_E
    vive in redbox_verify.py): il tool calcola U_E internamente se gli si passa R_terra.
"""
from __future__ import annotations

import math
from typing import Literal

from pydantic import BaseModel, Field

# Stima Ig contributo rete DSO (A) per zona — letteratura/prassi (range indicativi).
_IG_DSO_ZONA = {
    "urbana": (30.0, 80.0),       # rete fitta in cavo
    "suburbana": (20.0, 50.0),
    "rurale": (10.0, 30.0),       # prevalenza linee aeree
    "industriale": (40.0, 100.0),
}
# Ig DSO tipica neutro compensato (da §8.5.12.3.2: 51N 140%·Ig = 70/56 A → Ig ≈ 50/40 A).
_IG_NC_TIPICA = {20: 50.0, 15: 40.0}


class CorrenteGuastoTerraMtInput(BaseModel):
    tensione_nominale_kV: float = Field(20.0, gt=1, description="Tensione nominale rete MT (15/20 tipici)")
    modalita_calcolo: Literal["dati_dso_dichiarati", "neutro_isolato_puro", "stima_letteratura"] = \
        "dati_dso_dichiarati"

    # dati_dso_dichiarati
    ig_dso_dichiarata_A: float | None = Field(None, description="Ig comunicata dal DSO [A]")
    stato_neutro_dso: Literal["isolato", "compensato", "compensato_con_rinforzo"] | None = None

    # neutro_isolato_puro / stima_letteratura
    lunghezza_cavi_mt_utente_km: float | None = Field(None, ge=0)
    lunghezza_linee_aeree_utente_km: float = Field(0.0, ge=0)
    # stima_letteratura
    tipo_zona_dso: Literal["urbana", "suburbana", "rurale", "industriale"] | None = None
    corrente_rinforzo_wattmetrica_A: float | None = Field(None, description="Rinforzo attivo Petersen (50/350 A tipici)")
    capacita_omopolare_C0_uF_per_km: float = Field(0.3, gt=0, description="C0 cavo MT [µF/km]")

    # opzionale: chiusura catena Ig → U_E
    R_terra_ohm: float | None = Field(None, description="Se fornita, calcola U_E = R_terra·Ig")
    U_TP_limite_V: float = Field(200.0, description="Tensione di contatto ammissibile (CEI 99-3)")


class CorrenteGuastoTerraMtOutput(BaseModel):
    ig_calcolata_A: float
    ig_range_min_A: float | None = None
    ig_range_max_A: float | None = None
    modalita_usata: str
    metodo_calcolo: str
    formula_applicata: str
    parametri_assunti: dict
    firmabile_per_asseverazione: bool
    nota_firmabilita: str
    # catena U_E
    U_E_V: float | None = None
    verifica_UE_esito: Literal["ok", "ko", "non_calcolata"] = "non_calcolata"
    # soglia 67N
    soglia_67N_richiesta: bool
    esito_complessivo: Literal["ok", "warning", "stima_indicativa"]
    norma_riferimento: str = "CEI 0-16:2025-04 §5.2.1.7 + §8.5.12.3.2; CEI 11-25 (IEC 60909); CEI 99-3 (terra)"
    note_normative: list[str] = Field(default_factory=list)
    warnings: list[str] = Field(default_factory=list)


def _soglia_67N(U_kV: float, L_cavo_km: float | None) -> bool:
    """67N richiesta se rete cavo > 400 m a 20 kV / 533 m a 15 kV (CEI 0-16 All.2b nota 272)."""
    L_m = (L_cavo_km or 0.0) * 1000.0
    if U_kV >= 17.5:
        return L_m > 400.0
    return L_m > 533.0


def corrente_guasto_terra_mt(inp: CorrenteGuastoTerraMtInput) -> CorrenteGuastoTerraMtOutput:
    U = inp.tensione_nominale_kV
    warnings: list[str] = []
    note: list[str] = []
    ig_min = ig_max = None

    if inp.modalita_calcolo == "dati_dso_dichiarati":
        if inp.ig_dso_dichiarata_A is None:
            raise ValueError("modalità dati_dso_dichiarati: ig_dso_dichiarata_A obbligatoria")
        ig = float(inp.ig_dso_dichiarata_A)
        firmabile = True
        metodo = "input_dso_dichiarato"
        formula = "Ig = valore comunicato dal DSO (CEI 0-16 §5.2.1.7 / lettera di connessione)"
        nota = "Valore comunicato dal Distributore: firmabile per asseverazione."
        note.append("CEI 0-16 §5.2.1.7: Ig massima e tempo di eliminazione sono dichiarati dal DSO.")

    elif inp.modalita_calcolo == "neutro_isolato_puro":
        L1 = inp.lunghezza_linee_aeree_utente_km
        L2 = inp.lunghezza_cavi_mt_utente_km or 0.0
        ig = U * (0.003 * L1 + 0.2 * L2)
        firmabile = True
        metodo = "formula_empirica_CEI_0_16_5_2_1_7"
        formula = "Ig = U·(0,003·L_aerea + 0,2·L_cavo)  [U in kV, L in km]"
        nota = ("Formula empirica CEI 0-16 §5.2.1.7 per reti a neutro isolato: applicabile se "
                "la rete (utente+DSO) è effettivamente a neutro isolato. Approssimata; valori "
                "precisi via CEI 11-25 (IEC 60909).")
        note.append("CEI 0-16 §5.2.1.7: formula empirica convenzionale per neutro isolato.")
        if L2 == 0 and L1 == 0:
            warnings.append("Lunghezze nulle: Ig ≈ 0; verificare i dati di rete.")

    else:  # stima_letteratura
        L2 = inp.lunghezza_cavi_mt_utente_km or 0.0
        omega = 2 * math.pi * 50.0
        C0 = inp.capacita_omopolare_C0_uF_per_km * L2 * 1e-6  # F
        E_fase = (U * 1000.0) / math.sqrt(3)
        ig_utente_cap = 3 * omega * C0 * E_fase  # contributo capacitivo utente
        if inp.corrente_rinforzo_wattmetrica_A:
            base = max(inp.corrente_rinforzo_wattmetrica_A, ig_utente_cap)
            ig_min, ig_max = base, base * 1.4
        else:
            zona_min, zona_max = _IG_DSO_ZONA.get(inp.tipo_zona_dso or "suburbana", (20.0, 50.0))
            ig_min = ig_utente_cap + zona_min
            ig_max = ig_utente_cap + zona_max
        ig = (ig_min + ig_max) / 2
        firmabile = False
        metodo = "calcolo_capacitivo_C0_piu_stima_DSO"
        formula = "Ig ≈ 3ωC0·E_fase (utente) + contributo DSO stimato per zona"
        nota = ("STIMA indicativa (intervallo): NON firmabile per asseverazione. Per il documento "
                "finale richiedere la Ig ufficiale dal DSO (modalità dati_dso_dichiarati).")
        note.append("Range zona DSO da letteratura/prassi (cfr. tesi PoliTo Canova/Ireti §4.2.2.1).")
        note.append("CEI 0-16 §8.5.12.3.2: Ig tipica neutro compensato ≈ "
                    f"{_IG_NC_TIPICA.get(int(U), 50.0):.0f} A (51N al 140% → "
                    f"{_IG_NC_TIPICA.get(int(U), 50.0)*1.4:.0f} A).")
        warnings.append("Valore medio di un intervallo: usare con cautela, non per la firma.")

    # catena Ig → U_E (se R_terra fornita)
    U_E = None; verifica_UE = "non_calcolata"
    if inp.R_terra_ohm is not None:
        U_E = round(inp.R_terra_ohm * ig, 1)
        verifica_UE = "ok" if U_E <= inp.U_TP_limite_V else "ko"
        note.append(f"Catena Ig→U_E: U_E = R_terra·Ig = {inp.R_terra_ohm}·{ig:.1f} = {U_E} V "
                    f"(limite UTP {inp.U_TP_limite_V} V, CEI 99-3).")
        if verifica_UE == "ko":
            warnings.append(f"U_E={U_E} V > UTP {inp.U_TP_limite_V} V: verificare terra "
                            "(misura ρ, integrazione dispersore) o tempo eliminazione guasto.")

    s67 = _soglia_67N(U, inp.lunghezza_cavi_mt_utente_km)
    esito = "stima_indicativa" if not firmabile else ("warning" if warnings else "ok")

    return CorrenteGuastoTerraMtOutput(
        ig_calcolata_A=round(ig, 2),
        ig_range_min_A=round(ig_min, 2) if ig_min is not None else None,
        ig_range_max_A=round(ig_max, 2) if ig_max is not None else None,
        modalita_usata=inp.modalita_calcolo, metodo_calcolo=metodo, formula_applicata=formula,
        parametri_assunti={"U_kV": U, "L_cavo_km": inp.lunghezza_cavi_mt_utente_km,
                           "L_aerea_km": inp.lunghezza_linee_aeree_utente_km,
                           "zona": inp.tipo_zona_dso, "C0_uF_km": inp.capacita_omopolare_C0_uF_per_km},
        firmabile_per_asseverazione=firmabile, nota_firmabilita=nota,
        U_E_V=U_E, verifica_UE_esito=verifica_UE, soglia_67N_richiesta=s67,
        esito_complessivo=esito, note_normative=note, warnings=warnings)
