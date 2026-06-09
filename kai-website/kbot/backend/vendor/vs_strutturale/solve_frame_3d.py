"""Solver telaio spaziale 3D — metodo della rigidezza diretta (direct stiffness).

Risolve telai 3D elastico-lineari con 6 g.d.l./nodo (3 traslazioni + 3 rotazioni),
elementi trave con rigidezza assiale, torsionale e flessionale biassiale.

Caratteristiche:
- Elemento beam 3D 2 nodi × 6 dof → matrice locale 12×12 (Euler-Bernoulli)
- Trasformazione locale→globale con asse locale x = i→j e roll opzionale
- Vincoli per-nodo per-g.d.l. (incastro / cerniera / appoggio / carrello)
- Svincoli d'estremità d'asta (cerniere) via condensazione statica
- Carichi nodali (Fx..Mz) e distribuiti d'asta (componenti globali) + peso proprio
- Output: spostamenti nodali, REAZIONI ai vincoli, azioni d'estremità N/V/M/T per asta

Caso d'uso primario: porta-antenne TLC (palo + puntoni + telaio di ripartizione +
baggioli) per ottenere le reazioni vincolari reali ai baggioli — indispensabile per
distinguere schema "telaio aperto" da "telaio chiuso" e incastro da cerniera.

Convenzione: assi globali X, Y, Z. Forze N, lunghezze mm, E/G in MPa (=N/mm²),
A in mm², I e J in mm⁴, momenti in N·mm. Reazioni in N e N·mm.
g.d.l. nodo i ordine: [ux, uy, uz, rx, ry, rz] → dof globale 6·i+d.
"""

from __future__ import annotations

import numpy as np
from pydantic import BaseModel, ConfigDict, Field

from ._hashing import compute_inputs_hash
from .schemas import CalcResult, TraceStep

E_ACCIAIO_MPa = 210_000.0
G_ACCIAIO_MPa = 80_769.0
GAMMA_ACCIAIO_N_mm3 = 78.5e-6  # 78.5 kN/m³ = 78.5e-6 N/mm³

_DOF_NAMES = ("ux", "uy", "uz", "rx", "ry", "rz")
_DOF_IDX = {n: i for i, n in enumerate(_DOF_NAMES)}


# ---------------------------------------------------------------------------
# Input models
# ---------------------------------------------------------------------------

class Nodo3D(BaseModel):
    """Nodo del telaio 3D (coordinate in mm)."""
    x_mm: float
    y_mm: float
    z_mm: float
    nome: str = ""


class Asta3D(BaseModel):
    """Elemento trave 3D tra due nodi."""
    nodo_i: int
    nodo_j: int
    E_MPa: float = Field(E_ACCIAIO_MPa, gt=0)
    G_MPa: float = Field(G_ACCIAIO_MPa, gt=0)
    A_mm2: float = Field(..., gt=0)
    Iy_mm4: float = Field(..., gt=0, description="Inerzia flessione attorno asse locale y")
    Iz_mm4: float = Field(..., gt=0, description="Inerzia flessione attorno asse locale z")
    J_mm4: float = Field(..., gt=0, description="Inerzia torsionale")
    roll_deg: float = Field(0.0, description="Rotazione attorno all'asse locale x")
    rilasci_i: list[str] = Field(default_factory=list, description="g.d.l. svincolati al nodo i (es. ['ry','rz'] = cerniera flessionale)")
    rilasci_j: list[str] = Field(default_factory=list, description="g.d.l. svincolati al nodo j")
    nome: str = ""


class Vincolo3D(BaseModel):
    """Vincolo a un nodo: True = g.d.l. bloccato."""
    nodo: int
    ux: bool = False
    uy: bool = False
    uz: bool = False
    rx: bool = False
    ry: bool = False
    rz: bool = False

    @classmethod
    def incastro(cls, nodo: int) -> "Vincolo3D":
        return cls(nodo=nodo, ux=True, uy=True, uz=True, rx=True, ry=True, rz=True)

    @classmethod
    def cerniera(cls, nodo: int) -> "Vincolo3D":
        return cls(nodo=nodo, ux=True, uy=True, uz=True)

    def mask(self) -> list[bool]:
        return [self.ux, self.uy, self.uz, self.rx, self.ry, self.rz]


