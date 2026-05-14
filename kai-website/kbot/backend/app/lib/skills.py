"""Skill loader, mirroring kai-website/lib/skills/loader.ts.

Layout per skill:
    <SKILLS_DIR>/<name>/SKILL.md         (required)
    <SKILLS_DIR>/<name>/references/*.md  (optional, sorted by filename)

Missing skills are silently skipped with a warning log.
"""
from __future__ import annotations

import logging
from functools import lru_cache
from pathlib import Path
from typing import Iterable, List, Optional

from ..settings import SKILLS_DIR

log = logging.getLogger(__name__)


def _skill_root(name: str) -> Path:
    return SKILLS_DIR / name


def list_available_skills() -> List[str]:
    if not SKILLS_DIR.exists():
        return []
    return sorted(p.name for p in SKILLS_DIR.iterdir() if p.is_dir() and not p.name.startswith("."))


@lru_cache(maxsize=512)
def load_skill(name: str, include_references: bool = True, max_chars: Optional[int] = None) -> Optional[str]:
    root = _skill_root(name)
    skill_md = root / "SKILL.md"
    if not skill_md.exists():
        # also accept legacy lowercase
        alt = root / "skills.md"
        if alt.exists():
            skill_md = alt
        else:
            log.warning("Skill not found: %s (looking at %s)", name, root)
            return None

    try:
        parts = [skill_md.read_text(encoding="utf-8")]
    except (OSError, UnicodeDecodeError) as exc:
        log.warning("Failed reading SKILL.md for %s: %s", name, exc)
        return None

    if include_references:
        refs_dir = root / "references"
        if refs_dir.is_dir():
            for ref_path in sorted(refs_dir.glob("*.md")):
                try:
                    parts.append(ref_path.read_text(encoding="utf-8"))
                except (OSError, UnicodeDecodeError) as exc:
                    log.warning("Skipping non-UTF8 reference %s: %s", ref_path, exc)
                    continue

    content = "\n\n".join(p.strip() for p in parts if p.strip())
    if max_chars and len(content) > max_chars:
        content = content[: max_chars - 1].rstrip() + "…"
    return content


def load_skill_bundle(
    names: Iterable[str],
    *,
    max_total_chars: int,
    max_per_skill_chars: int = 5500,
    include_references: bool = False,
) -> str:
    """Build a single string with header per skill, capped to total chars."""
    pieces: List[str] = []
    total = 0
    for name in names:
        if not name:
            continue
        body = load_skill(name, include_references=include_references, max_chars=max_per_skill_chars)
        if not body:
            continue
        header = f"\n{'=' * 60}\n# SKILL: {name}\n{'=' * 60}\n\n"
        chunk = header + body
        if total + len(chunk) > max_total_chars:
            remaining = max_total_chars - total
            if remaining > len(header) + 200:
                chunk = chunk[:remaining].rstrip() + "…"
                pieces.append(chunk)
                total += len(chunk)
            break
        pieces.append(chunk)
        total += len(chunk)
    return "".join(pieces)
