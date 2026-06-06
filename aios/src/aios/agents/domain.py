from __future__ import annotations

import json
from dataclasses import dataclass, field
from typing import Any

from aios.autonomy import ActionType, AutonomyLevel
from aios.kernel import Kernel
from aios.founder import FounderModel
from aios.llm import LLM
from aios.tools import Tool

_SCHEMA = {"type": "object", "properties": {"proposte": {"type": "array", "items": {
    "type": "object", "properties": {
        "tipo": {"type": "string"}, "titolo": {"type": "string"},
        "contenuto": {"type": "string"}, "motivo": {"type": "string"},
        # Azione strutturata opzionale: eseguita SOLO all'approvazione (attuatore L1).
        "azione": {"type": "object", "properties": {
            "tabella": {"type": "string"}, "op": {"type": "string"},
            "match": {"type": "object"}, "dati": {"type": "object"}}}},
    "required": ["tipo", "titolo", "contenuto", "motivo"]}}}, "required": ["proposte"]}


@dataclass
class DomainConfig:
    name: str
    action: ActionType
    tool_name: str
    sensors: list           # list[tuple[str, dict]]
    system: str
    skill_focus: list = field(default_factory=list)
    knowledge_query: str = ""


@dataclass
class DomainResult:
    approval_ids: list
    proposals: list


def _as_dict_list(x) -> list[dict]:
    if isinstance(x, str):
        try:
            x = json.loads(x)
        except Exception:
            return []
    return [i for i in x if isinstance(i, dict)] if isinstance(x, list) else []


class DomainAgent:
    """Agente generico di dominio: legge i sensori configurati, applica contesto
    (Founder Model + knowledge + skill), propone, e all'approvazione scrive un
    deliverable in aios_deliverables. Riusa kernel/autonomia/skill condivisi."""

    def __init__(self, *, kernel: Kernel, llm: LLM, founder: FounderModel,
                 config: DomainConfig, skills: Any = None, knowledge: Any = None,
                 deliverable_client: Any = None, actor: str | None = None) -> None:
        # Store _dclient FIRST — the tool closure reads it at call time via self._dclient
        self._dclient = deliverable_client
        self.k = kernel
        self.llm = llm
        self.founder = founder
        self.cfg = config
        self.skills = skills
        self.knowledge = knowledge
        self.actor = actor or f"{config.name}_agent"
        if config.tool_name not in self.k.tools.names():
            self.k.register_tool(self._propose_tool())
        self.k.policy.set_level(config.action, AutonomyLevel.L1_PROPOSE)
        self.k.policy.set_cap(config.action, AutonomyLevel.L1_PROPOSE)

    def _propose_tool(self) -> Tool:
        dominio = self.cfg.name

        def _run(**payload):
            if self._dclient is not None:
                self._dclient.insert("aios_deliverables", {
                    "dominio": dominio, "tipo": payload.get("tipo"),
                    "titolo": payload.get("titolo"), "contenuto": payload.get("contenuto"),
                    "motivo": payload.get("motivo"), "stato": "approvato"})
            out = {"accettata": True, **payload}
            # Attuatore L1: se la proposta porta un'azione strutturata, eseguila ORA
            # (siamo già nel path di approvazione umana). Allowlist + no delete/denaro.
            azione = payload.get("azione")
            if azione and self._dclient is not None:
                try:
                    from aios.actuator import apply_action
                    out["attuatore"] = apply_action(self._dclient, azione)
                except Exception as exc:
                    out["attuatore"] = {"ok": False, "errore": str(exc)}
            return out

        return Tool(name=self.cfg.tool_name, action_type=self.cfg.action, run=_run)

    def _read(self, name, **a):
        return self.k.execute(name, actor=self.actor, args=a).result

    def _context(self) -> str:
        out = self.founder.to_prompt()
        if self.knowledge and self.cfg.knowledge_query:
            hits = self.knowledge.search(self.cfg.knowledge_query, k=5)
            if hits:
                out += "\n\n# CONOSCENZA K2-AI\n" + "\n".join(f"- {h}" for h in hits)
        if self.skills:
            for n in self.cfg.skill_focus:
                try:
                    out += f"\n\n## SKILL: {n}\n" + self.skills.load(n)[:700]
                except KeyError:
                    pass
        return out

    def run(self) -> DomainResult:
        data = {}
        names = self.k.tools.names()
        for tool, args in self.cfg.sensors:
            if tool in names:
                data[tool] = self._read(tool, **args)
        user = (self._context() + "\n\n# DATI REALI\n"
                + json.dumps(data, ensure_ascii=False)[:7000]
                + "\n\nProponi azioni concrete coprendo PIÙ funzioni diverse del reparto "
                  "(non solo una). Max 8.\n"
                  "Se una proposta implica una SCRITTURA interna concreta, aggiungi il campo "
                  '"azione": {"tabella","op":"insert|update","match"(per update),"dati"} usando '
                  "SOLO tabelle interne (es. pipeline_leads, invoices, finance_journal, board_tasks, "
                  "board_cost_items, aios_content_calendar, project_tasks, candidates, employees, "
                  "legal_documents). MAI denaro (revenue/conversions/Stripe), MAI delete, MAI dati kbot. "
                  "update richiede sempre match (es. {\"id\":\"...\"}). Se non serve scrittura, ometti 'azione'. "
                  "L'azione verrà eseguita SOLO dopo approvazione umana.\n"
                  "USA ESATTAMENTE QUESTE COLONNE (in 'dati'):\n"
                  "- board_tasks: title, notes, priority(alta|media|bassa), status(todo|doing|done)\n"
                  "- pipeline_leads: name, company, sector, status, score(1-10), next_action, pain_point, notes, email, value_eur\n"
                  "- invoices: number, client_name, amount_eur, status(bozza|emessa|pagata|scaduta), issued_at, due_at\n"
                  "- finance_journal: data, descrizione, conto, dare, avere, categoria\n"
                  "- board_cost_items: name, amount_eur, frequency(monthly|quarterly|annual|one_off), category, active\n"
                  "- aios_content_calendar: canale(instagram|blog), titolo, bozza, stato, data_programmata\n"
                  "- project_tasks: project_id, title, status, due_date\n"
                  "- candidates: full_name, role_applied, status, source, notes\n"
                  "- employees: full_name, role, department, contract_type, status\n"
                  "- legal_documents: tipo, controparte, stato, rischio, scadenza, note")
        parsed = self.llm.complete_json(system=self.cfg.system, user=user, schema=_SCHEMA)
        proposte = _as_dict_list(parsed.get("proposte"))
        ids = []
        for p in proposte:
            r = self.k.execute(self.cfg.tool_name, actor=self.actor, args=p)
            if r.approval_id is not None:
                ids.append(r.approval_id)
        return DomainResult(approval_ids=ids, proposals=proposte)
