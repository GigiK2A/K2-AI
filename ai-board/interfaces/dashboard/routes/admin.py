from __future__ import annotations

from datetime import UTC, datetime

from fastapi import APIRouter, Form, HTTPException, Request
from fastapi.responses import RedirectResponse
from loguru import logger

from core import notion_board
from core.board_auth import VALID_ROLES, hash_password, is_admin
from core.config import settings
from db.client import get_service_client
from interfaces.dashboard.routes import base_context, render, safely
from services.reports_service import get_mock_reports

router = APIRouter()

CONFIRM_DELETE_ALL = "CANCELLA TUTTO"

BOARD_TABLES = [
    {"name": "project_documents", "label": "Documenti progetto", "key": "id", "sentinel": "00000000-0000-0000-0000-000000000000"},
    {"name": "project_agent_links", "label": "Agenti progetto", "key": "id", "sentinel": "00000000-0000-0000-0000-000000000000"},
    {"name": "project_tasks", "label": "Task progetto", "key": "id", "sentinel": "00000000-0000-0000-0000-000000000000"},
    {"name": "project_phases", "label": "Fasi progetto", "key": "id", "sentinel": "00000000-0000-0000-0000-000000000000"},
    {"name": "approvals", "label": "Approvazioni", "key": "id", "sentinel": "00000000-0000-0000-0000-000000000000"},
    {"name": "agent_logs_archive", "label": "Archivio log agenti", "key": "id", "sentinel": "00000000-0000-0000-0000-000000000000"},
    {"name": "agent_logs", "label": "Log agenti", "key": "id", "sentinel": "00000000-0000-0000-0000-000000000000"},
    {"name": "tasks", "label": "Lavori", "key": "id", "sentinel": "00000000-0000-0000-0000-000000000000"},
    {"name": "pipeline_leads", "label": "Pipeline", "key": "id", "sentinel": "00000000-0000-0000-0000-000000000000"},
    {"name": "projects", "label": "Progetti", "key": "id", "sentinel": "00000000-0000-0000-0000-000000000000"},
    {"name": "shared_memory", "label": "Memoria condivisa", "key": "key", "sentinel": "__kai_never_delete__"},
]
ACCOUNT_ROLES = [
    ("admin", "Admin"),
    ("operator", "Operator"),
    ("viewer", "Viewer"),
]


def _require_admin(request: Request) -> None:
    if not (settings.board_auth_enabled or settings.app_env == "production"):
        return
    if not is_admin(getattr(request.state, "board_user", None)):
        raise HTTPException(status_code=403, detail="Solo admin")


def _table_count(table: dict) -> int:
    client = get_service_client()
    response = client.table(table["name"]).select(table["key"], count="exact").limit(1).execute()
    return int(response.count or 0)


def _board_counts() -> list[dict]:
    if notion_board.notion_enabled():
        counts = []
        for title in sorted(notion_board.get_database_ids()):
            if title in notion_board.IGNORED_DATABASES:
                continue
            count = safely(0, lambda title=title: notion_board.count_database_pages(title), f"Errore conteggio Notion {title}")
            counts.append({"name": title, "label": f"Notion · {title}", "count": count})
        return counts

    counts = []
    for table in BOARD_TABLES:
        count = safely(0, lambda table=table: _table_count(table), f"Errore conteggio {table['name']}")
        counts.append({**table, "count": count})
    return counts


def _load_accounts() -> list[dict]:
    client = get_service_client()
    return safely(
        [],
        lambda: client.table("board_users").select(
            "id,email,display_name,role,is_active,created_at,last_login_at"
        ).order("created_at", desc=True).execute().data or [],
        "Errore caricamento account board",
    )


def _is_missing_table_error(exc: Exception) -> bool:
    text = str(exc)
    return "Could not find the table" in text or "schema cache" in text


@router.get("/admin")
async def admin_page(request: Request, deleted: str | None = None, error: str | None = None):
    _require_admin(request)
    counts = _board_counts()
    context = base_context(request, active_page="admin", page_title="Admin")
    context.update(
        {
            "counts": counts,
            "total_records": sum(item["count"] for item in counts),
            "confirm_phrase": CONFIRM_DELETE_ALL,
            "deleted": deleted == "1",
            "error": error,
            "accounts": _load_accounts(),
            "account_roles": ACCOUNT_ROLES,
            "account_error": request.query_params.get("account_error"),
            "account_created": request.query_params.get("account_created") == "1",
        }
    )
    return render(request, "admin.html", context)


