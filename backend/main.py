"""FastAPI application entry point."""

from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from prometheus_client import make_asgi_app

from core.config import settings
from core.database import init_db, get_db
from core.metrics import (
    audit_processing_seconds,
    audit_requests_total,
    extraction_latency_seconds,
    rule_violations_total,
)
from routers import audit, rules

# Redis client - initialized in lifespan
_redis_client = None


async def get_redis_client():
    """Get Redis client. Returns None if Redis is unavailable."""
    return _redis_client


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan: init DB, Redis; cleanup on shutdown."""
    await init_db()

    redis_client = None
    try:
        import redis.asyncio as redis_async
        redis_client = redis_async.from_url(
            settings.redis_url,
            encoding="utf-8",
            decode_responses=False,
        )
        await redis_client.ping()
    except Exception:
        pass

    app.state.redis = redis_client
    global _redis_client
    _redis_client = redis_client

    yield

    if redis_client:
        await redis_client.close()


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
