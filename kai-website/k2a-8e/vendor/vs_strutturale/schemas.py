"""Schemi Pydantic per input/output dei tool MCP.

Principio: ogni grandezza fisica ha unità dichiarata esplicita.
Ogni output include traccia normativa per asseverabilità.
"""

from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, Field

from ._meta import get_git_sha


# ---------------------------------------------------------------------------
# Tipi base
# ---------------------------------------------------------------------------

ZonaVento = Literal[1, 2, 3, 4, 5, 6, 7, 8, 9]
CategoriaEsposizione = Literal["I", "II", "III", "IV", "V"]
ClasseRugosita = Literal["A", "B", "C", "D"]


class TraceStep(BaseModel):
    """Un passaggio di calcolo tracciato: formula simbolica + valori sostituiti."""

    label: str = Field(..., description="Etichetta breve (es. 'v_b,0')")
    formula: str = Field(..., description="Formula simbolica (es. 'v_b = v_b,0 · c_a')")
    substitution: str = Field(..., description="Valori sostituiti (es. 'v_b = 27 · 1.0')")
    value: float
    unit: str
    norm_ref: str = Field(..., description="Riferimento normativo (es. 'NTC 2018 §3.3.2')")
    notes: str = ""


class CalcResult(BaseModel):
    """Risultato standard di un tool MCP: valore + traccia completa.

    Include audit trail: tool, hash input, versione MCP e (se disponibile) git_sha.
    Ogni numero in una relazione DEVE essere accompagnato da tool#hash, così che
    sia riproducibile esattamente.
    """

    tool: str
    inputs_hash: str = Field(..., description="SHA256(JSON canonical inputs) — primi 16 hex")
    mcp_version: str = "0.1.0"
    git_sha: str | None = Field(
        default_factory=get_git_sha,
        description="SHA breve del commit che ha generato il risultato (audit trail L6). None fuori da git.",
    )
    out_of_scope: bool = False
    out_of_scope_reason: str = ""
    primary_value: float | None = None
    primary_unit: str = ""
    trace: list[TraceStep] = Field(default_factory=list)
    warnings: list[str] = Field(default_factory=list)


# ---------------------------------------------------------------------------
# wind_action — NTC 2018 §3.3
# ---------------------------------------------------------------------------


class WindActionInput(BaseModel):
    """Input azione del vento NTC 2018 §3.3."""

    # Localizzazione
    zona_vento: ZonaVento = Field(..., description="Zona vento NTC §3.3.2 (1-9)")
    altitudine_sito_m: float = Field(..., ge=0, le=3000, description="a_s in m s.l.m.")

    # Geometria
    quota_z_m: float = Field(..., gt=0, description="Quota z dal suolo del punto valutato")
    altezza_struttura_m: float = Field(..., gt=0, description="Altezza totale struttura")

    # Esposizione
    classe_rugosita: ClasseRugosita = Field(..., description="Classe rugosità terreno A/B/C/D")
    distanza_costa_km: float | None = Field(
        None, ge=0, description="Solo per zone 1-8 entro 30 km, isole, ecc."
    )
    coefficiente_topografico: float = Field(
        1.0, ge=1.0, le=1.5, description="c_t — default 1.0 in assenza di rilievi"
    )

    # Periodo di ritorno
    periodo_ritorno_anni: int = Field(50, ge=10, le=1000)


class WindActionOutput(CalcResult):
    """Output azione del vento: q_p(z) e grandezze intermedie."""

    v_b_ref_ms: float | None = None
    v_r_ms: float | None = None
    q_b_Nm2: float | None = None
    c_e_z: float | None = None
    q_p_z_Nm2: float | None = None
    categoria_esposizione: str = ""
