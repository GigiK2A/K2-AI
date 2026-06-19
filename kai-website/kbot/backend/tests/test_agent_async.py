"""Job async dell'agente A2: store + orchestrazione (agente → render 8e → store).
Agente e 8e mockati → nessun credito, nessuna rete. Verifica le transizioni di stato
e che l'esito del render finisca nel job (così pdf/poll passano dagli stessi endpoint)."""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from app.lib import agent_jobs  # noqa: E402


def test_create_is_agent_get():
    jid = agent_jobs.create("checkup_advisor")
    assert agent_jobs.is_agent_job(jid) and jid.startswith("agt_")
    assert not agent_jobs.is_agent_job("job_8e_abc")     # i job 8e non sono agent
    j = agent_jobs.get(jid)
    assert j["status"] == "running" and j["service_id"] == "checkup_advisor"
    assert agent_jobs.get("agt_inesistente") is None


def test_run_rendered(monkeypatch):
    from app.lib import boost_agent, engine, autofill
    monkeypatch.setattr(autofill, "extract_inputs", lambda session, campi: {"ragione_sociale": "X SRL"})
    monkeypatch.setattr(boost_agent, "run_boost_agent",
                        lambda *a, **k: {"delivered": True, "deliverable": {"meta": {"cliente": "X SRL"}},
                                         "metrics": {"calls": 3}, "provenance_calls": [1, 2, 3]})
    monkeypatch.setattr(engine, "render_deliverable_sync",
                        lambda *a, **k: {"status": "rendered", "citazioni": [],
                                         "outputs": {"pdf_path": "/tmp/x.pdf", "json_path": "/tmp/x.json"}})
    jid = agent_jobs.create("checkup_advisor")
    agent_jobs.run(jid, {"id": "s1"}, "checkup_advisor", "SKILL", ["executive_summary"], [])
    j = agent_jobs.get(jid)
    assert j["status"] == "rendered"
    assert j["outputs"]["pdf_path"] == "/tmp/x.pdf"      # outputs del render nel job agente
    assert j["validation"]["provenance_calls"] == 3      # metriche agente annotate


def test_run_agent_refused(monkeypatch):
    from app.lib import boost_agent, autofill
    monkeypatch.setattr(autofill, "extract_inputs", lambda session, campi: {})
    monkeypatch.setattr(boost_agent, "run_boost_agent",
                        lambda *a, **k: {"delivered": False, "problemi": ["sezione mancante"]})
    jid = agent_jobs.create("checkup_advisor")
    agent_jobs.run(jid, {}, "checkup_advisor", "SKILL", ["x"], [])
    j = agent_jobs.get(jid)
    assert j["status"] == "refused" and j["refusal_reason"] == "agent_refused"


def test_run_render_refused_dal_cage(monkeypatch):
    """Se il CAGE dell'8e blocca il deliverable dell'agente (render → EngineRefused),
    il job risulta refused col motivo del gate (non un crash)."""
    from app.lib import boost_agent, engine, autofill
    monkeypatch.setattr(autofill, "extract_inputs", lambda session, campi: {})
    monkeypatch.setattr(boost_agent, "run_boost_agent",
                        lambda *a, **k: {"delivered": True, "deliverable": {"x": 1}, "provenance_calls": []})

    def _raise(*a, **k):
        raise engine.EngineRefused("grounding_failed", "placeholder trapelato")
    monkeypatch.setattr(engine, "render_deliverable_sync", _raise)
    jid = agent_jobs.create("checkup_advisor")
    agent_jobs.run(jid, {}, "checkup_advisor", "SKILL", ["x"], [])
    j = agent_jobs.get(jid)
    assert j["status"] == "refused" and j["refusal_reason"] == "grounding_failed"


if __name__ == "__main__":
    import pytest
    sys.exit(pytest.main([__file__, "-q"]))
