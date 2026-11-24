"""Safely validate structured Gemini responses before showing any ratings."""
from __future__ import annotations

import json
from dataclasses import dataclass
from .rubric import DIMENSIONS, weighted_score, winner_for


class InvalidJudgeResponse(ValueError):
    pass


@dataclass(frozen=True)
class CandidateReview:
    candidate: str
    scores: dict[str, int]
    reasons: dict[str, str]
    strengths: tuple[str, ...]
    improvements: tuple[str, ...]
    total: float


@dataclass(frozen=True)
class JudgeReport:
    reviews: tuple[CandidateReview, CandidateReview]
    winner: str


def _text_list(value: object, field: str) -> tuple[str, ...]:
    if not isinstance(value, list) or not 1 <= len(value) <= 3:
        raise InvalidJudgeResponse(f"Missing or invalid {field} list.")
    if not all(isinstance(x, str) and x.strip() and len(x) <= 400 for x in value):
        raise InvalidJudgeResponse(f"Invalid {field} items.")
    return tuple(x.strip() for x in value)


def parse_judge_response(raw: str) -> JudgeReport:
    try:
        payload = json.loads(raw)
    except (ValueError, TypeError) as exc:
        raise InvalidJudgeResponse("Gemini did not return valid JSON.") from exc
    if not isinstance(payload, dict) or not isinstance(payload.get("evaluations"), list):
        raise InvalidJudgeResponse("Gemini response has no evaluations list.")
    evaluations = payload["evaluations"]
    if len(evaluations) != 2 or any(not isinstance(e, dict) for e in evaluations):
        raise InvalidJudgeResponse("Exactly two candidate evaluations are required.")
    by_candidate = {}
    for entry in evaluations:
        label = entry.get("candidate")
        if label not in ("A", "B") or label in by_candidate:
            raise InvalidJudgeResponse("Candidate IDs must be A and B exactly once.")
        scores = entry.get("scores")
        reasons = entry.get("reasons")
        if not isinstance(scores, dict) or not isinstance(reasons, dict):
            raise InvalidJudgeResponse("Missing scores or explanations.")
        if set(reasons) != set(DIMENSIONS):
            raise InvalidJudgeResponse("Every dimension needs a reason.")
        for reason in reasons.values():
            if not isinstance(reason, str) or not reason.strip() or len(reason) > 450:
                raise InvalidJudgeResponse("Empty or excessive dimension reason.")
        try:
            total = weighted_score(scores)
        except ValueError as exc:
            raise InvalidJudgeResponse(str(exc)) from exc
        by_candidate[label] = CandidateReview(
            candidate=label,
            scores=dict(scores),
            reasons={key: reasons[key].strip() for key in DIMENSIONS},
            strengths=_text_list(entry.get("strengths"), "strengths"),
            improvements=_text_list(entry.get("improvements"), "improvements"),
            total=total,
        )
    reviews = (by_candidate["A"], by_candidate["B"])
    return JudgeReport(reviews=reviews, winner=winner_for(reviews[0].total, reviews[1].total))


def to_data(report: JudgeReport, question: str, model: str) -> dict:
    return {
        "question": question,
        "judge_model": model,
        "winner": report.winner,
        "scoring_note": "Subjective Gemini ratings, not verified factual accuracy or calibrated confidence.",
        "candidates": [
            {
                "candidate": review.candidate,
                "weighted_index": review.total,
                "scores": review.scores,
                "reasons": review.reasons,
                "strengths": list(review.strengths),
                "improvements": list(review.improvements),
            }
            for review in report.reviews
        ],
    }
