"""Regression della review 'calo ordini' (consulente prima, report dopo).

Copre i comportamenti che DEVONO reggere a codice (non solo nel prompt):
- routing SEMANTICO: un caso marketing/vendite NON diventa 'Primo parere legale'
  (bug 'causa'); il legale vero continua a instradare;
- HOLD: la volontà dell'utente di continuare la consulenza blocca la generazione;
- pre-flight: senza consenso esplicito, una diagnosi non conclusa NON genera; il nome
  azienda NON è un segnale di readiness; una diagnosi solida sì;
- il prompt spiega il cambio di analisi e tratta il nome come personalizzazione.
"""
from __future__ import annotations

import sys
import types

# Stub delle dipendenze pesanti così build_system_prompt_v2 è importabile ovunque.
for _name, _attrs in (("dotenv", {"load_dotenv": lambda *a, **k: False}),):
    if _name not in sys.modules:
        _m = types.ModuleType(_name)
        [setattr(_m, k, v) for k, v in _attrs.items()]
        sys.modules[_name] = _m
try:  # pragma: no cover
    from supabase import Client as _ProbeClient  # noqa: F401
except Exception:  # pragma: no cover
    _m = types.ModuleType("supabase")
    _m.Client, _m.create_client = object, (lambda *a, **k: None)
    sys.modules["supabase"] = _m

from app.lib import signals, catalog, report_gate, finance_guard  # noqa: E402


# ── scenario del test: diagnosi marketing/vendite, piena di "causa" ──────────────────────
_MKT = ("gli ordini sono calati del 30%, il titolare pensa sia una questione di prezzi piu "
        "bassi dei concorrenti. voglio capire la causa del calo. quale puo essere la causa? "
        "il calo dei lead dal sito puo aver causato la riduzione degli ordini. la conversione "
        "dei preventivi e stabile. i lead dal sito sono diminuiti del 40%. questo puo essere "
        "causato da problemi di acquisizione digitale, traffico web, campagne marketing.")


# ── Test 2 — Marketing non deve diventare Legal ──────────────────────────────────────────
def test_marketing_scenario_non_diventa_legal():
    r = catalog.suggest_boost({"reportType": "diagnosi calo ordini",
                               "objective": "capire la causa del calo"}, user_text=_MKT)
    assert r is not None
    assert r["id"] != "primo_parere_legale"
    assert r["id"] in ("checkup_marketing", "checkup_seo", "checkup_controllo")


def test_causa_non_da_punteggio_legale():
    # 'causa'/'causare' onnipresenti in diagnosi: score legale DEVE restare 0.
    bd = catalog.route_breakdown({}, user_text=(
        "qual e la causa del problema, cosa lo ha causato, la causa piu probabile del calo, "
        "questo ha causato la riduzione"))
    assert bd["scores"].get("primo_parere_legale", 0) == 0


def test_legale_vero_ancora_instrada():
    r = catalog.suggest_boost(
        {"reportType": "parere legale"},
        user_text=("un cliente non paga e minaccia di farmi causa; valuto una diffida e un "
                   "contenzioso, mi serve un parere legale"))
    assert r is not None and r["id"] == "primo_parere_legale"


# ── Test 1 — Nessun report prematuro (HOLD) ──────────────────────────────────────────────
def test_hold_signal_riconosciuto():
    for t in ("voglio capire prima la causa, non generare ancora nulla",
              "continuiamo a ragionare", "non fare ancora il report",
              "prima arriviamo alla diagnosi", "voglio approfondire"):
        assert signals.wants_to_continue(t), t


def test_procedi_non_e_hold():
    for t in ("ok procedi, fai il report", "vai", "voglio il report subito"):
        assert not signals.wants_to_continue(t), t


def test_hold_blocca_generazione_anche_con_click():
    # HOLD è vincolante: vince anche su un'azione esplicita di generazione.
    g = report_gate.evaluate({"report_hold": True, "analysis_ready": True}, user_requested=True)
    assert g["allowed"] is False and g["reason"] == "hold_utente"


