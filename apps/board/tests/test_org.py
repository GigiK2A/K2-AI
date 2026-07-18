"""Test ermetici per l'organigramma del board (org.py)."""
from __future__ import annotations

import json

from aios.org import OrgChart, OrgRole


def test_default_has_ceo_and_six_directors():
    c = OrgChart.default()
    assert c.get("ceo") is not None
    assert len(c.roster()) == 6            # 6 direzioni, CEO escluso
    assert all(r.reports_to == "ceo" for r in c.roster())


def test_manager_and_peers():
    c = OrgChart.default()
    mgr = c.manager_of("finance_agent")
    assert mgr is not None and mgr.key == "ceo"
    peers = {p.key for p in c.peers_of("finance_agent")}
    assert "finance_agent" not in peers
    assert "marketing_agent" in peers and len(peers) == 5


def test_reports_of_ceo():
    c = OrgChart.default()
    assert len(c.reports_of("ceo")) == 6
    assert c.manager_of("ceo") is None     # radice


def test_context_for_injects_role_reporting_peers():
    c = OrgChart.default()
    ctx = c.context_for("finance_agent")
    assert "Direttore Finance" in ctx
    assert "Riporti al" in ctx and "CEO" in ctx
    assert "pari nel board" in ctx


def test_context_for_unknown_is_empty():
    assert OrgChart.default().context_for("sconosciuto") == ""


def test_roster_context_lists_mandates():
    rc = OrgChart.default().roster_context()
    assert "finance_agent" in rc and "marketing_agent" in rc
    assert "delegare" in rc.lower()


def test_env_override(monkeypatch):
    custom = [{"key": "ceo", "title": "Capo", "reports_to": None},
              {"key": "x_agent", "title": "Capo X", "reports_to": "ceo", "mandate": "roba X"}]
    monkeypatch.setenv("AIOS_ORG_JSON", json.dumps(custom))
    c = OrgChart.default()
    assert c.title("x_agent") == "Capo X"
    assert len(c.roster()) == 1


def test_as_dict_shape():
    rows = OrgChart.default().as_dict()
    assert rows and set(rows[0]) == {"key", "title", "reports_to", "mandate"}


def test_singleton_wiring():
    from aios import org
    chart = OrgChart([OrgRole("ceo", "C", None), OrgRole("a_agent", "A", "ceo")])
    org.set_chart(chart)
    assert org.get_chart().title("a_agent") == "A"
    org.set_chart(OrgChart.default())   # ripristina per gli altri test
