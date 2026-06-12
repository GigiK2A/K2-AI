"""Competitor scout: l'agente trova competitor da solo (web) → profili strutturati."""
import json

from aios.competitor_scout import CompetitorScout, competitors_tool
from aios.llm import FakeLLM


class _Founder:
    def to_prompt(self):
        return "# ICP\nPMI italiane 5-50 dip."


_JSON = json.dumps({"competitors": [
    {"name": "Acme AI", "website": "https://acme.it", "offering": "automazioni PMI",
     "positioning": "low cost", "pricing": "da 99€/mese", "strengths": "prezzo",
     "weaknesses": "poco verticale", "threat": 70, "differentiation": "noi siamo verticali",
     "source": "acme.it"},
    {"name": "Beta Studio", "threat": 20}]})


def test_find_parses_competitors():
    llm = FakeLLM(["ricerca grezza dal web…", _JSON])
    scout = CompetitorScout(llm, llm, _Founder())
    out = scout.find(n=2)
    assert len(out) == 2 and out[0]["name"] == "Acme AI" and out[0]["threat"] == 70


def test_to_row_shape_and_clamps():
    row = CompetitorScout.to_row({"name": "X" * 500, "threat": "55", "website": "",
                                  "offering": "o", "differentiation": "d"})
    assert len(row["name"]) == 200 and row["threat"] == 55
    assert row["website"] is None and row["status"] == "nuovo"
    assert set(row) <= {"name", "website", "offering", "positioning", "pricing", "strengths",
                        "weaknesses", "threat", "differentiation", "source", "status"}


def test_to_row_matches_allowlist_schema():
    from aios.actuator import _SCHEMA
    cols = _SCHEMA["marketing_competitors"]
    row = CompetitorScout.to_row({"name": "Y", "threat": 1})
    assert set(row) <= cols  # ogni colonna scritta esiste nello schema reale


def test_tool_graceful_without_table():
    class BadClient:
        def select(self, *a, **k):
            raise RuntimeError("no table")
    t = competitors_tool(BadClient())
    assert t.name == "leggi_competitor_trovati" and t.readonly is True
    assert t.run() == []
