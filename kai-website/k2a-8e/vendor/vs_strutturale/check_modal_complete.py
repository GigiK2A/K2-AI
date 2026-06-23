"""Analisi modale multimodale completa — modi superiori fino a mass participation ≥ target.

Estende `modal_analysis` (W3, solo modo 1) con un eigensolver FE stick-model
(Euler-Bernoulli, matrice di massa consistente):

    K φ = ω² M φ

Elemento trave 2 nodi, 4 DOF (w, θ per nodo). Mensola incastrata alla base (DOF base rimossi).
Masse concentrate sommate ai DOF traslazionali. Massa partecipante per modo:
    Γ_k = (φ_kᵀ M r)² / (φ_kᵀ M φ_k)   con r = vettore di trascinamento (1 sui DOF traslazionali)
    partecipazione_k = Γ_k / M_tot,trasl

Restituisce i modi finché la massa partecipante cumulata raggiunge target (default 90%).

NB: modello a sezione tubolare a parete sottile (A=π·D·t, I=π·(D/2)³·t), tronchi conici
discretizzati. Per il modo 1 coincide con `modal_analysis` (Rayleigh) entro la discretizzazione.
"""

from __future__ import annotations

import math

import numpy as np
from pydantic import BaseModel, Field

from ._hashing import compute_inputs_hash
from .modal_analysis import MassaConcentrata, TroncoModale
from .schemas import CalcResult, TraceStep


class CheckModalCompleteInput(BaseModel):
    tronchi: list[TroncoModale] = Field(..., min_length=1)
    masse_concentrate: list[MassaConcentrata] = Field(default_factory=list)
    target_mass_participation: float = Field(0.90, gt=0, le=1.0)
    n_elementi: int = Field(40, ge=4, le=400, description="Elementi FE totali")
    max_modi: int = Field(10, ge=1, le=30)


class ModoResult(BaseModel):
    modo: int
    frequenza_Hz: float
    periodo_s: float
    massa_partecipante_pct: float
    massa_cumulata_pct: float


class CheckModalCompleteOutput(CalcResult):
    modi_list: list[ModoResult] = Field(default_factory=list)
    n_modi_required: int | None = None
    target_reached: bool = False
    massa_totale_kg: float | None = None


def _sec_props(D: float, t_m: float):
    A = math.pi * D * t_m
    I = math.pi * (D / 2.0) ** 3 * t_m
    return A, I


def _D_at(z, tronchi):
    for tr in tronchi:
        if tr.z_base_m <= z <= tr.z_top_m:
            L = tr.z_top_m - tr.z_base_m
            frac = (z - tr.z_base_m) / L if L > 0 else 0.0
            return (tr.D_base_m + frac * (tr.D_top_m - tr.D_base_m),
                    tr.t_mm / 1000.0, tr.E_MPa * 1e6, tr.rho_kg_m3)
    # oltre l'ultimo tronco → estende l'ultimo
    tr = tronchi[-1]
    return tr.D_top_m, tr.t_mm / 1000.0, tr.E_MPa * 1e6, tr.rho_kg_m3


