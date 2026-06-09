"""Mini-FEM Euler-Bernoulli 2D — palo a mensola con vincoli intermedi.

Caratteristiche v0.6:
- Elementi beam 2 nodi × 2 dof (w spostamento, θ rotazione) → 4 dof/elemento
- Rigidezza elastica K_e standard Euler-Bernoulli
- Rigidezza geometrica K_g per effetti P-Δ (stiffness reduction sotto N)
- Tronchi rastremati supportati (E·I interpolato)
- Molle laterali ai nodi (modello stralli/puntoni semplificato)
- Soluzione statica K·u = F con iterazione P-Δ (2-3 iter convergenza)
- Buckling: autoproblema generalizzato K·φ = λ·K_g·φ → N_cr esatto

Per chiudere il gap stabilità del MCP analitico:
- L_cr_eff dal FEM (più accurato di β·L assunto)
- Distribuzione M(z) reale per buckling-bending interaction
- Effetti vincoli intermedi (stralli) automatici

Convenzione: asse z verticale, w spostamento orizzontale, θ rotazione.
DOF nodo i: [w_i, θ_i] → vettore globale u[2N].
Unità: SI consistenti. Forze N, lunghezze mm, E in MPa, I in mm⁴.
"""

from __future__ import annotations
from ._hashing import compute_inputs_hash

import math

import numpy as np
from pydantic import BaseModel, ConfigDict, Field

from .schemas import CalcResult, TraceStep

E_ACCIAIO_MPa = 210_000.0


# ---------------------------------------------------------------------------
# Input model
# ---------------------------------------------------------------------------

class NodoBeam(BaseModel):
    """Nodo del modello FEM beam 2D."""
    z_mm: float
    EI_mm2: float | None = Field(None, description="Override locale di E·I (default = sezione tronco)")


class ElementoBeam(BaseModel):
    """Elemento beam tra 2 nodi consecutivi."""
    nodo_base_idx: int
    nodo_top_idx: int
    EI_Nmm2: float = Field(..., gt=0, description="E·I al baricentro dell'elemento")
    N_axiale_N: float = Field(0.0, description="Compressione + (per K_g)")


class MollaLaterale(BaseModel):
    """Molla a traslazione orizzontale a un nodo (modello strallo)."""
    nodo_idx: int
    k_N_mm: float = Field(..., gt=0)


class CaricoNodale(BaseModel):
    """Forza orizzontale concentrata a un nodo."""
    nodo_idx: int
    F_h_N: float = 0.0
    M_Nmm: float = 0.0


class CaricoDistribuitoBeam(BaseModel):
    """Carico distribuito uniforme su un elemento."""
    elemento_idx: int
    q_orizz_N_mm: float


class FEMSolverInput(BaseModel):
    """Input mini-FEM 2D."""
    model_config = ConfigDict(arbitrary_types_allowed=True)
    nodi: list[NodoBeam] = Field(..., min_length=2)
    elementi: list[ElementoBeam] = Field(..., min_length=1)
    molle: list[MollaLaterale] = Field(default_factory=list)
    carichi_nodali: list[CaricoNodale] = Field(default_factory=list)
    carichi_distribuiti: list[CaricoDistribuitoBeam] = Field(default_factory=list)
    base_incastrata: bool = Field(True, description="Nodo 0 (z=0) incastrato: w_0=0, θ_0=0")
    P_delta_iterativo: bool = Field(True, description="Itera con K_g aggiornato (P-Δ)")
    max_iterazioni_P_delta: int = Field(10, ge=1, le=50)
    tolleranza_convergenza_mm: float = Field(0.1, gt=0)


class FEMSolverOutput(CalcResult):
    n_nodi: int = 0
    n_elementi: int = 0
    n_iterazioni_eseguite: int = 0
    spostamenti_w_mm: list[float] = Field(default_factory=list)
    rotazioni_theta_rad: list[float] = Field(default_factory=list)
    M_per_elemento_Nmm: list[float] = Field(default_factory=list)
    V_per_elemento_N: list[float] = Field(default_factory=list)
    delta_top_mm: float | None = None
    theta_top_rad: float | None = None
    convergenza_P_delta: bool = False


