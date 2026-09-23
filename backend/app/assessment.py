import random
import time

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field
from sqlalchemy import select, update

from .auth import CurrentUser, Db, limit
from .code_runner import runner
from .mixed import QuestionCount, mixed_config
from .models import (
    Answer,
    Attempt,
    AttemptQuestion,
    CodeSubmission,
    Company,
    IntegrityEvent,
    Pattern,
    Question,
    QuestionOption,
    Section,
    Track,
    User,
)
from .questions import question_snapshot, safe_question

router = APIRouter(prefix="/api", tags=["Assessments"])
DIFFICULTIES = ("beginner", "moderate", "pro")


def owned(db, user, attempt_id, lock=False):
    query = select(Attempt).where(Attempt.id == attempt_id, Attempt.user_id == user.id)
    attempt = db.scalar(query.with_for_update() if lock else query)
    if not attempt:
        raise HTTPException(404, "Assessment not found.")
    return attempt


def rows(db, attempt):
    return db.scalars(
        select(AttemptQuestion).where(AttemptQuestion.attempt_id == attempt.id).order_by(AttemptQuestion.position)
    ).all()


def answer_for(db, aq):
    return db.scalar(select(Answer).where(Answer.attempt_question_id == aq.id))


def rows_with_answers(db, attempt):
    questions = rows(db, attempt)
    answers = {
        a.attempt_question_id: a
        for a in db.scalars(select(Answer).where(Answer.attempt_question_id.in_([q.id for q in questions])))
    }
    return [(q, answers[q.id]) for q in questions]


def finish(db, attempt):
    if attempt.status == "completed":
        return attempt
    claimed = db.execute(
        update(Attempt).where(Attempt.id == attempt.id, Attempt.status == "active").values(status="scoring")
    )
    if not claimed.rowcount:
        db.refresh(attempt)
        return attempt
    sections, topics = {}, {}
    correct = incorrect = unanswered = 0
    coding_score = 0.0
    reflection_answers = []
    for aq, answer in rows_with_answers(db, attempt):
        q = aq.snapshot
        maximum = q["marks"] * q["weight"]
        if q["type"] == "reflection":
            reflection_answers.append(
                {
                    "title": q["title"],
                    "response": q["options"][answer.selected] if answer.selected is not None else None,
                }
            )
            continue
        score, outcome = 0.0, "unanswered"
        if q["type"] == "mcq" and answer.selected is not None:
            outcome = "correct" if answer.selected == q["correct_answer"] else "incorrect"
            score = maximum if outcome == "correct" else -q["negative_marks"] * q["weight"]
        elif q["type"] == "coding" and answer.code_result:
            result = answer.code_result
            if result:
                fraction = result["passed"] / max(1, result["total"])
                score = maximum * (fraction if q["partial_coding"] else int(fraction == 1))
                outcome = "correct" if fraction == 1 else "incorrect"
            else:
                outcome = "not_evaluated"
            coding_score += score
        correct += outcome == "correct"
        incorrect += outcome in ("incorrect", "not_evaluated")
        unanswered += outcome == "unanswered"
        for group, name in ((sections, aq.section), (topics, q["topic"])):
            entry = group.setdefault(
                name, {"name": name, "score": 0, "maximum": 0, "correct": 0, "answered": 0, "count": 0, "time_spent": 0}
            )
            entry["score"] += score
            entry["maximum"] += maximum
            entry["correct"] += outcome == "correct"
            entry["answered"] += outcome != "unanswered"
            entry["count"] += 1
            entry["time_spent"] += answer.time_spent
    total = sum(s["score"] for s in sections.values())
    maximum = sum(s["maximum"] for s in sections.values())
    attempt.status = "completed"
    attempt.submitted_at = min(time.time(), attempt.expires_at)
    attempt.result = {
        "score": round(total, 2),
        "maximum": maximum,
        "percentage": round(max(0, total) / max(1, maximum) * 100, 1),
        "correct": correct,
        "incorrect": incorrect,
        "unanswered": unanswered,
        "coding_score": coding_score,
        "time_used": max(0, round(attempt.submitted_at - attempt.started_at)),
        "sections": list(sections.values()),
        "topics": list(topics.values()),
        "reflections": reflection_answers,
    }
    db.commit()
    return attempt


