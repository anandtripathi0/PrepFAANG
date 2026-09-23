import time
import uuid

from sqlalchemy import JSON, Boolean, Float, ForeignKey, Index, Integer, String, Text, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column

from .db import Base


def uid():
    return str(uuid.uuid4())


class Entity:
    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=uid)
    created_at: Mapped[float] = mapped_column(Float, default=time.time)
    updated_at: Mapped[float] = mapped_column(Float, default=time.time, onupdate=time.time)


class User(Entity, Base):
    __tablename__ = "users"
    full_name: Mapped[str] = mapped_column(String(120))
    email: Mapped[str] = mapped_column(String(254), unique=True, index=True)
    password_hash: Mapped[str] = mapped_column(Text)
    email_verified: Mapped[bool] = mapped_column(Boolean, default=False)
    avatar: Mapped[str] = mapped_column(Text, default="")
    role: Mapped[str] = mapped_column(String(20), default="student")
    active: Mapped[bool] = mapped_column(Boolean, default=True)
    last_login: Mapped[float | None] = mapped_column(Float, nullable=True)


class UserProfile(Entity, Base):
    __tablename__ = "profiles"
    user_id: Mapped[str] = mapped_column(ForeignKey("users.id"), unique=True)
    details: Mapped[dict] = mapped_column(JSON, default=dict)


class Session(Entity, Base):
    __tablename__ = "sessions"
    user_id: Mapped[str] = mapped_column(ForeignKey("users.id"), index=True)
    token_hash: Mapped[str] = mapped_column(String(64), unique=True)
    csrf: Mapped[str] = mapped_column(String(64))
    expires_at: Mapped[float] = mapped_column(Float)


class AuthToken(Entity, Base):
    __tablename__ = "auth_tokens"
    user_id: Mapped[str] = mapped_column(ForeignKey("users.id"))
    token_hash: Mapped[str] = mapped_column(String(64), unique=True)
    purpose: Mapped[str] = mapped_column(String(20))
    expires_at: Mapped[float] = mapped_column(Float)
    used: Mapped[bool] = mapped_column(Boolean, default=False)


class RateBucket(Base):
    __tablename__ = "rate_buckets"
    key: Mapped[str] = mapped_column(String(64), primary_key=True)
    count: Mapped[int] = mapped_column(Integer, default=0)
    expires_at: Mapped[float] = mapped_column(Float)


class Company(Entity, Base):
    __tablename__ = "companies"
    slug: Mapped[str] = mapped_column(String(100), unique=True)
    name: Mapped[str] = mapped_column(String(120))
    category: Mapped[str] = mapped_column(String(80), index=True)
    description: Mapped[str] = mapped_column(Text)
    logo: Mapped[str] = mapped_column(Text, default="")
    active: Mapped[bool] = mapped_column(Boolean, default=True)


class Track(Entity, Base):
    __tablename__ = "tracks"
    company_id: Mapped[str] = mapped_column(ForeignKey("companies.id"), index=True)
    name: Mapped[str] = mapped_column(String(120))
    description: Mapped[str] = mapped_column(Text, default="Independent practice configuration")
    active: Mapped[bool] = mapped_column(Boolean, default=True)


class Pattern(Entity, Base):
    __tablename__ = "patterns"
    track_id: Mapped[str] = mapped_column(ForeignKey("tracks.id"), unique=True)
    duration_minutes: Mapped[int] = mapped_column(Integer, default=30)
    difficulty_rules: Mapped[dict] = mapped_column(JSON, default=lambda: {"beginner": 1.3, "moderate": 1, "pro": 0.8})
    review_policy: Mapped[str] = mapped_column(String(20), default="immediate")
    review_delay_hours: Mapped[int] = mapped_column(Integer, default=24)
    active: Mapped[bool] = mapped_column(Boolean, default=True)


class Section(Entity, Base):
    __tablename__ = "sections"
    pattern_id: Mapped[str] = mapped_column(ForeignKey("patterns.id"), index=True)
    name: Mapped[str] = mapped_column(String(100))
    position: Mapped[int] = mapped_column(Integer, default=0)
    topics: Mapped[list] = mapped_column(JSON)
    question_count: Mapped[int] = mapped_column(Integer, default=2)
    marks: Mapped[float] = mapped_column(Float, default=2)
    negative_marks: Mapped[float] = mapped_column(Float, default=0)
    weight: Mapped[float] = mapped_column(Float, default=1)
    partial_coding: Mapped[bool] = mapped_column(Boolean, default=True)


class Question(Entity, Base):
    __tablename__ = "questions"
    slug: Mapped[str] = mapped_column(String(150), unique=True)
    type: Mapped[str] = mapped_column(String(20), default="mcq")
    title: Mapped[str] = mapped_column(String(200))
    question: Mapped[str] = mapped_column(Text)
    correct_answer: Mapped[int | None] = mapped_column(Integer, nullable=True)
    explanation: Mapped[str] = mapped_column(Text)
    difficulty: Mapped[str] = mapped_column(String(20), index=True)
    topic: Mapped[str] = mapped_column(String(100), index=True)
    subtopic: Mapped[str] = mapped_column(String(100), default="")
    tags: Mapped[list] = mapped_column(JSON, default=list)
    company_tags: Mapped[list] = mapped_column(JSON, default=list)
    track_tags: Mapped[list] = mapped_column(JSON, default=list)
    estimated_time: Mapped[int] = mapped_column(Integer, default=90)
    status: Mapped[str] = mapped_column(String(20), default="active")


