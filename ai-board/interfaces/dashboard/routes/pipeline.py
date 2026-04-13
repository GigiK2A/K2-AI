from datetime import UTC, date, datetime, timedelta

from fastapi import APIRouter, Form, Request

from core import notion_board
from interfaces.dashboard.routes import base_context, parse_datetime, render, safely

router = APIRouter()

PIPELINE_COLUMNS = [
    {
        "key": "identified",
        "label": "Identificato",
        "show_menu": True,
        "empty_icon": "inbox",
        "empty_label": "Vuoto",
        "column_class": "",
    },
    {
        "key": "qualified",
        "label": "Qualificato",
        "show_menu": True,
        "empty_icon": "inbox",
        "empty_label": "Vuoto",
        "column_class": "",
    },
    {
        "key": "contacted",
        "label": "Contattato",
        "show_menu": True,
        "empty_icon": "inbox",
        "empty_label": "Vuoto",
        "column_class": "",
    },
    {
        "key": "call_scheduled",
        "label": "Call fissata",
        "show_menu": False,
        "empty_icon": "calendar_today",
        "empty_label": "Nessuna call",
        "column_class": "",
    },
    {
        "key": "proposal_sent",
        "label": "Proposta inviata",
        "show_menu": False,
        "empty_icon": "description",
        "empty_label": "Nessun preventivo",
        "column_class": "",
    },
    {
        "key": "won",
        "label": "Chiuso",
        "show_menu": False,
        "empty_icon": "verified",
        "empty_label": "Storico vuoto",
        "column_class": "opacity-50 grayscale-[0.2]",
    },
]
PIPELINE_STATUS_ORDER = [column["key"] for column in PIPELINE_COLUMNS]
PIPELINE_STATUS_LABELS = {column["key"]: column["label"] for column in PIPELINE_COLUMNS}

ITALIAN_MONTHS_SHORT = [
    "Gen",
    "Feb",
    "Mar",
    "Apr",
    "Mag",
    "Giu",
    "Lug",
    "Ago",
    "Set",
    "Ott",
    "Nov",
    "Dic",
]

ACCENT_SECTORS = {"studi tecnici", "fintech", "energia", "logistica"}
FOUNDER_AVATAR = (
    "https://lh3.googleusercontent.com/aida-public/AB6AXuBVYPcAMoeE8eBn9j-p7KDnO4_u4Ouw8l3CDIE-se_TraUi7E6dPuq4N4LGDeNGrs8aoY9so_R2-u_rF3ybaPJtU7Mbbk-diKFIwR6qXcsIRNl48c85Tp3U2zWxNj90f3T7OERjGJIy1_ZuQppjkL2ql-A39GA-ZoWL6UyCZgEMmmBEocreUQchT1i8LnItPTvm-I1xrRl_mevOrF0XOW4Q4NrsfBueQF4o9plcykJPikOxzterzUk0yv6KrOvRZ5DkDEOqoLXO3vI"
)
TEAM_AVATAR = (
    "https://lh3.googleusercontent.com/aida-public/AB6AXuD7Xby3FHniaqddWk7bwNWOHmkiwBZRuGmlYT8oWRlKTvtrQegiObvJN1iAMDw8WSEX--RDKHzDewLmxdfqB3I5_JsV7jE9-qhME9-Jgor1G4MNaq--fVQZT9RBpbPUWpoBb2Y4LSYAXWIV4RJY2JUQuYeiKjTrs4WAiZ7_JS_p1vmhL78WzmXmYhhNSHVtbciASWJ-_jdxHicxIAyZ_T84bwwZtApOdFRnqgwstf0GF2GkTO8DzWKnOKX0jQCcXg4XBoghfW_ugU4"
)


def _format_pipeline_date(raw_value: str | None) -> str:
    dt = parse_datetime(raw_value)
    if not dt:
        return "—"
    return f"{dt.day:02d} {ITALIAN_MONTHS_SHORT[dt.month - 1]} {dt.year}"


def _sector_style(sector: str | None) -> str:
    if (sector or "").strip().lower() in ACCENT_SECTORS:
        return "bg-primary-container text-on-primary-container"
    return "bg-surface-container-highest text-on-surface-variant"


def _score_style(score: int | None) -> str:
    if (score or 0) >= 8:
        return "bg-emerald-500"
    if (score or 0) >= 6:
        return "bg-amber-500"
    return "bg-slate-400"


def _action_icon(text: str) -> str:
    lowered = text.lower()
    if "richiesta" in lowered:
        return "event_repeat"
    if "decision maker" in lowered:
        return "person_check"
    if "interesse" in lowered:
        return "trending_up"
    if "follow-up" in lowered or "giorn" in lowered:
        return "schedule"
    if "richiamata" in lowered or "call" in lowered:
        return "phone_forwarded"
    if "mail" in lowered or "contatto" in lowered:
        return "mail"
    if "arricch" in lowered or "ricerca" in lowered:
        return "search"
    return "event_repeat"


def _lead_activity_text(lead: dict) -> str:
    for key in ("next_action", "pain_point", "channel", "offer_fit", "notes"):
        value = lead.get(key)
        if value:
            return str(value)
    return "Azione in definizione"


