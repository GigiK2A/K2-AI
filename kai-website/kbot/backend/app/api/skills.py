"""GET /api/kbot/skills — list available skills (name + short description).

Reads each skill's SKILL.md, parses YAML front-matter (or first non-empty
markdown line) to extract a short description. Cached in-process.
"""
from __future__ import annotations

import logging
import re
from functools import lru_cache
from pathlib import Path
from typing import List

from fastapi import APIRouter

from ..lib.skills import list_available_skills
from ..settings import SKILLS_DIR

router = APIRouter()
log = logging.getLogger(__name__)


_FRONTMATTER_RE = re.compile(r"^---\s*\n(.*?)\n---\s*\n", re.DOTALL)
_DESC_RE = re.compile(r"^description\s*:\s*(.+?)\s*$", re.MULTILINE | re.IGNORECASE)


def _short_desc(name: str) -> str:
    root: Path = SKILLS_DIR / name
    skill_md = root / "SKILL.md"
    if not skill_md.exists():
        alt = root / "skills.md"
        if alt.exists():
            skill_md = alt
        else:
            return ""
    try:
        text = skill_md.read_text(encoding="utf-8", errors="ignore")
    except OSError:
        return ""

    # Try YAML front-matter description.
    fm = _FRONTMATTER_RE.match(text)
    if fm:
        m = _DESC_RE.search(fm.group(1))
        if m:
            return m.group(1).strip().strip('"\'')[:240]

    # Fallback: first non-empty paragraph that is not a heading.
    body = text[fm.end():] if fm else text
    for raw in body.splitlines():
        line = raw.strip()
        if not line or line.startswith("#") or line.startswith("---"):
            continue
        return line[:240]
    return ""


@lru_cache(maxsize=1)
def _build_index() -> List[dict]:
    items = []
    for name in list_available_skills():
        items.append({"name": name, "description": _short_desc(name)})
    return items


@router.get("/skills")
def list_skills():
    return {"skills": _build_index()}
