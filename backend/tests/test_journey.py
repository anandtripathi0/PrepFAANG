import time

from conftest import register, start
from fastapi.testclient import TestClient
from sqlalchemy import select

from app import assessment
from app.main import app
from app.models import Attempt, AttemptQuestion, Pattern, User


def answer_payload(**kwargs):
    return {
        "selected": None,
        "code": "",
        "language": "python",
        "marked": False,
        "visited": True,
        "time_spent": 10,
        **kwargs,
    }


def test_complete_journey_and_isolation(client, db_factory, monkeypatch):
    user = register(client)
    assert client.post("/api/auth/logout").status_code == 200
    assert client.get("/api/analytics").status_code == 401
    login = client.post("/api/auth/login", json={"email": user["email"], "password": "Strong-passphrase-123"})
    assert login.status_code == 200
    client.headers["X-CSRF-Token"] = login.json()["csrf"]
    assert (
        client.put(
            "/api/users/profile",
            json={"full_name": "Test Learner", "college": "Sample College", "target_companies": ["Google"]},
        ).status_code
        == 200
    )
    assert client.get("/api/analytics").json()["average"] is None
    attempt_id = start(client)
    before = client.get("/api/attempts/" + attempt_id).json()
    assert len(before["questions"]) == 8
    assert before["expires_at"] > before["server_now"]
    assert all("correct_answer" not in q["question"] for q in before["questions"])
    first = before["questions"][0]
    with db_factory() as db:
        correct = db.get(AttemptQuestion, first["id"]).snapshot["correct_answer"]
    assert (
        client.put(
            f"/api/attempts/{attempt_id}/answers/{first['id']}", json=answer_payload(selected=correct, marked=True)
        ).status_code
        == 200
    )
    restored = client.get("/api/attempts/" + attempt_id).json()
    assert restored["expires_at"] == before["expires_at"]
    assert restored["questions"][0]["answer"]["selected"] == correct
    assert [q["id"] for q in before["questions"]] == [q["id"] for q in restored["questions"]]
    coding = next(q for q in before["questions"] if q["question"]["type"] == "coding")
    assert all(not t["hidden"] for t in coding["question"]["coding"]["tests"])
    calls = []

    def fake_runner(code, language, specification, hidden=False):
        cases = specification["tests"] if hidden else [t for t in specification["tests"] if not t["hidden"]]
        calls.append(hidden)
        return {"status": "Accepted", "passed": len(cases), "total": len(cases), "runtime_ms": 2, "tests": []}

    monkeypatch.setattr(assessment.runner, "evaluate", fake_runner)
    body = {
        "question_id": coding["question"]["id"],
        "attempt_id": attempt_id,
        "attempt_question_id": coding["id"],
        "language": "python",
        "code": "print(2)",
    }
    assert client.post("/api/code/evaluate", json={**body, "mode": "run"}).status_code == 200
    code_result = client.post("/api/code/evaluate", json={**body, "mode": "submit"}).json()
    assert calls == [False, True]
    assert code_result["passed"] == 4
    assert client.put("/api/bookmarks/" + first["question"]["id"]).status_code == 200
    assert client.post(f"/api/attempts/{attempt_id}/events", json={"kind": "TAB_SWITCH"}).status_code == 200
    for _ in range(2):
        assert client.post(f"/api/attempts/{attempt_id}/submit").status_code == 200
    result = client.get("/api/attempts/" + attempt_id).json()
    assert result["status"] == "completed"
    assert result["result"]["score"] == 8
    assert result["result"]["coding_score"] == 6
    assert result["review_available"]
    assert client.get("/api/history").json()["total"] == 1
    stats = client.get("/api/analytics").json()
    assert stats["attempts"] == 1 and stats["solved"] == 1
    assert stats["average"] == 40
    assert (
        client.put(f"/api/attempts/{attempt_id}/answers/{first['id']}", json=answer_payload(selected=0)).status_code
        == 409
    )
    second = TestClient(app)
    register(second, "second@example.com")
    assert second.get("/api/attempts/" + attempt_id).status_code == 404
    assert second.post("/api/attempts/" + attempt_id + "/submit").status_code == 404
    assert second.put(f"/api/attempts/{attempt_id}/answers/{first['id']}", json=answer_payload()).status_code == 404
    assert second.get("/api/code/submissions/" + code_result["id"]).status_code == 404
    assert second.get("/api/history").json()["items"] == []
    assert second.get("/api/analytics").json()["attempts"] == 0
    assert second.get("/api/bookmarks").json() == []
    assert client.post("/api/auth/logout").status_code == 200
    assert client.get("/api/attempts/" + attempt_id).status_code == 401


