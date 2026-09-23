from typing import Literal

from fastapi import APIRouter
from pydantic import BaseModel

from .auth import CurrentUser, Db, limit
from .mixed_bank import TOPICS

router = APIRouter(prefix="/api", tags=["Mixed preparation"])
QuestionCount = Literal[25, 50, 75]


def mixed_config(count, base=None):
    base = base or {"company": "Mixed preparation", "track": "Placement foundations"}
    return {
        **base,
        "mode": "mixed",
        "question_count": count,
        "duration_minutes": count * 2,
        "difficulty_rules": {"beginner": 1.2, "moderate": 1, "pro": 0.8},
        "review_policy": "immediate",
        "review_delay_hours": 0,
        "sections": [
            {
                "name": topic,
                "topics": [topic],
                "question_count": count // 5,
                "marks": 0 if topic == TOPICS[4] else 2,
                "negative_marks": 0,
                "weight": 1,
                "partial_coding": False,
            }
            for topic in TOPICS
        ],
    }


class MixedRequest(BaseModel):
    count: QuestionCount = 25
    difficulty: Literal["beginner", "moderate", "pro"] = "moderate"


@router.get("/assessments/mixed-pattern")
def preview(count: QuestionCount = 25):
    return mixed_config(count)


@router.post("/assessments/mixed", status_code=201)
def start(data: MixedRequest, user: CurrentUser, db: Db):
    from .assessment import create_attempt

    limit(db, "start:" + user.id, 20)
    return create_attempt(db, user, mixed_config(data.count), data.difficulty)


