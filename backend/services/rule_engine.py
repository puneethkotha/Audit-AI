"""Compliance rule engine."""

from typing import Any

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from core.metrics import rule_violations_total
from models.db import ComplianceRule, RuleCategory, RuleOperator, RuleSeverity
from models.schemas import ExtractedFields, RuleViolation


def _get_field_value(fields: ExtractedFields, field_name: str) -> Any:
    """Get field value from extracted fields."""
    data = fields.model_dump()
    return data.get(field_name)


def check_rule(
    rule: ComplianceRule,
    fields: ExtractedFields,
) -> RuleViolation | None:
    """Check a single rule against extracted fields. Returns violation if rule fails."""
    value = _get_field_value(fields, rule.field)
    operator = rule.operator
    expected = rule.value

    violated = False

    if operator == RuleOperator.not_null:
        violated = value is None or (
            isinstance(value, (list, str)) and len(value) == 0
        )
        if violated:
            expected = "not null"
            actual = str(value) if value is not None else "null"
    elif operator == RuleOperator.equals:
        violated = value != expected
        actual = str(value) if value is not None else "null"
    elif operator == RuleOperator.contains:
        if isinstance(value, list):
            violated = expected not in value if expected else False
        elif isinstance(value, str):
            violated = expected not in value.lower() if expected else False
        else:
            violated = True
        actual = str(value) if value is not None else "null"
    elif operator == RuleOperator.gt:
        try:
            num_val = float(value) if value is not None else float("-inf")
            threshold = float(expected) if expected else 0
            violated = num_val <= threshold
        except (TypeError, ValueError):
            violated = True
        actual = str(value) if value is not None else "null"
    elif operator == RuleOperator.lt:
        try:
            num_val = float(value) if value is not None else float("inf")
            threshold = float(expected) if expected else 0
            violated = num_val >= threshold
        except (TypeError, ValueError):
            violated = True
        actual = str(value) if value is not None else "null"
    elif operator == RuleOperator.in_list:
        if expected:
            items = [s.strip() for s in expected.split(",")]
            if isinstance(value, list):
                violated = any(
                    any(item.lower() in str(v).lower() for v in value)
                    for item in items
                )
            elif isinstance(value, str):
                violated = any(item.lower() in value.lower() for item in items)
            else:
                violated = False
        else:
            violated = False
        actual = str(value) if value is not None else "null"

    if not violated:
        return None

    recommendation = _build_recommendation(rule, value, expected, operator)
    rule_violations_total.labels(
        severity=rule.severity.value,
        category=rule.category.value,
    ).inc()

    return RuleViolation(
        rule_id=rule.id,
        rule_name=rule.name,
        severity=rule.severity.value,
        category=rule.category.value,
        field_checked=rule.field,
        expected=expected,
        actual=actual if violated else None,
        recommendation=recommendation,
    )


def _build_recommendation(
    rule: ComplianceRule,
    value: Any,
    expected: str | None,
    operator: RuleOperator,
) -> str:
    """Build a human-readable recommendation for fixing the violation."""
    base = f"Ensure {rule.field} meets compliance: "
    if operator == RuleOperator.not_null:
        return base + f"{rule.field} must be documented in the clinical note."
    if operator == RuleOperator.gt and expected:
        return base + f"{rule.field} should be greater than {expected}."
    if operator == RuleOperator.lt and expected:
        return base + f"{rule.field} should be less than {expected}."
    if operator == RuleOperator.equals and expected:
        return base + f"Expected '{expected}' but got '{value}'."
    if operator == RuleOperator.contains and expected:
        return base + f"{rule.field} should contain '{expected}'."
    if operator == RuleOperator.in_list and expected:
        return base + f"High-risk items detected. Verify documentation and necessity."
    return base + rule.description


async def run_rules(
    db: AsyncSession,
    fields: ExtractedFields,
) -> list[RuleViolation]:
    """Load active rules from DB and run them against extracted fields."""
    result = await db.execute(
        select(ComplianceRule).where(ComplianceRule.is_active == True)
    )
    rules = result.scalars().all()
    violations: list[RuleViolation] = []
    for rule in rules:
        v = check_rule(rule, fields)
        if v:
            violations.append(v)
    return violations
