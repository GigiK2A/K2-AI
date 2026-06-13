from __future__ import annotations

from typing import Any


def build_deliverable(*, titolo: str, insights: list[dict] | None = None,
                      proposte: list[dict] | None = None,
                      fonti: list[dict] | None = None) -> str:
    """Deliverable Verificato in markdown — ogni numero con la sua fonte."""
    parts = [f"# {titolo}\n"]
    if insights:
        parts.append("## Insight\n")
        for i in insights:
            parts.append(f"- **{i.get('titolo','')}** — {i.get('evidenza','')} "
                         f"-> _{i.get('azione','')}_")
        parts.append("")
    if proposte:
        parts.append("## Proposte\n")
        for p in proposte:
            parts.append(f"- **[{p.get('tipo','')}] {p.get('titolo','')}** — "
                         f"{p.get('contenuto','')}  \n  perche: {p.get('motivo','')}")
        parts.append("")
    parts.append("## Fonti\n")
    if fonti:
        for f in fonti:
            parts.append(f"- `{f.get('campo','')}` = {f.get('valore','')} "
                         f"(fonte: {f.get('fonte','')})")
    else:
        parts.append("- (nessuna fonte numerica dichiarata)")
    return "\n".join(parts) + "\n"
