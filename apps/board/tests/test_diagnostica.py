"""All'avvio il board deve dire cosa può davvero arrivare a destinazione.

Il braccio esterno è env-gated: senza N8N_WEBHOOK_URL ogni invio viene rifiutato.
Senza diagnostica lo si scopriva una approvazione alla volta.
"""
import pytest

from autonomy_loop import diagnostica


class _Conv:
    def __init__(self, n=0, esplode=False):
        self.n, self.esplode = n, esplode

    def bozze_in_attesa(self, limit=20):
        if self.esplode:
            raise RuntimeError("rete giù")
        return [{"id": i} for i in range(self.n)]


class _Approvals:
    def __init__(self, n=0):
        self.n = n

    def pending(self):
        return list(range(self.n))


class _Kernel:
    def __init__(self, n=0):
        self.approvals = _Approvals(n)


class _Platform:
    def __init__(self, pending=0, bozze=0, conv=True, esplode=False):
        self.kernel = _Kernel(pending)
        self.conversations = _Conv(bozze, esplode) if conv else None


def test_avverte_se_le_azioni_esterne_non_sono_configurate(monkeypatch):
    monkeypatch.delenv("N8N_WEBHOOK_URL", raising=False)
    out = diagnostica(_Platform())
    assert "⛔" in out and "N8N_WEBHOOK_URL" in out
    assert "non partiranno" in out.lower()


def test_conferma_quando_le_azioni_esterne_sono_configurate(monkeypatch):
    monkeypatch.setenv("N8N_WEBHOOK_URL", "https://n8n.example.it/webhook/k2ai")
    out = diagnostica(_Platform())
    assert "✅" in out and "configurate" in out
    assert "N8N_WEBHOOK_URL" not in out      # nessun allarme se è a posto


def test_riporta_arretrato_coda_e_bozze(monkeypatch):
    monkeypatch.setenv("N8N_WEBHOOK_URL", "https://n8n.example.it/webhook/k2ai")
    out = diagnostica(_Platform(pending=305, bozze=105))
    assert "305" in out and "105" in out


def test_non_solleva_se_una_fonte_e_illeggibile(monkeypatch):
    """La diagnostica non deve mai impedire l'avvio del loop."""
    monkeypatch.delenv("N8N_WEBHOOK_URL", raising=False)
    out = diagnostica(_Platform(bozze=3, esplode=True))
    assert "non leggibili" in out


def test_funziona_senza_modulo_conversazioni(monkeypatch):
    monkeypatch.delenv("N8N_WEBHOOK_URL", raising=False)
    out = diagnostica(_Platform(conv=False))
    assert "Diagnostica" in out
