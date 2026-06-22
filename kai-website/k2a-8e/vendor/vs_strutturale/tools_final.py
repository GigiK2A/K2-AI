"""Tool finali v0.4: distribute_anchor_reactions, lookup_fatigue_detail,
classify_static_scheme + get_rt_template, wind_action_extended."""

from __future__ import annotations
from ._hashing import compute_inputs_hash

import json
from pathlib import Path
from typing import Literal

from pydantic import BaseModel, Field

from .check_wind_fatigue import DETTAGLI_TIPICI_PALI_TLC
from .schemas import CalcResult, TraceStep

RT_PATH = Path(__file__).parent.parent.parent / "data" / "rt_templates.json"


# ---------------------------------------------------------------------------
# distribute_anchor_reactions — T per ogni ancoraggio in layout n×m
# ---------------------------------------------------------------------------

class AnchorPoint(BaseModel):
    x_mm: float
    y_mm: float
    nome: str = ""


class DistributeAnchorInput(BaseModel):
    """Distribuisce N+M_x+M_y+V su layout di ancoraggi 2D.

    Assume piastra rigida, asse neutro al baricentro. Trazione = − (cls non
    reagisce a trazione, ma per ancoraggi chimici tutti contribuiscono).

    T_i = N/n − M_x · y_i/Σy² − M_y · x_i/Σx²    (segno: + = compressione)
    """
    layout: list[AnchorPoint] = Field(..., min_length=2)
    N_Ed_kN: float = Field(0.0, description="+ trazione, − compressione (applicata al baricentro)")
    M_x_Ed_kNm: float = Field(0.0, description="Momento attorno asse x (genera T su lato +y)")
    M_y_Ed_kNm: float = Field(0.0, description="Momento attorno asse y")
    V_Ed_kN: float = Field(0.0, description="Taglio totale (distribuito uniforme su ancoraggi)")


class AnchorReaction(BaseModel):
    nome: str
    x_mm: float
    y_mm: float
    T_Ed_kN: float    # trazione positiva
    V_Ed_per_kN: float


class DistributeAnchorOutput(CalcResult):
    n_ancoraggi: int = 0
    reazioni: list[AnchorReaction] = Field(default_factory=list)
    T_max_kN: float | None = None
    T_max_ancoraggio_nome: str = ""
    V_per_ancoraggio_kN: float | None = None


def distribute_anchor_reactions(inp: DistributeAnchorInput) -> DistributeAnchorOutput:
    out = DistributeAnchorOutput(tool="distribute_anchor_reactions", inputs_hash=compute_inputs_hash(inp))
    n = len(inp.layout)

    # Baricentro
    x_g = sum(p.x_mm for p in inp.layout) / n
    y_g = sum(p.y_mm for p in inp.layout) / n
    # Coord relative al baricentro
    dx = [p.x_mm - x_g for p in inp.layout]
    dy = [p.y_mm - y_g for p in inp.layout]
    sum_y2 = sum(d * d for d in dy)
    sum_x2 = sum(d * d for d in dx)

    V_per = abs(inp.V_Ed_kN) / n
    out.V_per_ancoraggio_kN = V_per
    out.n_ancoraggi = n

    reazioni = []
    T_max = -float("inf")
    T_max_name = ""
    for i, p in enumerate(inp.layout):
        # Trazione positiva (M positivo provoca trazione sul lato +y per M_x).
        # Unità: M [kN·m] · y [mm] / Σy² [mm²] = kN·m/mm. Per ottenere kN: ×1000.
        T = inp.N_Ed_kN / n
        if sum_y2 > 0:
            T += inp.M_x_Ed_kNm * 1000.0 * dy[i] / sum_y2
        if sum_x2 > 0:
            T += inp.M_y_Ed_kNm * 1000.0 * dx[i] / sum_x2
        reazioni.append(AnchorReaction(
            nome=p.nome or f"A{i+1}", x_mm=p.x_mm, y_mm=p.y_mm,
            T_Ed_kN=T, V_Ed_per_kN=V_per,
        ))
        if T > T_max:
            T_max = T
            T_max_name = p.nome or f"A{i+1}"

    out.reazioni = reazioni
    out.T_max_kN = T_max
    out.T_max_ancoraggio_nome = T_max_name

    out.trace.append(TraceStep(
        label="distribuzione ancoraggi",
        formula="T_i = N/n + M_x·y_i/Σy² + M_y·x_i/Σx²",
        substitution=(
            f"n={n}, baricentro=({x_g:.1f}, {y_g:.1f}), Σy²={sum_y2:.0f}, Σx²={sum_x2:.0f} → "
            f"T_max={T_max:.2f} kN su {T_max_name}"
        ),
        value=T_max, unit="kN",
        norm_ref="Distribuzione lineare (piastra rigida) — EN 1992-4 §6.2.2",
    ))
    out.primary_value = T_max
    return out


# ---------------------------------------------------------------------------
# lookup_fatigue_detail — Δσ_C per dettaglio costruttivo
# ---------------------------------------------------------------------------

class LookupFatigueDetailInput(BaseModel):
    nome_dettaglio: str | None = Field(
        None,
        description=(
            "Es. 'flangia_bullonata_M_perpend', 'saldatura_testa_a_testa_classe_B'. "
            "Se None → restituisce tutta la lista."
        ),
    )


class LookupFatigueDetailOutput(CalcResult):
    dettagli: dict = Field(default_factory=dict)


