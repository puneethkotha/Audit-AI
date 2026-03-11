"""Seed default compliance rules. Run after DB is up."""

import asyncio
import sys

from sqlalchemy import select
from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine, AsyncSession

from core.config import settings
from models.db import Base, ComplianceRule, RuleCategory, RuleOperator, RuleSeverity


RULES = [
    {
        "name": "Diagnosis codes required",
        "description": "Diagnosis codes (ICD-10) must be documented for billing compliance",
        "field": "diagnosis_codes",
        "operator": RuleOperator.not_null,
        "value": None,
        "severity": RuleSeverity.CRITICAL,
        "category": RuleCategory.BILLING,
    },
    {
        "name": "Procedure codes required",
        "description": "Procedure codes (CPT) must be documented for billing compliance",
        "field": "procedure_codes",
        "operator": RuleOperator.not_null,
        "value": None,
        "severity": RuleSeverity.CRITICAL,
        "category": RuleCategory.BILLING,
    },
    {
        "name": "Extraction confidence threshold",
        "description": "Note clarity must yield confidence above 0.7 for reliable auditing",
        "field": "extraction_confidence",
        "operator": RuleOperator.gt,
        "value": "0.7",
        "severity": RuleSeverity.HIGH,
        "category": RuleCategory.COMPLIANCE,
    },
    {
        "name": "Visit type required",
        "description": "Visit type (inpatient/outpatient/telehealth) must be documented",
        "field": "visit_type",
        "operator": RuleOperator.not_null,
        "value": None,
        "severity": RuleSeverity.HIGH,
        "category": RuleCategory.CLINICAL,
    },
    {
        "name": "Patient age required",
        "description": "Patient age must be documented for proper coding",
        "field": "patient_age",
        "operator": RuleOperator.not_null,
        "value": None,
        "severity": RuleSeverity.MEDIUM,
        "category": RuleCategory.BILLING,
    },
    {
        "name": "Provider specialty required",
        "description": "Provider specialty must be documented for compliance",
        "field": "provider_specialty",
        "operator": RuleOperator.not_null,
        "value": None,
        "severity": RuleSeverity.MEDIUM,
        "category": RuleCategory.COMPLIANCE,
    },
    {
        "name": "High-risk medications flag",
        "description": "Flag notes mentioning high-risk opioid medications for review",
        "field": "medications_mentioned",
        "operator": RuleOperator.in_list,
        "value": "oxycodone, hydrocodone, fentanyl, morphine",
        "severity": RuleSeverity.LOW,
        "category": RuleCategory.CLINICAL,
    },
]


async def seed():
    """Create tables and seed rules if empty."""
    engine = create_async_engine(settings.async_database_url)
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    async_session = async_sessionmaker(
        engine, class_=AsyncSession, expire_on_commit=False
    )
    async with async_session() as session:
        result = await session.execute(select(ComplianceRule))
        existing = result.scalars().first()
        if existing:
            print("Rules already seeded. Skipping.")
            return

        for r in RULES:
            rule = ComplianceRule(**r)
            session.add(rule)
        await session.commit()
        print(f"Seeded {len(RULES)} compliance rules.")


if __name__ == "__main__":
    asyncio.run(seed())
    sys.exit(0)
