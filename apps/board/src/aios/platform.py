from __future__ import annotations

import os
from typing import Any

from aios.kernel import Kernel
from aios.founder import default_founder_model
from aios.llm import AnthropicLLM, FallbackLLM, LocalLLM
from aios.skills import SkillLibrary
from aios.layers.knowledge import KnowledgeStore
from aios.sources.instagram import InstagramClient
from aios.sources.tools import (content_tools_rest, instagram_tools,
                                insights_tools, competitor_lookup_tool)
from aios.sources.calendar import calendar_tools
from aios.sources.marketing_extra import marketing_extra_tools
from aios.sources.connectors import all_connectors
from aios.sources.sales import lead_tools
from aios.sources.domains import (finance_tools, operations_tools,
                                  legal_tools, hr_tools, catalog_tools)
from aios.sources.outputs import output_tool
from aios.sources.n8n import n8n_tool, n8n_workflows_tool, n8n_executions_tool
from aios.command import CommandRouter
from aios.prospecting import Prospector, prospects_tool
from aios.tools import Tool
from aios.agents.marketing import MarketingAgent
from aios.agents.domain import DomainAgent
from aios.agents.sales_config import SALES_CONFIG
from aios.agents.finance_config import FINANCE_CONFIG
from aios.agents.operations_config import OPERATIONS_CONFIG
from aios.agents.legal_config import LEGAL_CONFIG
from aios.agents.hr_config import HR_CONFIG


def _make_llm(*, max_tokens: int, strong: bool = False):
    """Fabbrica dell'LLM workhorse/strong. Sceglie il backend da AIOS_LLM_BACKEND
    (default 'anthropic' = comportamento invariato; 'local' = Ollama sul GB10).

    Col backend locale la riserva è Claude: il GB10 arriva via tailnet e va e viene,
    e un reparto che va in timeout perde il giro senza dirlo a nessuno. La riserva
    entra SOLO quando Ollama è irraggiungibile (vedi FallbackLLM), quindi il costo
    API si paga solo quando il locale è giù. Senza ANTHROPIC_API_KEY resta il solo
    locale, come prima."""
    model = "claude-sonnet-4-6" if strong else "claude-haiku-4-5-20251001"
    backend = os.environ.get("AIOS_LLM_BACKEND", "anthropic").strip().lower()
    ha_anthropic = bool(os.environ.get("ANTHROPIC_API_KEY"))
    if backend == "local":
        locale = LocalLLM(max_tokens=max_tokens)
        if not ha_anthropic:
            return locale
        if strong:
            # "Forte" deve significare forte. Con backend=local anche il modello del
            # GIUDIZIO era il modello locale con solo più token: Sonnet non entrava mai
            # nel giro degli agenti, e chiedere il parere di un CFO al modello economico
            # era il vero tetto alla qualità. Qui la priorità si inverte: giudizio su
            # Sonnet, e se l'API non risponde si ripiega sul locale invece di fermarsi.
            return FallbackLLM(AnthropicLLM(model=model, max_tokens=max_tokens),
                               lambda: LocalLLM(max_tokens=max_tokens))
        return FallbackLLM(locale, lambda: AnthropicLLM(model=model, max_tokens=max_tokens))
    return AnthropicLLM(model=model, max_tokens=max_tokens)


