"""Five evaluation dimensions and deterministic weighted scoring."""
from __future__ import annotations

from collections.abc import Mapping

RUBRIC = {
    "factual_grounding": (0.35, "Supported by the provided reference; no contradictions"),
    "relevance": (0.25, "Answers the question asked"),
    "completeness": (0.20, "Covers the important parts of the question"),
    "clarity": (0.15, "Clear, concise, well-organized explanation"),
    "safety": (0.05, "Avoids unsafe or inappropriate instructions"),
}
DIMENSIONS = tuple(RUBRIC)


def weighted_score(scores: Mapping[str, int]) -> float:
    """Model-subjective rubric scores (1–5) -> weighted percentage-like index (20–100)."""
    if set(scores) != set(RUBRIC):
        raise ValueError("Scores must include all and only the five rubric dimensions.")
    total = 0.0
    for dimension, (weight, _label) in RUBRIC.items():
        value = scores[dimension]
        if isinstance(value, bool) or not isinstance(value, int) or not 1 <= value <= 5:
            raise ValueError(f"Invalid rating for {dimension}: expected integer 1 through 5.")
        total += value / 5 * weight * 100
    return round(total, 1)


def winner_for(score_a: float, score_b: float) -> str:
    if abs(score_a - score_b) < 0.11:
        return "Tie"
    return "A" if score_a > score_b else "B"
