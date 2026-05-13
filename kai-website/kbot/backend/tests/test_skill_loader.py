"""Tests for multi-root skill loading and report premium fixes."""
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from app.main import (
    get_skill_packs,
    find_relevant_skills,
    report_sources_are_ready,
    build_report_not_ready_message,
    build_report_technical_error_message,
    SKILLS_ROOTS,
)


# ── Skill loader ────────────────────────────────────────────────────────────

def test_skills_roots_is_list():
    """SKILLS_ROOTS must be a list of paths, not a single path."""
    assert isinstance(SKILLS_ROOTS, list)
    assert len(SKILLS_ROOTS) >= 2


def test_hospitality_root_exists():
    """The hospitality skills folder must exist on disk."""
    hosp_root = next((r for r in SKILLS_ROOTS if "hospitality" in str(r)), None)
    assert hosp_root is not None, "No hospitality root in SKILLS_ROOTS"
    assert hosp_root.exists(), f"Hospitality root missing: {hosp_root}"


def test_get_skill_packs_returns_hospitality_skills():
    """Pool must contain at least the 4 core hospitality skills."""
    packs = get_skill_packs()
    names = {p["name"] for p in packs}
    core = {
        "orchestratore-hospitality",
        "check-host-express",
        "flusso-hostboost-ricettive",
        "property-management-revenue",
    }
    missing = core - names
    assert not missing, f"Missing hospitality skills: {missing}"


def test_get_skill_packs_retains_general_skills():
    """Pool must still contain at least one general P0x skill."""
    packs = get_skill_packs()
    names = {p["name"] for p in packs}
    general = [n for n in names if n.lower().startswith("p0") or n.lower().startswith("p1")]
    assert general, "General P0x/P1x skills not found in pool"


def test_skill_packs_have_required_keys():
    """Every pack must have id, name, markdown."""
    packs = get_skill_packs()
    assert packs, "No skill packs loaded"
    for pack in packs:
        assert "id" in pack
        assert "name" in pack
        assert "markdown" in pack
        assert len(pack["markdown"]) > 0, f"Empty markdown in pack: {pack['name']}"


def test_find_relevant_skills_accepts_preloaded_packs():
    """find_relevant_skills must accept pre-loaded packs to avoid double I/O."""
    packs = get_skill_packs()
    result = find_relevant_skills("RevPAR agriturismo", max_items=3, packs=packs)
    assert result, "Expected at least one skill"
    # All returned packs must come from the provided list
    pack_ids = {p["id"] for p in packs}
    for r in result:
        assert r["id"] in pack_ids


# ── report_sources_are_ready ─────────────────────────────────────────────────

def test_report_sources_are_ready_blocks_with_no_data():
    """No files, no history, short input → not ready."""
    ready, reason = report_sources_are_ready([], user_input="ciao", history=[])
    assert not ready
    assert reason


def test_report_sources_are_ready_passes_with_long_input():
    """Input >100 chars is enough to proceed."""
    long_input = "a" * 101
    ready, _ = report_sources_are_ready([], user_input=long_input, history=[])
    assert ready


def test_report_sources_are_ready_passes_with_numeric_data():
    """Short message with 3+ numbers (KPI data) is enough to proceed."""
    kpi_input = "RevPAR 42€, occupancy 58%, ADR 72€, apertura 240gg, 70% Booking.com"
    ready, _ = report_sources_are_ready([], user_input=kpi_input, history=[])
    assert ready


def test_report_sources_are_ready_passes_with_history():
    """Sufficient chat history (>300 chars total user content) → ready."""
    history = [
        {"role": "user", "content": "x" * 150},
        {"role": "assistant", "content": "y" * 200},
        {"role": "user", "content": "z" * 160},
    ]
    ready, _ = report_sources_are_ready([], user_input="ok", history=history)
    assert ready


def test_report_sources_are_ready_short_history_blocked():
    """Short history (<300 chars) with short input → not ready."""
    history = [{"role": "user", "content": "ciao"}]
    ready, _ = report_sources_are_ready([], user_input="ok", history=history)
    assert not ready


# ── Error messages ───────────────────────────────────────────────────────────

def test_build_report_not_ready_message_no_bilancio_word():
    """Data-missing message must not say 'bilancio' (wrong for hospitality context)."""
    msg = build_report_not_ready_message("non ho dati sufficienti")
    assert "bilancio" not in msg.lower()


def test_build_report_technical_error_message_distinct():
    """Technical error message must differ from data-missing message."""
    data_msg = build_report_not_ready_message("dati mancanti")
    tech_msg = build_report_technical_error_message("report troppo breve")
    assert data_msg != tech_msg
    assert "tecnico" in tech_msg.lower() or "problema" in tech_msg.lower()
