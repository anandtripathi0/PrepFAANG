import ssl

from conftest import register
from fastapi.testclient import TestClient

from app import auth
from app.main import app


def login(client, email, password="Strong-passphrase-123"):
    result = client.post("/api/auth/login", json={"email": email, "password": password})
    if result.status_code == 200:
        client.headers["X-CSRF-Token"] = result.json()["csrf"]
    return result


def test_password_change_revokes_sessions_and_reset_links(client):
    user = register(client)
    other = TestClient(app)
    assert login(other, user["email"]).status_code == 200
    reset = client.post("/api/auth/forgot-password", json={"email": user["email"]}).json()
    token = reset["development_link"].split("token=")[1]
    body = {"current_password": "wrong-password", "new_password": "A-new-password-123"}
    assert client.post("/api/auth/change-password", json=body).status_code == 400
    assert other.get("/api/auth/me").status_code == 200
    body["current_password"] = "Strong-passphrase-123"
    csrf = client.headers.pop("X-CSRF-Token")
    assert client.post("/api/auth/change-password", json=body).status_code == 403
    client.headers["X-CSRF-Token"] = csrf
    assert client.post("/api/auth/change-password", json=body).status_code == 200
    assert client.get("/api/auth/me").status_code == 401
    assert other.get("/api/auth/me").status_code == 401
    assert login(other, user["email"]).status_code == 401
    assert (
        client.post("/api/auth/reset-password", json={"token": token, "password": "Stolen-reset-123"}).status_code
        == 400
    )
    assert login(client, user["email"], body["new_password"]).status_code == 200
    other.close()


def test_logout_everywhere_preserves_other_accounts(client):
    user = register(client)
    second_device = TestClient(app)
    unrelated = TestClient(app)
    assert login(second_device, user["email"]).status_code == 200
    register(unrelated, "unrelated@example.com")
    assert client.post("/api/auth/logout-all").status_code == 200
    assert client.get("/api/auth/me").status_code == 401
    assert second_device.get("/api/auth/me").status_code == 401
    assert unrelated.get("/api/auth/me").status_code == 200
    second_device.close()
    unrelated.close()


def test_reset_invalidates_other_outstanding_links(client):
    user = register(client)
    tokens = [
        client.post("/api/auth/forgot-password", json={"email": user["email"]})
        .json()["development_link"]
        .split("token=")[1]
        for _ in range(2)
    ]
    assert (
        client.post("/api/auth/reset-password", json={"token": tokens[0], "password": "Fresh-password-123"}).status_code
        == 200
    )
    assert (
        client.post(
            "/api/auth/reset-password", json={"token": tokens[1], "password": "Another-password-123"}
        ).status_code
        == 400
    )


def test_cross_site_auth_is_rejected(client):
    response = client.post(
        "/api/auth/login",
        headers={"Sec-Fetch-Site": "cross-site"},
        json={"email": "test@example.com", "password": "Strong-passphrase-123"},
    )
    assert response.status_code == 403


def test_email_transport_verifies_certificates(client, db_factory, monkeypatch):
    from app.config import settings
    from app.models import User

    user = register(client)
    contexts = []
    messages = []

    class FakeSMTP:
        def __init__(self, *args, **kwargs):
            pass

        def __enter__(self):
            return self

        def __exit__(self, *args):
            pass

        def starttls(self, *, context):
            contexts.append(context)

        def login(self, *args):
            pass

        def send_message(self, message):
            messages.append(message)

    monkeypatch.setattr(auth.smtplib, "SMTP", FakeSMTP)
    monkeypatch.setattr(settings(), "email_host", "smtp.invalid")
    with db_factory() as db:
        auth.issue_email(db.get(User, user["id"]), "verify", db)
    assert contexts[0].verify_mode == ssl.CERT_REQUIRED
    assert contexts[0].check_hostname is True
    assert messages[0]["To"] == user["email"]
