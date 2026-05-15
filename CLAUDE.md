# GTIN Product Data Validator

Streamlit web app that validates GTINs against GS1 standards with retailer-specific context. Built for specialty food brands preparing product data for retailer submission.

## Stack

- **Python 3.10+** / Streamlit / pandas / reportlab
- **Hosting:** Streamlit Community Cloud (auto-deploys from main)
- **Tests:** pytest (`python -m pytest tests.py -v`)
- **No backend, no database, no auth** — all processing is in-session

## Key Files

| File | Role |
|------|------|
| `gtin_core.py` | Validation engine, scoring, retailer rules, cost estimation |
| `app.py` | Streamlit UI |
| `pdf_report.py` | Branded PDF report (reportlab) |
| `csv_report.py` | CSV export |
| `sample_data.py` | Realistic demo dataset with intentional errors |
| `tests.py` | pytest suite (50+ tests) |
| `styles/app.css` | Custom component CSS |
| `.streamlit/config.toml` | Theme and server config |

## Conventions

- Core logic in `gtin_core.py` — no UI imports allowed there
- Report generators import from `gtin_core` only
- Issue severities: CRITICAL (blocks submission), WARNING (will cause problems), INFO (advisory)
- Custom CSS in `styles/app.css` — Streamlit HTML components use `unsafe_allow_html=True`
- Retailer profiles are declarative dicts in `RETAILER_PROFILES`

## Running

```bash
streamlit run app.py          # dev server on :8501
python -m pytest tests.py -v  # run tests
```

## Current Focus

Project improvement plan in PLAN.md — audit-driven improvements across code quality, testing, DevEx, and UX.
