import pytest
from unittest.mock import patch, MagicMock
from app.auth import extract_clerk_user, ClerkUser


def test_extract_clerk_user_no_token():
    result = extract_clerk_user(None)
    assert result is None


def test_extract_clerk_user_invalid_token():
    result = extract_clerk_user("invalid.token.here")
    assert result is None


def test_extract_clerk_user_valid_token():
    mock_payload = {
        "sub": "user_abc123",
        "public_metadata": {"has_paid": True},
    }
    with patch("app.auth._decode_token", return_value=mock_payload):
        result = extract_clerk_user("valid.jwt.token")
    assert result is not None
    assert result.clerk_user_id == "user_abc123"
    assert result.has_paid is True


def test_extract_clerk_user_no_payment():
    mock_payload = {
        "sub": "user_xyz",
        "public_metadata": {},
    }
    with patch("app.auth._decode_token", return_value=mock_payload):
        result = extract_clerk_user("valid.jwt.token")
    assert result is not None
    assert result.has_paid is False