def test_expiry_and_snapshot(client, db_factory):
    register(client)
    aid = start(client, "pro")
    attempt = client.get("/api/attempts/" + aid).json()
    assert all(q["question"]["difficulty"] == "pro" for q in attempt["questions"])
    with db_factory() as db:
        row = db.get(Attempt, aid)
        pattern = db.get(Pattern, row.snapshot["id"])
        pattern.duration_minutes = 100
        row.expires_at = time.time() - 1
        db.commit()
    closed = client.get("/api/attempts/" + aid).json()
    assert closed["status"] == "completed"
    assert closed["snapshot"]["duration_minutes"] == 30
    assert closed["result"]["unanswered"] == 8
    assert client.post("/api/attempts/" + aid + "/submit").status_code == 200
    assert client.get("/api/history").json()["total"] == 1


def test_csrf_roles_password_reset_and_review_policy(client, db_factory):
    user = register(client)
    assert client.get("/api/admin/users").status_code == 403
    assert client.post("/api/admin/companies", json={}).status_code == 403
    token = client.headers.pop("X-CSRF-Token")
    assert client.post("/api/auth/logout").status_code == 403
    client.headers["X-CSRF-Token"] = token
    assert client.post("/api/auth/logout", headers={"Origin": "https://evil.example"}).status_code == 403
    with db_factory() as db:
        row = db.get(User, user["id"])
        assert row.password_hash.startswith("$argon2")
        row.role = "admin"
        db.commit()
    listing = client.get("/api/admin/users").json()
    assert "password_hash" not in listing[0]
    created = client.post(
        "/api/admin/companies",
        json={"slug": "example", "name": "Example", "category": "Startup", "description": "Original practice"},
    ).json()
    assert "id" in created
    assert client.put("/api/admin/users/" + user["id"], json={"active": False, "role": "student"}).status_code == 409
    aid = start(client)
    with db_factory() as db:
        row = db.get(Attempt, aid)
        row.snapshot = {**row.snapshot, "review_policy": "never"}
        db.commit()
    client.post("/api/attempts/" + aid + "/submit")
    assert client.get("/api/attempts/" + aid).json()["questions"] == []
    response = client.post("/api/auth/forgot-password", json={"email": user["email"]}).json()
    reset_token = response["development_link"].split("token=")[1]
    assert (
        client.post(
            "/api/auth/reset-password", json={"token": reset_token, "password": "New-strong-password-123"}
        ).status_code
        == 200
    )
    assert client.get("/api/auth/me").status_code == 401
    assert (
        client.post(
            "/api/auth/reset-password", json={"token": reset_token, "password": "Another-password-123"}
        ).status_code
        == 400
    )


def test_difficulty_shortage_and_duplicate_start(client):
    register(client)
    response = client.post(
        "/api/assessments/practice", json={"topic": "Quantitative Aptitude", "difficulty": "moderate", "count": 20}
    )
    assert response.status_code == 409
    aid = start(client, "beginner")
    q = client.get("/api/attempts/" + aid).json()
    assert all(a["question"]["difficulty"] == "beginner" for a in q["questions"])
    assert round(q["expires_at"] - q["started_at"]) == 2340
    company = client.get("/api/companies").json()[0]
    assert (
        client.post(
            "/api/assessments/start", json={"track_id": company["tracks"][0]["id"], "difficulty": "moderate"}
        ).status_code
        == 409
    )


def test_invalid_import_atomic_and_negative_marking(client, db_factory):
    user = register(client)
    with db_factory() as db:
        db.get(User, user["id"]).role = "admin"
        db.commit()
    import json

    assert (
        client.post(
            "/api/admin/questions/import", json={"format": "json", "content": json.dumps([{"slug": "bad"}])}
        ).status_code
        == 422
    )
    aid = start(client)
    with db_factory() as db:
        aq = db.scalar(
            select(AttemptQuestion).where(AttemptQuestion.attempt_id == aid).order_by(AttemptQuestion.position)
        )
        aq.snapshot = {**aq.snapshot, "negative_marks": 0.5, "weight": 2}
        correct, aqid = aq.snapshot["correct_answer"], aq.id
        db.commit()
    client.put(f"/api/attempts/{aid}/answers/{aqid}", json=answer_payload(selected=(correct + 1) % 4))
    client.post("/api/attempts/" + aid + "/submit")
    assert client.get("/api/attempts/" + aid).json()["result"]["score"] == -1


def test_rate_limit(client):
    for _ in range(5):
        assert client.post("/api/auth/forgot-password", json={"email": "none@example.com"}).status_code == 200
    assert client.post("/api/auth/forgot-password", json={"email": "none@example.com"}).status_code == 429
