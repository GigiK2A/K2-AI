"""SUITE DI REGRESSIONE dell'intake — gli scenari canonici degli stress test di Luca.

Ogni caso qui è un bug REALE trovato da un eval (lug 2026) e già costato un giro di
produzione. La suite è deterministica (nessuna chiamata LLM): verifica prompt, gate,
segnali, routing e enforcement. Se un refactor rompe uno di questi, il danno è già
noto — vedi il commento sul caso.
"""
from __future__ import annotations

import json
import types
import sys

import pytest

# shim leggeri per ambienti senza le dipendenze runtime (il codice sotto test è puro)
for _name, _attrs in (("dotenv", {"load_dotenv": lambda *a, **k: False}),):
    if _name not in sys.modules:
        _m = types.ModuleType(_name)
        [setattr(_m, k, v) for k, v in _attrs.items()]
        sys.modules[_name] = _m
try:  # pragma: no cover — l'import del NOME può riuscire (namespace pkg vuoto):
    from supabase import Client as _ProbeClient  # noqa: F401 — serve il simbolo vero
except Exception:  # pragma: no cover
    _m = types.ModuleType("supabase")
    _m.Client, _m.create_client = object, (lambda *a, **k: None)
    sys.modules["supabase"] = _m

from app.lib import signals, catalog  # noqa: E402
from app.lib.prompts import (  # noqa: E402
    build_system_prompt_v2, extract_summary, strip_summary_block,
    extract_diagnosi, strip_diagnosi_block,
)
from app.lib.readiness import required_fields_hint  # noqa: E402
from app.lib import quality_gate as qg  # noqa: E402


def _sess(msgs, collected=None):
    return {"messages": msgs, "collected_data": collected or {}}


def _u(t):
    return {"role": "user", "content": t}


def _a(t):
    return {"role": "assistant", "content": t}


class FakeResp:
    def __init__(self, text):
        self.content = [types.SimpleNamespace(type="text", text=text)]


class FakeClient:
    def __init__(self, answers):
        self.answers = list(answers)
        self.calls = 0

    @property
    def messages(self):
        return self

    def create(self, **kw):
        self.calls += 1
        return FakeResp(self.answers.pop(0))


# ---------------------------------------------------------------------------
# 1. SUMMARY: estrazione inline E multiriga (eval "report 0/10" — root cause:
#    gpt-oss emette il blocco inline, il vecchio regex pretendeva \n → mai estratto)
# ---------------------------------------------------------------------------

def test_summary_inline_e_multiriga():
    inline = 'Ok.\nCONSULENZA_SUMMARY_START {"reportType":"X"} CONSULENZA_SUMMARY_END'
    multi = 'Ok.\nCONSULENZA_SUMMARY_START\n{"reportType":"Y"}\nCONSULENZA_SUMMARY_END'
    assert extract_summary(inline) == {"reportType": "X"}
    assert extract_summary(multi) == {"reportType": "Y"}
    assert "CONSULENZA_SUMMARY" not in strip_summary_block(inline)


# ---------------------------------------------------------------------------
# 2. GUARDIA NEGAZIONE (eval "conto in rosso": il fallback forzava il report
#    proprio quando il bot dichiarava correttamente l'insufficienza)
# ---------------------------------------------------------------------------

def test_readiness_negata_non_forza():
    assert signals.is_ready_declared("Ho informazioni sufficienti: sto generando il report")
    assert not signals.is_ready_declared("Non ho ancora informazioni sufficienti per una diagnosi")
    assert not signals.is_ready_declared("Mancano ancora dati per valutare")
    assert not signals.is_ready_declared("Le informazioni non sono sufficienti: prima devo chiarire")


# ---------------------------------------------------------------------------
# 3. ROUTING M&A → MABoost (analisi DECISIONALE della valutazione, non LegalBoost né
#    FinanceBoost): la domanda è "il prezzo è corretto / procedo / come la valuto",
#    cioè una decisione di acquisizione. Fix del test acquisizione (lug 2026).
# ---------------------------------------------------------------------------

