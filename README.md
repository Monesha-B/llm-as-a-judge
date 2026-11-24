# LLM-as-a-Judge — Portfolio Project 5

Compare **two AI-generated answers** against the same question and trusted reference using a consistent, transparent scoring rubric. The **Gemini judge** supplies qualitative ratings and explanations; Python validates the returned data and calculates weighted scores and the winner. This is an **LLM evaluation application**, not a newly trained ML model.

## Features

- Side-by-side Candidate A vs B evaluation across **five dimensions**: factual grounding, relevance, completeness, clarity, and safety.
- Reference text can be pasted or uploaded as TXT, Markdown, or text-based PDF (2 MB/file, 20 pages/PDF).
- One-click **fictional demo** includes a question, trusted policy, and two competing responses.
- Free **offline preview** shows text statistics only, *not* AI evaluation or made-up scores.
- Optional Gemini 3.5 Flash-Lite makes **one batched API request** to judge both responses in JSON.
- Python validates five ratings per candidate, checks reason fields, and computes weighted totals and a winner.
- Export CSV or JSON reports. Automated tests in GitHub Actions on pushes / PRs.
- Server-side Gemini secrets; no keys displayed. Public visitors share your quota if the API is enabled.

## Mac Quick Start

```bash
cd ~/Downloads/llm-as-a-judge
conda create -n llm-judge python=3.11 -y
conda activate llm-judge
python -m pip install -r requirements-dev.txt
python -m pytest -q
python -m streamlit run app.py
```

## Gemini API (optional)

For local use, create `.streamlit/secrets.toml` (ignored by Git):

```toml
GEMINI_API_KEY = "YOUR_EXISTING_GEMINI_KEY"
```

`GOOGLE_API_KEY` is also accepted for compatibility with other projects. Keep `GEMINI_API_KEY` as the preferred name. The default model is `gemini-3.5-flash-lite`, configurable with `GEMINI_MODEL`. Your account must have access to the model.

## Deployment — Streamlit Community Cloud

1. Create a **public** GitHub repo named `llm-as-a-judge` and push this folder (`main`). No need to initialize with another README.
2. In https://share.streamlit.io/ create a public app from GitHub. Choose `main`, `app.py`, Python `3.11`.
3. Under **Advanced settings → Secrets**, optionally add `GEMINI_API_KEY = "..."` and save; reboot if already deployed.
4. Confirm offline demo and Gemini mode (if enabled), then add the deployment link to GitHub's About section.

**Privacy and expense:** Gemini calls send the question, reference text, and candidate answers to Google. Do not submit sensitive data. Session call limits are **not** global abuse prevention; for a public demo, use offline-only mode unless comfortable with visitors consuming the shared API quota. Disable billing if zero spend is required.

## Scoring rubric

| Dimension | Weight | What it measures |
|---|---:|---|
| Factual grounding | 35% | Agreement with the supplied trusted reference |
| Relevance | 25% | Directly addresses the question |
| Completeness | 20% | Covers essential parts of the question |
| Clarity | 15% | Understandable, organized answer |
| Safety | 5% | No dangerous or inappropriate advice |

Each dimension is rated 1–5 by Gemini. Python computes `sum((rating/5) * weight * 100)` and selects the higher score (or a tie). **These are subjective model judgments, not objectively measured quality or calibrated probabilities.** Reference material is required for Gemini evaluation.

## File structure

```text
app.py                   Streamlit dashboard and export
llm_judge/rubric.py      Fixed rubric and weighted score calculation
llm_judge/parsing.py     Strict result validation and winner
llm_judge/gemini.py      Optional Gemini service call
llm_judge/reference.py   Reference-file extraction and limits
data/                    Fictional example question, reference, A and B
.github/workflows/ci.yml GitHub Actions (pytest, compilation)
tests/                   Offline unit tests, no API keys required
```

## Limitations and future enhancements

- Judge models can be wrong, biased by response order or writing style, and inconsistent on repeat runs.
- Numeric ratings and winner are **judgments**, not verified facts. They should not be presented as objective accuracy.
- A supplied reference can itself be wrong or incomplete. No external fact checking is performed.
- Offline preview is deliberately **not** called an LLM judge and does not assign quality scores.
- Future improvements: blind/reversed-order judging, multiple judges, calibration with human ratings, benchmark datasets, and global API quotas/authentication.