class CaricoNodale3D(BaseModel):
    """Forze/momenti concentrati a un nodo (N, N·mm)."""
    nodo: int
    Fx_N: float = 0.0
    Fy_N: float = 0.0
    Fz_N: float = 0.0
    Mx_Nmm: float = 0.0
    My_Nmm: float = 0.0
    Mz_Nmm: float = 0.0


class CaricoDistribuito3D(BaseModel):
    """Carico uniforme su un'asta, componenti in assi GLOBALI (N/mm)."""
    asta_idx: int
    wx_N_mm: float = 0.0
    wy_N_mm: float = 0.0
    wz_N_mm: float = 0.0


class Frame3DInput(BaseModel):
    """Input solver telaio 3D."""
    model_config = ConfigDict(arbitrary_types_allowed=True)
    nodi: list[Nodo3D] = Field(..., min_length=2)
    aste: list[Asta3D] = Field(..., min_length=1)
    vincoli: list[Vincolo3D] = Field(..., min_length=1)
    carichi_nodali: list[CaricoNodale3D] = Field(default_factory=list)
    carichi_distribuiti: list[CaricoDistribuito3D] = Field(default_factory=list)
    peso_proprio: bool = Field(False, description="Aggiunge peso proprio acciaio (γ=78.5 kN/m³) come carico distribuito -Z")
    gamma_materiale_N_mm3: float = Field(GAMMA_ACCIAIO_N_mm3, description="Peso specifico per peso proprio")


# ---------------------------------------------------------------------------
# Output model
# ---------------------------------------------------------------------------

class ReazioneNodo(BaseModel):
    nodo: int
    nome: str = ""
    Fx_N: float = 0.0
    Fy_N: float = 0.0
    Fz_N: float = 0.0
    Mx_kNm: float = 0.0
    My_kNm: float = 0.0
    Mz_kNm: float = 0.0


class AzioniAsta(BaseModel):
    asta_idx: int
    nome: str = ""
    N_i_kN: float = 0.0   # + trazione
    Vy_i_kN: float = 0.0
    Vz_i_kN: float = 0.0
    T_i_kNm: float = 0.0
    My_i_kNm: float = 0.0
    Mz_i_kNm: float = 0.0
    N_j_kN: float = 0.0
    Vy_j_kN: float = 0.0
    Vz_j_kN: float = 0.0
    T_j_kNm: float = 0.0
    My_j_kNm: float = 0.0
    Mz_j_kNm: float = 0.0


class SpostamentoNodo(BaseModel):
    nodo: int
    nome: str = ""
    ux_mm: float = 0.0
    uy_mm: float = 0.0
    uz_mm: float = 0.0
    rx_rad: float = 0.0
    ry_rad: float = 0.0
    rz_rad: float = 0.0


class Frame3DOutput(CalcResult):
    n_nodi: int = 0
    n_aste: int = 0
    spostamenti: list[SpostamentoNodo] = Field(default_factory=list)
    reazioni: list[ReazioneNodo] = Field(default_factory=list)
    azioni_aste: list[AzioniAsta] = Field(default_factory=list)
    spostamento_max_mm: float | None = None
    equilibrio_residuo_N: float | None = None
    labile: bool = False


# ---------------------------------------------------------------------------
# Core matrices
# ---------------------------------------------------------------------------

def _k_local(E: float, G: float, A: float, Iy: float, Iz: float, J: float, L: float) -> np.ndarray:
    """Matrice di rigidezza locale 12×12 elemento beam 3D (Euler-Bernoulli).

    Ordine dof: [ux1,uy1,uz1,rx1,ry1,rz1, ux2,uy2,uz2,rx2,ry2,rz2]
    Flessione x-y (uy, rz) usa Iz ; flessione x-z (uz, ry) usa Iy.
    """
    k = np.zeros((12, 12))
    EA_L = E * A / L
    GJ_L = G * J / L
    # assiale
    k[0, 0] = k[6, 6] = EA_L
    k[0, 6] = k[6, 0] = -EA_L
    # torsione
    k[3, 3] = k[9, 9] = GJ_L
    k[3, 9] = k[9, 3] = -GJ_L
    # flessione nel piano x-y (Iz): dof uy=1,7 ; rz=5,11
    az = E * Iz
    k[1, 1] = k[7, 7] = 12 * az / L**3
    k[1, 7] = k[7, 1] = -12 * az / L**3
    k[1, 5] = k[5, 1] = k[1, 11] = k[11, 1] = 6 * az / L**2
    k[7, 5] = k[5, 7] = k[7, 11] = k[11, 7] = -6 * az / L**2
    k[5, 5] = k[11, 11] = 4 * az / L
    k[5, 11] = k[11, 5] = 2 * az / L
    # flessione nel piano x-z (Iy): dof uz=2,8 ; ry=4,10
    ay = E * Iy
    k[2, 2] = k[8, 8] = 12 * ay / L**3
    k[2, 8] = k[8, 2] = -12 * ay / L**3
    k[2, 4] = k[4, 2] = k[2, 10] = k[10, 2] = -6 * ay / L**2
    k[8, 4] = k[4, 8] = k[8, 10] = k[10, 8] = 6 * ay / L**2
    k[4, 4] = k[10, 10] = 4 * ay / L
    k[4, 10] = k[10, 4] = 2 * ay / L
    return k


