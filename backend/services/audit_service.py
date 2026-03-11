"""Audit orchestration service."""

import hashlib
import time
import uuid
from typing import Any

from sqlalchemy.ext.asyncio import AsyncSession

from core.config import settings
from core.metrics import audit_processing_seconds, audit_requests_total
from models.db import AuditResult, ClinicalNote, RiskLevel
from models.schemas import (
    AuditResultSchema,
    ExtractedFields,
    RuleViolation,
)
from services.extractor import ExtractionError, extract_fields
from services.rule_engine import run_rules


def _compute_risk_score(violations: list[RuleViolation]) -> int:
    """Compute risk score from violations. Cap at 100."""
    score = 0
    for v in violations:
        if v.severity == "CRITICAL":
            score += 40
        elif v.severity == "HIGH":
            score += 20
        elif v.severity == "MEDIUM":
            score += 10
        elif v.severity == "LOW":
            score += 5
    return min(100, score)


def _classify_risk_level(score: int) -> RiskLevel:
    """Classify risk level from score."""
    if score >= 80:
        return RiskLevel.CRITICAL
    if score >= 50:
        return RiskLevel.HIGH
    if score >= 20:
        return RiskLevel.MEDIUM
    return RiskLevel.LOW


async def get_dedup_key(redis_client: Any, note_hash: str) -> str | None:
    """Check Redis for deduplicated audit result. Returns audit_id if found."""
    if not redis_client:
        return None
    key = f"audit:dedup:{note_hash}"
    audit_id = await redis_client.get(key)
    return audit_id.decode() if audit_id else None


async def set_dedup_key(
    redis_client: Any,
    note_hash: str,
    audit_id: str,
) -> None:
    """Store audit_id in Redis for deduplication."""
    if not redis_client:
        return
    key = f"audit:dedup:{note_hash}"
    await redis_client.setex(
        key,
        settings.deduplication_ttl_seconds,
        audit_id,
    )


async def run_audit(
    db: AsyncSession,
    note_text: str,
    redis_client: Any,
) -> AuditResultSchema:
    """
    Run full audit pipeline: save note, extract fields, run rules, compute score, save result.
    Uses Redis for request deduplication (60s TTL).
    """
    start = time.perf_counter()
    note_hash = hashlib.sha256(note_text.encode()).hexdigest()

    # Check deduplication
    cached_id = await get_dedup_key(redis_client, note_hash)
    if cached_id:
        from sqlalchemy import select

        result = await db.execute(
            select(AuditResult).where(AuditResult.id == uuid.UUID(cached_id))
        )
        cached = result.scalar_one_or_none()
        if cached:
            elapsed = time.perf_counter() - start
            audit_processing_seconds.observe(elapsed)
            audit_requests_total.labels(risk_level=cached.risk_level.value).inc()
            return _audit_result_to_schema(cached)

    # 1. Save raw note
    note = ClinicalNote(raw_text=note_text)
    db.add(note)
    await db.flush()

    # 2. Extract fields
    try:
        fields = await extract_fields(note_text)
    except ExtractionError as e:
        raise e

    # 3. Run rules
    violations = await run_rules(db, fields)

    # 4. Compute score and level
    risk_score = _compute_risk_score(violations)
    risk_level = _classify_risk_level(risk_score)

    processing_time_ms = int((time.perf_counter() - start) * 1000)

    # 5. Save audit result
    audit = AuditResult(
        note_id=note.id,
        extracted_fields=fields.model_dump(),
        violations=[v.model_dump() for v in violations],
        risk_score=risk_score,
        risk_level=risk_level,
        processing_time_ms=processing_time_ms,
    )
    db.add(audit)
    await db.flush()

    # 6. Set dedup key
    await set_dedup_key(redis_client, note_hash, str(audit.id))

    elapsed = time.perf_counter() - start
    audit_processing_seconds.observe(elapsed)
    audit_requests_total.labels(risk_level=risk_level.value).inc()

    return _audit_result_to_schema(audit, fields, violations)


def _audit_result_to_schema(
    audit: AuditResult,
    fields: ExtractedFields | None = None,
    violations: list[RuleViolation] | None = None,
) -> AuditResultSchema:
    """Convert AuditResult to AuditResultSchema."""
    if fields is None:
        fields = ExtractedFields.model_validate(audit.extracted_fields)
    if violations is None:
        violations = [RuleViolation.model_validate(v) for v in audit.violations]

    critical_count = sum(1 for v in violations if v.severity == "CRITICAL")
    high_count = sum(1 for v in violations if v.severity == "HIGH")

    return AuditResultSchema(
        audit_id=audit.id,
        risk_score=audit.risk_score,
        risk_level=audit.risk_level.value,
        extracted_fields=fields,
        violations=violations,
        processing_time_ms=audit.processing_time_ms,
        total_violations=len(violations),
        critical_count=critical_count,
        high_count=high_count,
    )
