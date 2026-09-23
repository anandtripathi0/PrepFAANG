from datetime import datetime, timedelta, timezone

from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel, Field
from sqlalchemy import select

from .assessment import expire_user
from .auth import CurrentUser, Db
from .models import Announcement, Attempt, Bookmark, CodeSubmission, Company, Question, Track, UserProfile
from .questions import question_snapshot, safe_question

router = APIRouter(prefix="/api", tags=["Catalog and progress"])


@router.get("/companies")
def companies(
    db: Db, search: str = "", category: str = "", page: int = Query(1, ge=1), page_size: int = Query(30, ge=1, le=100)
):
    query = select(Company).where(Company.active.is_(True))
    if search:
        query = query.where(Company.name.ilike("%" + search + "%"))
    if category:
        query = query.where(Company.category == category)
    items = db.scalars(query.order_by(Company.name).offset((page - 1) * page_size).limit(page_size)).all()
    return [company_data(c, db) for c in items]


def company_data(company, db):
    tracks = db.scalars(select(Track).where(Track.company_id == company.id, Track.active.is_(True))).all()
    return {
        **{k: getattr(company, k) for k in ["id", "slug", "name", "description", "category", "logo"]},
        "tracks": [{"id": t.id, "name": t.name, "description": t.description} for t in tracks],
    }


@router.get("/companies/{slug}")
def company(slug: str, db: Db):
    row = db.scalar(select(Company).where(Company.slug == slug, Company.active.is_(True)))
    if not row:
        raise HTTPException(404, "Company not found.")
    return company_data(row, db)


@router.get("/questions")
def questions(
    db: Db,
    user: CurrentUser,
    type: str = "",
    topic: str = "",
    difficulty: str = "",
    search: str = "",
    page: int = Query(1, ge=1),
    page_size: int = Query(30, ge=1, le=100),
):
    query = select(Question).where(Question.status == "active")
    for key, value in [("type", type), ("topic", topic), ("difficulty", difficulty)]:
        if value:
            query = query.where(getattr(Question, key) == value)
    if search:
        query = query.where(Question.title.ilike("%" + search + "%"))
    return [
        safe_question(question_snapshot(q, db))
        for q in db.scalars(
            query.order_by(Question.topic, Question.title).offset((page - 1) * page_size).limit(page_size)
        )
    ]


@router.get("/topics")
def topics(db: Db):
    return list(
        db.scalars(select(Question.topic).where(Question.status == "active").distinct().order_by(Question.topic))
    )


@router.get("/questions/{slug}")
def question(slug: str, user: CurrentUser, db: Db):
    q = db.scalar(select(Question).where(Question.slug == slug, Question.status == "active"))
    if not q:
        raise HTTPException(404, "Question not found.")
    return safe_question(question_snapshot(q, db))


class ProfileRequest(BaseModel):
    full_name: str = Field(min_length=2, max_length=120)
    college: str = Field(default="", max_length=200)
    graduation_year: str = Field(default="", max_length=4)
    degree: str = Field(default="", max_length=80)
    branch: str = Field(default="", max_length=100)
    experience_level: str = Field(default="Student", max_length=60)
    target_companies: list[str] = Field(default_factory=list, max_length=20)
    target_roles: list[str] = Field(default_factory=list, max_length=20)
    onboarding_complete: bool = True
    leaderboard_opt_in: bool = False


@router.put("/users/profile")
def profile(data: ProfileRequest, user: CurrentUser, db: Db):
    user.full_name = data.full_name
    row = db.scalar(select(UserProfile).where(UserProfile.user_id == user.id))
    if not row:
        row = UserProfile(user_id=user.id)
        db.add(row)
    row.details = data.model_dump(exclude={"full_name"})
    db.commit()
    return {"saved": True}


def summary(a):
    return {
        "id": a.id,
        "company": a.snapshot["company"],
        "track": a.snapshot["track"],
        "difficulty": a.difficulty,
        "status": a.status,
        "started_at": a.started_at,
        "expires_at": a.expires_at,
        "result": a.result,
    }


@router.get("/history")
def history(
    user: CurrentUser,
    db: Db,
    company: str = "",
    difficulty: str = "",
    after: float = 0,
    min_score: float = 0,
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
):
    expire_user(db, user)
    query = select(Attempt).where(
        Attempt.user_id == user.id, Attempt.status == "completed", Attempt.started_at >= after
    )
    if difficulty:
        query = query.where(Attempt.difficulty == difficulty)
    items = [
        summary(a)
        for a in db.scalars(query.order_by(Attempt.started_at.desc()))
        if (not company or a.snapshot["company"] == company) and a.result["percentage"] >= min_score
    ]
    return {"items": items[(page - 1) * page_size : page * page_size], "total": len(items)}


