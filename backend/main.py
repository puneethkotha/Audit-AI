"""FastAPI application entry point."""

from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from prometheus_client import make_asgi_app

from core.database import init_db, get_db
from core.metrics import (
    audit_processing_seconds,
    audit_requests_total,
    extraction_latency_seconds,
    rule_violations_total,
)
from routers import audit, rules


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan: init DB."""
    await init_db()
    yield


app = FastAPI(
    title="AuditAI",
    description="Clinical note compliance auditing API",
    version="1.0.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:3000",
        "http://127.0.0.1:3000",
        "https://puneethkotha.github.io",
    ],
    allow_origin_regex=r"https://.*\.vercel\.app",
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(audit.router)
app.include_router(rules.router)


@app.get("/health")
async def health():
    """Health check endpoint."""
    return {"status": "ok"}


# Mount Prometheus metrics at /metrics
metrics_app = make_asgi_app()
app.mount("/metrics", metrics_app)