GUIDES = [
    {
        "topic": TOPICS[0],
        "name": "Quants",
        "description": "Translate the problem into quantities, choose a model, and check the units.",
        "lessons": [
            {
                "title": "Percentages and change",
                "rule": "Percentage change = (new − old) / old × 100. Successive changes multiply; they do not simply add.",
                "example": "A value of 200 rises 20%, then falls 10%: 200 × 1.2 × 0.9 = 216, an 8% net rise.",
            },
            {
                "title": "Ratios and averages",
                "rule": "Split a total into a+b parts for a:b. Use total quantity divided by total count for a weighted average.",
                "example": "Two groups of 10 and 20 learners average 50 and 80. Their combined mean is (500+1600)/30 = 70.",
            },
            {
                "title": "Work and speed",
                "rule": "Add work rates, not completion times. Average speed is total distance / total time.",
                "example": "Machines taking 6 and 12 hours have a combined rate of 1/6+1/12=1/4 job/hour: four hours together.",
            },
            {
                "title": "Probability and counting",
                "rule": "Without replacement, update the sample space after each draw. Use combinations when order does not matter.",
                "example": "Selecting two people from five gives 5×4/2 = 10 pairs.",
            },
            {
                "title": "Number systems and algebra",
                "rule": "Use LCM for shared repeating schedules. Write simultaneous equations before substituting.",
                "example": "Signals every 12 and 18 seconds next coincide after LCM(12,18)=36 seconds.",
            },
        ],
    },
    {
        "topic": TOPICS[1],
        "name": "Logical reasoning",
        "description": "Work from the stated constraints. Separate what must be true from what merely could be true.",
        "lessons": [
            {
                "title": "Sequences",
                "rule": "Check differences, ratios and alternating operations before guessing a pattern.",
                "example": "2, 5, 10, 17 has differences 3,5,7. Continuing the odd differences gives 26.",
            },
            {
                "title": "Syllogisms and conditions",
                "rule": "A implies B does not mean B implies A. Contraposition does hold: not B implies not A.",
                "example": "If all approved requests are signed, an unsigned request cannot be approved.",
            },
            {
                "title": "Arrangements and dependencies",
                "rule": "Represent before/after rules with arrows. Choose a sequence that respects every arrow.",
                "example": "A before C and B before C permit A,B,C or B,A,C, but not A,C,B.",
            },
            {
                "title": "Directions and ranks",
                "rule": "Track horizontal and vertical displacement separately. Queue length = front rank + back rank − 1.",
                "example": "Six metres east then two west leaves a net four metres east.",
            },
            {
                "title": "Counting guarantees",
                "rule": "For n groups, n×k+1 objects guarantee a group with at least k+1 objects.",
                "example": "With four colours, nine tokens guarantee at least three of a colour.",
            },
        ],
    },
    {
        "topic": TOPICS[2],
        "name": "Verbal ability",
        "description": "Read precisely, write clearly, and distinguish a claim from the evidence supporting it.",
        "lessons": [
            {
                "title": "Grammar essentials",
                "rule": "Match the verb to the head of the subject. Keep list items grammatically parallel.",
                "example": "The collection of reports is ready. The singular subject is collection.",
            },
            {
                "title": "Vocabulary in context",
                "rule": "Use the surrounding sentence to test a word's meaning rather than selecting the most familiar synonym.",
                "example": "A tentative conclusion is provisional, not necessarily wrong.",
            },
            {
                "title": "Reading comprehension",
                "rule": "Separate explicit statements, justified inferences and unsupported assumptions.",
                "example": "Sales rose after a campaign describes sequence; it does not alone prove the campaign caused the rise.",
            },
            {
                "title": "Critical reasoning",
                "rule": "Look for alternative explanations, selection bias and overgeneralization.",
                "example": "Volunteers may differ from nonvolunteers before a training intervention starts.",
            },
            {
                "title": "Clear expression",
                "rule": "Remove redundant phrases and make pronoun references unambiguous.",
                "example": "Replace collaborated together with collaborated.",
            },
        ],
    },
    {
        "topic": TOPICS[3],
        "name": "Data interpretation",
        "description": "Read the title, units, scale and denominator before calculating.",
        "lessons": [
            {
                "title": "Tables and totals",
                "rule": "Check whether rows are counts, rates or percentages before adding them.",
                "example": "Counts of 12, 18 and 20 sum to 50. Percentages with different denominators cannot be combined that way.",
            },
            {
                "title": "Growth and percentage points",
                "rule": "A move from 20% to 30% is 10 percentage points, but a 50% relative increase.",
                "example": "Relative growth uses the old value as the denominator: (30−20)/20.",
            },
            {
                "title": "Weighted statistics",
                "rule": "Compute totals before deriving an overall rate. Group sizes matter.",
                "example": "One defect among 10 units and nine among 90 units gives 10 defects among 100 units, or 10%.",
            },
            {
                "title": "Charts and units",
                "rule": "A pie-chart share p occupies p/100 × 360°. Normalize units before comparing bars.",
                "example": "A 25% share occupies 90°. Two GB and 500 MB total 2.5 GB when 1 GB = 1000 MB.",
            },
            {
                "title": "Median and range",
                "rule": "Sort data to find the middle. Range is maximum minus minimum.",
                "example": "For 3,7,4,9,6, the sorted list is 3,4,6,7,9: median 6 and range 6.",
            },
        ],
    },
    {
        "topic": TOPICS[4],
        "name": "Psychometric reflection",
        "description": "Explore everyday work preferences and habits. There is no ideal personality or correct response.",
        "lessons": [
            {
                "title": "Answer honestly",
                "rule": "Choose responses that describe your usual behaviour, rather than what you think an employer wants.",
                "example": "Think of a recent teamwork situation before responding to a collaboration statement.",
            },
            {
                "title": "Consider context",
                "rule": "Preferences can vary with role, workload and experience. A single response is not a diagnosis or fixed trait.",
                "example": "You may prefer independent work for analysis and group discussion for planning.",
            },
            {
                "title": "Use reflection constructively",
                "rule": "Choose one practical habit to experiment with. These items do not predict hiring success.",
                "example": "If you rarely clarify requirements, try writing three questions before your next task.",
            },
        ],
    },
]


@router.get("/learning")
def learning():
    return {
        "guides": GUIDES,
        "question_counts": [25, 50, 75],
        "notice": "All lessons and questions are independently authored. Reflection items are unscored and are not a validated psychological assessment.",
    }