@router.get("/analytics")
def analytics(user: CurrentUser, db: Db):
    expire_user(db, user)
    attempts = db.scalars(
        select(Attempt).where(Attempt.user_id == user.id, Attempt.status == "completed").order_by(Attempt.started_at)
    ).all()
    active = db.scalar(select(Attempt).where(Attempt.user_id == user.id, Attempt.status == "active"))
    scores = [a.result["percentage"] for a in attempts]
    topic_stats, company_stats, difficulty_stats = {}, {}, {}
    for a in attempts:
        for t in a.result["topics"]:
            stat = topic_stats.setdefault(t["name"], {"name": t["name"], "correct": 0, "count": 0, "time_spent": 0})
            for key in ("correct", "count", "time_spent"):
                stat[key] += t[key]
        for group, name in ((company_stats, a.snapshot["company"]), (difficulty_stats, a.difficulty)):
            group.setdefault(name, []).append(a.result["percentage"])
    topics = [{**t, "accuracy": round(t["correct"] / t["count"] * 100, 1)} for t in topic_stats.values()]
    submissions = db.scalars(
        select(CodeSubmission).where(CodeSubmission.user_id == user.id, CodeSubmission.mode == "submit")
    ).all()
    solved = len({s.question_id for s in submissions if s.result["status"] == "Accepted"})
    days = {datetime.fromtimestamp(a.started_at, timezone.utc).date() for a in attempts}
    current = datetime.now(timezone.utc).date()
    if current not in days:
        current -= timedelta(days=1)
    streak = 0
    while current in days:
        streak += 1
        current -= timedelta(days=1)
    profile = db.scalar(select(UserProfile).where(UserProfile.user_id == user.id))
    return {
        "attempts": len(attempts),
        "average": round(sum(scores) / len(scores), 1) if scores else None,
        "best": max(scores) if scores else None,
        "solved": solved,
        "streak": streak,
        "practice_seconds": sum(a.result["time_used"] for a in attempts),
        "active": summary(active) if active else None,
        "trend": [{"id": a.id, "date": a.started_at, "score": a.result["percentage"]} for a in attempts[-30:]],
        "recent": [summary(a) for a in attempts[-5:][::-1]],
        "topics": sorted(topics, key=lambda t: t["accuracy"]),
        "companies": [{"name": k, "score": round(sum(v) / len(v), 1)} for k, v in company_stats.items()],
        "difficulties": [{"name": k, "score": round(sum(v) / len(v), 1)} for k, v in difficulty_stats.items()],
        "coding_acceptance": round(
            sum(s.result["status"] == "Accepted" for s in submissions) / len(submissions) * 100, 1
        )
        if submissions
        else None,
        "target_companies": profile.details.get("target_companies", []) if profile else [],
        "recommendations": [
            f"Practice {t['name']}: {t['accuracy']}% correct across {t['count']} questions."
            for t in topics
            if t["accuracy"] < 60
        ],
    }


@router.get("/bookmarks")
def bookmarks(user: CurrentUser, db: Db):
    return [
        safe_question(question_snapshot(q, db))
        for bookmark in db.scalars(select(Bookmark).where(Bookmark.user_id == user.id))
        if (q := db.get(Question, bookmark.question_id)) is not None
    ]


@router.put("/bookmarks/{question_id}")
def add_bookmark(question_id: str, user: CurrentUser, db: Db):
    if not db.get(Question, question_id):
        raise HTTPException(404, "Question not found.")
    row = db.scalar(select(Bookmark).where(Bookmark.user_id == user.id, Bookmark.question_id == question_id))
    if not row:
        db.add(Bookmark(user_id=user.id, question_id=question_id))
        db.commit()
    return {"saved": True}


@router.delete("/bookmarks/{question_id}")
def remove_bookmark(question_id: str, user: CurrentUser, db: Db):
    row = db.scalar(select(Bookmark).where(Bookmark.user_id == user.id, Bookmark.question_id == question_id))
    if row:
        db.delete(row)
        db.commit()
    return {"saved": False}


@router.get("/announcements")
def announcements(db: Db):
    return [
        {"id": a.id, "title": a.title, "body": a.body}
        for a in db.scalars(select(Announcement).where(Announcement.active.is_(True)))
    ]
