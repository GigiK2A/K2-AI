"""Il check LLM della diagnostica deve misurare quello che vede l'utente della chat.

Regressione del 15/10/2026: il vecchio check (create, max_tokens=1) rispondeva
"ok" in 0,3 s mentre la chat moriva in ReadTimeout, perché il modello ragionava
per minuti prima di scrivere la prima parola.
"""
from types import SimpleNamespace as NS

from app.api import diagnostics


def _delta(text):
    return NS(type="content_block_delta", delta=NS(type="text_delta", text=text))


def _thinking_start():
    return NS(type="content_block_start", content_block=NS(type="thinking"))


class _Stream:
    def __init__(self, events, clock=None):
        self.events = events
        self.clock = clock

    def __enter__(self):
        return self

    def __exit__(self, *_a):
        return False

    def __iter__(self):
        for ev in self.events:
            if self.clock is not None:
                self.clock.advance()
            yield ev


def _fake_client(events, clock=None):
    class _Msgs:
        def stream(self, **_kw):
            return _Stream(events, clock)

    class _Client:
        def __init__(self, *_a, **_k):
            self.messages = _Msgs()

    return _Client


class _Clock:
    """perf_counter finto: ogni evento dello stream fa avanzare il tempo di `step` s."""

    def __init__(self, step):
        self.t = 0.0
        self.step = step

    def advance(self):
        self.t += self.step

    def __call__(self):
        return self.t


def _run(monkeypatch, events, step=None):
    monkeypatch.setattr(diagnostics, "ANTHROPIC_API_KEY", "test-key")
    clock = _Clock(step) if step is not None else None
    if clock is not None:
        monkeypatch.setattr(diagnostics.time, "perf_counter", clock)
    monkeypatch.setattr(diagnostics._anthropic, "Anthropic", _fake_client(events, clock))
    return diagnostics._check_anthropic()


def test_visible_text_is_ok(monkeypatch):
    res = _run(monkeypatch, [_delta("pronto")])
    assert res["status"] == "ok"
    assert res["reply"] == "pronto"
    assert res["route"] == "chat"


def test_only_thinking_no_text_is_error(monkeypatch):
    res = _run(monkeypatch, [_thinking_start()])
    assert res["status"] == "error"
    assert res["error"] == "NoVisibleText"
    assert res["thinking_blocks"] == 1


def test_text_after_budget_is_error(monkeypatch):
    # Ogni evento costa 20 s: il testo arriverebbe al terzo evento (60 s),
    # oltre il budget di 30 s → il check si ferma e segnala errore.
    events = [_thinking_start(), _thinking_start(), _delta("pronto")]
    res = _run(monkeypatch, events, step=20.0)
    assert res["status"] == "error"
    assert res["error"] == "NoVisibleText"


def test_slow_first_text_is_slow(monkeypatch):
    # Primo testo a 20 s: dentro il budget (30 s) ma oltre la soglia lenta (15 s).
    res = _run(monkeypatch, [_delta("pronto")], step=20.0)
    assert res["status"] == "slow"
    assert res["first_text_ms"] == 20000


def test_exception_is_error(monkeypatch):
    class _Boom:
        def __init__(self, *_a, **_k):
            raise RuntimeError("connessione rifiutata")

    monkeypatch.setattr(diagnostics, "ANTHROPIC_API_KEY", "test-key")
    monkeypatch.setattr(diagnostics._anthropic, "Anthropic", _Boom)
    res = diagnostics._check_anthropic()
    assert res["status"] == "error"
    assert res["error"] == "RuntimeError"
