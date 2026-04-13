from __future__ import annotations

from fastapi import APIRouter, Request

from db.client import get_service_client
from interfaces.dashboard.routes import base_context, parse_datetime, render, safely

router = APIRouter()

STATUS_META = {
    "identified": {"label": "Nuovo",       "badge": "bg-indigo-50 text-indigo-700", "dot": "bg-indigo-400"},
    "qualified":  {"label": "Qualificato", "badge": "bg-blue-50 text-blue-700",    "dot": "bg-blue-400"},
    "contacted":  {"label": "Contattato",  "badge": "bg-amber-50 text-amber-700",  "dot": "bg-amber-400"},
    "call_scheduled": {"label": "Call fissata", "badge": "bg-violet-50 text-violet-700", "dot": "bg-violet-400"},
    "proposal_sent":  {"label": "Proposta",    "badge": "bg-orange-50 text-orange-700", "dot": "bg-orange-400"},
    "won":        {"label": "Chiuso",      "badge": "bg-emerald-50 text-emerald-700", "dot": "bg-emerald-400"},
}


def _fmt_date(value: str | None) -> str:
    dt = parse_datetime(value)
    if not dt:
        return "—"
    return dt.strftime("%d/%m/%y %H:%M")


def _enrich_lead(lead: dict) -> dict:
    status = lead.get("status", "identified")
    meta = STATUS_META.get(status, STATUS_META["identified"])
    return {
        **lead,
        "status_label": meta["label"],
        "status_badge": meta["badge"],
        "status_dot":   meta["dot"],
        "created_fmt":  _fmt_date(lead.get("created_at")),
        "display_name": lead.get("name") or "—",
        "company_line": lead.get("company") or "",
        "sector_line":  lead.get("sector") or "",
    }


def _load_leads() -> list[dict]:
    client = get_service_client()
    rows = safely(
        [],
        lambda: client.table("pipeline_leads")
            .select("*")
            .eq("channel", "website_contact_form")
            .order("created_at", desc=True)
            .limit(200)
            .execute()
            .data or [],
        "Errore lettura lead sito",
    )
    return [_enrich_lead(row) for row in rows]


@router.get("/inbox")
async def inbox_page(request: Request):
    leads = _load_leads()
    context = base_context(request, active_page="inbox", page_title="Inbox")
    context["leads"] = leads
    context["total"] = len(leads)
    return render(request, "inbox.html", context)
