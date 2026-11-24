"""Project 5 Streamlit — compare two candidate AI answers with a rubric-based judge."""
from __future__ import annotations

import csv
import io
import json
import os
import re
from pathlib import Path

import streamlit as st

from llm_judge.gemini import DEFAULT_MODEL, JudgeServiceError, evaluate
from llm_judge.parsing import JudgeReport, to_data
from llm_judge.reference import extract_reference
from llm_judge.rubric import RUBRIC

ROOT = Path(__file__).resolve().parent
st.set_page_config(page_title="LLM-as-a-Judge", page_icon="⚖️", layout="wide")


def get_secret(name: str) -> str:
    """Read server-side secrets, never display credentials."""
    try:
        return str(st.secrets.get(name, "")).strip()
    except (FileNotFoundError, KeyError, OSError):
        return ""


def api_key() -> str:
    for name in ("GEMINI_API_KEY", "GOOGLE_API_KEY"):
        key = get_secret(name) or os.getenv(name, "").strip()
        if key and key != "replace-with-your-api-key":
            return key
    return ""


def create_csv(report: JudgeReport) -> bytes:
    output = io.StringIO()
    writer = csv.writer(output)
    writer.writerow(["candidate", "dimension", "rating_1_to_5", "weight_percent", "reason", "weighted_index"])
    for review in report.reviews:
        for dimension, (weight, _desc) in RUBRIC.items():
            writer.writerow([review.candidate, dimension, review.scores[dimension],
                             int(weight * 100), review.reasons[dimension], review.total])
    return output.getvalue().encode("utf-8")


def preview_stats(text: str, reference: str) -> dict:
    words = re.findall(r"\b[\w'-]+\b", text.lower())
    tokens = set(re.findall(r"\b[a-z]{4,}\b", text.lower()))
    ref_tokens = set(re.findall(r"\b[a-z]{4,}\b", reference.lower()))
    return {"words": len(words), "characters": len(text),
            "shared_reference_terms": len(tokens & ref_tokens)}


for key in ("question", "reference", "answer_a", "answer_b"):
    if key not in st.session_state:
        st.session_state[key] = ""
if "api_calls" not in st.session_state:
    st.session_state["api_calls"] = 0
if "report" not in st.session_state:
    st.session_state["report"] = None

st.title("⚖️ LLM-as-a-Judge")
st.caption("Compare two AI-generated answers using a transparent, weighted quality rubric.")

with st.sidebar:
    st.subheader("Evaluation settings")
    key = api_key()
    options = ["Offline preview (no scores or API)"]
    if key:
        options.append("Gemini rubric judge")
    method = st.radio("Mode", options)
    model = get_secret("GEMINI_MODEL") or os.getenv("GEMINI_MODEL", "").strip() or DEFAULT_MODEL
    if key:
        st.caption(f"Gemini model: `{model}`")
        st.caption(f"Gemini calls in this session: {st.session_state['api_calls']}/3")
    else:
        st.info("To enable Gemini, add GEMINI_API_KEY under Streamlit Cloud Secrets (or local secrets.toml).")
    st.divider()
    st.markdown("**Rubric and weights**")
    for dim, (weight, desc) in RUBRIC.items():
        st.caption(f"**{dim.replace('_', ' ').title()} · {weight:.0%}** — {desc}")
    st.divider()
    st.caption("Gemini mode sends supplied text to Google. Do not paste sensitive data. Public usage consumes your shared API quota. Session limits are not global limits.")

st.markdown("### 1. Question and trusted reference")
if st.button("Load fictional demo", type="secondary"):
    for key_name, filename in (
        ("question", "demo_question.txt"),
        ("reference", "demo_reference.txt"),
        ("answer_a", "demo_answer_a.txt"),
        ("answer_b", "demo_answer_b.txt"),
    ):
        st.session_state[key_name] = (ROOT / "data" / filename).read_text(encoding="utf-8")
    st.session_state["report"] = None
    st.rerun()

st.text_area("Evaluation question", key="question", height=90,
             placeholder="What did the user ask the AI models?")
st.text_area("Trusted reference / correct answer / grading criteria", key="reference", height=155,
             placeholder="Provide authoritative facts or an answer key to score factual grounding.")
reference_upload = st.file_uploader("Optional reference upload (TXT, MD, text-based PDF, max 2 MB)",
                                    type=["txt", "md", "pdf"])

