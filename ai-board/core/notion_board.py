from __future__ import annotations

from datetime import date, datetime, timedelta
from functools import lru_cache
import re
from typing import Any

import httpx

from core.config import settings

NOTION_API_BASE = "https://api.notion.com/v1"

DB_TASKS = "Task"
DB_PIPELINE = "Pipeline Lead"
DB_CLIENTS = "Clienti"
DB_PROJECTS = "Commesse"
DB_APPROVALS = "Approvazioni"
DB_LOGS = "Log AI"
DB_MEMORY = "Memoria / Decisioni"
IGNORED_DATABASES = {"Verbali / Sopralluoghi"}

TASK_STATUS_TO_NOTION = {
    "pending": "Da fare",
    "running": "In corso",
    "draft": "Backlog",
    "review": "In review",
    "approved": "Approvato",
    "done": "Fatto",
    "rejected": "Bloccato",
    "error": "Bloccato",
}
TASK_STATUS_FROM_NOTION = {value: key for key, value in TASK_STATUS_TO_NOTION.items()}
TASK_STATUS_FROM_NOTION["Backlog"] = "pending"
TASK_STATUS_FROM_NOTION["Bloccato"] = "error"

REQUESTED_BY_TO_NOTION = {
    "founder": "Founder",
    "website_contact_form": "Cliente",
    "website_k_bot": "K-BOT",
    "telegram": "Telegram",
    "ai_agent": "AI Agent",
    "agent": "AI Agent",
    "internal": "Interno",
}

PRIORITY_TO_NOTION = {
    1: "Critica",
    2: "Alta",
    3: "Media",
    4: "Bassa",
    5: "Bassa",
}
PRIORITY_FROM_NOTION = {
    "Critica": 1,
    "Alta": 2,
    "Media": 3,
    "Bassa": 4,
}

PIPELINE_STATUS_TO_NOTION = {
    "identified": "Identificato",
    "qualified": "Qualificato",
    "contacted": "Contattato",
    "call_scheduled": "Call fissata",
    "proposal_sent": "Proposta inviata",
    "won": "Vinto",
    "lost": "Perso",
}
PIPELINE_STATUS_FROM_NOTION = {value: key for key, value in PIPELINE_STATUS_TO_NOTION.items()}

PIPELINE_CHANNEL_TO_NOTION = {
    "website_contact_form": "Sito",
    "website_k_bot": "K-BOT",
    "kbot": "K-BOT",
    "telegram": "Interno",
    "founder": "Interno",
    "internal": "Interno",
}

APPROVAL_STATUS_TO_NOTION = {
    "draft": "Draft",
    "review": "In review",
    "approved": "Approvato",
    "rejected": "Respinto",
    "error": "Respinto",
}
APPROVAL_STATUS_FROM_NOTION = {value: key for key, value in APPROVAL_STATUS_TO_NOTION.items()}

LOG_STATUS_TO_NOTION = {
    "draft": "Success",
    "review": "In corso",
    "approved": "Success",
    "done": "Success",
    "success": "Success",
    "pending": "In corso",
    "running": "In corso",
    "error": "Errore",
    "rejected": "Errore",
}
LOG_STATUS_FROM_NOTION = {
    "Success": "success",
    "Errore": "error",
    "In corso": "running",
}

AGENT_TO_NOTION = {
    "chief_of_staff": "Chief of Staff",
    "solution_architect": "Solution Architect",
    "content_engine": "Content Engine",
    "sales_enablement": "Sales",
    "finance_kpi": "Finance",
    "market_intelligence": "Market Intelligence",
    "orchestrator": "Orchestrator",
    "legal": "Legal",
    "geo_seo": "Geo SEO",
    "lead_generation": "Sales",
}
AGENT_FROM_NOTION = {value: key for key, value in AGENT_TO_NOTION.items()}
LOG_AGENT_ALLOWED = {
    "Chief of Staff",
    "Solution Architect",
    "Content Engine",
    "Sales",
    "Finance",
    "Market Intelligence",
    "Orchestrator",
    "Legal",
    "Geo SEO",
}

PROVIDER_TO_NOTION = {
    "openai": "OpenAI",
    "anthropic": "Anthropic",
}
PROVIDER_FROM_NOTION = {value: key for key, value in PROVIDER_TO_NOTION.items()}

MEMORY_CATEGORY_TO_NOTION = {
    "business": "Processo",
    "offers": "Offerta",
    "proof": "Commerciale",
    "rules": "Metodo",
    "messaging": "Commerciale",
    "technical": "Tecnico",
    "tech": "Tecnico",
    "decision": "Decisione",
    "commercial": "Commerciale",
    "client": "Cliente",
}


class NotionBoardError(RuntimeError):
    pass


def notion_enabled() -> bool:
    return settings.board_data_backend == "notion" and bool(settings.notion_token and settings.notion_page_id)


def _headers() -> dict[str, str]:
    if not settings.notion_token:
        raise NotionBoardError("NOTION_TOKEN non configurato")
    return {
        "Authorization": f"Bearer {settings.notion_token}",
        "Notion-Version": settings.notion_version,
        "Content-Type": "application/json",
    }