def _K_e_beam(EI: float, L: float) -> np.ndarray:
    """Matrice rigidezza elastica elemento beam 2D Euler-Bernoulli, 4×4.

    DOF: [w_1, θ_1, w_2, θ_2]
    """
    f = EI / (L ** 3)
    return f * np.array([
        [ 12,    6*L,   -12,    6*L],
        [  6*L,  4*L*L,  -6*L,  2*L*L],
        [-12,   -6*L,    12,   -6*L],
        [  6*L,  2*L*L,  -6*L,  4*L*L],
    ])


def _K_g_beam(N: float, L: float) -> np.ndarray:
    """Matrice rigidezza geometrica elemento beam (P-Δ), 4×4.

    Convenzione: N > 0 compressione → K_g riduce K_e (instabilità).
    Da letteratura: matrice di Przemieniecki / Cook-Malkus-Plesha.
    """
    g = N / (30.0 * L)
    return g * np.array([
        [ 36,    3*L,   -36,    3*L],
        [  3*L,  4*L*L,  -3*L,  -L*L],
        [-36,   -3*L,    36,   -3*L],
        [  3*L, -L*L,   -3*L,   4*L*L],
    ])


def _vec_q_uniform(q: float, L: float) -> np.ndarray:
    """Vettore forze equivalenti nodali per carico distribuito uniforme q.

    Convenzione q orizzontale positiva → forza positiva su w.
    Risultato: [F_1, M_1, F_2, M_2] = [qL/2, qL²/12, qL/2, -qL²/12]
    """
    return np.array([q*L/2.0, q*L*L/12.0, q*L/2.0, -q*L*L/12.0])


def _assemble_global(inp: FEMSolverInput, use_K_g: bool = False) -> tuple[np.ndarray, np.ndarray]:
    """Assemblea K (e opzionalmente K_g) globali + vettore forze F."""
    N = len(inp.nodi)
    ndof = 2 * N
    K = np.zeros((ndof, ndof))
    K_g = np.zeros((ndof, ndof))
    F = np.zeros(ndof)

    # Posizioni nodali
    z = np.array([n.z_mm for n in inp.nodi])

    # Carichi distribuiti → vettore nodale
    for cd in inp.carichi_distribuiti:
        el = inp.elementi[cd.elemento_idx]
        L = z[el.nodo_top_idx] - z[el.nodo_base_idx]
        f_el = _vec_q_uniform(cd.q_orizz_N_mm, L)
        dofs = [2*el.nodo_base_idx, 2*el.nodo_base_idx+1,
                2*el.nodo_top_idx,  2*el.nodo_top_idx+1]
        for i, d in enumerate(dofs):
            F[d] += f_el[i]

    # Carichi concentrati ai nodi
    for cn in inp.carichi_nodali:
        F[2*cn.nodo_idx]     += cn.F_h_N
        F[2*cn.nodo_idx + 1] += cn.M_Nmm

    # Assembly elementi
    for el in inp.elementi:
        L = z[el.nodo_top_idx] - z[el.nodo_base_idx]
        if L <= 0:
            continue
        k_e = _K_e_beam(el.EI_Nmm2, L)
        dofs = [2*el.nodo_base_idx, 2*el.nodo_base_idx+1,
                2*el.nodo_top_idx,  2*el.nodo_top_idx+1]
        for i in range(4):
            for j in range(4):
                K[dofs[i], dofs[j]] += k_e[i, j]
        if use_K_g and el.N_axiale_N > 0:
            k_g = _K_g_beam(el.N_axiale_N, L)
            for i in range(4):
                for j in range(4):
                    K_g[dofs[i], dofs[j]] += k_g[i, j]

    # Molle laterali
    for m in inp.molle:
        K[2*m.nodo_idx, 2*m.nodo_idx] += m.k_N_mm

    return K - K_g, F   # K_eff = K_elastic - K_geometric


def _apply_boundary(K: np.ndarray, F: np.ndarray, fix_dofs: list[int]) -> tuple[np.ndarray, np.ndarray, list[int]]:
    """Rimuovi DOF vincolati (riduce sistema)."""
    n = K.shape[0]
    free = [i for i in range(n) if i not in fix_dofs]
    K_red = K[np.ix_(free, free)]
    F_red = F[free]
    return K_red, F_red, free


