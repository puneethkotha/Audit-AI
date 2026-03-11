"""Audit API routes."""

from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Request
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from core.database import get_db
from models.db import AuditResult
from models.schemas import (
    AuditRequest,
    AuditResultSchema,
    ExtractedFields,
    RuleViolation,
)
from services.audit_service import run_audit
from services.extractor import ExtractionError

router = APIRouter(prefix="/audit", tags=["audit"])


@router.post("", response_model=AuditResultSchema)
async def create_audit(
    body: AuditRequest,
    request: Request,
    db: AsyncSession = Depends(get_db),
):
    """Run compliance audit on a clinical note."""
    redis_client = getattr(request.app.state, "redis", None)
    try:
        return await run_audit(db, body.note_text, redis_client)
    except ExtractionError as e:
        raise HTTPException(status_code=500, detail=str(e)) from e


@router.get("/{audit_id}", response_model=AuditResultSchema)
async def get_audit(audit_id: UUID, db: AsyncSession = Depends(get_db)):
    """Retrieve a previously run audit by ID."""
    result = await db.execute(
        select(AuditResult).where(AuditResult.id == audit_id)
    )
    audit = result.scalar_one_or_none()
    if not audit:
        raise HTTPException(status_code=404, detail="Audit not found")

    return AuditResultSchema(
        audit_id=audit.id,
        risk_score=audit.risk_score,
        risk_level=audit.risk_level.value,
        extracted_fields=ExtractedFields.model_validate(audit.extracted_fields),
        violations=[RuleViolation.model_validate(v) for v in audit.violations],
        processing_time_ms=audit.processing_time_ms,
        total_violations=len(audit.violations),
        critical_count=sum(
            1 for v in audit.violations if v.get("severity") == "CRITICAL"
        ),
        high_count=sum(
            1 for v in audit.violations if v.get("severity") == "HIGH"
        ),
    )
