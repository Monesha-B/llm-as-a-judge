import json
import pytest
from llm_judge.parsing import InvalidJudgeResponse, parse_judge_response, to_data
from llm_judge.rubric import RUBRIC


def response():
    return {"evaluations": [
        {"candidate": letter, "scores": dict.fromkeys(RUBRIC, score),
         "reasons": dict.fromkeys(RUBRIC, "Evidence-based explanation"),
         "strengths": ["A clear strength"], "improvements": ["One recommendation"]}
        for letter, score in (("A", 5), ("B", 2))
    ]}


def test_good_response():
    report = parse_judge_response(json.dumps(response()))
    assert report.winner == "A"
    assert report.reviews[0].total == 100
    assert report.reviews[1].total == 40


def test_reversed_order():
    payload = response()
    payload["evaluations"].reverse()
    report = parse_judge_response(json.dumps(payload))
    assert [r.candidate for r in report.reviews] == ["A", "B"]


def test_export():
    report = parse_judge_response(json.dumps(response()))
    data = to_data(report, "What is the policy?", "test")
    assert data["winner"] == "A"
    assert len(data["candidates"]) == 2

@pytest.mark.parametrize("edit", [
    lambda p: p.update(evaluations=[]),
    lambda p: p["evaluations"][0].update(candidate="C"),
    lambda p: p["evaluations"][1].update(candidate="A"),
    lambda p: p["evaluations"][0]["scores"].update(clarity=6),
    lambda p: p["evaluations"][0]["scores"].pop("safety"),
    lambda p: p["evaluations"][0]["reasons"].update(clarity=""),
    lambda p: p["evaluations"][0].update(strengths=[]),
    lambda p: p["evaluations"][0].update(improvements=[42]),
])
def test_invalid_response(edit):
    payload = response()
    edit(payload)
    with pytest.raises(InvalidJudgeResponse):
        parse_judge_response(json.dumps(payload))


def test_invalid_json():
    with pytest.raises(InvalidJudgeResponse):
        parse_judge_response("not json")


def test_no_payload():
    with pytest.raises(InvalidJudgeResponse):
        parse_judge_response("{}")
