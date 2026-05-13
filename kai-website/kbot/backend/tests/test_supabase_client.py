import pytest
from unittest.mock import patch, MagicMock
from app.supabase_client import (
    get_conversation_memory_db,
    append_conversation_memory_db,
)


def _mock_supabase(rows=None):
    mock = MagicMock()
    mock.table.return_value.select.return_value.eq.return_value.eq.return_value \
        .order.return_value.limit.return_value.execute.return_value.data = rows or []
    mock.table.return_value.insert.return_value.execute.return_value.data = [{}]
    return mock


def test_get_conversation_memory_db_empty():
    with patch("app.supabase_client._client", _mock_supabase([])):
        result = get_conversation_memory_db("user_1", "conv_1")
    assert result == []


def test_get_conversation_memory_db_returns_rows():
    rows = [
        {"role": "user", "content": "ciao", "context_files": [], "ts": "2026-01-01"},
        {"role": "assistant", "content": "risposta", "context_files": [], "ts": "2026-01-01"},
    ]
    with patch("app.supabase_client._client", _mock_supabase(rows)):
        result = get_conversation_memory_db("user_1", "conv_1")
    assert len(result) == 2
    assert result[0]["role"] == "user"


def test_append_conversation_memory_db():
    mock = _mock_supabase()
    with patch("app.supabase_client._client", mock):
        append_conversation_memory_db("user_1", "conv_1", "user", "testo", [])
    mock.table.return_value.insert.assert_called_once()