def _request(method: str, path: str, **kwargs) -> dict:
    with httpx.Client(base_url=NOTION_API_BASE, timeout=25, headers=_headers()) as client:
        response = client.request(method, path, **kwargs)
    if response.status_code >= 400:
        raise NotionBoardError(f"Notion {response.status_code}: {response.text[:500]}")
    if not response.content:
        return {}
    return response.json()


@lru_cache(maxsize=1)
def get_database_ids() -> dict[str, str]:
    if not settings.notion_page_id:
        raise NotionBoardError("NOTION_PAGE_ID non configurato")

    database_ids: dict[str, str] = {}
    next_cursor = None
    while True:
        query = "?page_size=100"
        if next_cursor:
            query += f"&start_cursor={next_cursor}"
        payload = _request("GET", f"/blocks/{settings.notion_page_id}/children{query}")
        for block in payload.get("results", []):
            if block.get("type") == "child_database":
                title = block.get("child_database", {}).get("title")
                if title:
                    database_ids[title] = block["id"]
        if not payload.get("has_more"):
            return database_ids
        next_cursor = payload.get("next_cursor")


def _database_id(title: str) -> str:
    database_id = get_database_ids().get(title)
    if not database_id:
        raise NotionBoardError(f"Database Notion non trovato: {title}")
    return database_id


def _rich_text(value: str | None) -> dict:
    if not value:
        return {"rich_text": []}
    return {"rich_text": [{"text": {"content": str(value)[:1900]}}]}


def _title(value: str | None) -> dict:
    return {"title": [{"text": {"content": (value or "Senza titolo")[:1900]}}]}


def _select(value: str | None) -> dict:
    return {"select": {"name": value}} if value else {"select": None}


def _number(value: int | float | None) -> dict:
    return {"number": value}


def _date(value: str | date | datetime | None) -> dict:
    if not value:
        return {"date": None}
    if isinstance(value, datetime):
        start = value.isoformat()
    elif isinstance(value, date):
        start = value.isoformat()
    else:
        start = str(value)
    return {"date": {"start": start}}


def _checkbox(value: bool) -> dict:
    return {"checkbox": bool(value)}


def _relation(page_id: str | None) -> dict:
    return {"relation": [{"id": page_id}]} if page_id else {"relation": []}


def _relation_many(page_ids: list[str] | None) -> dict:
    ids = [item for item in (page_ids or []) if item]
    return {"relation": [{"id": item} for item in ids]}


def _merge_relation_ids(existing: list[str], *new_ids: str | None) -> list[str]:
    merged = list(existing)
    for item in new_ids:
        if item and item not in merged:
            merged.append(item)
    return merged


def _normalize_log_agent(agent: str | None) -> str:
    label = AGENT_TO_NOTION.get(agent or "", "") or (agent or "").replace("_", " ").title()
    return label if label in LOG_AGENT_ALLOWED else "Orchestrator"


def _children_from_text(text: str | None, heading: str | None = None) -> list[dict]:
    content = str(text or "")
    children: list[dict] = []
    if heading:
        children.append(
            {
                "object": "block",
                "type": "heading_3",
                "heading_3": {"rich_text": [{"type": "text", "text": {"content": heading[:1900]}}]},
            }
        )
    if not content.strip():
        return children
    for index in range(0, len(content), 1900):
        chunk = content[index:index + 1900]
        children.append(
            {
                "object": "block",
                "type": "paragraph",
                "paragraph": {"rich_text": [{"type": "text", "text": {"content": chunk}}]},
            }
        )
    return children


_MD_TOKEN_RE = re.compile(
    r"(\*\*.+?\*\*|__.+?__|(?<!\*)\*[^*\n]+\*(?!\*)|(?<!\w)_[^_\n]+_(?!\w)|`[^`]+`)",
    re.DOTALL,
)
_MD_HEADING_ONLY_RE = re.compile(r"^\*\*(.+?)\*\*$")
_MD_ATX_HEADING_RE = re.compile(r"^(#{1,6})\s+(.+)$")
_MD_UNORDERED_ITEM_RE = re.compile(r"^[-*]\s+(.+)$")
_MD_ORDERED_ITEM_RE = re.compile(r"^\d+[.)]\s+(.+)$")
_MD_DIVIDER_RE = re.compile(r"^[-_─—]{3,}$")


def _md_inline_to_rich_text(value: str) -> list[dict]:
    text = str(value or "")
    if not text:
        return []

    items: list[dict] = []
    cursor = 0

    def _push_chunk(chunk: str, bold: bool = False, italic: bool = False, code: bool = False) -> None:
        if not chunk:
            return
        for start in range(0, len(chunk), 1900):
            part = chunk[start:start + 1900]
            items.append(
                {
                    "type": "text",
                    "text": {"content": part},
                    "annotations": {
                        "bold": bool(bold),
                        "italic": bool(italic),
                        "code": bool(code),
                    },
                }
            )

    for match in _MD_TOKEN_RE.finditer(text):
        if match.start() > cursor:
            _push_chunk(text[cursor:match.start()])
        token = match.group(0)
        if token.startswith("**") and token.endswith("**"):
            _push_chunk(token[2:-2], bold=True)
        elif token.startswith("__") and token.endswith("__"):
            _push_chunk(token[2:-2], bold=True)
        elif token.startswith("*") and token.endswith("*"):
            _push_chunk(token[1:-1], italic=True)
        elif token.startswith("_") and token.endswith("_"):
            _push_chunk(token[1:-1], italic=True)
        elif token.startswith("`") and token.endswith("`"):
            _push_chunk(token[1:-1], code=True)
        else:
            _push_chunk(token)
        cursor = match.end()

    if cursor < len(text):
        _push_chunk(text[cursor:])
    return items