def expire_user(db, user):
    for attempt in db.scalars(
        select(Attempt).where(Attempt.user_id == user.id, Attempt.status == "active", Attempt.expires_at <= time.time())
    ):
        finish(db, attempt)


def pattern_data(db, track_id):
    track = db.get(Track, track_id)
    if not track or not track.active:
        raise HTTPException(404, "Track not found.")
    company = db.get(Company, track.company_id)
    pattern = db.scalar(select(Pattern).where(Pattern.track_id == track.id, Pattern.active.is_(True)))
    if not pattern or not company.active:
        raise HTTPException(404, "This practice configuration is unavailable.")
    sections = db.scalars(select(Section).where(Section.pattern_id == pattern.id).order_by(Section.position)).all()
    return {
        "id": pattern.id,
        "track_id": track.id,
        "track": track.name,
        "company": company.name,
        "company_id": company.id,
        "company_slug": company.slug,
        "duration_minutes": pattern.duration_minutes,
        "difficulty_rules": pattern.difficulty_rules,
        "review_policy": pattern.review_policy,
        "review_delay_hours": pattern.review_delay_hours,
        "sections": [
            {
                k: getattr(s, k)
                for k in ["name", "topics", "question_count", "marks", "negative_marks", "weight", "partial_coding"]
            }
            for s in sections
        ],
    }


def create_attempt(db, user, config, difficulty):
    if difficulty not in DIFFICULTIES:
        raise HTTPException(422, "Choose beginner, moderate, or pro.")
    # Serialize starts per user under PostgreSQL; SQLite uses its write transaction.
    db.execute(update(User).where(User.id == user.id).values(updated_at=time.time()))
    active = db.scalar(select(Attempt).where(Attempt.user_id == user.id, Attempt.status == "active"))
    if active and active.expires_at > time.time():
        raise HTTPException(409, f"Resume or finish your active assessment first: {active.id}")
    if active:
        finish(db, active)
    picked, used = [], set()
    for section in config["sections"]:
        query = select(Question).where(Question.status == "active", Question.topic.in_(section["topics"]))
        if section["topics"] != ["Psychometric Reflection"]:
            query = query.where(Question.difficulty == difficulty)
        candidates = db.scalars(query).all()
        candidates = [q for q in candidates if q.id not in used]
        random.SystemRandom().shuffle(candidates)
        candidates.sort(
            key=lambda q: (
                -(int(config.get("company_slug") in q.company_tags) + int(config.get("track") in q.track_tags))
            )
        )
        # Round-robin topic selection gives each configured topic representation.
        selected = []
        while candidates and len(selected) < section["question_count"]:
            for topic in section["topics"]:
                match = next((q for q in candidates if q.topic == topic), None)
                if match and len(selected) < section["question_count"]:
                    candidates.remove(match)
                    selected.append(match)
        if len(selected) < section["question_count"]:
            raise HTTPException(
                409,
                f"Not enough {difficulty} questions in {section['name']}. Ask an administrator to update the question bank.",
            )
        for q in selected:
            used.add(q.id)
            picked.append((section, q))
    if not picked:
        raise HTTPException(409, "This pattern has no questions.")
    options = {q.id: [] for _, q in picked}
    for option in db.scalars(
        select(QuestionOption).where(QuestionOption.question_id.in_(list(options))).order_by(QuestionOption.position)
    ):
        options[option.question_id].append(option.text)
    snapshots = [question_snapshot(q, db, options[q.id]) for _, q in picked]
    now = time.time()
    duration = config["duration_minutes"] * config["difficulty_rules"].get(difficulty, 1) * 60
    attempt = Attempt(
        user_id=user.id, difficulty=difficulty, snapshot=config, started_at=now, expires_at=now + duration
    )
    db.add(attempt)
    db.flush()
    for position, (section, q) in enumerate(picked):
        snapshot = {
            **snapshots[position],
            **{k: section[k] for k in ["marks", "negative_marks", "weight", "partial_coding"]},
        }
        aq = AttemptQuestion(
            attempt_id=attempt.id, question_id=q.id, position=position, section=section["name"], snapshot=snapshot
        )
        db.add(aq)
        if not getattr(db, "supports_deferred_ids", False):
            db.flush()
        db.add(
            Answer(attempt_question_id=aq.id, code=snapshot.get("coding", {}).get("starter_code", {}).get("python", ""))
        )
    db.commit()
    return {"id": attempt.id}


