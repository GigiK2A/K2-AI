"""Regression tests for the K-BOT scope fixes.

Covers two bugs from the Instagram-calendar chat:
1. Skill routing was driven by the analyzed site's *domain* (engineering) instead
   of the user's *intent* (a social content calendar) → wrong skills loaded.
2. The report classifier had no 'contenuti' category, so a calendar request was
   shoved into the 'marketing' analysis profile → no actual post topics.
"""
from __future__ import annotations

import importlib.util
import os

import pytest

_BACKEND = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def _load_standalone(rel_path: str, name: str):
    """Load a single module file without importing the whole app package."""
    spec = importlib.util.spec_from_file_location(name, os.path.join(_BACKEND, rel_path))
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


svc = _load_standalone("app/lib/services.py", "kbot_services_under_test")


def _calendar_session() -> dict:
    return {
        "collected_data": {
            "analyzed_urls": [
                {
                    "url": "https://studioassociatoevolution.com",
                    "title": "Studio Associato Evolution",
                    "summary": (
                        "Studio di ingegneria: energie rinnovabili, edilizia, "
                        "progettazione impianti, project management, direzione lavori."
                    ),
                }
            ]
        },
        "messages": [
            {"role": "user", "content": "guida dei contenuti per i miei post instagram, dal mio sito"},
            {"role": "assistant", "content": "ok"},
            {"role": "user", "content": "voglio proprio un calendario con i contenuti"},
            {"role": "user", "content": "post di formazione e vendita dei servizi, marketing ma non troppo"},
            {"role": "user", "content": "3 mesi, lunedi mercoledi e venerdi"},
        ],
    }


def test_content_calendar_intent_beats_engineering_site():
    session = _calendar_session()
    assert svc.infer_service_id_from_session(session) == "P11"
    skills = svc.resolve_skills_for_session(session)
    assert "campaign-plan" in skills
    assert "content-creation" in skills
    # Engineering skills from the site domain must NOT leak in.
    assert not any(
        s in skills for s in ("verifica-statica", "progettista-strutturale", "diagnosi-energetica-ege")
    )


def test_pure_engineering_request_still_routes_to_p04():
    eng = {
        "collected_data": {},
        "messages": [
            {"role": "user", "content": "mi serve una verifica statica strutturale e la direzione lavori del cantiere"}
        ],
    }
    assert svc.infer_service_id_from_session(eng) == "P04"


def test_empty_session_returns_none():
    assert svc.infer_service_id_from_session({"collected_data": {}, "messages": []}) is None


# --- Bug: le skill non venivano chiamate per i Boost (service_id "checkup_*") ---
# I Boost non sono pillar (P01-P20): get_service(checkup_*) → None → si caricava
# solo la BASE_SKILL. Ora un boost id risolve le sue skill specialistiche in modo
# DETERMINISTICO (senza dipendere dal testo della conversazione).
def test_boost_id_resolves_specialist_skills_deterministically():
    # nessun messaggio: la risoluzione NON deve dipendere dalla conversazione
    sess = {"collected_data": {"service_id": "checkup_controllo"}, "messages": []}
    skills = svc.resolve_skills_for_session(sess)
    assert skills != [svc.BASE_SKILL], "un boost non deve ricadere sulla sola BASE_SKILL"
    assert "cruscotto-direzionale" in skills  # skill del pillar P09 (Controllo di Gestione)
    assert svc.BASE_SKILL in skills           # la base resta sempre in testa


def test_boost_ma_gets_dedicated_ma_skills():
    # M&A non è un pillar: deve avere skill dedicate (DD + societario + finance)
    sess = {"collected_data": {"service_id": "checkup_ma"}, "messages": []}
    skills = svc.resolve_skills_for_session(sess)
    assert "flusso-due-diligence-mna" in skills
    assert "diritto-societario-italiano" in skills
    assert "corporate-finance" in skills


def test_boost_id_is_case_insensitive():
    # message.py normalizza il service_id in MAIUSCOLO: il fix deve reggerlo
    sess = {"collected_data": {"service_id": "CHECKUP_FINANZIARIO"}, "messages": []}
    skills = svc.resolve_skills_for_session(sess)
    assert "analisi-bilancio-pmi" in skills
    assert skills != [svc.BASE_SKILL]


def test_pillar_and_free_chat_resolution_unchanged():
    # regressione: P-id e chat libera restano invariati
    p09 = svc.resolve_skills_for_session({"collected_data": {"service_id": "P09"}})
    assert "cruscotto-direzionale" in p09
    empty = svc.resolve_skills_for_session({"collected_data": {}, "messages": []})
    assert empty == [svc.BASE_SKILL]


# --- Classifier / profile tests (need the analysis module → heavy deps in CI) ---
# These skip gracefully where anthropic/supabase aren't installed; the routing
# tests above run everywhere (services.py is stdlib-only).
try:  # pragma: no cover - import guard
    from app.lib.analysis import _classify_report, _build_report_profile  # type: ignore
    _HAVE_ANALYSIS = True
except Exception:  # pragma: no cover
    _HAVE_ANALYSIS = False


@pytest.mark.skipif(not _HAVE_ANALYSIS, reason="analysis module deps unavailable")
@pytest.mark.parametrize(
    "report_type,expected",
    [
        ("calendario editoriale instagram", "contenuti"),
        ("piano contenuti social", "contenuti"),
        ("analisi marketing funnel", "marketing"),
        ("audit seo del sito", "seo"),
        ("analisi di bilancio", "bilancio"),
    ],
)
def test_classifier_recognizes_content(report_type, expected):
    assert _classify_report(report_type) == expected


@pytest.mark.skipif(not _HAVE_ANALYSIS, reason="analysis module deps unavailable")
def test_contenuti_profile_has_full_calendar():
    profile = _build_report_profile("calendario editoriale")
    assert profile["category"] == "contenuti"
    blocks = profile["required_blocks"]
    assert "Calendario editoriale" in blocks
    # The 8-row array cap must be explicitly overridden for the calendar.
    assert "ECCEZIONE" in blocks