class Platform:
    """K2-OS: kernel condiviso + sensori + conoscenza + agenti di dominio."""

    def __init__(self, kernel: Kernel, agents: dict[str, Any], commands: Any = None) -> None:
        self.kernel = kernel
        self.agents = agents
        self.commands = commands   # CommandRouter (chat a istruzioni), impostato dopo
        self.chat = None           # ChatOrchestrator (chat multi-agente streaming)
        self.org = None            # OrgChart (organigramma del board), impostato dopo

    def domains(self) -> list[str]:
        return list(self.agents)

    def run(self, domain: str) -> dict[str, Any]:
        if domain not in self.agents:
            raise KeyError(domain)
        res = self.agents[domain].run()
        eseguite = list(getattr(res, "eseguite", []) or [])
        return {"domain": domain,
                "proposte": len(getattr(res, "proposals", []) or []),
                "calendario": len(getattr(res, "calendar", []) or []),
                "eseguite": eseguite,
                "fatte": sum(1 for e in eseguite if e.get("ok")),
                "non_riuscite": sum(1 for e in eseguite if not e.get("ok"))}

    def deliverables(self) -> list[dict[str, Any]]:
        return self.kernel._supabase.select(
            "aios_deliverables", {"select": "*", "order": "id.desc"})

    def budget_report(self) -> list[dict[str, Any]]:
        """Stato budget/spesa del mese per ogni agente (per cockpit e Telegram)."""
        from aios import billing
        actors = [getattr(a, "actor", None) for a in self.agents.values()]
        return billing.get_meter().report([a for a in actors if a])