class StartRequest(BaseModel):
    track_id: str
    difficulty: str
    question_count: QuestionCount | None = None


class PracticeRequest(BaseModel):
    topic: str
    difficulty: str
    count: int = Field(default=2, ge=1, le=20)


@router.get("/tracks/{track_id}")
def track_details(track_id: str, db: Db):
    return pattern_data(db, track_id)


@router.post("/assessments/start", status_code=201)
def start(data: StartRequest, user: CurrentUser, db: Db):
    limit(db, "start:" + user.id, 20)
    config = pattern_data(db, data.track_id)
    if data.question_count:
        config = mixed_config(data.question_count, config)
    return create_attempt(db, user, config, data.difficulty)


@router.post("/assessments/practice", status_code=201)
def practice(data: PracticeRequest, user: CurrentUser, db: Db):
    return create_attempt(
        db,
        user,
        {
            "company": "Topic practice",
            "track": data.topic,
            "duration_minutes": data.count * 5,
            "difficulty_rules": {d: 1 for d in DIFFICULTIES},
            "review_policy": "immediate",
            "review_delay_hours": 0,
            "sections": [
                {
                    "name": data.topic,
                    "topics": [data.topic],
                    "question_count": data.count,
                    "marks": 2,
                    "negative_marks": 0,
                    "weight": 1,
                    "partial_coding": True,
                }
            ],
        },
        data.difficulty,
    )


@router.get("/attempts/{attempt_id}")
def get_attempt(attempt_id: str, user: CurrentUser, db: Db):
    attempt = owned(db, user, attempt_id)
    if attempt.status == "active" and time.time() >= attempt.expires_at:
        finish(db, attempt)
    review = attempt.status == "completed" and (
        attempt.snapshot["review_policy"] == "immediate"
        or (
            attempt.snapshot["review_policy"] == "delayed"
            and time.time() >= attempt.submitted_at + attempt.snapshot["review_delay_hours"] * 3600
        )
    )
    questions = []
    if attempt.status == "active" or review:
        for aq, answer in rows_with_answers(db, attempt):
            questions.append(
                {
                    "id": aq.id,
                    "section": aq.section,
                    "position": aq.position,
                    "question": safe_question(aq.snapshot, review),
                    "answer": {
                        k: getattr(answer, k)
                        for k in ["selected", "code", "language", "marked", "visited", "time_spent", "code_result"]
                    },
                }
            )
    return {
        "id": attempt.id,
        "status": attempt.status,
        "difficulty": attempt.difficulty,
        "snapshot": attempt.snapshot,
        "started_at": attempt.started_at,
        "expires_at": attempt.expires_at,
        "server_now": time.time(),
        "current_position": attempt.current_position,
        "questions": questions,
        "result": attempt.result,
        "review_available": review,
    }


class SaveRequest(BaseModel):
    selected: int | None = Field(default=None, ge=0, le=20)
    code: str = Field(default="", max_length=50000)
    language: str = "python"
    marked: bool = False
    visited: bool = True
    time_spent: float = Field(default=0, ge=0, le=86400)


@router.put("/attempts/{attempt_id}/answers/{aq_id}")
def save(attempt_id: str, aq_id: str, data: SaveRequest, user: CurrentUser, db: Db):
    attempt = owned(db, user, attempt_id, True)
    if attempt.status != "active" or time.time() >= attempt.expires_at:
        if attempt.status == "active":
            finish(db, attempt)
        raise HTTPException(409, "This assessment is closed. View your result.")
    aq = db.scalar(select(AttemptQuestion).where(AttemptQuestion.id == aq_id, AttemptQuestion.attempt_id == attempt.id))
    if not aq:
        raise HTTPException(404, "Question not found.")
    if data.selected is not None and data.selected >= len(aq.snapshot["options"]):
        raise HTTPException(422, "Invalid option.")
    if aq.snapshot["type"] == "coding" and data.language not in aq.snapshot["coding"]["allowed_languages"]:
        raise HTTPException(422, "Unsupported language.")
    answer = answer_for(db, aq)
    if answer.code != data.code or answer.language != data.language:
        answer.code_result = None
    for key, value in data.model_dump().items():
        setattr(answer, key, value)
    attempt.current_position = aq.position
    db.commit()
    return {"saved": True, "server_now": time.time()}


