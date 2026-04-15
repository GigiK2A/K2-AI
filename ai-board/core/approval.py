from datetime import UTC, datetime, timedelta
from typing import Optional

from loguru import logger

from core import notion_board
from db.client import get_service_client
from db.models import TaskStatus

# Draft più vecchi di questo soglia vengono scaduti automaticamente
DRAFT_EXPIRY_HOURS = 48


def get_pending_approvals() -> list[dict]:
    """Restituisce tutti i draft in attesa di approvazione."""
    if notion_board.notion_enabled():
        return notion_board.list_approvals([TaskStatus.DRAFT.value, TaskStatus.REVIEW.value])

    client = get_service_client()
    response = (
        client.table("approvals")
        .select("*")
        .in_("status", [TaskStatus.DRAFT.value, TaskStatus.REVIEW.value])
        .order("created_at", desc=True)
        .execute()
    )
    return response.data or []


def approve(approval_id: str, notes: Optional[str] = None) -> bool:
    """Approva un draft. Restituisce True se operazione riuscita."""
    try:
        if notion_board.notion_enabled():
            approval = notion_board.update_approval_status(approval_id, TaskStatus.APPROVED.value, notes)
            task_id = approval.get("task_id") if approval else None
            if task_id:
                notion_board.update_task_status(task_id, TaskStatus.APPROVED.value)
                notion_board.update_logs_status_by_task(task_id, TaskStatus.APPROVED.value)
            logger.info(f"Approval Notion {approval_id} approvato")
            return True

        client = get_service_client()
        approval = get_approval(approval_id)
        client.table("approvals").update(
            {
                "status": TaskStatus.APPROVED.value,
                "founder_notes": notes,
                "reviewed_at": datetime.utcnow().isoformat(),
            }
        ).eq("id", approval_id).execute()
        task_id = approval.get("task_id") if approval else None
        if task_id:
            client.table("tasks").update({"status": TaskStatus.APPROVED.value}).eq("id", task_id).execute()
            client.table("agent_logs").update({"status": TaskStatus.APPROVED.value}).eq("task_id", task_id).execute()
        logger.info(f"Approval {approval_id} approvato")
        return True
    except Exception as exc:
        logger.error(f"Errore approvazione {approval_id}: {exc}")
        return False


def reject(approval_id: str, notes: Optional[str] = None) -> bool:
    """Rifiuta un draft e lo marca come rejected con eventuali note."""
    try:
        if notion_board.notion_enabled():
            approval = notion_board.update_approval_status(approval_id, TaskStatus.REJECTED.value, notes)
            task_id = approval.get("task_id") if approval else None
            if task_id:
                notion_board.update_task_status(task_id, TaskStatus.REJECTED.value)
                notion_board.update_logs_status_by_task(task_id, TaskStatus.REJECTED.value)
            logger.info(f"Approval Notion {approval_id} rifiutato")
            return True

        client = get_service_client()
        approval = get_approval(approval_id)
        client.table("approvals").update(
            {
                "status": TaskStatus.REJECTED.value,
                "founder_notes": notes,
                "reviewed_at": datetime.utcnow().isoformat(),
            }
        ).eq("id", approval_id).execute()
        task_id = approval.get("task_id") if approval else None
        if task_id:
            client.table("tasks").update({"status": TaskStatus.REJECTED.value}).eq("id", task_id).execute()
            client.table("agent_logs").update({"status": TaskStatus.REJECTED.value}).eq("task_id", task_id).execute()
        logger.info(f"Approval {approval_id} rifiutato")
        return True
    except Exception as exc:
        logger.error(f"Errore rifiuto {approval_id}: {exc}")
        return False


def expire_stale_approvals(max_age_hours: int = DRAFT_EXPIRY_HOURS) -> int:
    """Chiude tutti i draft pending più vecchi di max_age_hours.

    Restituisce il numero di draft scaduti.
    Non solleva eccezioni: fallisce silenziosamente con log.
    """
    expired_count = 0
    cutoff = datetime.now(UTC) - timedelta(hours=max_age_hours)
    note = f"Scaduto automaticamente dopo {max_age_hours}h senza revisione"

    try:
        pending = get_pending_approvals()
        for item in pending:
            try:
                raw = item.get("created_at") or ""
                if not raw:
                    continue
                # Gestisce sia datetime objects che stringhe ISO
                if isinstance(raw, datetime):
                    created_at = raw if raw.tzinfo else raw.replace(tzinfo=UTC)
                else:
                    raw_str = str(raw).replace("Z", "+00:00")
                    created_at = datetime.fromisoformat(raw_str)
                    if not created_at.tzinfo:
                        created_at = created_at.replace(tzinfo=UTC)

                if created_at <= cutoff:
                    approval_id = item.get("id")
                    if approval_id:
                        reject(approval_id, notes=note)
                        expired_count += 1
                        logger.info(f"Draft {approval_id} scaduto automaticamente (età: {max_age_hours}h)")
            except Exception as exc:
                logger.warning(f"Errore scadenza draft {item.get('id')}: {exc}")
    except Exception as exc:
        logger.error(f"Errore expire_stale_approvals: {exc}")

    if expired_count:
        logger.info(f"Scaduti {expired_count} draft stale (soglia: {max_age_hours}h)")
    return expired_count


def get_approval(approval_id: str) -> Optional[dict]:
    """Legge un singolo approval dal DB."""
    if notion_board.notion_enabled():
        return notion_board.get_approval(approval_id)

    client = get_service_client()
    response = client.table("approvals").select("*").eq("id", approval_id).single().execute()
    return response.data