def _children_from_markdown_text(text: str | None, heading: str | None = None) -> list[dict]:
    content = str(text or "")
    children: list[dict] = []
    if heading:
        children.append(
            {
                "object": "block",
                "type": "heading_3",
                "heading_3": {"rich_text": [{"type": "text", "text": {"content": heading[:1900]}}]},
            }
        )
    if not content.strip():
        return children

    for raw_line in content.splitlines():
        line = raw_line.rstrip()
        stripped = line.strip()
        if not stripped:
            children.append(
                {
                    "object": "block",
                    "type": "paragraph",
                    "paragraph": {"rich_text": [{"type": "text", "text": {"content": " "}}]},
                }
            )
            continue

        if _MD_DIVIDER_RE.fullmatch(stripped):
            children.append({"object": "block", "type": "divider", "divider": {}})
            continue

        atx_heading = _MD_ATX_HEADING_RE.match(stripped)
        if atx_heading:
            level = min(len(atx_heading.group(1)), 3)
            text_value = atx_heading.group(2).strip()
            rich = _md_inline_to_rich_text(text_value) or [{"type": "text", "text": {"content": text_value[:1900]}}]
            heading_type = "heading_2" if level <= 2 else "heading_3"
            children.append(
                {
                    "object": "block",
                    "type": heading_type,
                    heading_type: {"rich_text": rich},
                }
            )
            continue

        bold_heading = _MD_HEADING_ONLY_RE.match(stripped)
        if bold_heading:
            text_value = bold_heading.group(1).strip()
            rich = _md_inline_to_rich_text(text_value) or [{"type": "text", "text": {"content": text_value[:1900]}}]
            children.append(
                {
                    "object": "block",
                    "type": "heading_3",
                    "heading_3": {"rich_text": rich},
                }
            )
            continue

        unordered_item = _MD_UNORDERED_ITEM_RE.match(stripped)
        if unordered_item:
            text_value = unordered_item.group(1).strip()
            rich = _md_inline_to_rich_text(text_value) or [{"type": "text", "text": {"content": text_value[:1900]}}]
            children.append(
                {
                    "object": "block",
                    "type": "bulleted_list_item",
                    "bulleted_list_item": {"rich_text": rich},
                }
            )
            continue

        ordered_item = _MD_ORDERED_ITEM_RE.match(stripped)
        if ordered_item:
            text_value = ordered_item.group(1).strip()
            rich = _md_inline_to_rich_text(text_value) or [{"type": "text", "text": {"content": text_value[:1900]}}]
            children.append(
                {
                    "object": "block",
                    "type": "numbered_list_item",
                    "numbered_list_item": {"rich_text": rich},
                }
            )
            continue

        rich = _md_inline_to_rich_text(line)
        if not rich:
            rich = [{"type": "text", "text": {"content": " "}}]
        children.append(
            {
                "object": "block",
                "type": "paragraph",
                "paragraph": {"rich_text": rich},
            }
        )
    return children


def _plain_text(prop: dict | None) -> str:
    if not prop:
        return ""
    items = prop.get("rich_text") or prop.get("title") or []
    return "".join(item.get("plain_text", "") for item in items)


def _select_name(prop: dict | None) -> str | None:
    if not prop or not prop.get("select"):
        return None
    return prop["select"].get("name")


def _number_value(prop: dict | None) -> int | float | None:
    if not prop:
        return None
    return prop.get("number")


def _date_value(prop: dict | None) -> str | None:
    if not prop or not prop.get("date"):
        return None
    return prop["date"].get("start")


def _checkbox_value(prop: dict | None) -> bool:
    return bool(prop and prop.get("checkbox"))


def _relation_ids(prop: dict | None) -> list[str]:
    if not prop:
        return []
    return [item.get("id") for item in prop.get("relation") or [] if item.get("id")]


def _people_text(prop: dict | None) -> str:
    if not prop:
        return ""
    people = prop.get("people") or []
    names = [item.get("name") for item in people if item.get("name")]
    return ", ".join(names)


def _query_database(database_title: str, sorts: list[dict] | None = None) -> list[dict]:
    database_id = _database_id(database_title)
    return _query_database_by_id(database_id, sorts)


