from sqlalchemy import select

from .models import CodingProblem, CodingTestCase, QuestionOption


def question_snapshot(q, db, options=None):
    data = {
        key: getattr(q, key)
        for key in [
            "id",
            "slug",
            "type",
            "title",
            "question",
            "correct_answer",
            "explanation",
            "difficulty",
            "topic",
            "subtopic",
            "tags",
        ]
    }
    data["options"] = (
        options
        if options is not None
        else [
            o.text
            for o in db.scalars(
                select(QuestionOption).where(QuestionOption.question_id == q.id).order_by(QuestionOption.position)
            )
        ]
    )
    if q.type == "coding":
        problem = db.scalar(select(CodingProblem).where(CodingProblem.question_id == q.id))
        data["coding"] = {
            key: getattr(problem, key)
            for key in [
                "input_format",
                "output_format",
                "constraints",
                "starter_code",
                "allowed_languages",
                "time_limit",
                "memory_limit",
            ]
        }
        data["coding"]["tests"] = [
            {"input": t.input, "output": t.output, "hidden": t.hidden}
            for t in db.scalars(
                select(CodingTestCase).where(CodingTestCase.problem_id == problem.id).order_by(CodingTestCase.id)
            )
        ]
    return data


def safe_question(snapshot, review=False):
    data = {k: v for k, v in snapshot.items() if k not in ("correct_answer", "explanation") or review}
    if "coding" in data:
        data["coding"] = {**data["coding"], "tests": [t for t in data["coding"]["tests"] if not t["hidden"]]}
    return data
