import pytest
from unittest.mock import patch, MagicMock
from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)


def test_feedback_requires_auth():
    res = client.post("/api/feedback", json={"report_id": "r1", "rating": 5})
    assert res.status_code == 401


def test_feedback_invalid_rating():
    mock_user = MagicMock()
    mock_user.clerk_user_id = "user_1"
    with patch("app.auth.extract_clerk_user", return_value=mock_user):
        res = client.post(
            "/api/feedback",
            json={"report_id": "r1", "rating": 6},
            headers={"Authorization": "Bearer token"},
        )
    assert res.status_code == 422


def test_feedback_saves_ok():
    mock_user = MagicMock()
    mock_user.clerk_user_id = "user_1"
    mock_sb = MagicMock()
    mock_sb.table.return_value.insert.return_value.execute.return_value.data = [{}]
    with patch("app.auth.extract_clerk_user", return_value=mock_user), \
         patch("app.supabase_client._client", mock_sb):
        res = client.post(
            "/api/feedback",
            json={"report_id": "r1", "rating": 4, "comment": "ottimo"},
            headers={"Authorization": "Bearer token"},
        )
    assert res.status_code == 200
    assert res.json()["ok"] is True
