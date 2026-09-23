from collections import Counter

from conftest import register

from app.mixed_bank import TOPICS, build_questions
from app.models import AttemptQuestion


def test_original_bank_has_valid_unique_questions():
    bank = list(build_questions())
    assert len(bank) == 195
    assert len({q["slug"] for q in bank}) == 195
    for q in bank:
        assert len(q["options"]) == len(set(q["options"]))
        if q["type"] == "reflection":
            assert q["correct_answer"] is None
        else:
            assert 0 <= q["correct_answer"] < len(q["options"])


def test_all_mixed_sizes_and_unscored_reflections(client, db_factory):
    register(client)
    for count in [25, 50, 75]:
        created = client.post("/api/assessments/mixed", json={"count": count, "difficulty": "pro"})
        assert created.status_code == 201, created.text
        aid = created.json()["id"]
        state = client.get("/api/attempts/" + aid).json()
        assert len(state["questions"]) == count
        assert Counter(q["section"] for q in state["questions"]) == {t: count // 5 for t in TOPICS}
        assert len({q["question"]["id"] for q in state["questions"]}) == count
        assert all(
            q["question"]["difficulty"] == "pro" for q in state["questions"] if q["question"]["type"] != "reflection"
        )
        reflection = next(q for q in state["questions"] if q["question"]["type"] == "reflection")
        assert client.put(f"/api/attempts/{aid}/answers/{reflection['id']}", json={"selected": 4}).status_code == 200
        graded = next(q for q in state["questions"] if q["question"]["type"] == "mcq")
        with db_factory() as db:
            correct = db.get(AttemptQuestion, graded["id"]).snapshot["correct_answer"]
        assert client.put(f"/api/attempts/{aid}/answers/{graded['id']}", json={"selected": correct}).status_code == 200
        assert client.post("/api/attempts/" + aid + "/submit").status_code == 200
        result = client.get("/api/attempts/" + aid).json()["result"]
        assert result["score"] == 2
        assert result["maximum"] == count * 4 // 5 * 2
        assert len(result["reflections"]) == count // 5
        assert sum(x["response"] is not None for x in result["reflections"]) == 1
        assert all(t["name"] != "Psychometric Reflection" for t in result["topics"])
    assert client.get("/api/history").json()["total"] == 3
    assert client.post("/api/assessments/mixed", json={"count": 26, "difficulty": "pro"}).status_code == 422


def test_company_count_override_and_legacy_pattern(client):
    register(client)
    track = client.get("/api/companies").json()[0]["tracks"][0]["id"]
    aid = client.post(
        "/api/assessments/start", json={"track_id": track, "difficulty": "moderate", "question_count": 50}
    ).json()["id"]
    state = client.get("/api/attempts/" + aid).json()
    assert state["snapshot"]["mode"] == "mixed"
    assert state["snapshot"]["company"] != "Mixed preparation"
    assert len(state["questions"]) == 50
    client.post("/api/attempts/" + aid + "/submit")
    aid = client.post("/api/assessments/start", json={"track_id": track, "difficulty": "moderate"}).json()["id"]
    assert len(client.get("/api/attempts/" + aid).json()["questions"]) == 8
