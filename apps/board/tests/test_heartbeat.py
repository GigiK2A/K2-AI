"""Test ermetici per l'heartbeat per-agente (heartbeat.py)."""
from __future__ import annotations

from aios.heartbeat import HeartbeatScheduler, DEFAULT_INTERVAL_SECONDS

DOMAINS = ["marketing", "finance", "legal"]


def test_interval_default_and_override():
    hb = HeartbeatScheduler({"marketing": 3600}, default_seconds=86400)
    assert hb.interval_for("marketing") == 3600
    assert hb.interval_for("finance") == 86400


def test_never_run_is_due():
    hb = HeartbeatScheduler({}, default_seconds=100)
    assert set(hb.due(DOMAINS, now_epoch=1_000_000.0)) == set(DOMAINS)


def test_recently_run_not_due_stale_is_due():
    hb = HeartbeatScheduler({"marketing": 100, "finance": 100}, default_seconds=100)
    t0 = 1_000_000.0
    hb.mark_ran("marketing", t0)
    hb.mark_ran("finance", t0)
    # 50s dopo: nessuno dovuto
    assert hb.due(["marketing", "finance"], now_epoch=t0 + 50) == []
    # 120s dopo: entrambi dovuti di nuovo
    assert set(hb.due(["marketing", "finance"], now_epoch=t0 + 120)) == {"marketing", "finance"}


def test_per_agent_rhythm_differs():
    hb = HeartbeatScheduler({"marketing": 100, "finance": 1000}, default_seconds=500)
    t0 = 1_000_000.0
    hb.mark_ran("marketing", t0)
    hb.mark_ran("finance", t0)
    # a t0+200: marketing dovuto (int 100), finance no (int 1000)
    due = hb.due(["marketing", "finance"], now_epoch=t0 + 200)
    assert due == ["marketing"]


def test_next_due_in():
    hb = HeartbeatScheduler({"x": 100}, default_seconds=100)
    t0 = 1_000_000.0
    assert hb.next_due_in("x", t0) == 0.0     # mai partito → dovuto ora
    hb.mark_ran("x", t0)
    assert hb.next_due_in("x", t0 + 30) == 70.0


def test_enabled_reads_env(monkeypatch):
    monkeypatch.delenv("AIOS_HEARTBEATS", raising=False)
    assert HeartbeatScheduler.enabled() is False
    monkeypatch.setenv("AIOS_HEARTBEATS", '{"marketing": 3600}')
    assert HeartbeatScheduler.enabled() is True


def test_from_env_parses(monkeypatch):
    monkeypatch.setenv("AIOS_HEARTBEATS", '{"marketing": 3600, "finance": 7200}')
    monkeypatch.setenv("AIOS_HEARTBEAT_DEFAULT_SECONDS", "1234")
    hb = HeartbeatScheduler.from_env()
    assert hb.interval_for("marketing") == 3600
    assert hb.interval_for("finance") == 7200
    assert hb.interval_for("hr") == 1234       # default


def test_from_env_default_interval_without_config(monkeypatch):
    monkeypatch.delenv("AIOS_HEARTBEATS", raising=False)
    monkeypatch.delenv("AIOS_HEARTBEAT_DEFAULT_SECONDS", raising=False)
    hb = HeartbeatScheduler.from_env()
    assert hb.interval_for("qualsiasi") == DEFAULT_INTERVAL_SECONDS


# ── persistenza best-effort ─────────────────────────────────────────────────────
class _FakeClient:
    def __init__(self, rows=None):
        self.rows = rows or []
        self.upserts = []

    def select(self, table, params):
        return self.rows

    def upsert(self, table, row, *, on_conflict):
        self.upserts.append((table, row, on_conflict))
        return [row]


def test_hydrate_from_state():
    c = _FakeClient(rows=[{"actor": "marketing", "last_run_epoch": 1_000_000.0}])
    hb = HeartbeatScheduler({"marketing": 100}, client=c)
    # marketing è partito da poco (hydrate) → non dovuto a t0+50
    assert hb.due(["marketing"], now_epoch=1_000_050.0) == []


def test_mark_ran_persists():
    c = _FakeClient()
    hb = HeartbeatScheduler({"x": 100}, client=c)
    hb.mark_ran("x", 1_000_000.0)
    assert c.upserts and c.upserts[0][0] == "aios_heartbeats"
    assert c.upserts[0][1]["actor"] == "x"


def test_persist_never_raises():
    class Boom:
        def select(self, *a, **k): raise RuntimeError("db down")
        def upsert(self, *a, **k): raise RuntimeError("db down")
    hb = HeartbeatScheduler({"x": 100}, client=Boom())
    hb.mark_ran("x", 1_000_000.0)             # non deve sollevare (persist degrada)
    # appena partito → non dovuto; 200s dopo → di nuovo dovuto (intervallo 100s)
    assert hb.due(["x"], now_epoch=1_000_050.0) == []
    assert hb.due(["x"], now_epoch=1_000_200.0) == ["x"]