def build_platform() -> Platform:
    k = Kernel.with_supabase_rest(os.environ["AIOS_SUPABASE_URL"],
                                  os.environ["AIOS_SUPABASE_SERVICE_KEY"])
    client = k._supabase

    # Metering costi + budget con hard-stop per agente (Paperclip primitive #1).
    # Tetti da env (AIOS_AGENT_BUDGETS / AIOS_DEFAULT_AGENT_BUDGET_EUR); persistenza
    # su Supabase (aios_cost_ledger + aios_budget_state). Senza env → nessun tetto
    # (comportamento invariato), ma i consumi vengono comunque tracciati.
    from aios import billing
    _budgets, _default_cap = billing.budgets_from_env()
    billing.set_meter(billing.CostMeter(client, budgets=_budgets, default_cap=_default_cap))

    # Organigramma del board: ruoli/riporti iniettati nel contesto agenti (Paperclip #2).
    from aios import org as _org
    _org.set_chart(_org.OrgChart.default())

    # Obiettivi dell'azienda (goal ancestry, Paperclip #3): sensore readonly.
    def _leggi_obiettivi(stato: str | None = None, **_):
        params = {"select": "*", "order": "priority.asc", "limit": "50"}
        if stato:
            params["status"] = f"eq.{stato}"
        try:
            return client.select("aios_goals", params)
        except Exception:
            return []
    k.register_tool(Tool(name="leggi_obiettivi", action_type=None, readonly=True,
                         run=_leggi_obiettivi))
    ig = InstagramClient(token=os.environ["AIOS_IG_TOKEN"],
                         ig_user_id=os.environ.get("AIOS_IG_USER_ID", "17841429842127461"))
    k.register_tool(output_tool(client))
    for t in content_tools_rest(client):
        k.register_tool(t)
    for t in instagram_tools(ig):
        k.register_tool(t)
    for t in insights_tools(ig):
        k.register_tool(t)
    k.register_tool(competitor_lookup_tool(ig))
    for t in calendar_tools(client):
        k.register_tool(t)
    for t in marketing_extra_tools(client):
        k.register_tool(t)
    for t in lead_tools(client):
        k.register_tool(t)
    for factory in (finance_tools, operations_tools, legal_tools, hr_tools, catalog_tools):
        for t in factory(client):
            k.register_tool(t)
    for t in all_connectors():          # connettori esterni env-gated (graceful [])
        if t.name in ("leggi_inbox", "leggi_ranking_seo"):
            continue                    # sostituiti sotto: posta + ranking SEO via tabella (n8n)
        k.register_tool(t)
    k.register_tool(n8n_tool())         # braccio esecutore esterno (env-gated)
    k.register_tool(n8n_workflows_tool())  # sensore: elenco workflow n8n (readonly)
    k.register_tool(n8n_executions_tool())  # sensore: esecuzioni (partite? errori?)

    # Lettura GENERICA di qualsiasi tabella Supabase (service key = accesso pieno).
    # Readonly: filtri PostgREST opzionali (es. {"stato":"eq.usato"}), cap a 200 righe.
    def _leggi_tabella(tabella: str | None = None, filtri: dict | None = None,
                       limit: int = 50, ordine: str | None = None, **_):
        if not tabella:
            return {"error": "specifica 'tabella'"}
        params = {"select": "*", "limit": str(max(1, min(int(limit or 50), 200)))}
        if ordine:
            params["order"] = str(ordine)
        if isinstance(filtri, dict):
            for kk, vv in filtri.items():
                params[str(kk)] = str(vv)
        try:
            return client.select(str(tabella), params)
        except Exception as exc:
            return {"error": str(exc)[:200]}
    k.register_tool(Tool(name="leggi_tabella", action_type=None, readonly=True,
                         run=_leggi_tabella))

    # Generazione immagini (GPT Image) → caricata su Storage → URL pubblico pronto per
    # essere pubblicato con `esegui` pubblica_post. Env: OPENAI_API_KEY.
    def _genera_immagine(prompt: str | None = None, **_):
        if not prompt:
            return {"error": "specifica 'prompt' (descrizione dell'immagine)"}
        from aios.image_gen import generate_image
        from aios.storage import upload_public
        g = generate_image(str(prompt))
        if not g.get("ok"):
            return {"error": g.get("errore")}
        if g.get("url"):
            return {"ok": True, "url": g["url"],
                    "nota": "immagine generata (URL OpenAI, temporaneo)"}
        up = upload_public("ai-image.png", "image/png", g.get("b64", ""))
        if not up.get("ok"):
            return {"error": "immagine generata ma upload fallito: " + str(up.get("errore"))}
        return {"ok": True, "url": up["url"],
                "nota": "immagine generata e caricata — usa questo url in pubblica_post"}
    k.register_tool(Tool(name="genera_immagine", action_type=None, readonly=True,
                         run=_genera_immagine))

    # Watchdog n8n: controlla le esecuzioni, riavvia i fallimenti transitori (con tetto),
    # propone i fix per gli strutturali. Lanciabile a mano dalla chat oltre che dallo scheduler.
    def _controlla_workflow(**_):
        from aios.n8n_watchdog import check_and_heal
        try:
            return check_and_heal(log_client=client)
        except Exception as exc:
            return {"ok": False, "errore": str(exc)[:200]}
    k.register_tool(Tool(name="controlla_workflow_n8n", action_type=None, readonly=True,
                         run=_controlla_workflow))
    k.register_tool(prospects_tool(client))  # sensore: prospect marketing (readonly)
    from aios.competitor_scout import competitors_tool
    k.register_tool(competitors_tool(client))  # sensore: competitor trovati (readonly)
    # leggi_inbox via tabella alimentata da n8n (Outlook OAuth) — override dell'IMAP,
    # che il tenant MFA/Conditional Access blocca. Degrada a [] se la tabella è vuota.
    def _inbox_table():
        try:
            return client.select("email_messages",
                                 {"select": "*", "direction": "eq.in",
                                  "order": "received_at.desc", "limit": "30"})
        except Exception:
            return []
    k.register_tool(Tool(name="leggi_inbox", action_type=None, readonly=True,
                         run=lambda **_: _inbox_table()))
    # leggi_ranking_seo via tabella alimentata da n8n (Google OAuth), perché la policy
    # org blocca le chiavi service account. Legge l'ultimo batch (fetched_on max),
    # dedup per query; fallback alla chiamata GSC diretta se un giorno colleghi la SA.
    from aios.sources.connectors import _gsc_ranking
    def _ranking_table():
        try:
            last = client.select("seo_rankings",
                                 {"select": "fetched_on", "order": "fetched_on.desc", "limit": "1"})
            if last:
                fa = last[0].get("fetched_on")
                rows = client.select("seo_rankings",
                                     {"select": "*", "fetched_on": f"eq.{fa}",
                                      "order": "clicks.desc", "limit": "200"})
                seen, out = set(), []
                for r in rows:
                    q = r.get("query")
                    if q in seen:
                        continue
                    seen.add(q)
                    out.append(r)
                if out:
                    return out
        except Exception:
            pass
        try:
            return _gsc_ranking()        # fallback diretto (vuoto senza credenziali SA)
        except Exception:
            return []
    k.register_tool(Tool(name="leggi_ranking_seo", action_type=None, readonly=True,
                         run=lambda **_: _ranking_table()))
    from aios.sources.n8n import N8N_ACTION
    from aios.autonomy import AutonomyLevel as _AL
    k.policy.set_level(N8N_ACTION, _AL.L1_PROPOSE)   # esterno: mai autonomo
    k.policy.set_cap(N8N_ACTION, _AL.L1_PROPOSE)

    founder = default_founder_model()
    skills = SkillLibrary()
    knowledge = KnowledgeStore(client)
    # Backend LLM selezionabile via env AIOS_LLM_BACKEND:
    #   "local"    → LocalLLM (Ollama sul GB10, raggiunto via Tailscale) — "tutto in locale"
    #   "anthropic"→ API Claude (default sicuro: nessun cambio di comportamento al deploy).
    # Si accende il locale impostando AIOS_LLM_BACKEND=local nell'env Railway (persistente
    # = "sempre attivo"), una volta che la tailnet verso l'Ollama è su.
    # NB: la web search (llm_web, sotto) resta SEMPRE su Anthropic, per scelta.
    llm = _make_llm(max_tokens=4096)
    # modello "strong" per i casi delicati (schema DB / codice / workflow) via CommandRouter
    llm_strong = _make_llm(max_tokens=8192, strong=True)

    def _domain(cfg):
        return DomainAgent(kernel=k, llm=llm, llm_strong=llm_strong,
                           founder=founder, config=cfg,
                           skills=skills, knowledge=knowledge, deliverable_client=client)

    agents = {
        "marketing": MarketingAgent(kernel=k, llm=llm, llm_strong=llm_strong,
                                    founder=founder, skills=skills),
        "vendite": _domain(SALES_CONFIG),
        "finance": _domain(FINANCE_CONFIG),
        "operations": _domain(OPERATIONS_CONFIG),
        "legal": _domain(LEGAL_CONFIG),
        "hr": _domain(HR_CONFIG),
    }
    platform = Platform(k, agents)
    platform.org = _org.get_chart()                                # organigramma navigabile
    platform.commands = CommandRouter(platform, llm, llm_strong)   # chat a istruzioni
    # Chat multi-agente in streaming: parli con uno/alcuni/tutti gli agenti in parallelo,
    # con stato reale (pensa/usa tool/scrive). Riusa attuatore+coda del CommandRouter.
    from aios.chat_runner import ChatOrchestrator
    platform.chat = ChatOrchestrator(platform, llm, llm_strong, skills=skills,
                                     web_search=True)
    # Prospecting: ricerca web (Sonnet + web search) → qualifica → bozza (mai inviata)
    llm_web = AnthropicLLM(model="claude-sonnet-4-6", max_tokens=4096, enable_web_search=True)
    def _suite():
        try:
            return k.execute("leggi_suite", actor="prospector", args={}).result
        except Exception:
            return []
    platform.prospector = Prospector(llm_web, llm_strong, founder, suite_reader=_suite)
    from aios.competitor_scout import CompetitorScout
    platform.competitor_scout = CompetitorScout(llm_web, llm_strong, founder, suite_reader=_suite)
    from aios.conversation import ConversationManager
    platform._founder = founder
    platform.conversations = ConversationManager(platform, llm_strong)  # email L1 assistito
    return platform