def lookup_fatigue_detail(inp: LookupFatigueDetailInput) -> LookupFatigueDetailOutput:
    out = LookupFatigueDetailOutput(tool="lookup_fatigue_detail", inputs_hash=compute_inputs_hash(inp))
    if inp.nome_dettaglio:
        d = DETTAGLI_TIPICI_PALI_TLC.get(inp.nome_dettaglio)
        if not d:
            out.out_of_scope = True
            out.out_of_scope_reason = (
                f"Dettaglio '{inp.nome_dettaglio}' non in DB. Disponibili: "
                f"{list(DETTAGLI_TIPICI_PALI_TLC)}"
            )
            return out
        out.dettagli = {inp.nome_dettaglio: d}
        val = d["delta_sigma_C"]
    else:
        out.dettagli = DETTAGLI_TIPICI_PALI_TLC
        val = float(len(DETTAGLI_TIPICI_PALI_TLC))
    out.trace.append(TraceStep(
        label="dettaglio fatica",
        formula="lookup(nome_dettaglio) → Δσ_C [MPa]",
        substitution=f"nome={inp.nome_dettaglio} → {len(out.dettagli)} risultato/i",
        value=float(val), unit="MPa o n_records",
        norm_ref="EN 1993-1-9 Tab. 8.1-8.5 + Cellnex CNP_TS21_002",
    ))
    out.primary_value = float(val)
    return out


# ---------------------------------------------------------------------------
# classify_static_scheme + get_rt_template
# ---------------------------------------------------------------------------

_RT_CACHE: dict | None = None


def _load_rt() -> dict:
    global _RT_CACHE
    if _RT_CACHE is None:
        _RT_CACHE = json.loads(RT_PATH.read_text())
    return _RT_CACHE


class ClassifyStaticSchemeInput(BaseModel):
    vincoli: list[str] = Field(
        ..., min_length=1,
        description=(
            "Elenco vincoli rilevati al sopralluogo. Parole chiave: "
            "'torrino','baggioli','stralli','puntoni','telaio','parete','flangia'..."
        ),
    )
    h_struttura_m: float = Field(0.0, description="Altezza struttura per matching template")


class ClassifyStaticSchemeOutput(CalcResult):
    template_proposto: str = ""
    nome_template: str = ""
    confidenza_match: float | None = None
    suggerimento: str = ""
    schema_completo: dict = Field(default_factory=dict)


def classify_static_scheme(inp: ClassifyStaticSchemeInput) -> ClassifyStaticSchemeOutput:
    out = ClassifyStaticSchemeOutput(tool="classify_static_scheme", inputs_hash=compute_inputs_hash(inp))
    db = _load_rt()

    # Scoring per template:
    # - vincoli_tipici (peso 3) → match strutturale forte
    # - nome (peso 2)
    # - descrizione (peso 1) → cautelativo, match debole
    parole_chiave = [v.lower() for v in inp.vincoli]
    scores: dict[str, float] = {}
    for tpl_id, tpl in db.items():
        score = 0.0
        vincoli_tipici_txt = " ".join(tpl["vincoli_tipici"]).lower()
        nome_txt = tpl["nome"].lower()
        descr_txt = tpl["descrizione"].lower()
        for kw_full in parole_chiave:
            # Split parole multiple es. "base flangia" → ["base", "flangia"]
            for kw in kw_full.split():
                if len(kw) < 3:
                    continue
                if kw in vincoli_tipici_txt:
                    score += 3.0
                elif kw in nome_txt:
                    score += 2.0
                elif kw in descr_txt:
                    score += 1.0
        scores[tpl_id] = score

    best = max(scores, key=lambda k: scores[k])
    n_match = scores[best]
    max_possible = len(parole_chiave) * 3.0   # tutti match perfetti su vincoli_tipici
    conf = min(n_match / max_possible, 1.0) if max_possible > 0 else 0.0
    out.template_proposto = best
    out.nome_template = db[best]["nome"]
    out.confidenza_match = conf
    out.schema_completo = db[best]
    if conf < 0.3:
        out.suggerimento = (
            "Confidenza match BASSA. Sopralluogo insufficiente: "
            "richiedere foto+descrizione vincoli prima di procedere."
        )
    elif conf < 0.6:
        out.suggerimento = "Match parziale — verificare sopralluogo per conferma."
    else:
        out.suggerimento = "Match buono. Procedere con verifiche del template."

    out.trace.append(TraceStep(
        label="classificazione schema statico",
        formula="match keyword-based su 5 template RT-A/B/C/D/E",
        substitution=f"vincoli={inp.vincoli} → {best} ({db[best]['nome']}), conf={conf:.2f}",
        value=conf, unit="-",
        norm_ref="K2A vs-template-paline-rt — 5 tipologie standardizzate",
    ))
    out.primary_value = conf
    return out


class GetRtTemplateInput(BaseModel):
    template_id: Literal["RT-A", "RT-B", "RT-C", "RT-D", "RT-E"]


class GetRtTemplateOutput(CalcResult):
    schema_template: dict = Field(default_factory=dict)


def get_rt_template(inp: GetRtTemplateInput) -> GetRtTemplateOutput:
    out = GetRtTemplateOutput(tool="get_rt_template", inputs_hash=compute_inputs_hash(inp))
    db = _load_rt()
    out.schema_template = db.get(inp.template_id, {})
    out.trace.append(TraceStep(
        label="template RT",
        formula="lookup template",
        substitution=f"{inp.template_id} → {out.schema_template.get('nome', '?')}",
        value=1, unit="-",
        norm_ref="K2A vs-template-paline-rt v1.0",
    ))
    return out