def _query_database_by_id(database_id: str, sorts: list[dict] | None = None) -> list[dict]:
    results: list[dict] = []
    next_cursor = None
    while True:
        body: dict[str, Any] = {"page_size": 100}
        if sorts:
            body["sorts"] = sorts
        if next_cursor:
            body["start_cursor"] = next_cursor
        payload = _request("POST", f"/databases/{database_id}/query", json=body)
        results.extend(payload.get("results", []))
        if not payload.get("has_more"):
            return results
        next_cursor = payload.get("next_cursor")


def count_database_pages(database_title: str) -> int:
    return len([page for page in _query_database(database_title) if not page.get("archived")])


def archive_database_pages(database_title: str) -> int:
    archived = 0
    for page in _query_database(database_title):
        if page.get("archived"):
            continue
        _request("PATCH", f"/pages/{page['id']}", json={"archived": True})
        archived += 1
    return archived


def archive_all_board_data() -> dict[str, int]:
    archived_counts: dict[str, int] = {}
    for title in sorted(get_database_ids()):
        if title in IGNORED_DATABASES:
            continue
        archived_counts[title] = archive_database_pages(title)
    return archived_counts


def list_tasks(status_filter: str | None = None) -> list[dict]:
    pages = _query_database(DB_TASKS, sorts=[{"timestamp": "created_time", "direction": "descending"}])
    tasks = [_task_from_page(page) for page in pages if not page.get("archived")]
    if status_filter and status_filter != "all":
        tasks = [task for task in tasks if task.get("status") == status_filter]
    return tasks


def list_clients() -> list[dict]:
    pages = _query_database(DB_CLIENTS, sorts=[{"timestamp": "created_time", "direction": "descending"}])
    return [_client_from_page(page) for page in pages if not page.get("archived")]


def find_client_by_email(email: str) -> dict | None:
    target = (email or "").strip().lower()
    if not target:
        return None
    return next((client for client in list_clients() if (client.get("email") or "").strip().lower() == target), None)


def find_client_by_name(company_name: str) -> dict | None:
    target = (company_name or "").strip().lower()
    if not target:
        return None
    return next((client for client in list_clients() if (client.get("company_name") or "").strip().lower() == target), None)


def create_or_get_client(
    company_name: str,
    contact_name: str = "",
    email: str = "",
    sector: str = "Altro",
    phone: str = "",
    notes: str = "",
) -> str:
    existing = find_client_by_email(email) or find_client_by_name(company_name)
    if existing:
        client_id = existing["id"]
        _request(
            "PATCH",
            f"/pages/{client_id}",
            json={
                "properties": {
                    "Nome cliente / società": _title(company_name or existing.get("company_name") or "Cliente"),
                    "Referente": _rich_text(contact_name or existing.get("contact_name") or ""),
                    "Email": {"email": email or existing.get("email")},
                    "Settore": _select(sector or existing.get("sector") or "Altro"),
                    "Telefono": {"phone_number": phone or existing.get("phone")},
                    "Stato relazione": _select("Lead"),
                    "Note": _rich_text(notes or existing.get("notes") or ""),
                }
            },
        )
        return client_id

    payload = {
        "parent": {"database_id": _database_id(DB_CLIENTS)},
        "properties": {
            "Nome cliente / società": _title(company_name or contact_name or "Cliente"),
            "Referente": _rich_text(contact_name),
            "Email": {"email": email or None},
            "Settore": _select(sector or "Altro"),
            "Telefono": {"phone_number": phone or None},
            "Stato relazione": _select("Lead"),
            "Note": _rich_text(notes),
        },
    }
    page = _request("POST", "/pages", json=payload)
    return page["id"]


def create_project_for_client(
    client_id: str,
    lead_name: str,
    notes: str = "",
    offer_type: str = "Consulenza",
) -> str:
    payload = {
        "parent": {"database_id": _database_id(DB_PROJECTS)},
        "properties": {
            "Nome commessa": _title(f"Intake sito — {lead_name}"),
            "Cliente": _relation(client_id),
            "Stato": _select("Nuova"),
            "Tipo offerta": _select(offer_type),
            "Priorità": _select("Media"),
            "Data inizio": _date(date.today()),
            "Note operative": _rich_text(notes),
            "Prossima azione": _rich_text("Primo contatto e qualificazione iniziale"),
        },
    }
    page = _request("POST", "/pages", json=payload)
    return page["id"]


def create_client_intake_subpage(
    client_id: str,
    contact_name: str,
    email: str,
    message: str,
    source_page: str,
    internal_context: str = "",
    project_id: str | None = None,
    lead_id: str | None = None,
    task_id: str | None = None,
) -> str:
    title = f"Intake sito — {contact_name or 'Contatto'}"
    detail_lines = [
        f"Nome: {contact_name or 'Non indicato'}",
        f"Email: {email or 'Non indicata'}",
        f"Origine: {source_page or '/contatti.html'}",
        "",
        "Messaggio:",
        message or "Nessun messaggio",
    ]
    if internal_context:
        detail_lines += ["", "Contesto K-BOT:", internal_context]
    links: list[str] = []
    if project_id:
        links.append(f"- Commessa: {project_id}")
    if lead_id:
        links.append(f"- Lead: {lead_id}")
    if task_id:
        links.append(f"- Task: {task_id}")
    if links:
        detail_lines += ["", "Collegamenti operativi:", *links]
    payload = {
        "parent": {"page_id": client_id},
        "properties": {"title": _title(title)},
        "children": _children_from_markdown_text("\n".join(detail_lines), "Nuovo form dal sito"),
    }
    page = _request("POST", "/pages", json=payload)
    return page["id"]


