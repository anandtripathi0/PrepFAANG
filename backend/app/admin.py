import csv
import io
import json
from typing import Literal

from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel, ConfigDict, Field, ValidationError, model_validator
from sqlalchemy import delete, select

from .auth import Admin, Db
from .models import (
    Announcement,
    Attempt,
    CodingProblem,
    CodingTestCase,
    Company,
    Pattern,
    Question,
    QuestionOption,
    Section,
    Track,
    User,
)
from .questions import question_snapshot

router = APIRouter(prefix="/api/admin", tags=["Administration"])


class Strict(BaseModel):
    model_config = ConfigDict(extra="forbid")


class CompanyInput(Strict):
    slug: str = Field(pattern=r"^[a-z0-9-]{1,100}$")
    name: str = Field(min_length=1, max_length=120)
    category: str = Field(min_length=1, max_length=80)
    description: str = Field(max_length=10000)
    logo: str = Field(default="", max_length=2000)
    active: bool = True


class TrackInput(Strict):
    company_id: str
    name: str = Field(min_length=1, max_length=120)
    description: str = "Independent practice configuration"
    active: bool = True


class PatternInput(Strict):
    track_id: str
    duration_minutes: int = Field(ge=1, le=300)
    difficulty_rules: dict[str, float] = Field(default_factory=lambda: {"beginner": 1.3, "moderate": 1, "pro": 0.8})
    review_policy: Literal["immediate", "delayed", "never"] = "immediate"
    review_delay_hours: int = Field(default=24, ge=0, le=8760)
    active: bool = True

    @model_validator(mode="after")
    def rules(self):
        if set(self.difficulty_rules) != {"beginner", "moderate", "pro"} or not all(
            0.1 <= v <= 5 for v in self.difficulty_rules.values()
        ):
            raise ValueError("Set all three difficulty multipliers between 0.1 and 5.")
        return self


class SectionInput(Strict):
    pattern_id: str
    name: str = Field(min_length=1, max_length=100)
    position: int = Field(default=0, ge=0)
    topics: list[str] = Field(min_length=1, max_length=30)
    question_count: int = Field(ge=1, le=100)
    marks: float = Field(default=2, gt=0, le=100)
    negative_marks: float = Field(default=0, ge=0, le=100)
    weight: float = Field(default=1, gt=0, le=10)
    partial_coding: bool = True


class TestInput(Strict):
    input: str = Field(max_length=10000)
    output: str = Field(max_length=10000)
    hidden: bool = False


class CodingInput(Strict):
    input_format: str
    output_format: str
    constraints: str
    starter_code: dict[str, str]
    allowed_languages: list[Literal["python", "c", "cpp", "java", "javascript"]]
    time_limit: float = Field(default=2, gt=0, le=5)
    memory_limit: int = Field(default=256, ge=64, le=512)
    tests: list[TestInput] = Field(min_length=1, max_length=20)


class QuestionInput(Strict):
    slug: str = Field(pattern=r"^[a-z0-9-]{1,150}$")
    type: Literal["mcq", "coding", "reflection"] = "mcq"
    title: str = Field(min_length=1, max_length=200)
    question: str = Field(min_length=1, max_length=20000)
    options: list[str] = Field(default_factory=list, max_length=10)
    correct_answer: int | None = None
    explanation: str = Field(max_length=20000)
    difficulty: Literal["beginner", "moderate", "pro"]
    topic: str = Field(min_length=1, max_length=100)
    subtopic: str = ""
    tags: list[str] = Field(default_factory=list, max_length=30)
    company_tags: list[str] = Field(default_factory=list, max_length=100)
    track_tags: list[str] = Field(default_factory=list, max_length=100)
    estimated_time: int = Field(default=90, ge=1, le=3600)
    status: Literal["active", "archived"] = "active"
    coding: CodingInput | None = None

    @model_validator(mode="after")
    def valid_question(self):
        if self.type == "reflection" and (len(self.options) < 2 or self.correct_answer is not None):
            raise ValueError("Reflection items need options and no correct answer.")
        if self.type == "mcq" and (
            len(self.options) < 2 or self.correct_answer is None or not 0 <= self.correct_answer < len(self.options)
        ):
            raise ValueError("MCQs need at least two options and a valid correct_answer index.")
        if self.type == "coding" and (not self.coding or not self.coding.allowed_languages):
            raise ValueError("Coding questions need a problem specification and allowed languages.")
        return self


class UserInput(Strict):
    role: Literal["student", "admin"]
    active: bool


