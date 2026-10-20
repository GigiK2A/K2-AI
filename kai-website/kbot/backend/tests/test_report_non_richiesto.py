"""Il report non parte senza una richiesta dell'utente (20/10/2026: partiva alla domanda «ricontrolla i calcoli»)."""
from app.lib import report_gate


def _caso(**kw):
    c = {"diagnosi": {"confidenza": "media", "fase": "diagnosi", "ipotesi": [{"t": "x", "s": "aperta"}], "manca": "il mese"},
         "route_confidence": {"confident": True, "top": "checkup_fiscale"}}
    c.update(kw)
    return c


def test_senza_consenso_e_con_diagnosi_aperta_il_report_non_parte():
    g = report_gate.evaluate(_caso(), "checkup_fiscale", user_requested=False)
    assert not g["allowed"] and g["reason"] == "diagnosi_non_conclusa"


def test_il_clic_dell_utente_vale_come_consenso():
    assert report_gate.evaluate(_caso(), "checkup_fiscale", user_requested=True)["reason"] == "consenso_utente"


def test_hold_batte_tutto():
    assert report_gate.evaluate(_caso(report_hold=True), "x", user_requested=True)["reason"] == "hold_utente"


def test_riepilogo_gia_emesso_dal_bot_e_un_consenso():
    assert report_gate.evaluate(_caso(analysis_ready=True), "checkup_fiscale", user_requested=False)["allowed"]


def test_l_endpoint_auto_non_tratta_l_avvio_automatico_come_un_clic(monkeypatch):
    """/deliverables/auto con explicit=False deve passare user_requested=False al pre-flight."""
    from app.api import deliverables as D
    visto = {}
    real = D.report_gate.evaluate

    def spia(collected, servizio_id=None, user_requested=False):
        visto["u"] = user_requested
        return real(collected, servizio_id, user_requested)

    monkeypatch.setattr(D.report_gate, "evaluate", spia)
    monkeypatch.setattr(D.sessions, "get_session", lambda sid: {"id": sid, "user_id": None, "collected_data": _caso(), "messages": []})
    monkeypatch.setattr(D, "_check_ownership", lambda s, u: None)
    import asyncio
    from fastapi import BackgroundTasks, HTTPException
    for esplicito, atteso_bloccato in ((False, True), (True, False)):
        visto.clear()
        body = D.AutoBody(session_id="s1", explicit=esplicito)
        try:
            asyncio.run(D.auto_deliverable(body, BackgroundTasks(), None))
            bloccato = False
        except HTTPException as e:
            bloccato = (e.detail or {}).get("reason") == "consulenza_aperta"
        except Exception:
            bloccato = False                      # oltre il pre-flight: ci interessa solo che NON sia stato bloccato dal gate
        assert visto["u"] is esplicito
        assert bloccato is atteso_bloccato, esplicito


def test_il_prompt_delle_norme_non_esclude_piu_i_calcoli_fiscali():
    """Il prompt che propone le norme diceva «niente norme per i calcoli»: un calcolo di IVA/IRES/ammortamento restava
    senza fonti e il modello calcolava a memoria (20/10/2026). Ora distingue calcolo aritmetico e calcolo di legge."""
    from app.lib import norme_evidence as N
    t = N._SISTEMA_PROPOSTA
    assert "organizzazione, tecnica, calcoli)" not in t
    assert "APPLICA aliquote" in t and "D.P.R. 917/1986 art. 102" in t and "costo per contatto" in t


import pytest


@pytest.mark.parametrize("testo,atteso", [
    ("Ricontrolla i calcoli, mi sembrano sbagliati.", True),
    ("Puoi ricontrollare l'IVA?", True),
    ("Sei sicuro? Non mi tornano i mesi.", True),
    ("Hai sbagliato la quota del primo anno", True),
    ("Rifai i calcoli con IRES al 24%", True),
    ("Quanto costa assumere un apprendista?", False),
    ("Posso dedurre l'auto aziendale?", False),
    ("Fai il report", False),
    ("Procedi", False),
    ("", False),
])
def test_is_recheck(testo, atteso):
    from app.lib import signals
    assert signals.is_recheck(testo) is atteso


def _prompt(ultimo):
    from app.lib.prompts import build_system_prompt_v2
    msgs = [{"role": "user", "content": "Siamo una SRL, computer da 2.500 euro: ammortamento e IRES?"},
            {"role": "assistant", "content": "La quota del primo anno è 250 euro."},
            {"role": "user", "content": ultimo}]
    return build_system_prompt_v2(["diagnosi-ai-operativa-pmi"], {"messages": msgs, "collected_data": {}})


def test_il_prompt_chiede_di_rifare_i_calcoli_solo_nei_turni_di_ricontrollo():
    assert "RICONTROLLARE la tua risposta precedente" in _prompt("Ricontrolla i calcoli, mi sembrano sbagliati.")
    assert "RICONTROLLARE la tua risposta precedente" not in _prompt("E se il computer costasse 400 euro?")
    assert "non generarne" in _prompt("Ricontrolla i calcoli").lower() or "NON è una richiesta di report" in _prompt("Ricontrolla i calcoli")