def append_markdown_section_to_page(page_id: str, heading: str, content: str) -> None:
    children = _children_from_markdown_text(content, heading=heading)[:100]
    if not children:
        return
    _request("PATCH", f"/blocks/{page_id}/children", json={"children": children})


def _append_relations_on_page(page_id: str, relation_updates: dict[str, str | None]) -> None:
    page = _request("GET", f"/pages/{page_id}")
    props = page.get("properties", {})
    patch_props: dict[str, dict] = {}
    for prop_name, related_id in relation_updates.items():
        if not related_id:
            continue
        existing = _relation_ids(props.get(prop_name))
        merged = _merge_relation_ids(existing, related_id)
        patch_props[prop_name] = _relation_many(merged)
    if patch_props:
        _request("PATCH", f"/pages/{page_id}", json={"properties": patch_props})


def create_task(
    title: str,
    description: str = "",
    assigned_to: str = "",
    priority: int = 3,
    status: str = "pending",
    requested_by: str = "founder",
    notes: str = "",
    task_type: str = "Operativo",
    project_id: str | None = None,
    lead_id: str | None = None,
    client_id: str | None = None,
    due_date: str | date | datetime | None = None,
) -> str:
    database_id = _database_id(DB_TASKS)
    output_notes = notes
    if assigned_to:
        output_notes = f"Assegnato a: {assigned_to}\n{notes}".strip()
    payload = {
        "parent": {"database_id": database_id},
        "properties": {
            "Titolo task": _title(title),
            "Descrizione": _rich_text(description),
            "Tipo task": _select(task_type),
            "Richiesto da": _select(REQUESTED_BY_TO_NOTION.get(requested_by, "Interno")),
            "Stato": _select(TASK_STATUS_TO_NOTION.get(status, "Da fare")),
            "Priorità": _select(PRIORITY_TO_NOTION.get(priority, "Media")),
            "Scadenza": _date(due_date),
            "Output": _rich_text(output_notes),
            "Cliente": _relation(client_id),        # relation (rinominata da 'Cliente collegato')
            "Commessa": _relation(project_id),
            "Lead collegato": _relation(lead_id),
        },
    }
    page = _request("POST", "/pages", json=payload)
    return page["id"]


def update_task_status(task_id: str, status: str, notes: str | None = None) -> None:
    properties = {"Stato": _select(TASK_STATUS_TO_NOTION.get(status, "Da fare"))}
    if notes:
        properties["Output"] = _rich_text(notes)
    _request("PATCH", f"/pages/{task_id}", json={"properties": properties})


def archive_task(task_id: str) -> None:
    _request("PATCH", f"/pages/{task_id}", json={"archived": True})


def get_task(task_id: str) -> dict | None:
    page = _request("GET", f"/pages/{task_id}")
    if page.get("archived"):
        return None
    return _task_from_page(page)


def list_pipeline_leads() -> list[dict]:
    pages = _query_database(DB_PIPELINE, sorts=[{"timestamp": "created_time", "direction": "ascending"}])
    return [_lead_from_page(page) for page in pages if not page.get("archived")]


def create_pipeline_lead(
    name: str,
    company: str = "",
    sector: str = "",
    pain_point: str = "",
    channel: str = "",
    score: int = 5,
    next_action: str = "Qualifica iniziale",
    notes: str = "",
    client_id: str | None = None,
    project_id: str | None = None,
) -> str:
    database_id = _database_id(DB_PIPELINE)
    next_action_date = date.today() + timedelta(days=2)
    payload = {
        "parent": {"database_id": database_id},
        "properties": {
            "Nome lead": _title(name),
            "Azienda": _rich_text(company),
            "Settore": _select(sector or "Altro"),
            "Pain point": _rich_text(pain_point),
            "Canale": _select(PIPELINE_CHANNEL_TO_NOTION.get(channel, channel or "Interno")),
            "Stato": _select("Identificato"),
            "Score": _number(score),
            "Prossima azione": _rich_text(next_action),
            "Data prossima azione": _date(next_action_date),
            "Note": _rich_text(notes),
            "Cliente collegato": _relation(client_id),
            "Commessa creata": _relation(project_id),
        },
    }
    page = _request("POST", "/pages", json=payload)
    return page["id"]