class AnnouncementInput(Strict):
    title: str = Field(min_length=1, max_length=160)
    body: str = Field(min_length=1, max_length=10000)
    active: bool = True


ENTITIES = {
    "companies": (Company, CompanyInput),
    "tracks": (Track, TrackInput),
    "patterns": (Pattern, PatternInput),
    "sections": (Section, SectionInput),
    "questions": (Question, QuestionInput),
    "users": (User, UserInput),
    "announcements": (Announcement, AnnouncementInput),
}


def save_question(db, data, row=None):
    values = data.model_dump(exclude={"options", "coding"})
    if row is None:
        row = Question(**values)
        db.add(row)
        db.flush()
    else:
        for key, value in values.items():
            setattr(row, key, value)
        db.execute(delete(QuestionOption).where(QuestionOption.question_id == row.id))
        old = db.scalar(select(CodingProblem).where(CodingProblem.question_id == row.id))
        if old:
            db.execute(delete(CodingTestCase).where(CodingTestCase.problem_id == old.id))
            db.delete(old)
            db.flush()
    for position, text in enumerate(data.options):
        db.add(QuestionOption(question_id=row.id, position=position, text=text))
    if data.coding:
        problem = CodingProblem(question_id=row.id, **data.coding.model_dump(exclude={"tests"}))
        db.add(problem)
        db.flush()
        for case in data.coding.tests:
            db.add(CodingTestCase(problem_id=problem.id, **case.model_dump()))
    return row


def serialize(row):
    return {c.name: getattr(row, c.name) for c in row.__table__.columns if c.name not in ("password_hash",)}


@router.get("/{entity}")
def listing(entity: str, admin: Admin, db: Db, page: int = Query(1, ge=1), page_size: int = Query(50, ge=1, le=200)):
    model = Attempt if entity == "attempts" else ENTITIES.get(entity, (None,))[0]
    if not model:
        raise HTTPException(404, "Unknown resource.")
    items = db.scalars(
        select(model).order_by(model.created_at.desc()).offset((page - 1) * page_size).limit(page_size)
    ).all()
    if entity == "questions":
        return [{**serialize(q), **question_snapshot(q, db)} for q in items]
    return [serialize(row) for row in items]


def mutate(entity, payload, admin, db, record_id=None):
    if entity not in ENTITIES or (entity == "users" and not record_id):
        raise HTTPException(422, "Unsupported operation.")
    model, schema = ENTITIES[entity]
    try:
        data = schema.model_validate(payload)
    except ValidationError as exc:
        raise HTTPException(422, str(exc))
    row = db.get(model, record_id) if record_id else None
    if record_id and not row:
        raise HTTPException(404, "Record not found.")
    if entity == "users" and record_id == admin.id and (data.role != "admin" or not data.active):
        raise HTTPException(409, "You cannot disable or demote your own administrator account.")
    for field, target in [("company_id", Company), ("track_id", Track), ("pattern_id", Pattern)]:
        if hasattr(data, field) and not db.get(target, getattr(data, field)):
            raise HTTPException(422, f"{field} does not exist.")
    if entity == "questions":
        row = save_question(db, data, row)
    elif row:
        for key, value in data.model_dump().items():
            setattr(row, key, value)
    else:
        row = model(**data.model_dump())
        db.add(row)
    db.commit()
    return {"id": row.id}


class ImportRequest(BaseModel):
    format: Literal["json", "csv"]
    content: str = Field(max_length=2000000)


@router.post("/questions/import")
def import_questions(data: ImportRequest, admin: Admin, db: Db):
    try:
        items = json.loads(data.content) if data.format == "json" else list(csv.DictReader(io.StringIO(data.content)))
        if not isinstance(items, list) or not 1 <= len(items) <= 500:
            raise ValueError("Import between 1 and 500 questions.")
        validated = []
        for item in items:
            if data.format == "csv":
                for key in ("options", "tags", "company_tags", "track_tags", "coding"):
                    if item.get(key):
                        item[key] = json.loads(item[key])
                    else:
                        item.pop(key, None)
            validated.append(QuestionInput.model_validate(item))
        for question in validated:
            save_question(db, question)
        db.commit()
    except (ValueError, TypeError) as exc:
        db.rollback()
        raise HTTPException(422, str(exc))
    return {"imported": len(validated)}


@router.post("/{entity}", status_code=201)
def create(entity: str, payload: dict, admin: Admin, db: Db):
    return mutate(entity, payload, admin, db)


@router.put("/{entity}/{record_id}")
def edit(entity: str, record_id: str, payload: dict, admin: Admin, db: Db):
    return mutate(entity, payload, admin, db, record_id)
