"""SkillLibrary loader for marketing skills."""

from __future__ import annotations

import re
from pathlib import Path

_SKILLS_DIR = Path(__file__).parent / "skills"


def _parse_description(text: str) -> str:
    """Extract description from YAML frontmatter or fallback to first line."""
    # YAML frontmatter between leading --- ... ---
    m = re.match(r"^---\s*\n(.*?)\n---\s*\n", text, re.DOTALL)
    if m:
        fm = m.group(1)
        d = re.search(r"^description:\s*(.+)$", fm, re.MULTILINE)
        if d:
            return d.group(1).strip().strip('"').strip("'")
        n = re.search(r"^name:\s*(.+)$", fm, re.MULTILINE)
        if n:
            return n.group(1).strip()
    # fallback: first non-empty, non-heading line
    for line in text.splitlines():
        line = line.strip()
        if line and not line.startswith("#") and line != "---":
            return line
    return ""


class SkillLibrary:
    """Loader for marketing skill files."""

    def __init__(self, base: Path | None = None) -> None:
        """Initialize SkillLibrary with optional custom base path."""
        self._base = base or _SKILLS_DIR

    def names(self) -> list[str]:
        """Return sorted list of available skill names."""
        return sorted(p.parent.name for p in self._base.glob("*/SKILL.md"))

    def load(self, name: str) -> str:
        """Load full text of a skill file."""
        f = self._base / name / "SKILL.md"
        if not f.is_file():
            raise KeyError(name)
        return f.read_text(encoding="utf-8")

    def describe(self, name: str) -> str:
        """Extract description from a skill."""
        return _parse_description(self.load(name))

    def menu(self) -> str:
        """Generate a formatted menu of all skills with descriptions."""
        lines = []
        for n in self.names():
            desc = _parse_description(self.load(n))
            desc = (desc[:140] + "…") if len(desc) > 140 else desc
            lines.append(f"- {n}: {desc}")
        return "\n".join(lines)