# ── Test 3 — Mancano dati chiave → report non pronto ─────────────────────────────────────
def test_diagnosi_non_conclusa_blocca_senza_consenso():
    coll = {"diagnosi": {"ipotesi": [{"t": "acquisizione digitale", "s": "aperta"}],
                         "manca": "andamento del traffico web", "confidenza": "media"}}
    g = report_gate.evaluate(coll, user_requested=False)
    assert g["allowed"] is False and g["reason"] == "diagnosi_non_conclusa"


# ── Test 4 — Nome azienda non è readiness ────────────────────────────────────────────────
def test_nome_azienda_non_e_readiness():
    # ho solo l'identità cliente, ma la diagnosi è aperta → NON si genera.
    coll = {"extractedData": {"businessType": "arredamento su misura", "azienda": "Test Srl"},
            "diagnosi": {"ipotesi": [{"t": "lead dal sito", "s": "aperta"}],
                         "manca": "andamento traffico", "confidenza": "bassa"}}
    g = report_gate.evaluate(coll, user_requested=False)
    assert g["allowed"] is False


# ── Test 5 — Consulenza senza deliverable (resta in chat) ────────────────────────────────
def test_caso_esplorativo_resta_in_chat():
    coll = {"diagnosi": {"ipotesi": [{"t": "x", "s": "aperta"}, {"t": "y", "s": "aperta"}],
                         "confidenza": "bassa", "fase": "esplorazione"}}
    assert report_gate.evaluate(coll, user_requested=False)["allowed"] is False


# ── diagnosi solida → consentito (anche senza consenso esplicito) ────────────────────────
def test_diagnosi_solida_consente():
    coll = {"diagnosi": {"confidenza": "alta", "fase": "pronto",
                         "ipotesi": [{"t": "acquisizione digitale", "s": "probabile"}]}}
    g = report_gate.evaluate(coll, user_requested=False)
    assert g["allowed"] is True and g["reason"] == "diagnosi_solida"


def test_consenso_esplicito_consente_ma_hold_vince():
    # analysis_ready (summary emesso e accettato) = consenso → consente
    assert report_gate.evaluate({"analysis_ready": True})["allowed"] is True
    # ma se poi l'utente chiede di continuare, l'HOLD blocca comunque
    assert report_gate.evaluate({"analysis_ready": True, "report_hold": True})["allowed"] is False


# ── Test 6 — il prompt aggiorna l'analisi + nome = personalizzazione ─────────────────────
def _prompt():
    from app.lib.prompts import build_system_prompt_v2
    return build_system_prompt_v2([], {"messages": [{"role": "user", "content": "ciao"}],
                                       "collected_data": {}}, required_fields_hint="")


def test_prompt_aggiorna_analisi_e_nome_non_readiness():
    p = _prompt()
    assert "AGGIORNA L'ANALISI AD ALTA VOCE" in p
    assert "PERSONALIZZAZIONE, NON READINESS" in p
    assert "SENZA report" in p  # può chiudere senza report
    # non usa più la quantità come criterio sufficiente
    assert "NON significa «pronto»" in p


def test_prompt_stato_diagnostico_ha_confidenza_e_fase():
    # il blocco DIAGNOSI_STATO chiede confidenza + fase (pre-flight le legge)
    p = _prompt()
    assert '"confidenza"' in p and '"fase"' in p


# ── Review HR: ragionamento trasparente (prompt) ─────────────────────────────────────────
def test_prompt_ragionamento_trasparente():
    p = _prompt()
    assert "RAGIONAMENTO TRASPARENTE" in p
    # domande motivate + struttura di aggiornamento diagnosi + diagnosi provvisoria
    assert "DOMANDE MOTIVATE" in p
    assert "AGGIORNAMENTO ESPLICITO DELLA DIAGNOSI" in p
    assert "DIAGNOSI PROVVISORIA" in p
    # PRIMO ERRORE: testare l'ipotesi dubitata, non operazionalizzarla
    assert "NON OPERAZIONALIZZARLA" in p
    # probabilità per ipotesi (70/20/5/5) nel blocco di stato
    assert '"p"' in p


