"""Modalità AUDIT GUIDATO (review "audit GDPR guidato" — conversazione modello app outfit):
«è tutto in regola?» → prima risposta completa a scenari (Caso A/Caso B), poi una domanda
per turno in ordine di impatto con valutazione incrementale, tabella-semaforo che cresce,
correzione delle auto-qualificazioni del cliente, chiusura con punteggi separati e
conclusione condizionata.
"""
import sys
import types
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

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

from app.lib import privacy_case, signals  # noqa: E402

_OUTFIT = ("ho creato una nuova applicazione che genera outfit dalle foto degli utenti. "
           "vorrei capire se secondo il gpdr è tutto in regola")


# ── rilevazione della richiesta di conformità ────────────────────────────────────────────
def test_compliance_check_detected():
    for t in [_OUTFIT, "il mio e-commerce è a norma?", "siamo conformi al GDPR?",
              "voglio un audit privacy della mia app", "come mi metto in regola con l'IVA?"]:
        assert signals.is_compliance_check(t), t


def test_non_compliance_not_detected():
    for t in ["come riduco i tempi di incasso?", "meglio SRL o ditta individuale?",
              "un cliente non paga, cosa faccio?", "che KPI monitoro per il magazzino?"]:
        assert not signals.is_compliance_check(t), t


# ── prompt: sezione statica + richiamo deterministico ────────────────────────────────────
def _prompt(text):
    from app.lib.prompts import build_system_prompt_v2
    return build_system_prompt_v2([], {"messages": [{"role": "user", "content": text}],
                                       "collected_data": {}}, required_fields_hint="")


def test_audit_mode_section_always_present():
    p = _prompt("come riduco i tempi di incasso?")
    assert "MODALITÀ AUDIT GUIDATO" in p
    assert "UNA DOMANDA PER TURNO" in p
    assert "tabella-semaforo" in p
    assert "SCENARI alternativi" in p                        # Caso A / Caso B
    assert "il tetto delle 8-10 righe della consulenza immediata qui NON si applica" in p
    assert "il limite dei 6 turni NON si applica" in p
    assert "AUTO-qualificazioni" in p                        # correggere in entrambe le direzioni
    assert "punteggi SEPARATI per dimensione" in p
    assert "basandomi esclusivamente su quello che mi hai mostrato" in p


def test_audit_reminder_injected_only_on_compliance_request():
    assert "RICHIESTA DI CONFORMITÀ RILEVATA" in _prompt(_OUTFIT)
    assert "RICHIESTA DI CONFORMITÀ RILEVATA" not in _prompt("come riduco i tempi di incasso?")


def test_incremental_audit_behaviors_in_prompt():
    p = _prompt(_OUTFIT)
    assert "questa è probabilmente la più importante di tutta l'analisi" in p
    assert "questa è la prima criticità concreta che ho trovato" in p
    assert "ANTICIPA la risposta più probabile" in p
    assert "OPZIONI di risposta" in p
    assert "MICRO-CONCRETE" in p                              # riscrivi tu checkbox/consensi


# ── modulo privacy: sequenza d'audit specifica per i casi immagini/AI ────────────────────
def test_privacy_hint_audit_sequence():
    h = privacy_case.privacy_hint(_OUTFIT)
    assert "MODALITÀ AUDIT GUIDATO su questo caso" in h
    assert "LA domanda più importante: decide l'art. 9" in h  # embedding/template
    assert "retention" in h and "minori" in h
    assert "mai preselezionati" in h                          # consensi separati
    assert "fascia d'età meglio dell'età esatta" in h         # minimizzazione concreta
    assert "la FOTO in sé può contenerle" in h                # sensibili implicite nell'immagine
    assert "artt. 15/17" in h
    assert "conformità tecnica vs" in h                       # punteggi separati


def test_outfit_case_activates_both_blocks():
    p = _prompt(_OUTFIT)
    assert "CASO PRIVACY/AI SU IMMAGINI" in p                 # frame giuridico
    assert "RICHIESTA DI CONFORMITÀ RILEVATA" in p            # modalità audit