def _rotation_3x3(xi: np.ndarray, xj: np.ndarray, roll_deg: float) -> np.ndarray:
    """Matrice 3×3 dei coseni direttori (trasforma globale→locale).

    Righe = assi locali (ex, ey, ez) espressi in coordinate globali.
    """
    dx = xj - xi
    L = np.linalg.norm(dx)
    ex = dx / L
    # asse di riferimento: globale Z, salvo asta (quasi) verticale → globale X
    if abs(ex[2]) > 0.9999:
        ref = np.array([1.0, 0.0, 0.0])
    else:
        ref = np.array([0.0, 0.0, 1.0])
    ey = np.cross(ref, ex)
    ey /= np.linalg.norm(ey)
    ez = np.cross(ex, ey)
    # roll attorno a ex
    if abs(roll_deg) > 1e-9:
        c, s = np.cos(np.radians(roll_deg)), np.sin(np.radians(roll_deg))
        ey2 = c * ey + s * ez
        ez2 = -s * ey + c * ez
        ey, ez = ey2, ez2
    return np.vstack([ex, ey, ez])


def _T_12(R3: np.ndarray) -> np.ndarray:
    """Matrice di trasformazione 12×12 (blocco-diagonale di R3)."""
    T = np.zeros((12, 12))
    for b in range(4):
        T[3*b:3*b+3, 3*b:3*b+3] = R3
    return T


def _fixed_end_local(w_local: np.ndarray, L: float) -> np.ndarray:
    """Forze di incastro perfetto (local) per carico uniforme in assi locali.

    w_local = [wx, wy, wz] (N/mm) in assi locali. Ritorna vettore 12 (local).
    Segno: forze equivalenti nodali = carico equivalente applicato ai nodi.
    """
    wx, wy, wz = w_local
    f = np.zeros(12)
    # assiale
    f[0] = f[6] = wx * L / 2.0
    # piano x-y (wy → uy, rz)
    f[1] = f[7] = wy * L / 2.0
    f[5] = wy * L**2 / 12.0
    f[11] = -wy * L**2 / 12.0
    # piano x-z (wz → uz, ry) — segni coerenti con blocco Iy
    f[2] = f[8] = wz * L / 2.0
    f[4] = -wz * L**2 / 12.0
    f[10] = wz * L**2 / 12.0
    return f


def _release_dofs(asta: Asta3D) -> list[int]:
    out = []
    for n in asta.rilasci_i:
        if n in _DOF_IDX:
            out.append(_DOF_IDX[n])
    for n in asta.rilasci_j:
        if n in _DOF_IDX:
            out.append(_DOF_IDX[n] + 6)
    return sorted(set(out))


def _condense_releases(k: np.ndarray, fe: np.ndarray, rel: list[int]) -> tuple[np.ndarray, np.ndarray]:
    """Condensazione statica dei g.d.l. svincolati (cerniere)."""
    if not rel:
        return k, fe
    keep = [i for i in range(12) if i not in rel]
    krr = k[np.ix_(rel, rel)]
    krc = k[np.ix_(rel, keep)]
    kcr = k[np.ix_(keep, rel)]
    kcc = k[np.ix_(keep, keep)]
    try:
        krr_inv = np.linalg.inv(krr)
    except np.linalg.LinAlgError:
        return k, fe  # non condensabile → lascia (warning gestito a monte)
    kcc_star = kcc - kcr @ krr_inv @ krc
    fe_c = fe[keep] - kcr @ krr_inv @ fe[rel]
    k_star = np.zeros((12, 12))
    fe_star = np.zeros(12)
    for a, ia in enumerate(keep):
        fe_star[ia] = fe_c[a]
        for b, ib in enumerate(keep):
            k_star[ia, ib] = kcc_star[a, b]
    return k_star, fe_star


