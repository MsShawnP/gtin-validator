## Design System

Read `../lailara-design-system/LAILARA_DESIGN_SYSTEM.md` before any visual work — colors, typography, layout, components, charts, voice, interactions. It is the single source of truth.

---
# GTIN Product Data Validator

FastAPI + React web app that validates GTINs against GS1 standards with retailer-specific context. Built for specialty food brands preparing product data for retailer submission.

## Stack

- **Backend:** Python 3.10+ / FastAPI / pandas / reportlab
- **Frontend:** React 19 / Vite / TypeScript (strict)
- **Hosting:** Render free tier (Docker, auto-deploys from main)
- **Tests:** pytest (`pytest tests.py -v` for core, `pytest tests_api.py -v` for API)
- **No database, no auth** — in-memory cache with TTL for session state

## Key Files

| File | Role |
|------|------|
| `gtin_core.py` | Validation engine, scoring, retailer rules, cost estimation |
| `backend/main.py` | FastAPI app, CORS, static file mount |
| `backend/routes/` | API endpoints (validate, reports, sample, health) |
| `backend/schemas/` | Pydantic request/response models |
| `backend/serializers.py` | Dataclass-to-Pydantic conversion |
| `backend/cache.py` | In-memory result cache (TTL 30 min, max 100) |
| `pdf_report.py` | Branded PDF report (reportlab) |
| `csv_report.py` | CSV export |
| `sample_data.py` | Realistic demo dataset with intentional errors |
| `tests.py` | Core engine tests (50+) |
| `tests_api.py` | API endpoint tests (20) |
| `frontend/src/` | React SPA (components, api, types, reducer) |
| `docs/solutions/` | Documented solutions to past problems, organized by category with YAML frontmatter |

## Conventions

- Core logic in `gtin_core.py` — no UI or web framework imports allowed there
- Report generators import from `gtin_core` only
- Issue severities: CRITICAL (blocks submission), WARNING (will cause problems), INFO (advisory)
- Retailer profiles are declarative dicts in `RETAILER_PROFILES`
- CSS Modules with custom property tokens in `frontend/src/styles/`
- Backend is a thin HTTP layer — no business logic in routes

## Running

```bash
# Backend (dev)
uvicorn backend.main:app --reload        # API on :8000

# Frontend (dev)
cd frontend && npm run dev               # Vite on :5173, proxies /api to :8000

# Tests
pytest tests.py -v                       # core engine
pytest tests_api.py -v                   # API endpoints
cd frontend && npm run build             # frontend type-check + build

# Docker (production)
docker build -t gtin . && docker run -p 8000:8000 gtin
```

## API Endpoints

| Method | Path | Purpose |
|--------|------|---------|
| POST | `/api/validate` | Validate pasted GTINs |
| POST | `/api/validate/upload` | Validate from file upload |
| GET | `/api/reports/csv/{token}` | Download CSV report |
| GET | `/api/reports/corrected/{token}` | Download corrected GTINs |
| GET | `/api/reports/pdf/{token}` | Download PDF report |
| POST | `/api/completeness/{token}` | Data completeness analysis |
| GET | `/api/sample` | Sample data + description |
| GET | `/api/retailers` | Retailer profiles list |
| GET | `/api/health` | Health check |