@pytest.mark.parametrize("testo,atteso", [
    ("Mi hanno proposto di acquistare un concorrente locale. Chiedono 500.000 euro, ha perso "
     "clienti e ha problemi di liquidità. Il prezzo è corretto?", "checkup_ma"),
    ("Vorrei rilevare un'azienda, l'EBITDA è crollato. Procedo?", "checkup_ma"),
    ("Ho ricevuto una proposta di acquisizione del concorrente, come la valuto?", "checkup_ma"),
    # non-regressione: il caso finance PURO (nessun deal) resta finance
    ("La mia azienda ha problemi di liquidità e margini in calo, analisi di bilancio.", "checkup_finanziario"),
])
def test_routing_ma_vs_finance(testo, atteso):
    r = catalog.suggest_boost({}, user_text=testo)
    assert r and r["id"] == atteso


# ---------------------------------------------------------------------------
# 4. PROMPT: mai chiedere all'utente di fare il consulente (eval scalabilità:
#    "che tipo di report vuoi?" era ISTRUITO nel prompt cold-start)
# ---------------------------------------------------------------------------

def test_prompt_non_chiede_di_fare_il_consulente():
    p = build_system_prompt_v2([], _sess([_u("clima aziendale pessimo, dimissioni in aumento")]))
    assert "vuoi che produciamo insieme" not in p          # la vecchia domanda-esempio
    assert "NON CHIEDERE ALL'UTENTE DI FARE IL CONSULENTE" in p
    assert "DEDUCI TU il documento" in p


def test_prompt_stop_rule_bilanciata_e_antioscillazione():
    p = build_system_prompt_v2([], _sess([_u("x")]))
    assert "STOP RULE" in p and "IPOTESI ALTERNATIVE" in p
    assert "ANTI-OSCILLAZIONE" in p and "la raccolta dati è CHIUSA" in p
    assert "MAXIMUM INSIGHT, MINIMUM QUESTIONS" in p
    # caso legale: scala di escalation + profondità proporzionata (eval telefonata indiretta)
    assert "scala di escalation" in p and "Triage legale preliminare" in p


# ---------------------------------------------------------------------------
# 5. GATE URGENZA (eval crisi continuità: domanda ad alto valore, non fatturato)
# ---------------------------------------------------------------------------

def test_gate_urgenza_e_comprensione():
    crisi = build_system_prompt_v2([], _sess(
        [_u("Il responsabile è ricoverato, stipendi tra dieci giorni, nessuno ha accesso ai conti.")]))
    assert "FASE INTERVISTA (URGENZA)" in crisi
    normale = build_system_prompt_v2([], _sess([_u("Ho un problema col mio ecommerce.")]))
    assert "FASE COMPRENSIONE" in normale and "URGENZA)" not in normale
    # dal 2° turno utente il gate deterministico sparisce (governa la Stop Rule)
    t2 = build_system_prompt_v2([], _sess([_u("a"), _a("b"), _u("c")]))
    assert "FASE COMPRENSIONE" not in t2 and "FASE INTERVISTA" not in t2


# ---------------------------------------------------------------------------
# 6. TEMPLATE ≠ CONSULENZA (eval scalabilità: ragione sociale come barriera)
# ---------------------------------------------------------------------------

def test_required_fields_hint_template_vs_analisi():
    campi = [{"id": "ragione_sociale", "label": "Ragione sociale", "obbligatorio": True},
             {"id": "competitor", "label": "Competitor", "obbligatorio": True}]
    h = required_fields_hint(campi, "StrategyBoost — Strategia e crescita")
    assert "DATI DI ANALISI" in h and "INTESTARE" in h
    assert "PRELIMINARE" in h                 # campo mancante NON blocca il summary
    assert "DEVI raccoglierli" not in h       # il vecchio obbligo bloccante
    assert "StrategyBoost" not in h           # bug 18 lug: mai il nome interno del boost


def test_required_fields_hint_consulenza_ricca_sopprime_analisi():
    """Bug routing 18 lug: dopo una consulenza reale, il template NON deve far chiedere i
    campi di analisi (competitor, obiettivi…) — la consulenza è la fonte del report."""
    campi = [{"id": "ragione_sociale", "label": "Ragione sociale", "obbligatorio": True},
             {"id": "competitor", "label": "Competitor", "obbligatorio": True},
             {"id": "obiettivo_strategico", "label": "Obiettivo", "obbligatorio": True}]
    h = required_fields_hint(campi, "StrategyBoost — Strategia e crescita", consulenza_ricca=True)
    assert "StrategyBoost" not in h                       # niente nome interno
    assert "DATI DI ANALISI:" not in h                    # niente richiesta campi analisi
    assert "consulenza svolta è la FONTE" in h            # la consulenza è la fonte
    assert "nome dell'azienda" in h.lower()               # resta solo il nome per intestare