def create_pipeline_lead_from_contact(
    name: str,
    email: str,
    company_role: str = "",
    sector: str = "",
    message: str = "",
    source_page: str = "",
    internal_context: str = "",
) -> dict[str, str]:
    notes = "\n".join(
        part
        for part in [
            f"Email: {email}",
            f"Azienda / ruolo: {company_role or 'Non indicato'}",
            f"Origine: {source_page or 'Sito'}",
            "",
            "Messaggio:",
            message,
            "",
            "Contesto K-BOT:",
            internal_context,
        ]
        if part is not None and part != ""
    )
    company_name = (company_role or "").strip() or name
    client_id = create_or_get_client(
        company_name=company_name,
        contact_name=name,
        email=email,
        sector=sector or "Altro",
        notes=notes[:1900],
    )
    project_id = create_project_for_client(
        client_id=client_id,
        lead_name=name,
        notes=notes[:1900],
        offer_type="Consulenza",
    )
    lead_id = create_pipeline_lead(
        name=name,
        company=company_name,
        sector=sector or "Altro",
        pain_point=message[:1900],
        channel="website_contact_form",
        score=6,
        next_action="Ricontattare il lead e qualificare il caso",
        notes=notes,
        client_id=client_id,
        project_id=project_id,
    )
    _append_relations_on_page(
        client_id,
        {
            "Lead collegati": lead_id,
            "Commesse": project_id,
        },
    )
    _append_relations_on_page(
        project_id,
        {
            "Lead collegati": lead_id,
        },
    )
    return {"client_id": client_id, "project_id": project_id, "lead_id": lead_id}


def update_lead_status(lead_id: str, status: str) -> None:
    _request(
        "PATCH",
        f"/pages/{lead_id}",
        json={"properties": {"Stato": _select(PIPELINE_STATUS_TO_NOTION.get(status, "Identificato"))}},
    )


def archive_lead(lead_id: str) -> None:
    _request("PATCH", f"/pages/{lead_id}", json={"archived": True})


def create_approval(
    task_id: str | None,
    agent: str,
    content_type: str,
    content_preview: str,
    full_content: dict[str, Any] | None = None,
    project_id: str | None = None,
) -> str:
    database_id = _database_id(DB_APPROVALS)
    full_content_text = ""
    if full_content:
        import json

        full_content_text = json.dumps(full_content, ensure_ascii=False, indent=2, default=str)
    payload = {
        "parent": {"database_id": database_id},
        "properties": {
            "Titolo approvazione": _title(f"{AGENT_TO_NOTION.get(agent, agent)} · {content_type}"),
            "Stato": _select("Draft"),
            "Tipo contenuto": _select(_content_type_to_notion(content_type)),
            "Anteprima contenuto": _rich_text(content_preview),
            "Note founder": _rich_text(full_content_text[:1900] if full_content_text else ""),
            "Task": _relation(task_id),
            "Commessa": _relation(project_id),
        },
        "children": _children_from_text(full_content_text, "Contenuto completo")[:100],
    }
    page = _request("POST", "/pages", json=payload)
    return page["id"]


def list_approvals(statuses: list[str] | None = None, limit: int | None = None) -> list[dict]:
    pages = _query_database(DB_APPROVALS, sorts=[{"timestamp": "created_time", "direction": "descending"}])
    approvals = [_approval_from_page(page, include_children=False) for page in pages if not page.get("archived")]
    if statuses:
        allowed = set(statuses)
        approvals = [item for item in approvals if item.get("status") in allowed]
    if limit:
        approvals = approvals[:limit]
    return approvals


def get_approval(approval_id: str) -> dict | None:
    page = _request("GET", f"/pages/{approval_id}")
    if page.get("archived"):
        return None
    return _approval_from_page(page, include_children=True)


def update_approval_status(approval_id: str, status: str, notes: str | None = None) -> dict | None:
    properties: dict[str, Any] = {
        "Stato": _select(APPROVAL_STATUS_TO_NOTION.get(status, "Draft")),
        "Data revisione": _date(datetime.now()),
    }
    if notes:
        properties["Note founder"] = _rich_text(notes)
    _request("PATCH", f"/pages/{approval_id}", json={"properties": properties})
    return get_approval(approval_id)


def create_agent_log(
    agent: str,
    action: str,
    output_summary: str,
    status: str,
    task_id: str | None = None,
    input_summary: str | None = None,
    duration_ms: int | None = None,
    tokens_used: int | None = None,
    llm_provider: str | None = None,
    llm_model: str | None = None,
    approval_id: str | None = None,
    project_id: str | None = None,
    requires_approval: bool = False,
) -> str:
    database_id = _database_id(DB_LOGS)
    provider_value = PROVIDER_TO_NOTION.get(str(llm_provider or "").lower(), "Altro") if llm_provider else None
    payload = {
        "parent": {"database_id": database_id},
        "properties": {
            "Titolo log": _title(action or "Attività AI"),
            "Agente": _select(_normalize_log_agent(agent)),
            "Azione": _rich_text(action),
            "Input summary": _rich_text(input_summary),
            "Output summary": _rich_text(output_summary),
            "Stato": _select(LOG_STATUS_TO_NOTION.get(status, "In corso")),
            "Provider LLM": _select(provider_value),
            "Modello": _rich_text(llm_model),
            "Token usati": _number(tokens_used),
            "Durata ms": _number(duration_ms),
            "Richiede approvazione": _checkbox(requires_approval),
            "Task": _relation(task_id),
            "Approvazione collegata": _relation(approval_id),
            "Commessa": _relation(project_id),
        },
    }
    page = _request("POST", "/pages", json=payload)
    return page["id"]


