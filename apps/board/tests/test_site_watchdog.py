"""Controllo esterno del sito: soglia, richiamo, ripristino, nessun invio spurio."""
import aios.site_watchdog as sw
from aios.site_watchdog import Monitor, Target


class _Clock:
    def __init__(self):
        self.t = 1_000_000.0

    def __call__(self):
        return self.t

    def minuti(self, n):
        self.t += n * 60


def _monitor(esiti, clock=None):
    """esiti: dict nome -> lista di (ok, dettaglio) consumata un giro alla volta."""
    inviati = []
    clock = clock or _Clock()
    targets = [Target(n, f"http://x/{n}", note="nota") for n in esiti]

    def probe(t):
        return esiti[t.name].pop(0)

    return Monitor(targets, inviati.append, probe_fn=probe, clock=clock), inviati, clock


def test_un_solo_errore_non_avvisa():
    m, inviati, _ = _monitor({"sito": [(False, "HTTP 502"), (True, "HTTP 200")]})
    assert m.tick() == [] and m.tick() == [] and inviati == []


def test_due_errori_avvisano_una_volta_sola():
    m, inviati, c = _monitor({"sito": [(False, "HTTP 502")] * 4})
    m.tick()
    c.minuti(1)
    primo = m.tick()
    assert len(primo) == 1 and "NON risponde" in primo[0] and "sito" in primo[0] and "nota" in primo[0]
    c.minuti(1)
    assert m.tick() == [] and m.tick() == []          # nessuno spam finché non scade il richiamo
    assert len(inviati) == 1


def test_richiamo_dopo_il_tempo_e_ripristino_con_durata():
    m, inviati, c = _monitor({"sito": [(False, "timeout")] * 5 + [(True, "HTTP 200 in 90 ms")]})
    for _ in range(2):
        m.tick()
        c.minuti(1)
    c.minuti(sw.REMIND_MIN)
    richiamo = m.tick()
    assert len(richiamo) == 1 and "giù da circa" in richiamo[0]
    c.minuti(1)
    m.tick()
    c.minuti(1)
    m.tick()
    c.minuti(1)
    ripristino = m.tick()
    assert len(ripristino) == 1 and "di nuovo raggiungibile" in ripristino[0]
    assert "min" in ripristino[0]


def test_ripristino_senza_avviso_precedente_non_scrive():
    # un solo errore (sotto soglia) poi ok: nessun «tornato su» per un guasto mai segnalato
    m, inviati, _ = _monitor({"sito": [(False, "x"), (True, "ok")]})
    m.tick()
    m.tick()
    assert inviati == []


def test_bersagli_indipendenti():
    m, inviati, c = _monitor({"sito": [(True, "ok")] * 3, "8e": [(False, "502")] * 3})
    m.tick()
    c.minuti(1)
    out = m.tick()
    assert len(out) == 1 and "8e" in out[0] and "sito" not in out[0]


def test_invio_fallito_non_ferma_il_controllo():
    c = _Clock()

    def boom(_):
        raise RuntimeError("telegram giù")

    m = Monitor([Target("sito", "http://x")], boom, probe_fn=lambda t: (False, "x"), clock=c)
    m.tick()
    c.minuti(1)
    assert len(m.tick()) == 1                          # il messaggio è comunque registrato come inviato


def test_probe_classifica_i_codici(monkeypatch):
    import urllib.error

    class _R:
        status = 200

        def __enter__(self):
            return self

        def __exit__(self, *a):
            return False

    monkeypatch.setattr(sw.urllib.request, "urlopen", lambda req, timeout=0: _R())
    ok, det = sw.probe(Target("s", "http://x"))
    assert ok and det.startswith("HTTP 200")

    def http401(req, timeout=0):
        raise urllib.error.HTTPError("http://x", 401, "no", {}, None)

    monkeypatch.setattr(sw.urllib.request, "urlopen", http401)
    assert sw.probe(Target("s", "http://x", ok_codes=(200, 401)))[0] is True
    assert sw.probe(Target("s", "http://x", ok_codes=(200,)))[0] is False

    def http502(req, timeout=0):
        raise urllib.error.HTTPError("http://x", 502, "bad", {}, None)

    monkeypatch.setattr(sw.urllib.request, "urlopen", http502)
    assert sw.probe(Target("s", "http://x", ok_codes=(200, 401)))[0] is False

    def rete(req, timeout=0):
        raise TimeoutError("lento")

    monkeypatch.setattr(sw.urllib.request, "urlopen", rete)
    ok, det = sw.probe(Target("s", "http://x"))
    assert ok is False and "TimeoutError" in det
