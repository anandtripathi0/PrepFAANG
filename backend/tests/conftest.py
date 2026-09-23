import os
import uuid

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app import seed
from app.config import settings
from app.db import Base, get_db
from app.main import app
from app.mixed_bank import seed_mixed


@pytest.fixture
def db_factory(monkeypatch):
    engine = create_engine("sqlite://", connect_args={"check_same_thread": False}, poolclass=StaticPool)
    Base.metadata.create_all(engine)
    factory = sessionmaker(engine, expire_on_commit=False)
    monkeypatch.setattr(seed, "SessionLocal", factory)
    seed.seed()
    with factory() as db:
        seed_mixed(db)
    monkeypatch.setattr(settings(), "email_host", "")
    mongo_name = None
    if os.environ.get("TEST_MONGO") == "1":
        from sqlalchemy import select

        from app.mongo import MongoSession, client, collection_name, database, ensure_indexes

        mongo_name = "prepfaang_test_" + uuid.uuid4().hex[:20]
        monkeypatch.setattr(settings(), "database_name", mongo_name)
        ensure_indexes()
        with factory() as db:
            for mapper in Base.registry.mappers:
                model = mapper.class_
                primary = list(mapper.local_table.primary_key.columns)[0].name
                docs = [
                    {"_id": getattr(row, primary), **{c.name: getattr(row, c.name) for c in mapper.local_table.columns}}
                    for row in db.scalars(select(model))
                ]
                if docs:
                    database()[collection_name(model)].insert_many(docs)
        factory = MongoSession

    def dependency():
        with factory() as db:
            yield db

    app.dependency_overrides[get_db] = dependency
    yield factory
    app.dependency_overrides.clear()
    if mongo_name and mongo_name.startswith("prepfaang_test_") and len(mongo_name) == 34:
        client().drop_database(mongo_name)
    engine.dispose()


@pytest.fixture
def client(db_factory):
    return TestClient(app)


def register(client, email="student@example.com"):
    response = client.post(
        "/api/auth/signup", json={"full_name": "Test Learner", "email": email, "password": "Strong-passphrase-123"}
    )
    assert response.status_code == 201, response.text
    client.headers["X-CSRF-Token"] = response.json()["csrf"]
    return response.json()["user"]


def start(client, difficulty="moderate"):
    company = client.get("/api/companies").json()[0]
    track = company["tracks"][0]
    response = client.post("/api/assessments/start", json={"track_id": track["id"], "difficulty": difficulty})
    assert response.status_code == 201, response.text
    return response.json()["id"]