def list_agent_logs(agent_name: str | None = None, limit: int = 500) -> list[dict]:
    pages = _query_database(DB_LOGS, sorts=[{"timestamp": "created_time", "direction": "descending"}])
    logs = [_log_from_page(page) for page in pages if not page.get("archived")]
    if agent_name:
        logs = [row for row in logs if row.get("agent") == agent_name]
    return logs[:limit]


def update_logs_status_by_task(task_id: str, status: str) -> None:
    for log in list_agent_logs(limit=500):
        if log.get("task_id") == task_id:
            _request("PATCH", f"/pages/{log['id']}", json={"properties": {"Stato": _select(LOG_STATUS_TO_NOTION.get(status, "In corso"))}})


def list_memory_items() -> list[dict]:
    pages = _query_database(DB_MEMORY, sorts=[{"property": "Categoria", "direction": "ascending"}])
    return [_memory_from_page(page) for page in pages if not page.get("archived")]


def upsert_memory_item(key: str, value: Any, category: str, updated_by: str = "founder") -> str:
    import json

    text_value = json.dumps(value, ensure_ascii=False, default=str) if not isinstance(value, str) else value
    database_id = _database_id(DB_MEMORY)
    existing = next((item for item in list_memory_items() if item.get("key") == key), None)
    props = {
        "Titolo": _title(key),
        "Valore / contenuto": _rich_text(text_value),
        "Categoria": _select(MEMORY_CATEGORY_TO_NOTION.get(category, "Processo")),
        "Fonte": _select("AI" if updated_by not in {"founder", "Founder"} else "Founder"),
    }
    if existing:
        _request("PATCH", f"/pages/{existing['id']}", json={"properties": props})
        return existing["id"]
    page = _request("POST", "/pages", json={"parent": {"database_id": database_id}, "properties": props})
    return page["id"]


def create_lead_from_task(task_id: str) -> str | None:
    task = get_task(task_id)
    if not task:
        return None
    lead_id = create_pipeline_lead(
        name=task.get("title") or "Lead da lavoro",
        sector="PMI",
        pain_point=task.get("description") or task.get("title") or "",
        channel=task.get("source_label") or "Interno",
        score={1: 9, 2: 8, 3: 6, 4: 5, 5: 4}.get(task.get("priority") or 3, 6),
        next_action="Qualifica iniziale dal board",
        notes=f"Spostato da Lavori. Task originale: {task_id}.",
    )
    update_task_status(task_id, "done")
    return lead_id


def _content_type_to_notion(content_type: str) -> str:
    lowered = (content_type or "").lower()
    if any(token in lowered for token in ("proposal", "proposta")):
        return "Proposta"
    if any(token in lowered for token in ("document", "doc", "report", "pdf")):
        return "Documento"
    if any(token in lowered for token in ("quote", "preventivo")):
        return "Preventivo"
    if "verbale" in lowered:
        return "Verbale"
    if any(token in lowered for token in ("agent", "ai", "output", "chat")):
        return "Output AI"
    return "Altro"


def _content_type_from_notion(content_type: str | None) -> str:
    mapping = {
        "Documento": "document",
        "Proposta": "proposal",
        "Output AI": "agent_output",
        "Preventivo": "quote",
        "Verbale": "report",
        "Altro": "agent_output",
    }
    return mapping.get(content_type or "", "agent_output")


def _blocks_plain_text(block_id: str) -> str:
    chunks: list[str] = []
    next_cursor = None
    while True:
        query = "?page_size=100"
        if next_cursor:
            query += f"&start_cursor={next_cursor}"
        payload = _request("GET", f"/blocks/{block_id}/children{query}")
        for block in payload.get("results", []):
            block_type = block.get("type")
            rich_text = block.get(block_type or "", {}).get("rich_text", []) if block_type else []
            plain = "".join(item.get("plain_text", "") for item in rich_text)
            if plain:
                chunks.append(plain)
        if not payload.get("has_more"):
            return "\n\n".join(chunks).strip()
        next_cursor = payload.get("next_cursor")


def _task_from_page(page: dict) -> dict:
    props = page.get("properties", {})
    notion_status = _select_name(props.get("Stato")) or "Da fare"
    notion_priority = _select_name(props.get("Priorità")) or "Media"
    requested_by = _select_name(props.get("Richiesto da")) or "Founder"
    due_date = (
        _date_value(props.get("Scadenza"))
        or _date_value(props.get("Data scadenza"))
        or _date_value(props.get("Deadline"))
        or _date_value(props.get("Due date"))
    )
    return {
        "id": page["id"],
        "title": _plain_text(props.get("Titolo task")),
        "description": _plain_text(props.get("Descrizione")),
        "assigned_to": _people_text(props.get("Assegnato a")) or "Notion",
        "requested_by": requested_by.lower().replace(" ", "_"),
        "source_label": requested_by,
        "status": TASK_STATUS_FROM_NOTION.get(notion_status, "pending"),
        "priority": PRIORITY_FROM_NOTION.get(notion_priority, 3),
        "due_date": due_date,
        "notes": _plain_text(props.get("Output")) or _plain_text(props.get("Blocco / rischio")),
        "created_at": page.get("created_time"),
        "updated_at": page.get("last_edited_time"),
    }


