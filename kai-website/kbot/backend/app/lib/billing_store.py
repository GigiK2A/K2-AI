"""Accesso DB per il layer billing (abbonamenti + crediti).

Wrappa le tabelle/RPC della migration 006 (kbot_subscriptions, kbot_credit_ledger,
kbot_credit_balance/consume/grant) via service_role. Logica di prezzo/regole in
`billing.py` (pura); qui solo I/O Supabase. Tutte le funzioni degradano in modo
sicuro se Supabase non è configurato (ritornano default/None) così l'app resta
avviabile in dev.
"""
from __future__ import annotations

import logging
from datetime import datetime, timedelta, timezone
from typing import Optional

from . import billing
from .supabase_admin import get_admin_client

log = logging.getLogger(__name__)


def get_plan(user_id: str) -> str:
    """Piano corrente dell'utente ('free' se assente/non attivo)."""
    try:
        r = (get_admin_client().table("kbot_subscriptions")
             .select("plan,status").eq("user_id", user_id).limit(1).execute())
        row = (r.data or [None])[0]
        if row and row.get("status") == "active":
            return row.get("plan") or "free"
    except Exception as exc:  # tabella assente in dev / errore rete
        log.debug("get_plan fallback free: %s", exc)
    return "free"


def credit_balance(user_id: str) -> int:
    try:
        r = get_admin_client().rpc("kbot_credit_balance", {"p_user": user_id}).execute()
        return int(r.data or 0)
    except Exception as exc:
        log.debug("credit_balance 0: %s", exc)
        return 0


def grant_credits(user_id: str, amount: int, reason: str, ref: Optional[str] = None,
                  expires_days: Optional[int] = None) -> Optional[int]:
    if amount <= 0:
        return None
    expires = None
    if expires_days:
        expires = (datetime.now(timezone.utc) + timedelta(days=expires_days)).isoformat()
    try:
        r = get_admin_client().rpc("kbot_grant_credits", {
            "p_user": user_id, "p_amount": amount, "p_reason": reason,
            "p_ref": ref, "p_expires": expires}).execute()
        return int(r.data)
    except Exception as exc:
        log.warning("grant_credits fallito: %s", exc)
        return None


def consume_credits(user_id: str, amount: int, reason: str = "consume",
                    ref: Optional[str] = None) -> tuple[bool, int]:
    """(ok, nuovo_saldo). ok=False se crediti insufficienti o errore."""
    try:
        r = get_admin_client().rpc("kbot_consume_credits", {
            "p_user": user_id, "p_amount": amount, "p_reason": reason, "p_ref": ref}).execute()
        return True, int(r.data)
    except Exception as exc:
        msg = str(exc)
        if "insufficient_credits" not in msg:
            log.warning("consume_credits errore: %s", exc)
        return False, credit_balance(user_id)


def upsert_subscription(user_id: str, plan: str, status: str = "active",
                        stripe_customer_id: Optional[str] = None,
                        stripe_subscription_id: Optional[str] = None,
                        current_period_end: Optional[str] = None) -> None:
    try:
        get_admin_client().table("kbot_subscriptions").upsert({
            "user_id": user_id, "plan": plan, "status": status,
            "stripe_customer_id": stripe_customer_id,
            "stripe_subscription_id": stripe_subscription_id,
            "current_period_end": current_period_end,
            "updated_at": datetime.now(timezone.utc).isoformat(),
        }, on_conflict="user_id").execute()
    except Exception as exc:
        log.warning("upsert_subscription fallito: %s", exc)


def grant_monthly_plan_credits(user_id: str, plan: str) -> Optional[int]:
    """Accredita i crediti mensili del piano (scadenza 30gg, leva fidelizzazione L2)."""
    n = billing.crediti_mensili(plan)
    if n <= 0:
        return None
    return grant_credits(user_id, n, reason="monthly_grant", ref=plan, expires_days=30)