class QuestionOption(Entity, Base):
    __tablename__ = "question_options"
    question_id: Mapped[str] = mapped_column(ForeignKey("questions.id"), index=True)
    position: Mapped[int] = mapped_column(Integer)
    text: Mapped[str] = mapped_column(Text)


class CodingProblem(Entity, Base):
    __tablename__ = "coding_problems"
    question_id: Mapped[str] = mapped_column(ForeignKey("questions.id"), unique=True)
    input_format: Mapped[str] = mapped_column(Text)
    output_format: Mapped[str] = mapped_column(Text)
    constraints: Mapped[str] = mapped_column(Text)
    starter_code: Mapped[dict] = mapped_column(JSON)
    allowed_languages: Mapped[list] = mapped_column(JSON)
    time_limit: Mapped[float] = mapped_column(Float, default=2)
    memory_limit: Mapped[int] = mapped_column(Integer, default=256)


class CodingTestCase(Entity, Base):
    __tablename__ = "coding_tests"
    problem_id: Mapped[str] = mapped_column(ForeignKey("coding_problems.id"), index=True)
    input: Mapped[str] = mapped_column(Text)
    output: Mapped[str] = mapped_column(Text)
    hidden: Mapped[bool] = mapped_column(Boolean, default=False)


class Attempt(Entity, Base):
    __tablename__ = "attempts"
    user_id: Mapped[str] = mapped_column(ForeignKey("users.id"), index=True)
    status: Mapped[str] = mapped_column(String(20), default="active", index=True)
    difficulty: Mapped[str] = mapped_column(String(20))
    snapshot: Mapped[dict] = mapped_column(JSON)
    started_at: Mapped[float] = mapped_column(Float, default=time.time)
    expires_at: Mapped[float] = mapped_column(Float)
    submitted_at: Mapped[float | None] = mapped_column(Float, nullable=True)
    current_position: Mapped[int] = mapped_column(Integer, default=0)
    result: Mapped[dict | None] = mapped_column(JSON, nullable=True)
    __table_args__ = (Index("ix_attempt_user_status", "user_id", "status"),)


class AttemptQuestion(Entity, Base):
    __tablename__ = "attempt_questions"
    attempt_id: Mapped[str] = mapped_column(ForeignKey("attempts.id"), index=True)
    question_id: Mapped[str] = mapped_column(ForeignKey("questions.id"))
    position: Mapped[int] = mapped_column(Integer)
    section: Mapped[str] = mapped_column(String(100))
    snapshot: Mapped[dict] = mapped_column(JSON)
    __table_args__ = (UniqueConstraint("attempt_id", "position"),)


class Answer(Entity, Base):
    __tablename__ = "answers"
    attempt_question_id: Mapped[str] = mapped_column(ForeignKey("attempt_questions.id"), unique=True)
    selected: Mapped[int | None] = mapped_column(Integer, nullable=True)
    code: Mapped[str] = mapped_column(Text, default="")
    language: Mapped[str] = mapped_column(String(30), default="python")
    marked: Mapped[bool] = mapped_column(Boolean, default=False)
    visited: Mapped[bool] = mapped_column(Boolean, default=False)
    time_spent: Mapped[float] = mapped_column(Float, default=0)
    code_result: Mapped[dict | None] = mapped_column(JSON, nullable=True)


class CodeSubmission(Entity, Base):
    __tablename__ = "code_submissions"
    user_id: Mapped[str] = mapped_column(ForeignKey("users.id"), index=True)
    question_id: Mapped[str] = mapped_column(ForeignKey("questions.id"))
    attempt_question_id: Mapped[str | None] = mapped_column(ForeignKey("attempt_questions.id"), nullable=True)
    code: Mapped[str] = mapped_column(Text)
    language: Mapped[str] = mapped_column(String(30))
    result: Mapped[dict] = mapped_column(JSON)
    mode: Mapped[str] = mapped_column(String(20))


class IntegrityEvent(Entity, Base):
    __tablename__ = "integrity_events"
    attempt_id: Mapped[str] = mapped_column(ForeignKey("attempts.id"), index=True)
    kind: Mapped[str] = mapped_column(String(30))


class Bookmark(Entity, Base):
    __tablename__ = "bookmarks"
    user_id: Mapped[str] = mapped_column(ForeignKey("users.id"), index=True)
    question_id: Mapped[str] = mapped_column(ForeignKey("questions.id"))
    __table_args__ = (UniqueConstraint("user_id", "question_id"),)


class Announcement(Entity, Base):
    __tablename__ = "announcements"
    title: Mapped[str] = mapped_column(String(160))
    body: Mapped[str] = mapped_column(Text)
    active: Mapped[bool] = mapped_column(Boolean, default=True)