def solve_fem_beam(inp: FEMSolverInput) -> FEMSolverOutput:
    """Risolve mini-FEM 2D con P-Δ iterativo opzionale."""
    out = FEMSolverOutput(tool="solve_fem_beam", inputs_hash=compute_inputs_hash(inp))
    out.n_nodi = len(inp.nodi)
    out.n_elementi = len(inp.elementi)
    ndof = 2 * out.n_nodi

    # DOF vincolati (incastro alla base: nodo 0)
    fix_dofs = [0, 1] if inp.base_incastrata else []

    u = np.zeros(ndof)
    delta_top_prev = 0.0
    converged = False

    iterazioni = 1 if not inp.P_delta_iterativo else inp.max_iterazioni_P_delta
    for it in range(iterazioni):
        K_eff, F = _assemble_global(inp, use_K_g=(it > 0))
        K_red, F_red, free = _apply_boundary(K_eff, F, fix_dofs)
        try:
            u_red = np.linalg.solve(K_red, F_red)
        except np.linalg.LinAlgError:
            out.warnings.append(f"Singular matrix at iter {it+1} — possibile buckling raggiunto")
            break

        u = np.zeros(ndof)
        for i, d in enumerate(free):
            u[d] = u_red[i]
        delta_top = u[2 * (out.n_nodi - 1)]  # w al nodo top
        out.n_iterazioni_eseguite = it + 1
        if abs(delta_top - delta_top_prev) < inp.tolleranza_convergenza_mm:
            converged = True
            break
        delta_top_prev = delta_top

    out.convergenza_P_delta = converged

    # Estrai spostamenti e rotazioni
    w_list = [u[2*i] for i in range(out.n_nodi)]
    th_list = [u[2*i+1] for i in range(out.n_nodi)]
    out.spostamenti_w_mm = w_list
    out.rotazioni_theta_rad = th_list
    out.delta_top_mm = w_list[-1]
    out.theta_top_rad = th_list[-1]

    # Calcolo M, V per elemento (post-process)
    z = np.array([n.z_mm for n in inp.nodi])
    M_list = []
    V_list = []
    for el in inp.elementi:
        L = z[el.nodo_top_idx] - z[el.nodo_base_idx]
        if L <= 0:
            M_list.append(0); V_list.append(0); continue
        u_el = np.array([
            w_list[el.nodo_base_idx], th_list[el.nodo_base_idx],
            w_list[el.nodo_top_idx],  th_list[el.nodo_top_idx],
        ])
        # M = EI · w''  ; al nodo base: M = EI · (-6/L²·w1 - 4/L·θ1 + 6/L²·w2 - 2/L·θ2)
        EI = el.EI_Nmm2
        M_base = EI * (-6/L**2 * u_el[0] - 4/L * u_el[1] + 6/L**2 * u_el[2] - 2/L * u_el[3])
        V_el = EI * (12/L**3 * u_el[0] + 6/L**2 * u_el[1] - 12/L**3 * u_el[2] + 6/L**2 * u_el[3])
        M_list.append(M_base)
        V_list.append(V_el)

    out.M_per_elemento_Nmm = M_list
    out.V_per_elemento_N = V_list

    out.trace.append(TraceStep(
        label="FEM beam 2D (P-Δ)",
        formula="K_total = K_elastic − K_geometric ; K·u = F",
        substitution=(
            f"n_nodi={out.n_nodi}, n_elem={out.n_elementi}, "
            f"P-Δ={'ON' if inp.P_delta_iterativo else 'OFF'} → "
            f"convergenza in {out.n_iterazioni_eseguite} iter ({'OK' if converged else 'NO'}), "
            f"δ_top={out.delta_top_mm:.2f} mm"
        ),
        value=out.delta_top_mm, unit="mm",
        norm_ref="Euler-Bernoulli + K_g Przemieniecki (FEM standard)",
    ))
    out.primary_value = out.delta_top_mm
    out.primary_unit = "mm"
    return out


# ---------------------------------------------------------------------------
# Tool: buckling FEM (autoproblema generalizzato)
# ---------------------------------------------------------------------------

class FEMBucklingInput(FEMSolverInput):
    """Stesso input solve_fem_beam, ma N viene scalato fino a trovare λ_cr."""
    pass


