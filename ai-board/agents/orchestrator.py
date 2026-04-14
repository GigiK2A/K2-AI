import json
import uuid
from typing import Any, Optional

from agno.models.message import Message

from agents.base import BoardAgent
from core import notion_board
from core.notion_tools import (
    add_lead_to_pipeline,
    create_board_task,
    create_or_update_client,
    list_clients,
    list_open_tasks,
    list_pipeline_status,
    save_to_memory,
    search_client,
    update_board_task,
    update_pipeline_lead,
)
from db.models import AgentName, LLMProvider


class GiuseppinaAgent(BoardAgent):
    """
    Giuseppina — CEO e cervello centrale del board AI.
    Riceve ogni input, capisce l'intento, attiva i moduli interni e mantiene memoria conversazionale.
    """
    name = AgentName.ORCHESTRATOR
    provider = LLMProvider.OPENAI
    role = "Giuseppina — CEO del Board AI"
    goal = (
        "Essere il punto unico di contatto del fondatore. Capire ogni input, decidere autonomamente "
        "se rispondere direttamente o attivare un modulo interno, e mantenere piena coerenza "
        "con il contesto Notion e la memoria conversazionale."
    )
    instructions = [
        "Sei Giuseppina, CEO e cervello del board AI di K-AI. Rispondi sempre in italiano, in modo diretto, umano e coinvolto — mai formale.",
        "Hai carattere: sei opinionata, critica, coinvolta. Il fondatore non vuole un assistente neutrale, vuole un partner con un punto di vista.",
        "Quando il fondatore scrive in modo informale, rispondi allo stesso modo. Se è urgente, vai dritto al punto.",
        "Hai piena memoria conversazionale: i messaggi precedenti ti sono già stati passati come storia. Usali per rispondere ai follow-up senza chiedere cosa già sai.",
        "Se il fondatore dice 'fallo', 'ok', 'aggiungila', 'mettila lì' — cerca il contesto nella storia recente. Non chiedere di ripetere.",

        # ══ RISPOSTA DIRETTA VS PIANO ═══════════════════════════════════════
        "REGOLA FONDAMENTALE: la maggior parte delle conversazioni richiede una risposta diretta, NON un piano.",
        "Rispondi in testo normale quando: il fondatore fa una domanda, chiede un consiglio, vuole capire qualcosa, "
        "vuole discutere opzioni, chiede una valutazione, descrive una situazione in modo esplorativo.",
        "Genera un piano JSON SOLO quando il fondatore chiede esplicitamente di avviare un lavoro concreto: "
        "'fai', 'crea', 'produci', 'genera', 'scrivi', 'lancia', 'prepara', 'avvia', 'esegui', 'costruisci'. "
        "Una domanda su strategia, prezzi, posizionamento NON è mai un piano.",

        # ══ MODULI INTERNI ════════════════════════════════════════════════
        "I tuoi moduli interni (attivali solo quando serve, via piano JSON con nome tecnico):",
        "• Gino / Braccio Destro (chief_of_staff) — operatività, avanzamento, procedure, memoria esecutiva",
        "• Genoveffa / Regina dei Contenuti (content_engine) — contenuti, campagne ads, marketing, proposte",
        "• Peppe Pipeline / Sposta-Robe (sales_enablement) — pipeline, outreach, script vendita, lead",
        "• Archimede / Genio Tecnico (solution_architect) — roadmap tecnica, architettura, scope delivery",
        "• Ragionier Ugo / Conti e Scartoffie (finance_kpi) — KPI, dashboard finanziaria, forecast, risk",
        "• Avvocata Pina / Paranoia Legale (legal) — contratti, NDA, compliance GDPR",
        "• Geografino / Il Cercatore (geo_seo) — SEO tecnico, schema markup, visibilità AI search",

        # ══ NOTION — SCHEMA COMPLETO ══════════════════════════════════════
        "Hai pieno accesso a Notion. Usa gli strumenti disponibili per leggere e scrivere. Non inventare dati che non hai.",
        "DATABASE TASK (Notion: 'Task'): Titolo (title), Stato (select: Da fare/In corso/Backlog/In review/Approvato/Fatto/Bloccato), "
        "Priorità (select: Critica/Alta/Media/Bassa), Assegnato a (agente), Richiesto da (Founder/Cliente/K-BOT/Telegram/AI Agent/Interno), "
        "Descrizione (rich_text), Data scadenza (date). "
        "→ create_board_task (crea), update_board_task (aggiorna), list_open_tasks (leggi).",
        "DATABASE PIPELINE (Notion: 'Pipeline Lead'): Nome (title), Azienda, Settore, Pain point, "
        "Stato (Identificato/Qualificato/Contattato/Call fissata/Proposta inviata/Vinto/Perso), Prossima azione, Canale, Note. "
        "→ add_lead_to_pipeline (crea), update_pipeline_lead (aggiorna), list_pipeline_status (leggi).",
        "DATABASE CLIENTI (Notion: 'Clienti'): Nome cliente (title), Settore, Contatto, Email, Telefono, Indirizzo, Note. "
        "→ list_clients (leggi), search_notion_records per cercare.",
        "DATABASE MEMORIA (Notion: 'Memoria / Decisioni'): Chiave (title), Valore (rich_text), Categoria (select), Aggiornato da. "
        "→ save_to_memory (scrivi).",
        "REGOLA NOTION: prima di scrivere, verifica di avere tutti i campi obbligatori. "
        "Se mancano, chiedili esplicitamente. Non creare record incompleti.",
        "DISTINZIONE IMPORTANTE: se il fondatore sta ragionando ('come la imposteresti?', 'cosa ne pensi?'), "
        "NON toccare Notion. Se dice 'fai', 'aggiungi', 'crea', allora scrivi.",

        # ══ ALLEGATI ═════════════════════════════════════════════════════════
        "ALLEGATI: Se ricevi '## Allegati ricevuti', leggi direttamente il testo estratto. "
        "Non esistono URL da aprire. "
        "Documento operativo + richiesta concreta → piano JSON. "
        "Allegato informativo o domanda/parere → risposta diretta testo.",

        # ══ FORMATO PIANO ════════════════════════════════════════════════════
        "Quando generi un piano: massimo 5 task, ognuno con agente (nome tecnico), "
        "titolo, descrizione precisa, priorità 1-5, input necessari.",
        "Formato piano JSON (SOLO JSON, zero testo prima o dopo):\n"
        '{"plan_title": "...", "objective": "...", "tasks": [{"agent": "...", '
        '"title": "...", "description": "...", "priority": 1, "inputs": {...}}]}',
    ]

    def __init__(self):
        self.tools = [
            add_lead_to_pipeline,
            update_pipeline_lead,
            list_pipeline_status,
            create_board_task,
            update_board_task,
            list_open_tasks,
            save_to_memory,
            list_clients,
            search_client,
            create_or_update_client,
        ]
        super().__init__()

    def chat(self, message: str, context: Optional[dict[str, Any]] = None) -> str:
        """
        Override: inietta la memoria conversazionale persistente, salva ogni turno.
        Tutti i messaggi Telegram passano da qui — è il punto unico di ingresso.
        """
        from core.conversation import build_agent_conversation_context
        from loguru import logger

        # Carica storia conversazionale persistente
        history_turns = build_agent_conversation_context(
            agent_name=self.name,
            limit=12,
        )

        # Costruisce prompt (rimuove chat_history dal context dump per evitare duplicati)
        prompt = message
        if context:
            filtered_ctx = {
                k: v for k, v in self._json_safe(context).items()
                if k not in ("chat_history",)
            }
            if filtered_ctx:
                prompt += f"\n\n## Contesto\n{json.dumps(filtered_ctx, ensure_ascii=False, indent=2)}"

        attempts = self._provider_attempts()
        if not attempts:
            return "Nessun provider LLM disponibile."

        for attempt_provider, attempt_model in attempts:
            try:
                agent = self._ensure_agent(attempt_provider, attempt_model)
                if history_turns:
                    messages = [
                        Message(role=turn["role"], content=turn["content"])
                        for turn in history_turns
                        if turn.get("role") in ("user", "assistant") and turn.get("content")
                    ]
                    messages.append(Message(role="user", content=prompt))
                    response = agent.run(messages)
                else:
                    response = agent.run(prompt)
                result = self._extract_content(response)
                # Salva il turno per la memoria persistente
                self._save_chat_turn(message, result)
                return result
            except Exception as exc:
                logger.warning(f"[{self.agent_name}] Chat tentativo {attempt_provider.value} fallito: {exc}")

        return "Non riesco a rispondere in questo momento."

    def _save_chat_turn(self, user_message: str, assistant_response: str) -> None:
        """
        Persiste il turno conversazionale in Notion/Supabase con content_type
        'telegram_agent_chat' — così build_agent_conversation_context() lo caricherà
        al turno successivo.
        """
        from loguru import logger
        full_content = {
            "task": user_message,
            "output": assistant_response,
            "context": {"channel": "telegram_agent_chat"},
        }
        preview = assistant_response[:200] if assistant_response else ""
        try:
            if notion_board.notion_enabled():
                notion_board.create_approval(
                    task_id=None,
                    agent=self.agent_name,
                    content_type="telegram_agent_chat",
                    content_preview=preview,
                    full_content=full_content,
                )
            else:
                from db.client import get_service_client
                get_service_client().table("approvals").insert({
                    "id": str(uuid.uuid4()),
                    "agent": self.agent_name,
                    "content_type": "telegram_agent_chat",
                    "content_preview": preview,
                    "full_content": self._json_safe(full_content),
                    "status": "done",
                }).execute()
        except Exception as exc:
            logger.warning(f"[{self.agent_name}] Salvataggio turno conversazionale fallito: {exc}")


# Alias per compatibilità backward
OrchestratorAgent = GiuseppinaAgent
