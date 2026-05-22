# Failures Log

Record what didn't work and why, so we don't repeat mistakes.

## 2026-05-22: slowapi rate limiting looked correct but was silently non-functional

**What happened:** The /improve pass added rate limiting with all the right pieces visible — `@limiter.limit("10/minute")` decorators, `app.state.limiter`, exception handler. But it created two separate Limiter instances (one in main.py, one in validate.py) and never added `SlowAPIMiddleware`. Rate limiting was completely inert.

**Why it failed:** slowapi requires three things connected together: a single shared Limiter, that Limiter on `app.state.limiter`, and `SlowAPIMiddleware` on the app. Having any subset silently does nothing — no errors, no warnings.

**How we caught it:** `/ce:code-review` found it. Manual testing wouldn't have caught it easily because the app works normally — it just doesn't enforce limits.

**Lesson:** When adding security controls that fail silently, always write a negative test that proves the control is active (e.g., send 11 requests and assert 429). Code review is the last line of defense for silent failures.

**Tags:** slowapi, rate-limiting, silent-failure, middleware, integration