def _prepare_lead(lead: dict, status: str, index: int) -> dict:
    activity_text = _lead_activity_text(lead)
    highlight = status == "identified" and index == 0
    next_status = _next_status(status)
    return {
        **lead,
        "display_name": lead.get("company") or lead.get("name") or "Lead",
        "sector_label": lead.get("sector") or "Lead",
        "sector_class": _sector_style(lead.get("sector")),
        "score_value": lead.get("score") if lead.get("score") is not None else "?",
        "score_dot_class": _score_style(lead.get("score")),
        "activity_text": activity_text,
        "activity_icon": _action_icon(activity_text),
        "date_label": _format_pipeline_date(lead.get("created_at") or lead.get("next_action_date")),
        "highlighted": highlight,
        "show_avatar": highlight,
        "avatar_url": TEAM_AVATAR,
        "next_status": next_status,
        "next_status_label": PIPELINE_STATUS_LABELS.get(next_status, "") if next_status else "",
    }


def _next_status(status: str) -> str | None:
    try:
        index = PIPELINE_STATUS_ORDER.index(status)
    except ValueError:
        return PIPELINE_STATUS_ORDER[0]
    if index >= len(PIPELINE_STATUS_ORDER) - 1:
        return None
    return PIPELINE_STATUS_ORDER[index + 1]


def _build_suggestion(columns: dict[str, list[dict]]) -> dict:
    now = datetime.now(UTC)
    candidate = None
    for status_key in ("identified", "qualified", "contacted"):
        leads = columns.get(status_key, [])
        if leads:
            candidate = leads[0]
            break

    if not candidate:
        return {
            "title": "Suggerimento AI",
            "text": "La pipeline è vuota. Crea un nuovo lead per iniziare il flusso di acquisizione.",
        }

    last_touch = parse_datetime(candidate.get("updated_at") or candidate.get("created_at")) or now
    days_idle = max(0, (now.date() - last_touch.date()).days)
    sector = (candidate.get("sector") or "").strip().lower()

    if sector == "studi tecnici":
        recommendation = "Ti consiglio di inviare il case study 'Legal Tech'."
    elif sector in {"software", "fintech"}:
        recommendation = "Ti consiglio di proporre una call breve con demo operativa."
    else:
        recommendation = "Ti consiglio di inviare un follow-up personalizzato questa settimana."

    return {
        "title": "Suggerimento AI",
        "text": f"{candidate.get('company') or candidate.get('name') or 'Questo lead'} non riceve contatti da {days_idle} giorni. {recommendation}",
    }


def _load_pipeline_columns() -> dict[str, list[dict]]:
    if not notion_board.notion_enabled():
        return {item["key"]: [] for item in PIPELINE_COLUMNS}

    leads = safely([], notion_board.list_pipeline_leads, "Errore caricamento pipeline Notion")
    columns = {item["key"]: [] for item in PIPELINE_COLUMNS}
    for lead in leads:
        status = lead.get("status", "identified")
        columns.setdefault(status, []).append(lead)
    return columns


def _pipeline_page_context() -> dict:
    raw_columns = _load_pipeline_columns()
    rendered_columns = []
    for column in PIPELINE_COLUMNS:
        leads = raw_columns.get(column["key"], [])
        rendered_columns.append(
            {
                **column,
                "count": len(leads),
                "leads": [_prepare_lead(lead, column["key"], index) for index, lead in enumerate(leads)],
            }
        )
    return {
        "columns_meta": rendered_columns,
        "suggestion": _build_suggestion(raw_columns),
        "founder_avatar": FOUNDER_AVATAR,
    }


@router.get("/pipeline")
async def pipeline_page(request: Request):
    context = base_context(request, active_page="pipeline", page_title="Pipeline")
    context.update(_pipeline_page_context())
    return render(request, "pipeline.html", context)


@router.post("/pipeline/lead")
async def create_lead(
    request: Request,
    name: str = Form(...),
    company: str = Form(default=""),
    sector: str = Form(default=""),
    pain_point: str = Form(default=""),
    channel: str = Form(default=""),
):
    if notion_board.notion_enabled():
        notion_board.create_pipeline_lead(
            name=name,
            company=company,
            sector=sector,
            pain_point=pain_point,
            channel=channel,
        )

    context = {"request": request}
    context.update(_pipeline_page_context())
    return render(request, "partials/pipeline_board.html", context)


@router.post("/pipeline/lead/{lead_id}/status")
async def update_lead_status(request: Request, lead_id: str, new_status: str = Form(...)):
    if notion_board.notion_enabled() and new_status in PIPELINE_STATUS_ORDER:
        notion_board.update_lead_status(lead_id, new_status)

    context = {"request": request}
    context.update(_pipeline_page_context())
    return render(request, "partials/pipeline_board.html", context)


@router.post("/pipeline/lead/{lead_id}/delete")
async def delete_lead(request: Request, lead_id: str):
    if notion_board.notion_enabled():
        notion_board.archive_lead(lead_id)

    context = {"request": request}
    context.update(_pipeline_page_context())
    return render(request, "partials/pipeline_board.html", context)
