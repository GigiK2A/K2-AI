"""Adattamento al profilo del cliente (review): K2 stima quanto è tecnico/emotivo
l'interlocutore e calibra registro e profondità — un imprenditore non tecnico non va
sommerso di EBITDA/DCF; i dati tecnici arrivano tardi, dopo aver capito problema e persona.
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

from app.lib import client_profile as CP  # noqa: E402


# ── stima della tecnicità ────────────────────────────────────────────────────────────────
def test_non_technical_entrepreneur():
    # il caso del test: imprenditore anziano, linguaggio umano, nessun numero
    p = CP.estimate_client_profile(["Non sopporto più il mio socio e voglio uscire dalla società."])
    assert p["tecnicita"] == "bassa"
    assert p["emotivo"] is True


def test_technical_interlocutor():
    p = CP.estimate_client_profile(
        ["Vorrei valutare l'uscita: EBITDA 800k, PFN 1.2M, che multiplo EV/EBITDA applichiamo?"])
    assert p["tecnicita"] == "alta"


def test_neutral_defaults_when_empty():
    assert CP.estimate_client_profile([]) == {"tecnicita": "media", "emotivo": False}


def test_only_user_messages_count():
    # dai SOLO i messaggi utente (il chiamante filtra); qui verifichiamo che i termini
    # tecnici nel testo utente alzino la tecnicità
    p = CP.estimate_client_profile(["il cash flow è negativo e la marginalità è scesa al 4%"])
    assert p["tecnicita"] in ("media", "alta")


# ── vale per OGNI settore, non solo M&A/finanza ──────────────────────────────────────────
def test_adaptation_is_cross_domain():
    # legale, HR, vendite in linguaggio semplice → poco tecnico (va accompagnato)
    for msg in ("Un mio cliente non mi paga da mesi e non so cosa fare.",
                "Ho un dipendente che crea problemi e non so come gestirlo.",
                "Le vendite sono calate e non capisco perché."):
        assert CP.estimate_client_profile([msg])["tecnicita"] == "bassa", msg
    # interlocutore tecnico in ambito LEGALE (non finanziario) → tecnicità alzata
    p = CP.estimate_client_profile(
        ["Valuto la risoluzione del contratto per inadempimento: la clausola risolutiva "
         "espressa regge o rischio la prescrizione?"])
    assert p["tecnicita"] in ("media", "alta")


def test_emotional_detected_across_contexts():
    # la componente emotiva non è legata all'M&A
    assert CP.estimate_client_profile(["Con questo dipendente non ne posso più."])["emotivo"]
    assert CP.estimate_client_profile(["Sono esausto, litigo ogni giorno col mio socio."])["emotivo"]


# ── calibrazione (hint) ──────────────────────────────────────────────────────────────────
def test_hint_for_non_technical_avoids_jargon():
    h = CP.profile_hint({"tecnicita": "bassa", "emotivo": False})
    assert "parla SEMPLICE" in h
    assert "gergo" in h.lower() and "checklist" in h.lower()
    # cross-domain: non nomina solo il finanziario
    assert "legale" in h.lower() and "fiscale" in h.lower()


def test_hint_for_emotional_deepens_person():
    h = CP.profile_hint({"tecnicita": "media", "emotivo": True})
    assert "PERSONALE" in h and "in fretta" in h


def test_no_hint_for_technical_non_emotional():
    # interlocutore tecnico e non emotivo → default va bene → nessun blocco di rumore
    assert CP.profile_hint({"tecnicita": "alta", "emotivo": False}) == ""
    assert CP.profile_hint({"tecnicita": "media", "emotivo": False}) == ""


def test_hint_from_session_fail_open():
    assert CP.hint_from_session({"messages": [{"role": "user", "content": "non ne posso più"}]})
    assert CP.hint_from_session({}) == ""          # nessun messaggio → nessun blocco
    assert CP.hint_from_session(None) == ""        # fail-open


# ── wiring nel prompt ────────────────────────────────────────────────────────────────────
def test_prompt_calibrates_for_non_technical_client():
    from app.lib.prompts import build_system_prompt_v2
    sess = {"messages": [{"role": "user",
                          "content": "Non sopporto più il mio socio e voglio uscire."}],
            "collected_data": {}}
    p = build_system_prompt_v2([], sess, required_fields_hint="")
    assert "ADATTA AL PROFILO DELLA PERSONA" in p          # sezione sempre presente
    assert "parla SEMPLICE" in p                            # calibrazione dinamica iniettata
    assert "dimensione PERSONALE" in p


def test_prompt_no_calibration_noise_for_technical():
    from app.lib.prompts import build_system_prompt_v2
    sess = {"messages": [{"role": "user",
                          "content": "EBITDA 800k, PFN 1.2M, multiplo EV/EBITDA da applicare?"}],
            "collected_data": {}}
    p = build_system_prompt_v2([], sess, required_fields_hint="")
    assert "ADATTA AL PROFILO DELLA PERSONA" in p          # la regola generale resta
    assert "parla SEMPLICE" not in p                        # ma nessuna calibrazione "poco tecnico"
