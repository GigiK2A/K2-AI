"""Gli agenti devono sapere che giorno è, e le date di piano non stanno nel passato.

Il 21 ago 2026 Vendite ha messo la prossima azione di NOVE lead al «2023-11-20»: data
valida, accettata da Postgres, sbagliata di tre anni. Nessun prompt del board diceva la
data, quindi il modello ha ripiegato su quella del suo addestramento.

È l'errore peggiore di quelli visti finora: i 400 almeno urlavano, questo scrive una
riga apparentemente sana e fa credere che i solleciti fossero da fare tre anni fa.
"""
import time

import pytest

from aios.actuator import _sanitize, _valore_ammesso
from aios.adesso import blocco_data, data_assurda, oggi_iso

# 21 agosto 2026, 12:00
ADESSO = time.mktime(time.strptime("2026-08-21 12:00", "%Y-%m-%d %H:%M"))


# ---- la data nel prompt ----
def test_il_blocco_dice_la_data_in_chiaro_e_in_iso():
    b = blocco_data(ADESSO)
    assert "2026-08-21" in b
    assert "21 agosto 2026" in b
    assert "venerdì" in b               # 21 ago 2026 è un venerdì


def test_il_blocco_dice_come_usarla():
    b = blocco_data(ADESSO)
    assert "entro 7 giorni" in b and "non da una data che ricordi" in b
    assert "diverso da 2026" in b       # il controllo che avrebbe fermato il 2023


def test_oggi_iso_e_una_data_vera():
    assert oggi_iso(ADESSO) == "2026-08-21"
    assert len(oggi_iso()) == 10


def test_la_chat_mette_la_data_nel_prompt():
    from types import SimpleNamespace

    from aios.chat_runner import ChatAgent, ChatOrchestrator
    from aios.kernel import Kernel
    platform = SimpleNamespace(kernel=Kernel(), agents={}, commands=None, chat=None,
                              prospector=None)
    orch = ChatOrchestrator(platform, None, None, skills=None)
    sysp = ChatAgent(orch, "vendite", None)._system_prompt()
    assert "CHE GIORNO È" in sysp and str(time.localtime().tm_year) in sysp


def test_gli_agenti_del_loop_ce_l_hanno_nel_contesto():
    import inspect

    from aios.agents import domain
    sorgente = inspect.getsource(domain)
    assert "blocco_data()" in sorgente


# ---- il guardrail sulle date di piano ----
@pytest.mark.parametrize("colonna", ["next_action_date", "expected_close_date",
                                     "scadenza", "expiry_date"])
def test_una_data_di_piano_nel_passato_remoto_non_passa(colonna):
    assert _valore_ammesso(colonna, "2023-11-20") is False


@pytest.mark.parametrize("colonna", ["last_contact_at", "due_at", "created_at",
                                     "date_completed", "paid_at"])
def test_le_date_di_fatto_nel_passato_restano_valide(colonna):
    """Un contatto avvenuto o un task in ritardo stanno legittimamente dietro."""
    assert _valore_ammesso(colonna, "2023-11-20") is True


def test_un_piano_futuro_passa():
    futuro = time.strftime("%Y-%m-%d", time.localtime(time.time() + 7 * 86400))
    assert _valore_ammesso("next_action_date", futuro) is True


def test_un_ritardo_di_pochi_giorni_e_plausibile():
    """Un sollecito con due settimane di ritardo è un fatto, non un'invenzione."""
    poco = time.strftime("%Y-%m-%d", time.localtime(time.time() - 14 * 86400))
    assert _valore_ammesso("next_action_date", poco) is True


def test_data_assurda_solo_su_date_vere():
    assert data_assurda("2023-11-20", ADESSO) is True
    assert data_assurda("2026-08-20", ADESSO) is False
    assert data_assurda("entro 7 giorni", ADESSO) is False   # non è questo il controllo
    assert data_assurda("", ADESSO) is False


# ---- effetto sulla riga scritta ----
def test_la_data_inventata_finisce_nelle_note_non_nella_colonna():
    """Non si perde l'informazione e non si scrive un piano falso: la riga resta, la
    colonna resta vuota e il testo va dove l'owner lo legge."""
    out = _sanitize("pipeline_leads",
                    {"name": "Alfa", "next_action": "primo contatto",
                     "next_action_date": "2023-11-20"}, "insert")
    assert "next_action_date" not in out
    assert "2023-11-20" in out["notes"]
    assert out["next_action"] == "primo contatto"     # il resto della riga è intatto
