from __future__ import annotations

import base64
import hashlib
import hmac
import json
import secrets
from datetime import UTC, datetime, timedelta
from typing import Any

from fastapi import Request
from loguru import logger

from core.config import settings
from db.client import get_service_client

SESSION_COOKIE_NAME = "kai_board_session"
PASSWORD_HASH_ITERATIONS = 240_000
VALID_ROLES = {"admin", "operator", "viewer"}


def hash_password(password: str) -> str:
    salt = secrets.token_bytes(16)
    digest = hashlib.pbkdf2_hmac(
        "sha256",
        password.encode("utf-8"),
        salt,
        PASSWORD_HASH_ITERATIONS,
    )
    return "pbkdf2_sha256${}${}${}".format(
        PASSWORD_HASH_ITERATIONS,
        base64.b64encode(salt).decode("ascii"),
        base64.b64encode(digest).decode("ascii"),
    )


def verify_password(password: str, password_hash: str) -> bool:
    try:
        algorithm, iterations, salt_b64, digest_b64 = password_hash.split("$", 3)
        if algorithm != "pbkdf2_sha256":
            return False
        salt = base64.b64decode(salt_b64)
        expected_digest = base64.b64decode(digest_b64)
        actual_digest = hashlib.pbkdf2_hmac(
            "sha256",
            password.encode("utf-8"),
            salt,
            int(iterations),
        )
        return secrets.compare_digest(actual_digest, expected_digest)
    except Exception:
        return False


def _pad_base64(value: str) -> str:
    return value + "=" * (-len(value) % 4)


def _env_session_secret() -> bytes:
    if not settings.board_password:
        raise RuntimeError("BOARD_PASSWORD non configurata per sessioni env")
    return settings.board_password.encode("utf-8")


def _sign_env_payload(payload: str) -> str:
    return hmac.new(_env_session_secret(), payload.encode("utf-8"), hashlib.sha256).hexdigest()


def _create_env_token(payload: dict[str, Any]) -> str:
    payload_json = json.dumps(payload, separators=(",", ":"), sort_keys=True, ensure_ascii=False)
    payload_b64 = base64.urlsafe_b64encode(payload_json.encode("utf-8")).decode("utf-8").rstrip("=")
    signature = _sign_env_payload(payload_b64)
    return f"env:{payload_b64}.{signature}"


def _parse_env_token(token: str) -> dict[str, Any] | None:
    if not token.startswith("env:"):
        return None
    payload_sig = token[4:]
    if "." not in payload_sig:
        return None
    payload_b64, signature = payload_sig.rsplit(".", 1)
    if not secrets.compare_digest(signature, _sign_env_payload(payload_b64)):
        return None
    try:
        payload_json = base64.urlsafe_b64decode(_pad_base64(payload_b64)).decode("utf-8")
        payload = json.loads(payload_json)
    except Exception:
        return None
    if not isinstance(payload, dict):
        return None
    return payload


def hash_session_token(token: str) -> str:
    return hashlib.sha256(token.encode("utf-8")).hexdigest()


def create_session(user_id: str, request: Request) -> tuple[str, datetime]:
    token = secrets.token_urlsafe(48)
    expires_at = datetime.now(UTC) + timedelta(hours=settings.board_session_hours)
    client = get_service_client()
    client.table("board_sessions").insert(
        {
            "user_id": user_id,
            "token_hash": hash_session_token(token),
            "expires_at": expires_at.isoformat(),
            "user_agent": request.headers.get("user-agent"),
            "ip_address": _client_ip(request),
        }
    ).execute()
    return token, expires_at


def delete_session(token: str | None) -> None:
    if not token:
        return
    if token.startswith("env:"):
        return
    try:
        get_service_client().table("board_sessions").delete().eq("token_hash", hash_session_token(token)).execute()
    except Exception as exc:
        logger.warning(f"Errore cancellazione sessione board: {exc}")


def authenticate_user(email: str, password: str) -> dict[str, Any] | None:
    try:
        if settings.board_username and settings.board_password:
            username = settings.board_username.strip().lower()
            if email.strip().lower() == username and secrets.compare_digest(password, settings.board_password):
                return {
                    "id": "env_admin",
                    "email": username,
                    "display_name": "Admin",
                    "role": "admin",
                    "is_active": True,
                    "is_env": True,
                }

        client = get_service_client()
        response = client.table("board_users").select("*").eq("email", email.strip().lower()).eq("is_active", True).limit(1).execute()
        user = (response.data or [None])[0]
        if not user or not verify_password(password, user.get("password_hash") or ""):
            return None
        client.table("board_users").update({"last_login_at": datetime.now(UTC).isoformat()}).eq("id", user["id"]).execute()
        return _public_user(user)
    except Exception as exc:
        logger.warning(f"Errore autenticazione board: {exc}")
        return None


def create_env_session(user: dict[str, Any], request: Request) -> tuple[str, datetime]:
    expires_at = datetime.now(UTC) + timedelta(hours=settings.board_session_hours)
    payload = {
        "id": user.get("id"),
        "email": user.get("email"),
        "display_name": user.get("display_name"),
        "role": user.get("role", "admin"),
        "expires_at": expires_at.isoformat(),
    }
    return _create_env_token(payload), expires_at


def get_user_from_session(token: str | None) -> dict[str, Any] | None:
    if not token:
        return None

    if token.startswith("env:"):
        payload = _parse_env_token(token)
        if not payload:
            return None
        expires_at = payload.get("expires_at")
        if not expires_at or expires_at <= datetime.now(UTC).isoformat():
            return None
        return _public_user(payload)

    try:
        now = datetime.now(UTC).isoformat()
        client = get_service_client()
        session_response = client.table("board_sessions").select("id,user_id,expires_at").eq("token_hash", hash_session_token(token)).gt("expires_at", now).limit(1).execute()
        session = (session_response.data or [None])[0]
        if not session:
            return None

        user_response = client.table("board_users").select("*").eq("id", session["user_id"]).eq("is_active", True).limit(1).execute()
        user = (user_response.data or [None])[0]
        if not user:
            delete_session(token)
            return None

        client.table("board_sessions").update({"last_seen_at": now}).eq("id", session["id"]).execute()
        return _public_user(user)
    except Exception as exc:
        logger.warning(f"Errore lettura sessione board: {exc}")
        return None


def is_admin(user: dict[str, Any] | None) -> bool:
    return bool(user and user.get("role") == "admin")


def _public_user(user: dict[str, Any]) -> dict[str, Any]:
    return {
        "id": user.get("id"),
        "email": user.get("email"),
        "display_name": user.get("display_name") or user.get("email"),
        "role": user.get("role") or "viewer",
        "is_env": False,
    }


def _client_ip(request: Request) -> str:
    forwarded_for = request.headers.get("x-forwarded-for", "")
    if forwarded_for:
        return forwarded_for.split(",", 1)[0].strip()
    return request.client.host if request.client else "unknown"