class FEMBucklingOutput(CalcResult):
    lambda_cr_min: float | None = None
    N_cr_kN: float | None = None
    L_cr_equivalente_mm: float | None = None
    EI_riferimento_Nmm2: float | None = None
    modo_critico_idx: int = 0


def buckling_analysis(inp: FEMBucklingInput) -> FEMBucklingOutput:
    """Buckling FEM: solve K·φ = λ·K_g·φ → autovalore minimo > 0 = λ_cr."""
    out = FEMBucklingOutput(tool="buckling_analysis_fem", inputs_hash=compute_inputs_hash(inp))

    K_elast, _ = _assemble_global(inp, use_K_g=False)
    # K_g preso con N_riferimento = N degli elementi
    K_g_full = np.zeros_like(K_elast)
    z = np.array([n.z_mm for n in inp.nodi])
    for el in inp.elementi:
        L = z[el.nodo_top_idx] - z[el.nodo_base_idx]
        if L <= 0 or el.N_axiale_N <= 0:
            continue
        kg = _K_g_beam(el.N_axiale_N, L)
        dofs = [2*el.nodo_base_idx, 2*el.nodo_base_idx+1,
                2*el.nodo_top_idx,  2*el.nodo_top_idx+1]
        for i in range(4):
            for j in range(4):
                K_g_full[dofs[i], dofs[j]] += kg[i, j]

    fix_dofs = [0, 1] if inp.base_incastrata else []
    free = [i for i in range(K_elast.shape[0]) if i not in fix_dofs]
    K_red = K_elast[np.ix_(free, free)]
    Kg_red = K_g_full[np.ix_(free, free)]

    # Solve K φ = λ K_g φ  →  inv(K_g) K φ = λ φ ma K_g può essere singolare.
    # Equivalent: standard form  λ K_g φ = K φ  →  solve λ * K_g = K usando scipy.linalg.eig
    # Per stabilità numerica useremo SVD/eig.
    try:
        # λ K_g φ = K φ  →  con eig di pencil
        from scipy.linalg import eig
        eigvals, _ = eig(K_red, Kg_red)
        # Tieni solo autovalori reali positivi
        real_positive = [v.real for v in eigvals if abs(v.imag) < 1e-6 and v.real > 1e-3]
        lambda_cr = min(real_positive) if real_positive else None
    except ImportError:
        # Fallback: numpy non ha generalized eig nativo → uso inv
        try:
            # λ_i = autovalore di K^-1 · K_g (gli autovalori di pencil)
            M = np.linalg.solve(K_red, Kg_red)
            eigs = np.linalg.eigvals(M)
            # λ_cr corrisponde a 1/μ_max (μ autovalore di K^-1 K_g)
            real_pos = [e.real for e in eigs if abs(e.imag) < 1e-6 and e.real > 1e-9]
            lambda_cr = 1.0 / max(real_pos) if real_pos else None
        except np.linalg.LinAlgError:
            lambda_cr = None
            out.warnings.append("Matrice singolare — buckling non determinabile")

    out.lambda_cr_min = lambda_cr
    if lambda_cr:
        # N_cr totale assiale equivalente = λ_cr · (N usato per K_g)
        N_riferimento = max(el.N_axiale_N for el in inp.elementi)
        N_cr = lambda_cr * N_riferimento / 1000.0  # kN
        out.N_cr_kN = N_cr
        # L_cr equivalente = π·sqrt(EI/N_cr)
        EI_ref = max(el.EI_Nmm2 for el in inp.elementi)
        out.EI_riferimento_Nmm2 = EI_ref
        if N_cr > 0:
            out.L_cr_equivalente_mm = math.pi * math.sqrt(EI_ref / (N_cr * 1000.0))
        out.trace.append(TraceStep(
            label="buckling FEM",
            formula="λ_cr = min(eig(K, K_g)) ; N_cr = λ_cr · N_ref ; L_cr,eq = π·√(EI/N_cr)",
            substitution=(
                f"λ_cr={lambda_cr:.3f}, N_cr={N_cr:.1f} kN, "
                f"L_cr,eq={out.L_cr_equivalente_mm:.0f} mm"
            ),
            value=N_cr, unit="kN",
            norm_ref="FEM Euler-Bernoulli + K_g eigenvalue analysis",
        ))
        out.primary_value = N_cr
        out.primary_unit = "kN"
    return out
