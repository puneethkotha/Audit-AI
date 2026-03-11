"""Compliance rules API routes."""

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from core.database import get_db
from models.db import ComplianceRule, RuleCategory, RuleOperator, RuleSeverity
from models.schemas import ComplianceRuleCreate, ComplianceRuleResponse

router = APIRouter(prefix="/rules", tags=["rules"])


@router.get("", response_model=list[ComplianceRuleResponse])
async def list_rules(db: AsyncSession = Depends(get_db)):
    """List all compliance rules."""
    result = await db.execute(select(ComplianceRule).order_by(ComplianceRule.id))
    rules = result.scalars().all()
    return [
        ComplianceRuleResponse(
            id=r.id,
            name=r.name,
            description=r.description,
            field=r.field,
            operator=r.operator.value,
            value=r.value,
            severity=r.severity.value,
            category=r.category.value,
            is_active=r.is_active,
        )
        for r in rules
    ]


@router.post("", response_model=ComplianceRuleResponse)
async def create_rule(
    body: ComplianceRuleCreate,
    db: AsyncSession = Depends(get_db),
):
    """Create a new compliance rule."""
    rule = ComplianceRule(
        name=body.name,
        description=body.description,
        field=body.field,
        operator=RuleOperator(body.operator),
        value=body.value,
        severity=RuleSeverity(body.severity),
        category=RuleCategory(body.category),
        is_active=body.is_active,
    )
    db.add(rule)
    await db.flush()
    await db.refresh(rule)
    return ComplianceRuleResponse(
        id=rule.id,
        name=rule.name,
        description=rule.description,
        field=rule.field,
        operator=rule.operator.value,
        value=rule.value,
        severity=rule.severity.value,
        category=rule.category.value,
        is_active=rule.is_active,
    )