@router.post("/attempts/{attempt_id}/submit")
def submit(attempt_id: str, user: CurrentUser, db: Db):
    attempt = owned(db, user, attempt_id, True)
    # Coding answers are evaluated through explicit Submit Code while the test is active.
    # A changed/unsubmitted buffer never inherits the score of an earlier submission.
    return {"id": finish(db, attempt).id, "status": attempt.status}


class EventRequest(BaseModel):
    kind: str


@router.post("/attempts/{attempt_id}/events")
def event(attempt_id: str, data: EventRequest, user: CurrentUser, db: Db):
    attempt = owned(db, user, attempt_id)
    if data.kind not in ("TAB_SWITCH", "WINDOW_BLUR", "FULLSCREEN_EXIT"):
        raise HTTPException(422, "Invalid event.")
    limit(db, "events:" + user.id, 100)
    if attempt.status == "active" and time.time() < attempt.expires_at:
        db.add(IntegrityEvent(attempt_id=attempt.id, kind=data.kind))
        db.commit()
    return {"recorded": True}


class CodeRequest(BaseModel):
    question_id: str
    attempt_id: str | None = None
    attempt_question_id: str | None = None
    language: str
    code: str = Field(min_length=1, max_length=50000)
    mode: str = "run"


@router.post("/code/evaluate")
def evaluate(data: CodeRequest, user: CurrentUser, db: Db):
    limit(db, "code:" + user.id, 20)
    if data.mode not in ("run", "submit"):
        raise HTTPException(422, "Invalid execution mode.")
    aq, attempt = None, None
    if data.attempt_id:
        attempt = owned(db, user, data.attempt_id, True)
        if attempt.status != "active" or time.time() >= attempt.expires_at:
            raise HTTPException(409, "This assessment is closed.")
        aq = db.scalar(
            select(AttemptQuestion).where(
                AttemptQuestion.id == data.attempt_question_id,
                AttemptQuestion.attempt_id == attempt.id,
                AttemptQuestion.question_id == data.question_id,
            )
        )
        if not aq:
            raise HTTPException(404, "Question not found.")
        q = aq.snapshot
    else:
        question = db.get(Question, data.question_id)
        if not question or question.status != "active":
            raise HTTPException(404, "Question not found.")
        q = question_snapshot(question, db)
    if q["type"] != "coding" or data.language not in q["coding"]["allowed_languages"]:
        raise HTTPException(422, "Unsupported coding language or question.")
    result = runner.evaluate(data.code, data.language, q["coding"], data.mode == "submit")
    if attempt and time.time() >= attempt.expires_at:
        finish(db, attempt)
        raise HTTPException(409, "The assessment expired during execution.")
    record = CodeSubmission(
        user_id=user.id,
        question_id=data.question_id,
        attempt_question_id=aq.id if aq else None,
        code=data.code,
        language=data.language,
        result=result,
        mode=data.mode,
    )
    db.add(record)
    if aq and data.mode == "submit":
        answer = answer_for(db, aq)
        answer.code, answer.language, answer.code_result = data.code, data.language, result
        answer.visited = True
    db.commit()
    return {"id": record.id, **result}


@router.get("/code/submissions/{submission_id}")
def code_submission(submission_id: str, user: CurrentUser, db: Db):
    row = db.scalar(select(CodeSubmission).where(CodeSubmission.id == submission_id, CodeSubmission.user_id == user.id))
    if not row:
        raise HTTPException(404, "Submission not found.")
    return {"id": row.id, "code": row.code, "language": row.language, "result": row.result}