def test_prompt_ipotesi_pesate_reiniettate():
    # se lo stato diagnostico persistito ha probabilità, vengono ri-iniettate nel prompt
    from app.lib.prompts import build_system_prompt_v2
    sess = {"messages": [{"role": "user", "content": "ok"}],
            "collected_data": {"diagnosi": {
                "fase": "diagnosi", "confidenza": "media",
                "ipotesi": [{"t": "problema organizzativo", "s": "probabile", "p": 70},
                            {"t": "leadership", "s": "aperta", "p": 20},
                            {"t": "retribuzione", "s": "esclusa", "p": 5}],
                "manca": "esiti stay interview"}}}
    p = build_system_prompt_v2([], sess, required_fields_hint="")
    assert "70%" in p and "problema organizzativo" in p
    assert "RIDISTRIBUISCI le probabilità" in p


# ── PRIMO ERRORE (belt deterministico): niente campi-form durante la diagnosi ────────────
def test_required_fields_hint_soppresso_durante_diagnosi():
    from app.lib import readiness
    # campi diagnostici del boost (es. costi/personale di ControlBoost)
    campi = [{"id": "costo_personale", "label": "Costo del personale", "obbligatorio": True},
             {"id": "mese", "label": "Mese", "obbligatorio": True}]
    # consulenza_ricca/diagnosi in corso = True → NON elenca i campi di analisi del template
    hint_diag = readiness.required_fields_hint(campi, consulenza_ricca=True)
    assert "costo_personale" not in hint_diag
    # senza gate (baseline) i campi verrebbero elencati → è ciò che si evita in diagnosi
    hint_base = readiness.required_fields_hint(campi, consulenza_ricca=False)
    assert "costo_personale" in hint_base


# ── #1 Guardia numeri finanziari inventati (ROI/payback/% del fatturato) ─────────────────
def test_finance_guard_softens_invented_numbers():
    cases = [
        "Il ROI sarà del 25%.",
        "Il payback sarà di 3 anni.",
        "I 500.000 euro rappresentano il 10-12% del fatturato.",
        "Il ritorno sull'investimento atteso è del 20%.",
        "L'investimento si ripaga in 2 anni.",
    ]
    for t in cases:
        out = finance_guard.sanitize(t)
        assert out != t, t
        # niente più cifra percentuale/anni inventata come proiezione
        assert "non è stimabile" in out or "non determinabile" in out


def test_finance_guard_keeps_legit_numbers():
    for t in ["Il prezzo di listino è 500 euro.",
              "Hai dichiarato un fatturato di 2 milioni.",
              "Servono 3 mesi per completare il progetto.",
              "L'IVA è al 22%.",
              "Abbiamo perso 2 clienti."]:
        assert finance_guard.sanitize(t) == t, t


# ── Prompt consolidato (review consolidamento) ───────────────────────────────────────────
def test_prompt_consolidamento_ragionamento():
    p = _prompt()
    assert "PRIORITÀ ASSOLUTA" in p and "Non è possibile stimare" in p     # #1
    assert "FATTI ≠ IPOTESI ≠ ASSUNZIONI" in p                            # #2
    assert "METTI IN DISCUSSIONE IL FRAMING" in p                         # #4
    assert "INCLUSO «NON FARE NULLA»" in p                                # #5
    assert "SPIEGAZIONI ALTERNATIVE" in p and "confirmation-bias" in p    # #6
    assert "CONCLUSIONI DECISIVE" in p                                    # #9
    assert "COSA POTREBBE FARMI CAMBIARE" in p                            # #10
