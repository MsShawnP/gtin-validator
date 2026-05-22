import os
from pathlib import Path

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from slowapi.errors import RateLimitExceeded
from slowapi.middleware import SlowAPIMiddleware
from starlette.middleware.base import RequestResponseEndpoint
from starlette.responses import Response

from backend.limiter import limiter
from backend.routes import health, reports, sample, validate

_is_production = os.getenv("ENVIRONMENT", "").lower() == "production"

app = FastAPI(
    title="GTIN Validator API",
    version="1.0.0",
    docs_url=None if _is_production else "/api/docs",
    redoc_url=None if _is_production else "/api/redoc",
)

app.state.limiter = limiter
app.add_middleware(SlowAPIMiddleware)


@app.exception_handler(RateLimitExceeded)
async def _rate_limit_handler(request: Request, exc: RateLimitExceeded) -> Response:
    return Response(
        content='{"detail":"Too many requests. Please try again shortly."}',
        status_code=429,
        media_type="application/json",
    )

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173"],
    allow_methods=["GET", "POST"],
    allow_headers=["Content-Type"],
)


@app.middleware("http")
async def security_headers(request: Request, call_next: RequestResponseEndpoint) -> Response:
    response = await call_next(request)
    response.headers["X-Content-Type-Options"] = "nosniff"
    response.headers["X-Frame-Options"] = "DENY"
    response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
    return response


app.include_router(health.router, prefix="/api", tags=["health"])
app.include_router(validate.router, prefix="/api", tags=["validation"])
app.include_router(reports.router, prefix="/api/reports", tags=["reports"])
app.include_router(sample.router, prefix="/api", tags=["data"])

frontend_dist = Path(__file__).resolve().parent.parent / "frontend" / "dist"
if frontend_dist.is_dir():
    app.mount("/", StaticFiles(directory=str(frontend_dist), html=True), name="spa")
