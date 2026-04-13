import json
import re
from datetime import UTC, datetime
from html import escape
from pathlib import Path
from typing import Any

import markdown
from fastapi import Request
from fastapi.templating import Jinja2Templates
from loguru import logger
from markupsafe import Markup

from core import notion_board
from db.client import get_service_client
from core.text import markdown_to_plain_text, truncate_text

TEMPLATES_DIR = Path(__file__).resolve().parent.parent / "templates"
templates = Jinja2Templates(directory=str(TEMPLATES_DIR))

NAV_ITEMS = [
    {"key": "home",     "label": "Panoramica", "icon": "grid_view",    "href": "/"},
    {"key": "inbox",    "label": "Inbox",      "icon": "inbox",        "href": "/inbox"},
    {"key": "pipeline", "label": "Pipeline",   "icon": "account_tree", "href": "/pipeline"},
    {"key": "lavori",   "label": "Lavori",     "icon": "checklist",    "href": "/lavori"},
    {"key": "workshop_admin", "label": "Workshop", "icon": "deployed_code", "href": "/workshop-admin"},
    {"key": "admin",    "label": "Admin",      "icon": "settings",     "href": "/admin"},
]


def format_datetime(value: Any) -> str:
    if not value:
        return "—"
    dt = parse_datetime(value)
    if dt is None:
        return str(value)
    return dt.astimezone(UTC).strftime("%d/%m/%Y %H:%M UTC")


def format_date(value: Any) -> str:
    if not value:
        return "—"
    if isinstance(value, str) and len(value) >= 10:
        return value[:10]
    dt = parse_datetime(value)
    if dt is None:
        return str(value)
    return dt.date().isoformat()


def pretty_json(value: Any) -> str:
    return json.dumps(value, ensure_ascii=False, indent=2, default=str)


def _normalize_ai_chart_config(raw_value: Any) -> dict[str, Any]:
    if not isinstance(raw_value, dict):
        raise ValueError("Configurazione grafico non valida")

    if "data" in raw_value:
        config = dict(raw_value)
        config.setdefault("type", "bar")
        return config

    labels = raw_value.get("labels")
    datasets = raw_value.get("datasets")
    if not isinstance(labels, list) or not isinstance(datasets, list):
        raise ValueError("Il grafico richiede labels e datasets")

    return {
        "type": raw_value.get("type", "bar"),
        "data": {
            "labels": labels,
            "datasets": datasets,
        },
        "options": raw_value.get("options", {"responsive": True, "plugins": {"legend": {"position": "bottom"}}}),
    }


def _inject_chart_blocks(text: str) -> str:
    pattern = re.compile(r"```(?:grafico|chart)\s*\n(.*?)```", re.DOTALL | re.IGNORECASE)

    def replace(match: re.Match[str]) -> str:
        payload = match.group(1).strip()
        try:
            config = _normalize_ai_chart_config(json.loads(payload))
            title = ""
            options = config.get("options")
            if isinstance(options, dict):
                plugins = options.get("plugins")
                if isinstance(plugins, dict):
                    title_block = plugins.get("title")
                    if isinstance(title_block, dict) and title_block.get("display") and title_block.get("text"):
                        title = str(title_block["text"])
            serialized = escape(json.dumps(config, ensure_ascii=False))
            title_html = (
                f'<p class="text-xs font-bold uppercase tracking-widest text-on-surface-variant mb-3">{escape(title)}</p>'
                if title
                else ""
            )
            return (
                '<div class="my-4 rounded-xl border border-outline-variant/10 bg-surface-container-lowest p-4">'
                f"{title_html}"
                f'<canvas data-ai-chart-config="{serialized}"></canvas>'
                "</div>"
            )
        except Exception:
            return (
                '<div class="my-4 rounded-xl border border-rose-100 bg-rose-50 p-4 text-xs text-rose-700">'
                "Blocco grafico non valido."
                "</div>"
            )

    return pattern.sub(replace, text)


def render_markdown(value: Any) -> Markup:
    text = "" if value is None else str(value)
    if not text.strip():
        return Markup("")
    enriched_text = _inject_chart_blocks(text)
    html = markdown.markdown(
        enriched_text,
        extensions=[
            "extra",
            "tables",
            "fenced_code",
            "nl2br",
            "sane_lists",
        ],
        output_format="html5",
    )
    return Markup(html)


def truncate(value: Any, length: int = 80) -> str:
    return truncate_text(value, length)


templates.env.filters["datetime"] = format_datetime
templates.env.filters["date_only"] = format_date
templates.env.filters["pretty_json"] = pretty_json
templates.env.filters["markdown_html"] = render_markdown
templates.env.filters["plain_text"] = markdown_to_plain_text
templates.env.filters["truncate"] = truncate


def is_htmx(request: Request) -> bool:
    return request.headers.get("HX-Request", "").lower() == "true"


def parse_datetime(value: Any) -> datetime | None:
    if isinstance(value, datetime):
        return value if value.tzinfo else value.replace(tzinfo=UTC)
    if not value:
        return None
    text = str(value).replace("Z", "+00:00")
    try:
        dt = datetime.fromisoformat(text)
    except ValueError:
        return None
    return dt if dt.tzinfo else dt.replace(tzinfo=UTC)


def render(request: Request, template_name: str, context: dict[str, Any]):
    return templates.TemplateResponse(
        request=request,
        name=template_name,
        context=context,
    )


def base_context(request: Request, active_page: str, page_title: str, page_subtitle: str = "") -> dict[str, Any]:
    return {
        "request": request,
        "current_user": getattr(request.state, "board_user", None),
        "active_page": active_page,
        "page_title": page_title,
        "page_subtitle": page_subtitle,
        "nav_items": NAV_ITEMS,
        "sidebar_approvals_count": get_pending_approvals_count(),
        "sidebar_lavori_count": get_projects_count(),
    }


def get_pending_approvals_count() -> int:
    if notion_board.notion_enabled():
        try:
            return len(notion_board.list_approvals(["draft", "review"]))
        except Exception as exc:
            logger.warning(f"Errore conteggio approvals Notion sidebar: {exc}")
            return 0

    try:
        client = get_service_client()
        response = client.table("approvals").select("id,status").in_("status", ["draft", "review"]).execute()
        return len(response.data or [])
    except Exception as exc:
        logger.warning(f"Errore conteggio approvals sidebar: {exc}")
        return 0


def get_projects_count() -> int:
    if notion_board.notion_enabled():
        try:
            return len(notion_board.list_tasks())
        except Exception as exc:
            logger.warning(f"Errore conteggio lavori Notion sidebar: {exc}")
            return 0

    try:
        client = get_service_client()
        response = client.table("projects").select("id", count="exact").execute()
        return int(response.count or 0)
    except Exception as exc:
        logger.warning(f"Errore conteggio lavori sidebar: {exc}")
        return 0


def parse_form_value(raw_value: str) -> Any:
    value = raw_value.strip()
    if not value:
        return ""
    try:
        return json.loads(value)
    except json.JSONDecodeError:
        return raw_value


def safely(default: Any, operation, message: str) -> Any:
    try:
        return operation()
    except Exception as exc:
        logger.warning(f"{message}: {exc}")
        return default
