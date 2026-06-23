"""Grafici integrativi del Layer 4 (Tappa 3) — riusabili per ogni tipologia.

Genera PNG dai risultati deterministici del Layer 3 (ExecutionResult): i grafici sono
**condizionali ai dati disponibili** (es. la curva Icc solo se c'è una cabina/trafo,
la selettività solo se in pipeline) → graceful per tutte le tipologie.

matplotlib è dipendenza OPZIONALE ([grafici]): se assente, `genera_grafici` ritorna []
senza errori (il documento si genera comunque, senza la sezione grafici).
"""
from __future__ import annotations

from pathlib import Path

from . import typography as ty


def _matplotlib():
    try:
        import matplotlib
        matplotlib.use("Agg")
        import matplotlib.pyplot as plt
        return plt
    except Exception:  # noqa: BLE001 — dipendenza opzionale assente
        return None


def _g_caduta(plt, linee: list, dest: Path) -> Path | None:
    dati = [(l.linea_id, (l.caduta_tensione or {}).get("delta_V_percento"))
            for l in linee if (l.caduta_tensione or {}).get("delta_V_percento") is not None]
    if not dati:
        return None
    fig, ax = plt.subplots(figsize=(6.0, 3.0))
    nomi = [d[0] for d in dati]
    val = [float(d[1]) for d in dati]
    col = ["#1E7A32" if v <= 4 else "#C00000" for v in val]
    ax.bar(nomi, val, color=col)
    ax.axhline(4, ls="--", color="#555", lw=1)
    ax.text(len(val) - 0.5, 4.1, "limite 4% (CEI 64-8 §525)", fontsize=7, color="#555", ha="right")
    ax.set_ylabel("Caduta di tensione ΔV [%]")
    ax.set_title("Caduta di tensione per linea", fontsize=10)
    for i, v in enumerate(val):
        ax.text(i, v + 0.05, f"{ty._fmt(v, 1)}%", ha="center", fontsize=8)
    fig.tight_layout()
    p = dest / "g_caduta.png"
    fig.savefig(p, dpi=150); plt.close(fig)
    return p


def _g_icc(plt, icc_calcs: list, dest: Path) -> Path | None:
    serie = {}
    for c in icc_calcs:
        for k in ("Icc_MT_kA", "Icc_BT_kA", "Ik3max_kA", "Ik3min_kA"):
            if k in c and c[k] is not None and k not in serie:
                serie[k] = float(c[k])
    if not serie:
        return None
    etich = {"Icc_MT_kA": "Icc MT", "Icc_BT_kA": "Icc BT", "Ik3max_kA": "Ik3max", "Ik3min_kA": "Ik3min"}
    fig, ax = plt.subplots(figsize=(6.0, 3.0))
    nomi = [etich[k] for k in serie]
    val = list(serie.values())
    ax.bar(nomi, val, color="#2A6FB0")
    ax.set_ylabel("Corrente di cortocircuito [kA]")
    ax.set_title("Correnti di cortocircuito (IEC 60909)", fontsize=10)
    for i, v in enumerate(val):
        ax.text(i, v + max(val) * 0.01, ty._fmt(v, 2), ha="center", fontsize=8)
    fig.tight_layout()
    p = dest / "g_icc.png"
    fig.savefig(p, dpi=150); plt.close(fig)
    return p


def _g_selettivita(plt, sel: dict | None, dest: Path) -> Path | None:
    if not sel:
        return None
    coppie = sel.get("coppie_analizzate", [])
    livelli, tempi = [], []
    for cp in coppie:
        if cp.get("upstream") not in livelli:
            livelli.append(cp.get("upstream"))
    # ricostruisce i tempi dai delta non è affidabile: usa la lista catena se presente
    cat = sel.get("catena") or sel.get("livelli")
    if isinstance(cat, list) and cat and isinstance(cat[0], dict):
        livelli = [c.get("nome", f"L{i}") for i, c in enumerate(cat)]
        tempi = [c.get("t_intervento_s") for c in cat]
    if not tempi or any(t is None for t in tempi):
        return None
    fig, ax = plt.subplots(figsize=(6.0, 3.2))
    y = range(len(livelli))
    ax.barh(list(y), tempi, color="#2A6FB0")
    ax.set_yticks(list(y)); ax.set_yticklabels(livelli, fontsize=8); ax.invert_yaxis()
    ax.set_xlabel("Tempo di intervento [s]")
    ax.set_title("Selettività verticale della catena", fontsize=10)
    fig.tight_layout()
    p = dest / "g_selettivita.png"
    fig.savefig(p, dpi=150); plt.close(fig)
    return p


def _g_esito(plt, ex, dest: Path) -> Path | None:
    val = [ex.n_step_ok, ex.n_step_divergent, ex.n_step_failed, ex.n_step_skipped]
    nomi = ["OK", "divergenti", "falliti", "skip"]
    col = ["#1E7A32", "#C87A00", "#C00000", "#999999"]
    fig, ax = plt.subplots(figsize=(5.0, 2.6))
    ax.bar(nomi, val, color=col)
    ax.set_title("Esito esecuzione verifiche (Layer 3)", fontsize=10)
    for i, v in enumerate(val):
        ax.text(i, v + 0.1, str(v), ha="center", fontsize=9, fontweight="bold")
    fig.tight_layout()
    p = dest / "g_esito.png"
    fig.savefig(p, dpi=150); plt.close(fig)
    return p


def genera_grafici(ex, dest_dir: Path) -> list[tuple[str, Path]]:
    """Ritorna [(didascalia, png_path)] dei grafici disponibili per questo caso.
    Lista vuota se matplotlib non è installato (graceful)."""
    plt = _matplotlib()
    if plt is None:
        return []
    dest_dir.mkdir(parents=True, exist_ok=True)
    d = ex.dimensioni
    out: list[tuple[str, Path]] = []
    for cap, p in [
        ("Esito delle verifiche eseguite (Layer 3)", _g_esito(plt, ex, dest_dir)),
        ("Correnti di cortocircuito", _g_icc(plt, d.icc_calculations, dest_dir)),
        ("Caduta di tensione per linea", _g_caduta(plt, d.dimensionamento_linee, dest_dir)),
        ("Selettività della catena di protezione", _g_selettivita(plt, d.selettivita, dest_dir)),
    ]:
        if p is not None:
            out.append((cap, p))
    return out