def _lead_from_page(page: dict) -> dict:
    props = page.get("properties", {})
    notion_status = _select_name(props.get("Stato")) or "Identificato"
    return {
        "id": page["id"],
        "name": _plain_text(props.get("Nome lead")),
        "company": _plain_text(props.get("Azienda")),
        "sector": _select_name(props.get("Settore")),
        "channel": _select_name(props.get("Canale")),
        "pain_point": _plain_text(props.get("Pain point")),
        "offer_fit": _plain_text(props.get("Fit offerta")),
        "status": PIPELINE_STATUS_FROM_NOTION.get(notion_status, "identified"),
        "score": _number_value(props.get("Score")),
        "next_action": _plain_text(props.get("Prossima azione")),
        "next_action_date": _date_value(props.get("Data prossima azione")),
        "notes": _plain_text(props.get("Note")),
        "created_at": page.get("created_time"),
        "updated_at": page.get("last_edited_time"),
    }


def _approval_from_page(page: dict, include_children: bool = False) -> dict:
    props = page.get("properties", {})
    title_text = _plain_text(props.get("Titolo approvazione"))
    agent_label = title_text.split(" · ", 1)[0] if title_text else "notion"
    status = APPROVAL_STATUS_FROM_NOTION.get(_select_name(props.get("Stato")) or "Draft", "draft")
    task_ids = _relation_ids(props.get("Task"))
    content_type = _content_type_from_notion(_select_name(props.get("Tipo contenuto")))
    preview = _plain_text(props.get("Anteprima contenuto"))
    full_text = _blocks_plain_text(page["id"]) if include_children else ""
    full_content: dict[str, Any] = {}
    if full_text:
        try:
            import json

            marker = "Contenuto completo"
            payload = full_text.split(marker, 1)[-1].strip() if marker in full_text else full_text
            full_content = json.loads(payload)
        except Exception:
            full_content = {"output": full_text}
    return {
        "id": page["id"],
        "task_id": task_ids[0] if task_ids else None,
        "agent": AGENT_FROM_NOTION.get(agent_label, agent_label),
        "content_type": content_type,
        "content_preview": preview,
        "full_content": full_content,
        "status": status,
        "founder_notes": _plain_text(props.get("Note founder")),
        "created_at": page.get("created_time") or page.get("properties", {}).get("Data richiesta", {}).get("created_time"),
        "reviewed_at": _date_value(props.get("Data revisione")),
    }


def _log_from_page(page: dict) -> dict:
    props = page.get("properties", {})
    agent_label = _select_name(props.get("Agente"))
    task_ids = _relation_ids(props.get("Task"))
    provider_label = _select_name(props.get("Provider LLM"))
    return {
        "id": page["id"],
        "agent": AGENT_FROM_NOTION.get(agent_label or "", agent_label or "notion"),
        "task_id": task_ids[0] if task_ids else None,
        "action": _plain_text(props.get("Azione")) or _plain_text(props.get("Titolo log")),
        "llm_provider": PROVIDER_FROM_NOTION.get(provider_label or "", provider_label),
        "llm_model": _plain_text(props.get("Modello")),
        "input_summary": _plain_text(props.get("Input summary")),
        "output_summary": _plain_text(props.get("Output summary")),
        "status": LOG_STATUS_FROM_NOTION.get(_select_name(props.get("Stato")) or "In corso", "running"),
        "tokens_used": _number_value(props.get("Token usati")),
        "duration_ms": _number_value(props.get("Durata ms")),
        "requires_approval": _checkbox_value(props.get("Richiede approvazione")),
        "created_at": page.get("created_time"),
    }


def _memory_from_page(page: dict) -> dict:
    props = page.get("properties", {})
    key = _plain_text(props.get("Titolo"))
    value_text = _plain_text(props.get("Valore / contenuto"))
    try:
        import json

        value: Any = json.loads(value_text)
    except Exception:
        value = value_text
    category_label = _select_name(props.get("Categoria")) or "Processo"
    category = next((key for key, label in MEMORY_CATEGORY_TO_NOTION.items() if label == category_label), category_label.lower())
    return {
        "id": page["id"],
        "key": key,
        "value": value,
        "category": category,
        "updated_at": page.get("last_edited_time"),
        "updated_by": "notion",
    }


def _client_from_page(page: dict) -> dict:
    props = page.get("properties", {})
    return {
        "id": page["id"],
        "company_name": _plain_text(props.get("Nome cliente / società")),
        "contact_name": _plain_text(props.get("Referente")),
        "email": props.get("Email", {}).get("email") if props.get("Email") else None,
        "phone": props.get("Telefono", {}).get("phone_number") if props.get("Telefono") else None,
        "sector": _select_name(props.get("Settore")),
        "status": _select_name(props.get("Stato relazione")),
        "notes": _plain_text(props.get("Note")),
        "created_at": page.get("created_time"),
        "updated_at": page.get("last_edited_time"),
    }
