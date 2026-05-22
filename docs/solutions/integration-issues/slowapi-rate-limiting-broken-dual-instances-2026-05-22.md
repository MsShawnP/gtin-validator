---
title: "SlowAPI rate limiting non-functional due to duplicate Limiter instances and missing middleware"
date: 2026-05-22
category: integration-issues
module: backend
problem_type: integration_issue
component: tooling
symptoms:
  - "Rate limit decorators present but never enforced — no 429 responses returned"
  - "Two separate Limiter instances in different modules with no shared state"
  - "SlowAPIMiddleware never registered on the FastAPI app"
  - "Empty strings from fillna inflated CRITICAL validation error counts on file uploads"
root_cause: config_error
resolution_type: code_fix
severity: high
tags:
  - fastapi
  - slowapi
  - rate-limiting
  - middleware
  - singleton-pattern
  - render
---

# SlowAPI rate limiting non-functional due to duplicate Limiter instances and missing middleware

## Problem

slowapi rate limiting in a FastAPI application was completely non-functional despite decorators, exception handlers, and `app.state.limiter` all being present. Two independent `Limiter` instances existed in separate modules, and `SlowAPIMiddleware` was never added to the app, so no request was ever rate-limited. On Render free tier with CPU-intensive validation endpoints, this left the app unprotected against abuse.

## Symptoms

- No rate limiting enforced: endpoints decorated with `@limiter.limit("10/minute")` accepted unlimited requests
- Silent failure: no errors, warnings, or log output indicating rate limiting was inactive
- Inflated CRITICAL errors on file uploads from empty strings preserved by `fillna("")`
- 429 responses undocumented in OpenAPI schema

## What Didn't Work

The initial improvement pass added rate limiting that looked correct on the surface. All the right pieces were present individually:

- `app.state.limiter = Limiter(key_func=get_remote_address)` in `main.py`
- `@limiter.limit("10/minute")` decorators on endpoints in `validate.py`
- `app.add_exception_handler(RateLimitExceeded, ...)` registered

But the pieces were never connected. `validate.py` created its own `Limiter` instance locally, so decorators referenced an orphan with no relationship to the app. `SlowAPIMiddleware` was never added, so even the registered limiter had no enforcement hook. No integration test exercised rate limiting, so the broken wiring was never caught.

## Solution

Created `backend/limiter.py` as a single shared module:

```python
from slowapi import Limiter
from slowapi.util import get_remote_address

limiter = Limiter(key_func=get_remote_address)
```

Updated `backend/main.py` to import the shared instance and add the middleware:

```python
from slowapi.middleware import SlowAPIMiddleware
from backend.limiter import limiter

app.state.limiter = limiter
app.add_middleware(SlowAPIMiddleware)

@app.exception_handler(RateLimitExceeded)
async def _rate_limit_handler(request: Request, exc: RateLimitExceeded) -> Response:
    return Response(
        content='{"detail":"Too many requests. Please try again shortly."}',
        status_code=429,
        media_type="application/json",
    )
```

Updated `backend/routes/validate.py` to import the shared instance and document 429:

```python
from backend.limiter import limiter

@router.post("/validate", responses={429: {"description": "Rate limit exceeded"}})
@limiter.limit("10/minute")
def validate_text(request: Request, body: ValidateTextRequest) -> dict:
    ...
```

Filtered empty strings after fillna:

```python
gtins = [g for g in df[col].fillna("").astype(str).tolist() if g.strip()]
```

Fixed type annotations in `backend/cache.py`:

```python
def store_result(
    batch_result: BatchResult, dataframe: pd.DataFrame | None = None
) -> str:
```

## Why This Works

slowapi requires a specific three-part wiring:

1. **Single Limiter instance** — decorators and the app must reference the same object. A second instance in `validate.py` meant decorators talked to a Limiter that knew nothing about the app.
2. **`app.state.limiter`** — slowapi's middleware looks up the Limiter from `app.state.limiter` at runtime.
3. **`SlowAPIMiddleware`** — the enforcement mechanism that wraps every request, checks limits, and raises `RateLimitExceeded`. Without it, the Limiter is inert.

The shared module pattern (`backend/limiter.py`) ensures both `main.py` and `validate.py` reference the same object.

## Prevention

- **Integration test for rate limiting.** Send N+1 requests and assert the last returns 429. This is the only way to verify rate limiting works end-to-end.
- **Single-instance pattern for shared infrastructure.** Any cross-cutting concern (rate limiter, metrics, logger config) should live in its own module. Never instantiate infrastructure objects locally in route files. Grep for duplicate instantiation: `grep -rn "Limiter(" backend/` should return exactly one hit.
- **Middleware registration checklist.** When adding any middleware-dependent feature, verify the middleware is registered via `app.add_middleware()`.
- **Silent failure detection.** Libraries that fail silently (slowapi, monitoring tools) need negative tests that prove the feature is active, not just that the code doesn't crash.
- **fillna guard pattern.** When converting DataFrame columns to lists, always filter empty/whitespace strings: `values = [v for v in df[col].fillna("").astype(str).tolist() if v.strip()]`

## Related Issues

- No prior documentation on rate limiting in this project
- Deployed on Render free tier where unbounded requests can exhaust the single instance (auto memory [claude])
