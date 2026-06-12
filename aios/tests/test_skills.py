"""Tests for SkillLibrary loader."""

import pytest

from aios.skills import SkillLibrary


def test_lists_marketing_skills():
    lib = SkillLibrary()
    names = lib.names()
    assert "content-creation" in names
    assert "brand-voice" in names
    assert len(names) >= 30


def test_load_returns_skill_text():
    lib = SkillLibrary()
    text = lib.load("content-creation")
    assert isinstance(text, str) and len(text) > 100


def test_load_unknown_raises():
    lib = SkillLibrary()
    with pytest.raises(KeyError):
        lib.load("does-not-exist")


def test_menu_has_name_and_description():
    lib = SkillLibrary()
    menu = lib.menu()
    assert "content-creation" in menu
    # description text from frontmatter should appear for at least one skill
    assert "marketing" in menu.lower() or "content" in menu.lower()
    # menu should be one line per skill, reasonably compact
    assert menu.count("\n") >= 30
