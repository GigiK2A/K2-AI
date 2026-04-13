import json
import time
import uuid
from typing import Any, Optional

from agno.agent import Agent
from agno.models.anthropic import Claude
from agno.models.openai import OpenAIChat
from loguru import logger

from core import notion_board
from core.config import settings
from core.memory import get_memory_as_context
from db.client import get_service_client
from db.models import AgentName, LLMProvider, TaskStatus
from interfaces.telegram.notifier import notify_draft_ready, notify_error, notify_sync


def get_search_tool():
    """Restituisce Tavily se disponibile, altrimenti DuckDuckGo."""
    if settings.tavily_api_key:
        from agno.tools.tavily import TavilyTools

        return TavilyTools(api_key=settings.tavily_api_key)

    from agno.tools.duckduckgo import DuckDuckGoTools

    return DuckDuckGoTools()


class BoardAgent:
    """
    Classe base per tutti gli agenti del board.
    Ogni agente eredita questa classe e sovrascrive:
    - name: AgentName
    - role: str (titolo del ruolo)
    - goal: str (obiettivo principale)
    - instructions: list[str] (istruzioni specifiche)
    - provider: LLMProvider (anthropic o openai)
    - model: str (override del modello, opzionale)
    """

    name: AgentName | None = None
    role: str = ""
    goal: str = ""
    instructions: list[str] = []
    provider: LLMProvider = LLMProvider.ANTHROPIC
    model: Optional[str] = None
    fallback_provider: LLMProvider | None = None
    fallback_model: Optional[str] = None
    tools: list[Any] = []

    def __init__(
        self,
        provider: str | LLMProvider | None = None,
        model: Optional[str] = None,
        fallback_provider: str | LLMProvider | None = None,
        fallback_model: Optional[str] = None,
    ):
        if provider is not None:
            self.provider = self._coerce_provider(provider)
        if model is not None:
            self.model = model
        if fallback_provider is not None:
            self.fallback_provider = self._coerce_provider(fallback_provider)
        if fallback_model is not None:
            self.fallback_model = fallback_model

        self.primary_provider = self.provider
        self.primary_model = self.model or self._default_model_for_provider(self.primary_provider)
        self.secondary_provider = self.fallback_provider or self._alternate_provider(self.primary_provider)
        self.secondary_model = self.fallback_model or self._default_model_for_provider(self.secondary_provider)

        self.tools_list = list(self.tools)
        self._agents: dict[tuple[str, str], Agent] = {}

    @property
    def agent_name(self) -> str:
        return self.name.value if self.name else "base_agent"

    def _coerce_provider(self, provider: str | LLMProvider) -> LLMProvider:
        if isinstance(provider, LLMProvider):
            return provider
        return LLMProvider(provider.lower())

    def _default_model_for_provider(self, provider: LLMProvider) -> str:
        if provider == LLMProvider.ANTHROPIC:
            return settings.default_anthropic_model
        if provider == LLMProvider.OPENAI:
            return settings.default_openai_model
        raise ValueError(f"Provider non supportato: {provider}")

    def _alternate_provider(self, provider: LLMProvider) -> LLMProvider:
        return LLMProvider.OPENAI if provider == LLMProvider.ANTHROPIC else LLMProvider.ANTHROPIC

    def _is_provider_available(self, provider: LLMProvider) -> bool:
        if provider == LLMProvider.ANTHROPIC:
            return bool(settings.anthropic_api_key.strip())
        if provider == LLMProvider.OPENAI:
            return bool(settings.openai_api_key.strip())
        return False

    def _provider_attempts(self) -> list[tuple[LLMProvider, str]]:
        attempts: list[tuple[LLMProvider, str]] = []
        for provider, model_id in (
            (self.primary_provider, self.primary_model),
            (self.secondary_provider, self.secondary_model),
        ):
            key = (provider.value, model_id)
            if not self._is_provider_available(provider):
                logger.warning(f"[{self.agent_name}] Provider {provider.value} non disponibile: chiave API mancante.")
                continue
            if key in {(item[0].value, item[1]) for item in attempts}:
                continue
            attempts.append((provider, model_id))
        return attempts

    def _get_model(self, provider: LLMProvider, model_id: str):
        """Restituisce il modello Agno corretto in base al provider."""
        if provider == LLMProvider.ANTHROPIC:
            return Claude(id=model_id, api_key=settings.anthropic_api_key)
        if provider == LLMProvider.OPENAI:
            return OpenAIChat(id=model_id, api_key=settings.openai_api_key)
        raise ValueError(f"Provider non supportato: {provider}")

    def _build_system_prompt(self) -> str:
        """Costruisce il system prompt completo con memoria condivisa iniettata."""
        memory_context = get_memory_as_context()
        instructions_text = "\n".join(f"- {instruction}" for instruction in self.instructions) or "- Nessuna istruzione specifica"

        return f"""Sei {self.role or self.agent_name} nel board AI di un business di consulenza AI.

## IL TUO OBIETTIVO
{self.goal or "Supportare il board con output strutturati e controllati."}

## ISTRUZIONI OPERATIVE
{instructions_text}

## REGOLE FONDAMENTALI
- Sei un membro del board, non un esecutore: dai pareri, opinioni e decisioni, non solo riassunti
- Non inventare dati, casi studio o metriche che non hai
- Usa sempre l'italiano, linguaggio professionale ma diretto
- Se non hai abbastanza informazioni per completare il task, segnalalo esplicitamente e chiedi solo quello che ti serve davvero
- Quando utile usa Markdown: grassetto, corsivo, liste, tabelle — mai struttura pesante per messaggi semplici
- Se una visualizzazione aiuta davvero, puoi includere un grafico con un blocco ```grafico``` contenente JSON compatibile Chart.js
- Esempio grafico:
```grafico
{{"type":"bar","data":{{"labels":["A","B"],"datasets":[{{"label":"Serie","data":[10,20]}}]}}}}
```
- Quando ti viene chiesto di generare un documento formale (PDF, DOCX, XLSX, HTML), producilo e segnala che è pronto per approvazione
- Considera Notion come registro operativo del board: task, lead, approvazioni, log e decisioni devono essere trattati come elementi persistenti e aggiornabili, non come semplice chat
- Quando produci un output operativo, scrivi in modo che possa essere archiviato in Notion: titolo chiaro, decisione/azione, contesto minimo e prossimo passo
- Se una richiesta genera un'opportunità commerciale o un lavoro, esplicita se va in Pipeline, Task o Approvazioni

## COME RAGIONARE E RISPONDERE

Prima di rispondere, fai questa sequenza mentale:
1. **Qual è il problema reale?** Non rispondere alla superficie — rispondi alla sostanza
2. **Cosa si aspetta il fondatore?** Una risposta rapida? Un'analisi approfondita? Un documento? Una decisione?
3. **Qual è il formato giusto?** Vedi la sezione FORMATO RISPOSTA sotto
4. **Qual è la mia posizione?** Prendila. Non fare l'assistente neutrale

Regole di ragionamento:
- Sii critico e opinionato: il fondatore non ha bisogno di un riassunto, ha bisogno di un punto di vista esperto
- Quando ti vengono presentate opzioni, analizza ognuna con occhio critico — qual è il problema? il rischio nascosto? il presupposto fragile?
- Dai raccomandazioni dirette in prima persona: "quello che farei io è...", "questa scelta ha senso se...", "questa non la farei perché..."
- Identifica i rischi reali e i punti deboli — non glissare sui problemi per sembrare positivo
- Scrivi come un consulente senior che parla direttamente al fondatore, non come un assistente che riassume
- Non iniziare mai con "Ho preparato..." o "Ho analizzato..." — inizia subito con il contenuto o con la tua lettura

## FORMATO RISPOSTA — ADATTA AL CONTESTO

Leggi la richiesta e scegli il formato in base al tipo di interazione:

**Messaggio corto (2-6 righe):**
- Domanda diretta con risposta semplice: "che cos'è X?", "quando è Y?", "hai fatto Z?"
- Conferma, aggiornamento rapido, risposta binaria
- Reazione a qualcosa che il fondatore ha scritto senza chiedere un'analisi

**Messaggio lungo (testo strutturato con sezioni, bullet, tabelle):**
- Analisi di opzioni, valutazione di strategie, raccomandazione su una scelta complessa
- Richiesta esplicita di parere su un tema con molte variabili
- Task operativo che richiede un output strutturato (piano, lista, procedura)
- Risposta ad allegati con contenuto da interpretare

**Documento (PDF, DOCX, XLSX, HTML):**
- Solo se il fondatore chiede esplicitamente un file: "dammi il PDF", "genera la proposta", "crea il report"
- Solo se il task è un deliverable formale da consegnare o archiviare
- MAI generare un documento solo perché l'argomento è complesso o hai molte cose da dire

**Quando sei in dubbio: testo lungo strutturato, non documento.**

Regole aggiuntive:
- Non aggiungere mai un riassunto finale dopo aver risposto — il fondatore legge la risposta
- Termina con 1-3 domande specifiche solo quando la risposta lo richiede per sbloccare la decisione successiva. Non sempre.
- Non usare mai frasi di chiusura generiche tipo "Spero di esserti stato utile" o "Resto a disposizione"

{memory_context}"""

    def _build_agent(self, provider: LLMProvider, model_id: str) -> Agent:
        """Costruisce l'istanza Agno Agent."""
        return Agent(
            name=self.agent_name,
            model=self._get_model(provider, model_id),
            description=self.role or self.agent_name,
            instructions=self._build_system_prompt(),
            tools=self.tools_list,
            markdown=True,
        )

    def _ensure_agent(self, provider: LLMProvider, model_id: str) -> Agent:
        """Costruisce l'agent Agno solo al primo utilizzo per provider/modello."""
        key = (provider.value, model_id)
        if key not in self._agents:
            self._agents[key] = self._build_agent(provider, model_id)
        return self._agents[key]

    def chat(self, message: str, context: Optional[dict[str, Any]] = None) -> str:
        """
        Risposta conversazionale diretta: nessun task, nessuna approval, nessuna notifica.
        Usato per interazione board-member in Telegram.
        """
        prompt = message
        if context:
            safe_ctx = self._json_safe(context)
            prompt += f"\n\n## Contesto\n{json.dumps(safe_ctx, ensure_ascii=False, indent=2)}"

        attempts = self._provider_attempts()
        if not attempts:
            return "Nessun provider LLM disponibile."

        for attempt_provider, attempt_model in attempts:
            try:
                response = self._ensure_agent(attempt_provider, attempt_model).run(prompt)
                return self._extract_content(response)
            except Exception as exc:
                logger.warning(f"[{self.agent_name}] Chat tentativo {attempt_provider.value} fallito: {exc}")

        return "Non riesco a rispondere in questo momento."

    def run(self, task: str, context: Optional[dict[str, Any]] = None) -> dict[str, Any]:
        """
        Esegue il task e restituisce sempre un dict con questa struttura:
        {
            "status": "draft" | "error",
            "agent": str,
            "task": str,
            "output": Any,
            "approval_required": bool,
            "approval_id": str | None,
            "tokens_used": int | None,
            "duration_ms": int
        }
        """
        start = time.time()
        task_id = str(uuid.uuid4())
        internal_meta, prompt_context = self._split_internal_meta(context)
        safe_context = self._json_safe(prompt_context) if prompt_context else None
        project_id = internal_meta.get("project_id")
        content_type = internal_meta.get("content_type", "agent_output")
        requested_by = internal_meta.get("requested_by", "founder")

        prompt = task
        if safe_context:
            prompt += f"\n\n## Contesto aggiuntivo\n{json.dumps(safe_context, ensure_ascii=False, indent=2)}"

        logger.info(f"[{self.agent_name}] Avvio task: {task[:80]}...")
        stored_task_id = self._create_task(task_id=task_id, task=task, context=safe_context, requested_by=requested_by)
        if stored_task_id:
            task_id = stored_task_id

        attempts = self._provider_attempts()
        if not attempts:
            error_message = "Nessun provider LLM disponibile. Configura almeno una chiave valida tra OPENAI_API_KEY e ANTHROPIC_API_KEY."
            logger.error(f"[{self.agent_name}] {error_message}")
            notify_sync(notify_error(agent_name=self.agent_name, error=error_message))
            self._update_task_status(task_id, TaskStatus.REJECTED.value, error_message)
            self._log(
                task_id=task_id,
                action=task[:100],
                output_summary=error_message,
                status="error",
                duration_ms=int((time.time() - start) * 1000),
                tokens_used=None,
                llm_provider=None,
                llm_model=None,
            )
            return {
                "status": "error",
                "agent": self.agent_name,
                "task": task,
                "output": None,
                "error": error_message,
                "approval_required": False,
                "approval_id": None,
                "tokens_used": None,
                "duration_ms": int((time.time() - start) * 1000),
                "llm_provider": None,
                "llm_model": None,
                "fallback_used": False,
            }

        attempt_errors: list[str] = []
        response = None
        used_provider: LLMProvider | None = None
        used_model: Optional[str] = None

        for index, (attempt_provider, attempt_model) in enumerate(attempts, start=1):
            try:
                if index > 1:
                    logger.warning(
                        f"[{self.agent_name}] Failover attivo: nuovo tentativo con {attempt_provider.value}:{attempt_model}"
                    )
                response = self._ensure_agent(attempt_provider, attempt_model).run(prompt)
                used_provider = attempt_provider
                used_model = attempt_model
                break
            except Exception as exc:
                attempt_errors.append(f"{attempt_provider.value}:{attempt_model} -> {exc}")
                logger.warning(
                    f"[{self.agent_name}] Tentativo {attempt_provider.value}:{attempt_model} fallito: {exc}"
                )

        try:
            if response is None or used_provider is None or used_model is None:
                raise RuntimeError(" | ".join(attempt_errors) or "Esecuzione agente fallita")

            duration_ms = int((time.time() - start) * 1000)
            output_text = self._extract_content(response)
            tokens_used = self._extract_tokens_used(response)

            approval_id = self._create_approval(
                task_id=task_id,
                content_type=content_type,
                content_preview=output_text[:200],
                full_content={"task": task, "output": output_text, "context": safe_context},
                project_id=project_id,
            )

            self._update_task_status(task_id, TaskStatus.DRAFT.value, output_text[:500])
            self._log(
                task_id=task_id,
                action=task[:100],
                output_summary=output_text[:200],
                status=TaskStatus.DRAFT.value,
                duration_ms=duration_ms,
                tokens_used=tokens_used,
                llm_provider=used_provider,
                llm_model=used_model,
                project_id=project_id,
            )

            logger.success(f"[{self.agent_name}] Task completato in {duration_ms}ms")
            if used_provider != self.primary_provider:
                logger.success(
                    f"[{self.agent_name}] Output generato tramite fallback {used_provider.value}:{used_model}"
                )
            if approval_id:
                notify_sync(notify_draft_ready(agent_name=self.agent_name, approval_id=approval_id, preview=output_text))

            return {
                "status": TaskStatus.DRAFT.value,
                "agent": self.agent_name,
                "task": task,
                "output": output_text,
                "approval_required": True,
                "approval_id": approval_id,
                "tokens_used": tokens_used,
                "duration_ms": duration_ms,
                "llm_provider": used_provider.value,
                "llm_model": used_model,
                "fallback_used": used_provider != self.primary_provider,
            }
        except Exception as exc:
            duration_ms = int((time.time() - start) * 1000)
            full_error = str(exc)
            if attempt_errors and full_error not in attempt_errors[-1]:
                full_error = " | ".join(attempt_errors + [full_error])
            elif attempt_errors:
                full_error = " | ".join(attempt_errors)
            logger.error(f"[{self.agent_name}] Errore: {full_error}")
            notify_sync(notify_error(agent_name=self.agent_name, error=full_error))

            self._update_task_status(task_id, TaskStatus.REJECTED.value, full_error)
            self._log(
                task_id=task_id,
                action=task[:100],
                output_summary=full_error,
                status="error",
                duration_ms=duration_ms,
                tokens_used=None,
                llm_provider=used_provider,
                llm_model=used_model,
                project_id=project_id,
            )

            return {
                "status": "error",
                "agent": self.agent_name,
                "task": task,
                "output": None,
                "error": full_error,
                "approval_required": False,
                "approval_id": None,
                "tokens_used": None,
                "duration_ms": duration_ms,
                "llm_provider": used_provider.value if used_provider else None,
                "llm_model": used_model,
                "fallback_used": used_provider is not None and used_provider != self.primary_provider,
            }

    def _create_task(
        self,
        task_id: str,
        task: str,
        context: Optional[dict[str, Any]],
        requested_by: str = "founder",
    ) -> Optional[str]:
        """Crea un record task per mantenere coerenti log e approval con le FK del DB."""
        try:
            if notion_board.notion_enabled():
                return notion_board.create_task(
                    title=task[:120],
                    description=task,
                    assigned_to=self.agent_name,
                    priority=3,
                    status=TaskStatus.RUNNING.value,
                    requested_by=requested_by,
                    notes=json.dumps(context or {}, ensure_ascii=False, default=str)[:1500] if context else "",
                    task_type="AI",
                )

            client = get_service_client()
            client.table("tasks").insert(
                {
                    "id": task_id,
                    "title": task[:120],
                    "description": task,
                    "assigned_to": self.agent_name,
                    "requested_by": requested_by,
                    "status": TaskStatus.RUNNING.value,
                    "priority": 3,
                    "input_data": context,
                }
            ).execute()
            return task_id
        except Exception as exc:
            logger.warning(f"Errore creazione task {task_id}: {exc}")
            if notion_board.notion_enabled():
                raise
            return None

    def _update_task_status(self, task_id: str, status: str, notes: Optional[str] = None) -> None:
        try:
            if notion_board.notion_enabled():
                notion_board.update_task_status(task_id, status, notes)
                return

            client = get_service_client()
            payload: dict[str, Any] = {"status": status}
            if notes:
                payload["notes"] = notes
            client.table("tasks").update(payload).eq("id", task_id).execute()
        except Exception as exc:
            logger.warning(f"Errore aggiornamento task {task_id}: {exc}")
            if notion_board.notion_enabled():
                raise

    def _create_approval(
        self,
        task_id: str,
        content_type: str,
        content_preview: str,
        full_content: dict[str, Any],
        project_id: Optional[str] = None,
    ) -> Optional[str]:
        """Salva il draft nella tabella approvals."""
        try:
            if notion_board.notion_enabled():
                return notion_board.create_approval(
                    task_id=task_id,
                    agent=self.agent_name,
                    content_type=content_type,
                    content_preview=content_preview,
                    full_content=self._json_safe(full_content),
                    project_id=project_id,
                )

            client = get_service_client()
            approval_id = str(uuid.uuid4())
            client.table("approvals").insert(
                {
                    "id": approval_id,
                    "task_id": task_id,
                    "agent": self.agent_name,
                    "content_type": content_type,
                    "content_preview": content_preview,
                    "full_content": self._json_safe(full_content),
                    "status": TaskStatus.DRAFT.value,
                    "project_id": project_id,
                }
            ).execute()
            return approval_id
        except Exception as exc:
            logger.warning(f"Errore salvataggio approval: {exc}")
            if notion_board.notion_enabled():
                raise
            return None

    def _log(
        self,
        task_id: str,
        action: str,
        output_summary: str,
        status: str,
        duration_ms: int,
        tokens_used: Optional[int],
        llm_provider: Optional[LLMProvider],
        llm_model: Optional[str],
        project_id: Optional[str] = None,
    ) -> None:
        """Log dell'esecuzione."""
        try:
            if notion_board.notion_enabled():
                notion_board.create_agent_log(
                    agent=self.agent_name,
                    task_id=task_id,
                    action=action,
                    output_summary=output_summary,
                    status=status,
                    duration_ms=duration_ms,
                    tokens_used=tokens_used,
                    llm_provider=llm_provider.value if llm_provider else None,
                    llm_model=llm_model,
                    project_id=project_id,
                    requires_approval=status == TaskStatus.DRAFT.value,
                )
                return

            client = get_service_client()
            client.table("agent_logs").insert(
                {
                    "agent": self.agent_name,
                    "task_id": task_id,
                    "action": action,
                    "llm_provider": llm_provider.value if llm_provider else None,
                    "llm_model": llm_model,
                    "output_summary": output_summary,
                    "status": status,
                    "tokens_used": tokens_used,
                    "duration_ms": duration_ms,
                    "project_id": project_id,
                }
            ).execute()
        except Exception as exc:
            logger.warning(f"Errore log agente: {exc}")
            if notion_board.notion_enabled():
                raise

    def _extract_content(self, response: Any) -> str:
        if hasattr(response, "content"):
            return str(response.content)
        if hasattr(response, "output"):
            return str(response.output)
        return str(response)

    def _extract_tokens_used(self, response: Any) -> Optional[int]:
        usage = getattr(response, "usage", None) or getattr(response, "metrics", None)
        if usage is None:
            return None
        if isinstance(usage, dict):
            for key in ("total_tokens", "tokens", "output_tokens"):
                value = usage.get(key)
                if isinstance(value, int):
                    return value
        total_tokens = getattr(usage, "total_tokens", None)
        if isinstance(total_tokens, int):
            return total_tokens
        return None

    def _json_safe(self, value: Any) -> Any:
        return json.loads(json.dumps(value, ensure_ascii=False, default=str))

    def _split_internal_meta(self, context: Optional[dict[str, Any]]) -> tuple[dict[str, Any], Optional[dict[str, Any]]]:
        if not isinstance(context, dict):
            return {}, context

        copied = dict(context)
        internal = copied.pop("__board", {})
        if not isinstance(internal, dict):
            internal = {}
        return internal, copied or None
