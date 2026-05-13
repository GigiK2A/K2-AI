import pytest
from unittest.mock import patch, MagicMock
from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)


def test_checkout_requires_auth():
    res = client.post("/api/stripe/checkout")
    assert res.status_code == 401


def test_checkout_returns_url():
    mock_session = MagicMock()
    mock_session.url = "https://checkout.stripe.com/test_session"

    mock_user = MagicMock()
    mock_user.clerk_user_id = "user_test"
    mock_user.has_paid = False

    with patch("app.stripe_routes.stripe.checkout.Session.create", return_value=mock_session), \
         patch("app.auth.extract_clerk_user", return_value=mock_user):
        res = client.post(
            "/api/stripe/checkout",
            headers={"Authorization": "Bearer fake_token"},
        )
    assert res.status_code == 200
    assert res.json()["url"] == "https://checkout.stripe.com/test_session"
