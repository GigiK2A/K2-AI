"""Typography ingegneristica italiana per il Layer 4.

Separatore decimale = virgola, separatore migliaia = punto. Scaling automatico di
unità (A/kA, W/kW/MVA, V/kV). Tutte le funzioni accettano None → "n.d.".
"""
from __future__ import annotations


def _fmt(x: float, decimali: int = 2) -> str:
    """Numero con virgola decimale e punto per le migliaia."""
    s = f"{x:,.{decimali}f}"  # es. '1,234.50'
    return s.replace(",", "§").replace(".", ",").replace("§", ".")


def format_corrente(a: float | None, decimali: int = 1) -> str:
    if a is None:
        return "n.d."
    if abs(a) >= 1000:
        return f"{_fmt(a / 1000.0, max(decimali, 2))} kA"
    return f"{_fmt(a, decimali)} A"


def format_potenza(kw: float | None, decimali: int = 1, unita: str = "kW") -> str:
    """Input in kW (o kVA se unita='kVA'). Scala a MW/MVA sopra 1000. (Compat)."""
    if kw is None:
        return "n.d."
    if abs(kw) >= 1000:
        u = "MVA" if unita == "kVA" else "MW"
        return f"{_fmt(kw / 1000.0, max(decimali, 2))} {u}"
    return f"{_fmt(kw, decimali)} {unita}"


def format_potenza_apparente(kva: float | None) -> str:
    """Potenza apparente (trafo/GE). Input in kVA. <1 kVA→VA, ≥1000 kVA→MVA (2 dec)."""
    if kva is None:
        return "n.d."
    va = kva * 1000.0
    if abs(va) < 1000:
        return f"{_fmt(va, 0)} VA"
    if abs(kva) >= 1000:
        return f"{_fmt(kva / 1000.0, 2)} MVA"
    dec = 0 if float(kva).is_integer() else 1
    return f"{_fmt(kva, dec)} kVA"


def format_potenza_attiva(kw: float | None) -> str:
    """Potenza attiva (carichi/FV). Input in kW. ≥1000 kW→MW (2 dec)."""
    if kw is None:
        return "n.d."
    if abs(kw) >= 1000:
        return f"{_fmt(kw / 1000.0, 2)} MW"
    dec = 0 if float(kw).is_integer() else 1
    return f"{_fmt(kw, dec)} kW"


_SUP = {"0": "⁰", "1": "¹", "2": "²", "3": "³", "4": "⁴", "5": "⁵",
        "6": "⁶", "7": "⁷", "8": "⁸", "9": "⁹", "-": "⁻"}


def _superscript(n: int) -> str:
    return "".join(_SUP[c] for c in str(n))


def format_scientific_italian(x: float | None, sig: int = 2) -> str:
    """Notazione scientifica italiana: '3,99 × 10⁻⁶'. Per |x| in (0.001, 9999)
    usa decimale standard. 0 → '0'."""
    if x is None:
        return "n.d."
    if x == 0:
        return "0"
    import math
    ax = abs(x)
    if 0.001 < ax < 9999:
        return _fmt(x, sig)
    esp = int(math.floor(math.log10(ax)))
    mant = x / (10 ** esp)
    return f"{_fmt(mant, sig)} × 10{_superscript(esp)}"


def format_tensione(v: float | None, decimali: int = 0) -> str:
    if v is None:
        return "n.d."
    if abs(v) >= 1000:
        return f"{_fmt(v / 1000.0, 1)} kV"
    return f"{_fmt(v, decimali)} V"


def format_sezione(mmq: float | None) -> str:
    if mmq is None:
        return "n.d."
    val = int(mmq) if float(mmq).is_integer() else mmq
    return f"{_fmt(val, 0 if isinstance(val, int) else 1)} mm²"


def format_resistenza(ohm: float | None, decimali: int = 2) -> str:
    if ohm is None:
        return "n.d."
    if abs(ohm) >= 1000:
        return f"{_fmt(ohm / 1000.0, 2)} kΩ"
    return f"{_fmt(ohm, decimali)} Ω"


def format_percentuale(frac_o_pct: float | None, gia_percento: bool = True,
                       decimali: int = 1) -> str:
    if frac_o_pct is None:
        return "n.d."
    val = frac_o_pct if gia_percento else frac_o_pct * 100.0
    return f"{_fmt(val, decimali)} %"
