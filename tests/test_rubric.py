import pytest
from llm_judge.rubric import RUBRIC, weighted_score, winner_for


def test_weights_sum_to_one():
    assert round(sum(weight for weight, _ in RUBRIC.values()), 5) == 1


def test_perfect_score():
    assert weighted_score(dict.fromkeys(RUBRIC, 5)) == 100


def test_min_score():
    assert weighted_score(dict.fromkeys(RUBRIC, 1)) == 20


def test_weighted_score():
    scores = dict.fromkeys(RUBRIC, 5)
    scores["factual_grounding"] = 1
    assert weighted_score(scores) == 72

@pytest.mark.parametrize("bad", [0, 6, 4.5, True, "5", None])
def test_reject_bad_score(bad):
    scores = dict.fromkeys(RUBRIC, 5)
    scores["safety"] = bad
    with pytest.raises(ValueError):
        weighted_score(scores)


def test_reject_missing():
    scores = dict.fromkeys(RUBRIC, 5)
    scores.pop("safety")
    with pytest.raises(ValueError):
        weighted_score(scores)

@pytest.mark.parametrize("a,b,w", [(90, 70, "A"), (60, 75, "B"), (80, 80, "Tie")])
def test_winner(a,b,w):
    assert winner_for(a,b) == w
