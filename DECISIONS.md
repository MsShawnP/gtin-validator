# Decisions Log

## 2026-05-15: Migrate from Streamlit to FastAPI + React

**Decision:** Replace the Streamlit UI entirely with a React 19 + TypeScript SPA backed by a FastAPI API. Core validation engine (`gtin_core.py`) stays unchanged.

**Why:** Streamlit's rerun model causes full-page reloads on every interaction, slow initial load, and clunky UX. For a portfolio piece targeting operations teams, the UI needs to feel professional and responsive.

**Alternatives considered:**
- **Gradio** — same rerun model problem as Streamlit
- **Keep Streamlit, optimize** — fundamental architecture limitation, not a tuning problem
- **Incremental migration** — rejected in favor of clean replacement since the core engine is decoupled

**Key sub-decisions:**
- **No component library** (MUI, Chakra) — the existing design is distinctive, a library would fight it and add 200KB+ bundle weight. CSS Modules with custom property tokens instead.
- **No router** — single-page tool with phase-based rendering (idle → loading → results), not a multi-page app.
- **useReducer over Redux/Zustand** — 8 state variables, linear workflow, no global store needed.
- **Scroll-spy sidebar over tabs** — 10 analysis sections are too many for tabs. IntersectionObserver highlights active section as user scrolls.
- **Single deploy** — FastAPI serves both API and SPA static files from one Docker container on Render free tier.
- **In-memory cache** — dict with 30-min TTL for validation results, keyed by UUID token. Report downloads use the token to avoid re-validation.

## 2026-05-15: Consolidate PDF rendering functions

**Decision:** Merge `render_group_with_continuation` and `render_multi_issue_group` into a single `render_item_group` function with optional `recommendation_text` parameter.

**Why:** ~80 lines of near-identical pagination logic. One function handles both cases with a conditional header height.

## 2026-05-16: Never expose raw exceptions in API error responses

**Decision:** Backend error handlers must return user-friendly messages to the client. Raw Python exceptions (`str(exc)`, `f"...{exc}"`) must not appear in HTTPException detail strings.

**Why:** A prospect uploading a malformed file saw Python stack traces in the UI error banner, undermining credibility. Friendly messages for the client; full details logged server-side.

**Scope:** All backend error handlers in `backend/routes/`.

**Do not:** Use `f"...{exc}"` or `str(exc)` in HTTPException detail messages. Log the real exception with `logger.error()` or let it propagate to FastAPI's default 500 handler.