st.markdown("### 2. AI-generated answers to compare")
left, right = st.columns(2)
with left:
    st.text_area("Candidate A", key="answer_a", height=195)
with right:
    st.text_area("Candidate B", key="answer_b", height=195)

running_gemini = method == "Gemini rubric judge"
exhausted = running_gemini and st.session_state["api_calls"] >= 3
if exhausted:
    st.warning("This browser session reached three Gemini evaluations. Offline preview remains available.")
button_label = "Evaluate both with Gemini" if running_gemini else "Preview candidates offline"
if st.button(button_label, type="primary", disabled=exhausted):
    st.session_state["report"] = None
    question = st.session_state["question"].strip()[:3000]
    reference = st.session_state["reference"].strip()[:25000]
    a = st.session_state["answer_a"].strip()[:10000]
    b = st.session_state["answer_b"].strip()[:10000]
    if reference_upload is not None:
        try:
            file_text = extract_reference(reference_upload.name, reference_upload.getvalue())
            reference = (reference + "\n\n" + file_text).strip()[:25000]
        except ValueError as exc:
            st.error(str(exc))
            st.stop()
    if not all((question, reference, a, b)):
        st.error("Enter a question, trusted reference, and both candidate answers (or load the demo).")
    elif not running_gemini:
        st.session_state["preview"] = (preview_stats(a, reference), preview_stats(b, reference))
        st.info("Offline preview reports text statistics only. It does not judge factual quality.")
    else:
        st.session_state.pop("preview", None)
        st.session_state["api_calls"] += 1
        with st.spinner("Gemini is evaluating both answers against the rubric..."):
            try:
                st.session_state["report"] = evaluate(question, reference, a, b, key, model)
                st.session_state["report_question"] = question
                st.session_state["report_model"] = model
            except JudgeServiceError as exc:
                st.error(str(exc))

if method == "Offline preview (no scores or API)" and "preview" in st.session_state:
    st.divider()
    st.markdown("### 3. Offline text preview — not a quality score")
    a_stats, b_stats = st.session_state["preview"]
    st.table([{"Metric": "Word count", "A": a_stats["words"], "B": b_stats["words"]},
              {"Metric": "Characters", "A": a_stats["characters"], "B": b_stats["characters"]},
              {"Metric": "Unique terms also in reference (not proof of correctness)",
               "A": a_stats["shared_reference_terms"], "B": b_stats["shared_reference_terms"]}])
    st.caption("Longer or similar-looking answers are not necessarily better. Enable Gemini for rubric judgments.")

report = st.session_state["report"]
if report is not None and running_gemini:
    st.divider()
    st.markdown("### 3. Gemini evaluation results")
    a_review, b_review = report.reviews
    c1, c2, c3 = st.columns(3)
    c1.metric("Candidate A · weighted index", f"{a_review.total:.1f} / 100")
    c2.metric("Candidate B · weighted index", f"{b_review.total:.1f} / 100")
    c3.metric("Higher-scoring candidate", report.winner)
    st.caption("Subjective Gemini quality ratings, not verified factual accuracy. Python computes weighted scores and winner from the five ratings.")
    rows = []
    for dim, (weight, _desc) in RUBRIC.items():
        rows.append({"Dimension": dim.replace("_", " ").title(), "Weight": f"{weight:.0%}",
                     "Candidate A": a_review.scores[dim], "Candidate B": b_review.scores[dim]})
    st.table(rows)
    for review in report.reviews:
        with st.expander(f"Candidate {review.candidate} — reasoning and recommendations", expanded=True):
            for dim in RUBRIC:
                st.markdown(f"**{dim.replace('_',' ').title()} ({review.scores[dim]}/5)** — {review.reasons[dim]}")
            st.markdown("**Strengths:** " + "; ".join(review.strengths))
            st.markdown("**Improvements:** " + "; ".join(review.improvements))

    payload = to_data(report, st.session_state.get("report_question", ""), st.session_state.get("report_model", DEFAULT_MODEL))
    d1, d2 = st.columns(2)
    with d1:
        st.download_button("Download JSON report", json.dumps(payload, indent=2).encode("utf-8"),
                           "llm_judge_report.json", mime="application/json")
    with d2:
        st.download_button("Download CSV report", create_csv(report),
                           "llm_judge_report.csv", mime="text/csv")
    st.info("The judge is another LLM. Human review is recommended for important decisions.")

st.divider()
st.caption("Portfolio Project 5 · Python · Streamlit · Gemini API · Pytest · GitHub Actions")
