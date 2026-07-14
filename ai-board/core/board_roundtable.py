"""Roundtable del board: Giuseppina convoca più agenti e sintetizza le loro voci.

Flusso:
1. `select_relevant_agents` sceglie 2-4 membri pertinenti alla domanda
   (via LLM se disponibile, con fallback euristico e default sensato).
2. ogni membro dà il suo parere (agent.chat, quindi con le sue skill) in parallelo.
3. Giuseppina (orchestrator) sintetizza una raccomandazione finale.

Usato dal comando Telegram /consiglio e quando il fondatore chiede esplicitamente
"cosa ne pensa il board".
"""

from __future__ import annotations

import asyncio
import json
from dataclasses import dataclass
from typing import Any

from loguru import logger

from core.config import settings
from core.orchestrator import chat_agent
from db.models import AgentName

# Membri consultabili nel roundtable (Giuseppina resta il sintetizzatore, non una voce).
BOARD_ROSTER: list[AgentName] = [
    AgentName.CHIEF_OF_STAFF,
    AgentName.CONTENT_ENGINE,
    AgentName.MARKET_INTELLIGENCE,
    AgentName.SALES_ENABLEMENT,
    AgentName.SOLUTION_ARCHITECT,
    AgentName.FINANCE_KPI,
    AgentName.LEGAL,
    AgentName.GEO_SEO,
]

_DEFAULT_PICK: list[AgentName] = [
    AgentName.CHIEF_OF_STAFF,
    AgentName.FINANCE_KPI,
    AgentName.SOLUTION_ARCHITECT,
]

# Nomi persona per la sintesi. Tenuti qui (core) per non far dipendere core da
# interfaces; l'etichetta ricca col nome reale nel menu resta in presentation.
_PERSONA_NAME: dict[AgentName, str] = {
    AgentName.ORCHESTRATOR: "Giuseppina",
    AgentName.CHIEF_OF_STAFF: "Gino",
    AgentName.CONTENT_ENGINE: "Genoveffa",
    AgentName.MARKET_INTELLIGENCE: "Market Intelligence",
    AgentName.SALES_ENABLEMENT: "Peppe",
    AgentName.SOLUTION_ARCHITECT: "Archimede",
    AgentName.FINANCE_KPI: "Ragionier Ugo",
    AgentName.LEGAL: "Avvocata Pina",
    AgentName.GEO_SEO: "Geografino",
}

# Parole chiave → membro, per il fallback euristico quando l'LLM non è disponibile.
_KEYWORD_HINTS: dict[AgentName, tuple[str, ...]] = {
    AgentName.FINANCE_KPI: ("prezzo", "prezzi", "margine", "costo", "budget", "fatturato", "kpi", "cash", "conti", "economic"),
    AgentName.LEGAL: ("contratto", "legale", "gdpr", "privacy", "nda", "clausola", "rischio legale", "normativ"),
    AgentName.SALES_ENABLEMENT: ("cliente", "vendita", "vendite", "pipeline", "lead", "prospect", "offerta", "trattativa", "commerciale"),
    AgentName.CONTENT_ENGINE: ("contenuto", "post", "marketing", "campagna", "ads", "social", "linkedin", "copy", "brand"),
    AgentName.MARKET_INTELLIGENCE: ("mercato", "concorrente", "competitor", "trend", "settore", "opportunit"),
    AgentName.SOLUTION_ARCHITECT: ("progetto", "soluzione", "architettura", "tecnic", "implementazione", "delivery", "stack", "integrazione"),
    AgentName.GEO_SEO: ("seo", "geo", "ricerca", "posizionamento", "keyword", "sito", "traffico", "crawl"),
    AgentName.CHIEF_OF_STAFF: ("organizza", "priorit", "operativ", "task", "scadenz", "coordina"),
}


@dataclass
class BoardVoice:
    agent: AgentName
    text: str


@dataclass
class RoundtableResult:
    question: str
    agents: list[AgentName]
    voices: list[BoardVoice]
    synthesis: str


def _openai_client():
    if not (settings.openai_api_key or "").strip():
        return None
    try:
        from openai import OpenAI

        return OpenAI(api_key=settings.openai_api_key)
    except Exception as exc:  # pragma: no cover
        logger.warning(f"OpenAI client non disponibile per il roundtable: {exc}")
        return None


