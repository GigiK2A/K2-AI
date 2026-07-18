"""Obiettivi dell'azienda con gerarchia — la "goal ancestry" di Paperclip.

"Context flows from the task up through the project and company goals — your agent
always knows what to do and why." Prima l'AIOS aveva solo obiettivi come testo
libero in shared_memory; gli agenti proponevano senza vedere il *perché*.

Qui gli obiettivi sono un albero (`aios_goals`, self-FK `parent_goal_id`):
  mission → obiettivo strategico → obiettivo di progetto.
L'albero degli obiettivi ATTIVI viene iniettato nel contesto di ogni agente, così
ogni proposta è ancorata a un obiettivo reale e non è un'idea a caso.

Gli obiettivi si creano/aggiornano attraverso il normale flusso propose→approva
(la tabella è in ALLOWLIST, non BLOCKED): li può proporre il CEO o un direttore.
Degrada a "nessun contesto" senza DB, così i test restano ermetici.
"""

from __future__ import annotations

from typing import Any, Optional

GOALS_TABLE = "aios_goals"


def load_active(client: Any, limit: int = 25) -> list[dict]:
    """Obiettivi attivi ordinati per priorità (1 = più alta). [] senza DB/errore."""
    if client is None:
        return []
    try:
        return client.select(GOALS_TABLE, {
            "select": "*", "status": "eq.active",
            "order": "priority.asc", "limit": str(int(limit))})
    except Exception:
        return []


def _tree_lines(goals: list[dict]) -> list[str]:
    """Rende l'albero degli obiettivi (parent_goal_id) come righe indentate."""
    by_id = {g.get("id"): g for g in goals if g.get("id") is not None}

    def title(g: dict) -> str:
        t = str(g.get("title") or "(obiettivo senza titolo)")
        desc = str(g.get("description") or "").strip()
        return t + (f" — {desc[:140]}" if desc else "")

    children: dict[Any, list[dict]] = {}
    roots: list[dict] = []
    for g in goals:
        parent = g.get("parent_goal_id")
        if parent and parent in by_id:
            children.setdefault(parent, []).append(g)
        else:
            roots.append(g)

    lines: list[str] = []
    seen: set = set()

    def walk(g: dict, depth: int) -> None:
        gid = g.get("id")
        if gid in seen:          # guardia anti-ciclo
            return
        seen.add(gid)
        lines.append("  " * depth + "- " + title(g))
        for c in children.get(gid, []):
            walk(c, depth + 1)

    for r in roots:
        walk(r, 0)
    # eventuali orfani non raggiunti (parent mancante ma non root) → in coda
    for g in goals:
        if g.get("id") not in seen:
            lines.append("- " + title(g))
    return lines


def ancestry_context(client: Any, limit: int = 25) -> str:
    """Blocco 'OBIETTIVI DELL'AZIENDA' da iniettare nel prompt dell'agente."""
    goals = load_active(client, limit=limit)
    if not goals:
        return ""
    lines = ["## OBIETTIVI DELL'AZIENDA (il perché di ogni tua proposta)"]
    lines += _tree_lines(goals)
    lines.append("Ancora ogni proposta concreta a uno di questi obiettivi. "
                 "Se una proposta non serve nessun obiettivo attivo, chiediti se vale davvero.")
    return "\n".join(lines)