# ---------------------------------------------------------------------------
# 7. QUALITY GATE: enforcement + anti-oscillazione (eval e-commerce: "annuncia
#    il report poi altra domanda" = il critico rimandava in intake all'infinito)
# ---------------------------------------------------------------------------

_DRAFT = ('Ho informazioni sufficienti: sto generando il report.\n'
          'CONSULENZA_SUMMARY_START {"reportType":"x"} CONSULENZA_SUMMARY_END')
_PREMATURO = json.dumps({"premature_summary": True, "assertive_diagnosis": False,
                         "drastic_actions": False, "depth_mismatch": False,
                         "missing_question": "Gli addebiti sono riconosciuti?",
                         "rewrite": "Prima devo chiarire la natura dei movimenti."})


def test_quality_gate_prematuro_bloccato_a_inizio_intake():
    out = qg.review(FakeClient([_PREMATURO]), "m", [_u("il conto è in rosso")], _DRAFT)
    assert "CONSULENZA_SUMMARY" not in out and "riconosciuti" in out


def test_quality_gate_antioscillazione_dopo_5_turni():
    long_conv = [_u("1"), _a("x"), _u("2"), _a("x"), _u("3"), _a("x"), _u("4"), _a("x"), _u("5")]
    out = qg.review(FakeClient([_PREMATURO]), "m", long_conv, _DRAFT)
    assert "CONSULENZA_SUMMARY_START" in out    # il critico non può più rimandare in intake


def test_quality_gate_fail_open():
    assert qg.review(FakeClient(["boh"]), "m", [_u("a")], _DRAFT) == _DRAFT


def test_quality_gate_preserva_diagnosi_nel_rewrite():
    draft = (_DRAFT + '\nDIAGNOSI_STATO_START {"ipotesi":[{"t":"a","s":"aperta"}],"manca":null} '
             'DIAGNOSI_STATO_END')
    out = qg.review(FakeClient([_PREMATURO]), "m", [_u("il conto è in rosso")], draft)
    assert "DIAGNOSI_STATO_START" in out        # la memoria di lavoro non si azzera


# ---------------------------------------------------------------------------
# 8. STATO DIAGNOSTICO (miglioria comportamentale: ipotesi fuori dalla "testa")
# ---------------------------------------------------------------------------

def test_diagnosi_estrazione_e_iniezione():
    t = ('Qual è il DSO?\nDIAGNOSI_STATO_START {"ipotesi":[{"t":"crisi di incasso","s":"aperta"}],'
         '"manca":"aging crediti"} DIAGNOSI_STATO_END')
    d = extract_diagnosi(t)
    assert d and d["ipotesi"][0]["t"] == "crisi di incasso"
    assert "DIAGNOSI_STATO" not in strip_diagnosi_block(t)
    p = build_system_prompt_v2([], _sess([_u("a")], {"diagnosi": d}))
    assert "STATO DIAGNOSTICO" in p and "crisi di incasso" in p and "aging crediti" in p
    # l'istruzione a emettere il blocco c'è SEMPRE
    assert "DIAGNOSI_STATO_START" in p


# ---------------------------------------------------------------------------
# 9. STANDARD CONSULENTE SENIOR presente nei prompt di generazione 8e
#    (spec strategico: insight/decision support/score disciplinati)
# ---------------------------------------------------------------------------

def test_senior_standard_nell_8e():
    import pathlib
    src = (pathlib.Path(__file__).resolve().parents[3] / "k2a-8e" / "app" / "llm.py").read_text()
    for marker in ("STANDARD CONSULENTE SENIOR", "COSA PROBABILMENTE NON VEDI",
                   "ESEMPIO DI TAGLIO", "MEGLIO NESSUN NUMERO"):
        assert marker in src, marker
