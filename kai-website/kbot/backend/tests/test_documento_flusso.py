"""Documento separato: i marcatori sopravvivono alle guardie, nessun report sulle richieste di documento, ragione sociale e boost."""
import json

import pytest

from app.api import message as M
from app.lib import documento as D

DOC = ("Ecco la PEC.\n\n<<<DOCUMENTO: PEC di contestazione>>>\nOggetto: contestazione fattura n. [numero]\n\n"
       "Spett.le DemoSoft S.r.l., con la presente contestiamo le difformità del gestionale rispetto al contratto firmato il "
       "[data]. Sospendiamo il pagamento della parte contestata fino alla regolarizzazione.\n\nDistinti saluti\n"
       "<<<FINE DOCUMENTO>>>\n\nVerifica: numero e data della fattura, e la clausola di pagamento del contratto.")
SUMMARY = ('\nCONSULENZA_SUMMARY_START {"reportType":"x","objective":"y","scope":"z"} CONSULENZA_SUMMARY_END')


def _msgs(*u):
    out = []
    for i, t in enumerate(u):
        out += [{"role": "user", "content": t}] + ([{"role": "assistant", "content": "ok"}] if i < len(u) - 1 else [])
    return out


def test_i_marcatori_sopravvivono_a_tutte_le_guardie():
    visible, summary, _ = M._extract_gated_summary(DOC, _msgs("Scrivimi una PEC per contestare il software"), {})
    b = D.estrai(visible)
    assert len(b) == 1 and b[0]["completo"] and "Spett.le DemoSoft" in b[0]["testo"]


def test_una_richiesta_di_documento_non_apre_il_generatore_dei_report():
    for richiesta in ("Scrivimi una PEC per contestare il software", "Genera un documento interno di valutazione dell'incidente"):
        _, summary, _ = M._extract_gated_summary(DOC + SUMMARY, _msgs("a", "b", "c", "d", richiesta), {})
        assert summary is None, richiesta


def test_una_richiesta_di_report_conserva_il_riepilogo():
    _, summary, _ = M._extract_gated_summary("Preparo il report." + SUMMARY, _msgs("a", "b", "c", "d", "Procedi, fai il report"), {})
    assert summary


def test_la_regola_del_documento_entra_nel_prompt_solo_per_le_richieste_di_documento():
    from app.lib.indici_e_bozze import blocchi
    assert "<<<DOCUMENTO" in blocchi("Scrivimi una PEC per contestare il gestionale difettoso")
    assert "<<<DOCUMENTO" in blocchi("Prepara il registro interno dei data breach")
    assert "<<<DOCUMENTO" not in blocchi("Posso sospendere il pagamento della fattura?")


def test_verifica_bozze_riconosce_il_blocco_come_bozza():
    from app.lib import verifica_bozze as V
    assert V.contiene_bozza(DOC) and V.richiesta_bozza("Prepara il registro interno dei data breach")


def test_la_ragione_sociale_detta_in_chat_arriva_al_generatore():
    from app.api.deliverables import _session_company
    sess = {"collected_data": {"scheda_cliente": {"ragione_sociale": {"valore": "DemoTech S.r.l.", "citazione": "DemoTech S.r.l.", "turno": 3}}}}
    assert _session_company(sess) == "DemoTech S.r.l."
    assert _session_company({"collected_data": {}}) is None
    assert _session_company({"collected_data": {}, "_profilo": {"ragione_sociale": "Profilo Srl"}}) == "Profilo Srl"


def test_il_boost_predefinito_non_si_assegna_a_un_incidente_gdpr():
    msgs = _msgs("Un dipendente ha mandato per errore un Excel con i dati di 120 clienti a un cliente",
                 "Il destinatario conferma di averlo cancellato", "Dobbiamo notificare al Garante?",
                 "Genera il registro interno di valutazione dell'incidente")
    c = {}
    M._recompute_boost(c, msgs, None)
    assert not c.get("boost_suggerito"), c.get("boost_suggerito")


def test_un_boost_di_ripiego_rimasto_da_prima_si_toglie():
    from app.lib import catalog
    msgs = _msgs("Un dipendente ha mandato per errore un Excel con i dati di 120 clienti", "Il destinatario lo ha cancellato", "Dobbiamo notificare al Garante?")
    c = {"boost_suggerito": catalog._BOOST_DEFAULT, "boost_suggerito_label": "ControlBoost"}
    M._recompute_boost(c, msgs, None)
    assert "boost_suggerito" not in c


def test_un_boost_vero_resta():
    msgs = _msgs("Ho ricevuto un avviso di accertamento fiscale", "Devo fare il ravvedimento operoso sull'IVA", "Quali sanzioni pago all'Agenzia delle Entrate?")
    c = {}
    M._recompute_boost(c, msgs, None)
    assert c.get("boost_suggerito") == "checkup_fiscale"


def test_il_critico_di_qualita_non_gira_su_un_documento_richiesto():
    """Costava fino a 51 s di «verifica» e poteva riscrivere il documento (misurato il 20/10/2026)."""
    from types import SimpleNamespace
    chiamate = []

    class C:
        def __init__(self):
            self.messages = SimpleNamespace(create=lambda **k: chiamate.append(k) or SimpleNamespace(content=[SimpleNamespace(type="text", text="{}")]))

    testo = ("Ecco la PEC, con la diffida al fornitore.\n\n<<<DOCUMENTO: PEC>>>\nOggetto: sospensione del pagamento per inadempimento, "
             "diffida ad adempiere e richiesta di risarcimento. " + "Testo del documento. " * 20 + "\n<<<FINE DOCUMENTO>>>\n\nVerifica i dati.")
    msgs = _msgs("Scrivimi una PEC per contestare il software difettoso e sospendere il pagamento")
    M._postprocess_turn(C(), "sys", [{"role": "user", "content": "x"}], msgs, testo, {})
    assert not chiamate, "il critico è partito su un documento richiesto"
    # senza documento il critico resta attivo (stesso testo con parole di rischio)
    M._postprocess_turn(C(), "sys", [{"role": "user", "content": "x"}], _msgs("Posso sospendere il pagamento?"),
                        "Puoi sospendere il pagamento per inadempimento, ma attento alla responsabilità.", {})
    assert chiamate