def check_modal_complete(inp: CheckModalCompleteInput) -> CheckModalCompleteOutput:
    out = CheckModalCompleteOutput(tool="check_modal_complete", inputs_hash=compute_inputs_hash(inp))

    H = max(tr.z_top_m for tr in inp.tronchi)
    ne = inp.n_elementi
    nn = ne + 1
    Le = H / ne
    ndof = 2 * nn

    K = np.zeros((ndof, ndof))
    M = np.zeros((ndof, ndof))

    for e in range(ne):
        z0 = e * Le
        zc = z0 + Le / 2.0
        D, t_m, E_Pa, rho = _D_at(zc, inp.tronchi)
        A, I = _sec_props(D, t_m)
        EI = E_Pa * I
        mu = rho * A
        L = Le
        ke = EI / L ** 3 * np.array([
            [12, 6 * L, -12, 6 * L],
            [6 * L, 4 * L * L, -6 * L, 2 * L * L],
            [-12, -6 * L, 12, -6 * L],
            [6 * L, 2 * L * L, -6 * L, 4 * L * L],
        ])
        me = mu * L / 420.0 * np.array([
            [156, 22 * L, 54, -13 * L],
            [22 * L, 4 * L * L, 13 * L, -3 * L * L],
            [54, 13 * L, 156, -22 * L],
            [-13 * L, -3 * L * L, -22 * L, 4 * L * L],
        ])
        idx = [2 * e, 2 * e + 1, 2 * e + 2, 2 * e + 3]
        K[np.ix_(idx, idx)] += ke
        M[np.ix_(idx, idx)] += me

    # masse concentrate sui DOF traslazionali del nodo più vicino
    for mc in inp.masse_concentrate:
        node = int(round(mc.z_m / Le))
        node = min(max(node, 0), nn - 1)
        M[2 * node, 2 * node] += mc.massa_kg

    # vincolo incastro base: rimuovi DOF nodo 0 (w0, θ0)
    free = list(range(2, ndof))
    Kf = K[np.ix_(free, free)]
    Mf = M[np.ix_(free, free)]

    # eigenproblema generalizzato simmetrico K φ = ω² M φ via riduzione di Cholesky:
    # M = L Lᵀ ; A = L⁻¹ K L⁻ᵀ (simmetrica) ; A y = λ y ; φ = L⁻ᵀ y
    Lc = np.linalg.cholesky(Mf)
    Linv = np.linalg.inv(Lc)
    A = Linv @ Kf @ Linv.T
    A = 0.5 * (A + A.T)  # forza simmetria numerica
    eigval, Y = np.linalg.eigh(A)
    eigvec = Linv.T @ Y
    order = np.argsort(eigval)
    eigval = eigval[order]
    eigvec = eigvec[:, order]

    # vettore trascinamento r: 1 sui DOF traslazionali (pari), 0 sui rotazionali (dispari)
    r = np.zeros(len(free))
    for i, dof in enumerate(free):
        if dof % 2 == 0:
            r[i] = 1.0

    M_tot_transl = float(r @ Mf @ r)
    out.massa_totale_kg = M_tot_transl

    modi = []
    cum = 0.0
    n_req = None
    for k in range(min(inp.max_modi, len(eigval))):
        w2 = eigval[k]
        if w2 <= 0:
            continue
        omega = math.sqrt(w2)
        f = omega / (2.0 * math.pi)
        phi = eigvec[:, k]
        mk = float(phi @ Mf @ phi)
        Lk = float(phi @ Mf @ r)
        m_eff = Lk * Lk / mk if mk > 0 else 0.0
        part = m_eff / M_tot_transl * 100.0 if M_tot_transl > 0 else 0.0
        cum += part
        modi.append(ModoResult(modo=k + 1, frequenza_Hz=f, periodo_s=1.0 / f,
                               massa_partecipante_pct=part, massa_cumulata_pct=min(cum, 100.0)))
        if n_req is None and cum >= inp.target_mass_participation * 100.0:
            n_req = k + 1
            break

    out.modi_list = modi
    out.n_modi_required = n_req
    out.target_reached = n_req is not None

    out.trace.append(TraceStep(
        label="modi (FE eigen)",
        formula="K φ = ω² M φ ; f = ω/2π ; partecipazione = (φᵀMr)²/(φᵀMφ)/M_tot",
        substitution="; ".join(
            f"modo {m.modo}: {m.frequenza_Hz:.3f} Hz, {m.massa_partecipante_pct:.1f}% "
            f"(cum {m.massa_cumulata_pct:.1f}%)" for m in modi
        ),
        value=modi[0].frequenza_Hz if modi else 0.0, unit="Hz",
        norm_ref="EN 1998-1 §4.3.3.3 + NTC 2018 §7.3.3.1 (massa partecipante ≥85%)",
    ))

    # Sanity (§12.13)
    if modi and modi[-1].massa_cumulata_pct > 100.0001:
        raise ValueError("Massa partecipante cumulata > 100%: errore numerico.")
    if not out.target_reached:
        out.warnings.append(
            f"Target {inp.target_mass_participation:.0%} non raggiunto in {len(modi)} modi "
            f"(cumulata {cum:.1f}%): aumentare max_modi o verificare massa concentrata vs distribuita."
        )
    if modi and modi[0].massa_partecipante_pct < 50.0:
        out.warnings.append(
            f"Modo 1 partecipa solo {modi[0].massa_partecipante_pct:.1f}%: struttura con modi "
            "superiori significativi (non cantilever regolare)."
        )

    out.primary_value = float(n_req) if n_req else float(len(modi))
    out.primary_unit = "modi"
    return out
