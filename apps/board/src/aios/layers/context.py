from __future__ import annotations

from aios.founder import FounderModel


class ContextLayer:
    """Strato (1) Contesto: chi siamo (Founder Model) + conoscenza di dominio."""

    def __init__(self, founder: FounderModel, knowledge: list[str] | None = None) -> None:
        self.founder = founder
        self.knowledge = list(knowledge or [])

    def assemble(self) -> str:
        out = self.founder.to_prompt()
        if self.knowledge:
            out += "\n\n# CONTESTO / CONOSCENZA\n" + "\n".join(f"- {k}" for k in self.knowledge)
        return out