@router.get("/admin/reports")
async def admin_reports_page(request: Request):
    _require_admin(request)
    reports = get_mock_reports()
    context = base_context(
        request,
        active_page="reports",
        page_title="Report generati",
        page_subtitle="Archivio interno dei report K-BOT",
    )
    context.update(
        {
            "reports": reports,
            "report_count": len(reports),
            "ready_count": sum(1 for report in reports if report["status"] == "ready"),
            "reports_site_url": settings.reports_site_url.rstrip("/"),
        }
    )
    return render(request, "admin_reports.html", context)


@router.post("/admin/delete-all")
async def delete_all_board_data(request: Request, confirmation: str = Form(...)):
    _require_admin(request)
    if confirmation.strip() != CONFIRM_DELETE_ALL:
        return RedirectResponse(url="/admin?error=confirm", status_code=303)

    deleted_tables: list[str] = []
    if notion_board.notion_enabled():
        try:
            archived_counts = notion_board.archive_all_board_data()
            deleted_tables = [f"Notion/{title}:{count}" for title, count in archived_counts.items()]
        except Exception as exc:
            logger.error(f"Errore archiviazione dati Notion: {exc}")
            return RedirectResponse(url="/admin?error=notion", status_code=303)

        logger.warning(
            "Archiviazione completa board Notion richiesta da dashboard alle {}. Database: {}",
            datetime.now(UTC).isoformat(),
            ", ".join(deleted_tables),
        )
        return RedirectResponse(url="/admin?deleted=1", status_code=303)

    client = get_service_client()
    for table in BOARD_TABLES:
        try:
            client.table(table["name"]).delete().neq(table["key"], table["sentinel"]).execute()
            deleted_tables.append(table["name"])
        except Exception as exc:
            if _is_missing_table_error(exc):
                logger.warning(f"Tabella non presente, saltata durante la cancellazione: {table['name']}")
                continue
            logger.error(f"Errore cancellazione {table['name']}: {exc}")
            return RedirectResponse(url=f"/admin?error={table['name']}", status_code=303)

    logger.warning(
        "Cancellazione completa board richiesta da dashboard alle {}. Tabelle: {}",
        datetime.now(UTC).isoformat(),
        ", ".join(deleted_tables),
    )
    return RedirectResponse(url="/admin?deleted=1", status_code=303)


@router.post("/admin/accounts")
async def create_account(
    request: Request,
    email: str = Form(...),
    display_name: str = Form(default=""),
    role: str = Form(default="viewer"),
    password: str = Form(...),
):
    _require_admin(request)
    normalized_email = email.strip().lower()
    if role not in VALID_ROLES:
        return RedirectResponse(url="/admin?account_error=role", status_code=303)
    if len(password) < 10:
        return RedirectResponse(url="/admin?account_error=password", status_code=303)

    try:
        get_service_client().table("board_users").insert(
            {
                "email": normalized_email,
                "display_name": display_name.strip() or None,
                "role": role,
                "password_hash": hash_password(password),
                "is_active": True,
            }
        ).execute()
    except Exception as exc:
        logger.warning(f"Errore creazione account board {normalized_email}: {exc}")
        return RedirectResponse(url="/admin?account_error=create", status_code=303)
    return RedirectResponse(url="/admin?account_created=1", status_code=303)


@router.post("/admin/accounts/{user_id}/status")
async def update_account_status(request: Request, user_id: str, is_active: str = Form(...)):
    _require_admin(request)
    current_user = getattr(request.state, "board_user", None)
    if current_user and current_user.get("id") == user_id and is_active != "true":
        return RedirectResponse(url="/admin?account_error=self", status_code=303)

    get_service_client().table("board_users").update(
        {"is_active": is_active == "true", "updated_at": datetime.now(UTC).isoformat()}
    ).eq("id", user_id).execute()
    if is_active != "true":
        get_service_client().table("board_sessions").delete().eq("user_id", user_id).execute()
    return RedirectResponse(url="/admin", status_code=303)


@router.post("/admin/accounts/{user_id}/password")
async def update_account_password(request: Request, user_id: str, password: str = Form(...)):
    _require_admin(request)
    if len(password) < 10:
        return RedirectResponse(url="/admin?account_error=password", status_code=303)

    client = get_service_client()
    client.table("board_users").update(
        {
            "password_hash": hash_password(password),
            "updated_at": datetime.now(UTC).isoformat(),
        }
    ).eq("id", user_id).execute()
    client.table("board_sessions").delete().eq("user_id", user_id).execute()
    return RedirectResponse(url="/admin", status_code=303)
