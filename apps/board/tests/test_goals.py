"""Test ermetici per la goal ancestry (goals.py)."""
from __future__ import annotations

from aios import goals
from aios.goals import ancestry_context, load_active, _tree_lines


class _FakeClient:
    def __init__(self, rows):
        self._rows = rows

    def select(self, table, params):
        assert table == goals.GOALS_TABLE
        rows = self._rows
        if params.get("status") == "eq.active":
            rows = [r for r in rows if r.get("status") == "active"]
        return sorted(rows, key=lambda r: r.get("priority", 3))


_GOALS = [
    {"id": 1, "title": "Chiudere 3 clienti PMI in Umbria", "parent_goal_id": None,
     "status": "active", "priority": 1, "description": "focus servizi AI"},
    {"id": 2, "title": "Pipeline: 20 lead qualificati", "parent_goal_id": 1,
     "status": "active", "priority": 2},
    {"id": 3, "title": "Obiettivo chiuso", "parent_goal_id": None,
     "status": "done", "priority": 1},
]


def test_load_active_filters_and_orders():
    rows = load_active(_FakeClient(_GOALS))
    ids = [r["id"] for r in rows]
    assert 3 not in ids            # 'done' escluso
    assert ids == [1, 2]           # ordinati per priorità


def test_load_active_without_client_is_empty():
    assert load_active(None) == []


def test_tree_nests_children_under_parents():
    lines = _tree_lines([r for r in _GOALS if r["status"] == "active"])
    # il figlio (id 2) è indentato sotto il padre (id 1)
    joined = "\n".join(lines)
    assert "Chiudere 3 clienti" in joined
    child_line = next(l for l in lines if "Pipeline" in l)
    assert child_line.startswith("  - ")   # indentato di un livello


def test_ancestry_context_has_header_and_goals():
    ctx = ancestry_context(_FakeClient(_GOALS))
    assert "OBIETTIVI DELL'AZIENDA" in ctx
    assert "Chiudere 3 clienti" in ctx
    assert "Pipeline" in ctx
    assert "Ancora ogni proposta" in ctx


def test_ancestry_context_empty_without_goals():
    assert ancestry_context(_FakeClient([])) == ""
    assert ancestry_context(None) == ""


def test_tree_handles_orphan_and_cycle():
    # parent inesistente (orfano) + auto-riferimento (ciclo) non devono rompere/loopare
    rows = [
        {"id": 10, "title": "Orfano", "parent_goal_id": 999, "status": "active", "priority": 1},
        {"id": 11, "title": "Ciclo", "parent_goal_id": 11, "status": "active", "priority": 1},
    ]
    lines = _tree_lines(rows)
    assert any("Orfano" in l for l in lines)
    assert any("Ciclo" in l for l in lines)