def _llm_select(question: str, max_agents: int) -> list[AgentName]:
    client = _openai_client()
    if client is None:
        return []
    roster_values = [agent.value for agent in BOARD_ROSTER]
    prompt = (
        "Sei il coordinatore di un board AI. Dato il messaggio del fondatore, scegli "
        f"da 2 a {max_agents} membri PERTINENTI tra questi: {', '.join(roster_values)}. "
        'Rispondi SOLO con JSON valido: {"agents": ["...", "..."]}. '
        "Scegli solo chi ha davvero qualcosa da dire su questo tema."
    )
    try:
        response = client.chat.completions.create(
            model=settings.default_openai_mini_model or settings.default_openai_model,
            temperature=0,
            response_format={"type": "json_object"},
            messages=[
                {"role": "system", "content": prompt},
                {"role": "user", "content": question},
            ],
        )
        payload = json.loads(response.choices[0].message.content or "{}")
        raw = payload.get("agents") or []
    except Exception as exc:
        logger.warning(f"Selezione LLM roundtable fallita: {exc}")
        return []

    picked: list[AgentName] = []
    for value in raw:
        try:
            agent = AgentName(str(value).strip())
        except ValueError:
            continue
        if agent in BOARD_ROSTER and agent not in picked:
            picked.append(agent)
    return picked[:max_agents]


def _heuristic_select(question: str, max_agents: int) -> list[AgentName]:
    lowered = (question or "").lower()
    scored: list[tuple[int, AgentName]] = []
    for agent, hints in _KEYWORD_HINTS.items():
        hits = sum(1 for hint in hints if hint in lowered)
        if hits:
            scored.append((hits, agent))
    scored.sort(key=lambda item: item[0], reverse=True)
    return [agent for _, agent in scored[:max_agents]]


def select_relevant_agents(question: str, max_agents: int = 4) -> list[AgentName]:
    picks = _llm_select(question, max_agents)
    if picks:
        return picks
    picks = _heuristic_select(question, max_agents)
    if picks:
        return picks
    return list(_DEFAULT_PICK)


def _voice_prompt(question: str) -> str:
    return (
        f"Il fondatore ha portato questo al board:\n\n«{question}»\n\n"
        "Dai il TUO parere dalla tua area di competenza: diretto, opinionato, concreto. "
        "3-6 righe. Prendi posizione, segnala il rischio o l'opportunità che vedi tu. "
        "Niente saluti, niente premesse, niente riassunto della domanda."
    )


def _collect_voice(agent: AgentName, question: str, context: dict[str, Any] | None) -> BoardVoice | None:
    try:
        text = chat_agent(agent, _voice_prompt(question), context)
        if text and text.strip():
            return BoardVoice(agent=agent, text=text.strip())
    except Exception as exc:
        logger.warning(f"[roundtable] Voce di {agent.value} fallita: {exc}")
    return None


def _synthesize(question: str, voices: list[BoardVoice]) -> str:
    if not voices:
        return "Il board non ha prodotto pareri utili su questo tema. Riprova a spiegarmi meglio cosa ti serve."

    voices_block = "\n\n".join(
        f"— {_PERSONA_NAME.get(voice.agent, voice.agent.value)}:\n{voice.text}" for voice in voices
    )
    synth_prompt = (
        f"Il fondatore ha chiesto al board:\n«{question}»\n\n"
        f"Questi sono i pareri raccolti dai membri:\n\n{voices_block}\n\n"
        "Sintetizza come CEO del board: 1) la raccomandazione operativa (cosa farei io), "
        "2) i 2-3 punti su cui i membri concordano, 3) l'eventuale tensione/rischio da tenere d'occhio, "
        "4) il prossimo passo concreto. Diretta e in prima persona, niente riassunto delle voci una per una."
    )
    try:
        return chat_agent(AgentName.ORCHESTRATOR, synth_prompt).strip()
    except Exception as exc:
        logger.warning(f"[roundtable] Sintesi Giuseppina fallita: {exc}")
        return "Ho raccolto i pareri del board ma non sono riuscita a sintetizzarli ora. Te li giro qui sopra."


async def convene(
    question: str,
    context: dict[str, Any] | None = None,
    max_agents: int = 4,
) -> RoundtableResult:
    """Convoca il board sulla domanda e restituisce voci + sintesi di Giuseppina."""
    agents = select_relevant_agents(question, max_agents=max_agents)
    logger.info(f"[roundtable] Convoco: {', '.join(a.value for a in agents)}")

    voice_results = await asyncio.gather(
        *[asyncio.to_thread(_collect_voice, agent, question, context) for agent in agents]
    )
    voices = [voice for voice in voice_results if voice is not None]

    synthesis = await asyncio.to_thread(_synthesize, question, voices)
    return RoundtableResult(question=question, agents=agents, voices=voices, synthesis=synthesis)
