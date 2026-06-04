from __future__ import annotations

import re

from aios.llm import LLM
from aios.skills import SkillLibrary

_SYSTEM = ("Crei nuove skill per l'AIOS K2 in stile Anthropic SKILL.md (frontmatter "
           "name+description, poi istruzioni). Rispondi SOLO JSON: "
           '{"name":"slug-kebab","skill_md":"---\\nname: ...\\ndescription: ...\\n---\\n<corpo>"}')


class DevelopmentLayer:
    """Strato (5) Sviluppo: crea nuove skill su misura, salvate nella libreria."""

    def __init__(self, *, llm: LLM, skills: SkillLibrary) -> None:
        self.llm = llm
        self.skills = skills

    def create_skill(self, descrizione: str) -> str:
        parsed = self.llm.complete_json(system=_SYSTEM, user="Richiesta: " + descrizione)
        name = re.sub(r"[^a-z0-9-]", "", str(parsed.get("name", "")).lower().replace(" ", "-"))
        body = parsed.get("skill_md", "")
        if not name or not body:
            raise ValueError("skill non valida dal modello")
        d = self.skills._base / name
        d.mkdir(parents=True, exist_ok=True)
        (d / "SKILL.md").write_text(body, encoding="utf-8")
        return name