# ---------------------------------------------------------------------------
# Solver
# ---------------------------------------------------------------------------

def solve_frame_3d(inp: Frame3DInput) -> Frame3DOutput:
    out = Frame3DOutput(tool="solve_frame_3d", inputs_hash=compute_inputs_hash(inp))
    N = len(inp.nodi)
    ndof = 6 * N
    out.n_nodi = N
    out.n_aste = len(inp.aste)

    coords = np.array([[n.x_mm, n.y_mm, n.z_mm] for n in inp.nodi])
    K = np.zeros((ndof, ndof))
    F = np.zeros(ndof)

    # cache per recupero azioni d'estremità
    el_cache = []

    for el in inp.aste:
        xi, xj = coords[el.nodo_i], coords[el.nodo_j]
        L = float(np.linalg.norm(xj - xi))
        if L <= 0:
            out.warnings.append(f"Asta {el.nome or '?'} lunghezza nulla — saltata")
            el_cache.append(None)
            continue
        kl = _k_local(el.E_MPa, el.G_MPa, el.A_mm2, el.Iy_mm4, el.Iz_mm4, el.J_mm4, L)
        R3 = _rotation_3x3(xi, xj, el.roll_deg)
        T = _T_12(R3)

        # carico distribuito d'asta (globale → locale)
        fe_local = np.zeros(12)
        w_glob = np.zeros(3)
        for cd in inp.carichi_distribuiti:
            if cd.asta_idx == inp.aste.index(el):
                w_glob += np.array([cd.wx_N_mm, cd.wy_N_mm, cd.wz_N_mm])
        if inp.peso_proprio:
            w_glob[2] += -inp.gamma_materiale_N_mm3 * el.A_mm2
        if np.any(w_glob):
            w_local = R3 @ w_glob
            fe_local = _fixed_end_local(w_local, L)

        rel = _release_dofs(el)
        kl_c, fe_c = _condense_releases(kl, fe_local, rel)

        kg = T.T @ kl_c @ T
        fe_glob = T.T @ fe_c

        dofs = list(range(6*el.nodo_i, 6*el.nodo_i+6)) + list(range(6*el.nodo_j, 6*el.nodo_j+6))
        for a in range(12):
            F[dofs[a]] += fe_glob[a]
            for b in range(12):
                K[dofs[a], dofs[b]] += kg[a, b]
        el_cache.append((kl_c, fe_c, T, dofs, L))

    # carichi nodali
    for cn in inp.carichi_nodali:
        base = 6 * cn.nodo
        F[base+0] += cn.Fx_N
        F[base+1] += cn.Fy_N
        F[base+2] += cn.Fz_N
        F[base+3] += cn.Mx_Nmm
        F[base+4] += cn.My_Nmm
        F[base+5] += cn.Mz_Nmm

    # vincoli
    fixed = []
    for v in inp.vincoli:
        for d, locked in enumerate(v.mask()):
            if locked:
                fixed.append(6*v.nodo + d)
    fixed = sorted(set(fixed))
    free = [i for i in range(ndof) if i not in fixed]

    u = np.zeros(ndof)
    Kff = K[np.ix_(free, free)]
    Ff = F[free]
    try:
        uf = np.linalg.solve(Kff, Ff)
    except np.linalg.LinAlgError:
        out.labile = True
        out.warnings.append("Matrice di rigidezza singolare: struttura labile o vincoli insufficienti")
        return out
    # check condizionamento
    if np.linalg.cond(Kff) > 1e12:
        out.warnings.append("Matrice mal condizionata (cond>1e12): possibile quasi-labilità")
    for i, d in enumerate(free):
        u[d] = uf[i]

    # reazioni: R = K·u − F (sui dof vincolati)
    R = K @ u - F

    # output spostamenti
    umax = 0.0
    for i, nd in enumerate(inp.nodi):
        s = SpostamentoNodo(
            nodo=i, nome=nd.nome,
            ux_mm=u[6*i+0], uy_mm=u[6*i+1], uz_mm=u[6*i+2],
            rx_rad=u[6*i+3], ry_rad=u[6*i+4], rz_rad=u[6*i+5],
        )
        out.spostamenti.append(s)
        umax = max(umax, abs(s.ux_mm), abs(s.uy_mm), abs(s.uz_mm))
    out.spostamento_max_mm = umax

    # reazioni ai nodi vincolati
    nodi_vincolati = sorted({v.nodo for v in inp.vincoli})
    for nv in nodi_vincolati:
        b = 6 * nv
        out.reazioni.append(ReazioneNodo(
            nodo=nv, nome=inp.nodi[nv].nome,
            Fx_N=R[b+0], Fy_N=R[b+1], Fz_N=R[b+2],
            Mx_kNm=R[b+3]/1e6, My_kNm=R[b+4]/1e6, Mz_kNm=R[b+5]/1e6,
        ))

    # azioni d'estremità per asta (in assi locali): f_loc = k_loc·(T·u_el) − fe_loc
    for idx, el in enumerate(inp.aste):
        cache = el_cache[idx]
        if cache is None:
            out.azioni_aste.append(AzioniAsta(asta_idx=idx, nome=el.nome))
            continue
        kl_c, fe_c, T, dofs, L = cache
        u_el = np.array([u[d] for d in dofs])
        f_loc = kl_c @ (T @ u_el) - fe_c
        out.azioni_aste.append(AzioniAsta(
            asta_idx=idx, nome=el.nome,
            N_i_kN=-f_loc[0]/1e3, Vy_i_kN=f_loc[1]/1e3, Vz_i_kN=f_loc[2]/1e3,
            T_i_kNm=f_loc[3]/1e6, My_i_kNm=f_loc[4]/1e6, Mz_i_kNm=f_loc[5]/1e6,
            N_j_kN=f_loc[6]/1e3, Vy_j_kN=f_loc[7]/1e3, Vz_j_kN=f_loc[8]/1e3,
            T_j_kNm=f_loc[9]/1e6, My_j_kNm=f_loc[10]/1e6, Mz_j_kNm=f_loc[11]/1e6,
        ))

    # equilibrio globale: somma reazioni + carichi applicati ≈ 0
    res = 0.0
    for k_ax in range(3):
        somma = sum(R[6*nv+k_ax] for nv in nodi_vincolati) + sum(F[6*i+k_ax] for i in range(N))
        res = max(res, abs(somma))
    out.equilibrio_residuo_N = res
    if res > 1.0:
        out.warnings.append(f"Residuo di equilibrio {res:.3f} N > 1 N — verificare modello")

    n_rilasci = sum(len(_release_dofs(a)) for a in inp.aste)

    out.trace.append(TraceStep(
        label="analisi statica lineare",
        formula="K·u = F (metodo della rigidezza diretta, beam Euler-Bernoulli 3D, 6 dof/nodo)",
        substitution=(
            f"n_nodi={N}, n_aste={out.n_aste}, n_DOF={6*N}, dof liberi={len(free)} → "
            f"u_max={umax:.2f} mm"
        ),
        value=umax, unit="mm",
        norm_ref="NTC §4.2.3 / EN 1993-1-1 §5.2.1 — analisi globale elastica",
    ))
    out.trace.append(TraceStep(
        label="matrice di rigidezza elemento + svincoli",
        formula="k_glob = Tᵀ·k_loc·T ; condensazione statica dei g.d.l. svincolati (cerniere)",
        substitution=(
            f"n_aste={out.n_aste}, g.d.l. svincolati totali={n_rilasci} "
            f"({'con cerniere' if n_rilasci else 'tutti continui'})"
        ),
        value=float(n_rilasci), unit="-",
        norm_ref="EN 1993-1-1 §5.4.1 (matrice elemento) / §5.1.2 (svincoli)",
    ))
    out.trace.append(TraceStep(
        label="equilibrio globale",
        formula="R = K·u − F ; Σ(reazioni) + Σ(carichi) ≈ 0",
        substitution=(
            f"residuo max = {res:.2e} N (tolleranza 1 N) → "
            f"{'OK' if res < 1.0 else 'VERIFICARE'} ; labile={out.labile}"
        ),
        value=res, unit="N",
        norm_ref="NTC §4.2.1 / EN 1990 §6.1 — equilibrio",
    ))
    out.primary_value = umax
    out.primary_unit = "mm"
    return out
