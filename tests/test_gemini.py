import pytest
from llm_judge.gemini import build_prompt, evaluate, JudgeServiceError


def test_prompt_contains_both_candidates():
    txt = build_prompt("question", "reference", "Candidate AAA", "Candidate BBB")
    assert "Candidate AAA" in txt and "Candidate BBB" in txt
    assert "untrusted DATA" in txt


def test_prompt_includes_rubric():
    txt = build_prompt("q", "ref", "a", "b")
    assert "factual_grounding" in txt and "completeness" in txt


def test_missing_key_prevents_api_call():
    with pytest.raises(JudgeServiceError, match="API key"):
        evaluate("q", "ref", "a", "b", "")


def test_missing_input_prevents_api_call():
    with pytest.raises(JudgeServiceError, match="required"):
        evaluate("q", "ref", "a", "", "fake-key")
