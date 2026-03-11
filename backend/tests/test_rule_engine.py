"""Tests for compliance rule engine."""

from unittest.mock import MagicMock

import pytest

from models.db import RuleCategory, RuleOperator, RuleSeverity
from models.schemas import ExtractedFields
from services.rule_engine import check_rule


def _make_rule(
    field: str,
    operator: RuleOperator,
    value: str | None,
    severity: RuleSeverity,
    category: RuleCategory,
    name: str = "Test rule",
    description: str = "Test description",
) -> MagicMock:
    r = MagicMock()
    r.id = 1
    r.name = name
    r.description = description
    r.field = field
    r.operator = operator
    r.value = value
    r.severity = severity
    r.category = category
    return r


def test_rule_not_null_violation_empty_list():
    """Empty diagnosis_codes triggers not_null violation."""
    rule = _make_rule(
        field="diagnosis_codes",
        operator=RuleOperator.not_null,
        value=None,
        severity=RuleSeverity.CRITICAL,
        category=RuleCategory.BILLING,
    )
    fields = ExtractedFields(
        patient_age=67,
        diagnosis_codes=[],
        procedure_codes=["99213"],
        visit_type="inpatient",
        provider_specialty="cardiology",
        medications_mentioned=[],
        risk_flags_raw=[],
        extraction_confidence=0.95,
    )
    v = check_rule(rule, fields)
    assert v is not None
    assert v.severity == "CRITICAL"
    assert v.field_checked == "diagnosis_codes"


def test_rule_not_null_no_violation():
    """Non-empty diagnosis_codes passes not_null."""
    rule = _make_rule(
        field="diagnosis_codes",
        operator=RuleOperator.not_null,
        value=None,
        severity=RuleSeverity.CRITICAL,
        category=RuleCategory.BILLING,
    )
    fields = ExtractedFields(
        patient_age=67,
        diagnosis_codes=["I10", "E11.9"],
        procedure_codes=["99213"],
        visit_type="inpatient",
        provider_specialty="cardiology",
        medications_mentioned=[],
        risk_flags_raw=[],
        extraction_confidence=0.95,
    )
    v = check_rule(rule, fields)
    assert v is None


def test_rule_gt_violation_low_confidence():
    """extraction_confidence below 0.7 triggers violation."""
    rule = _make_rule(
        field="extraction_confidence",
        operator=RuleOperator.gt,
        value="0.7",
        severity=RuleSeverity.HIGH,
        category=RuleCategory.COMPLIANCE,
    )
    fields = ExtractedFields(
        patient_age=67,
        diagnosis_codes=["I10"],
        procedure_codes=["99213"],
        visit_type="inpatient",
        provider_specialty="cardiology",
        medications_mentioned=[],
        risk_flags_raw=[],
        extraction_confidence=0.5,
    )
    v = check_rule(rule, fields)
    assert v is not None
    assert v.severity == "HIGH"


def test_rule_in_list_opioid_flag():
    """Medications containing opioid triggers in_list violation."""
    rule = _make_rule(
        field="medications_mentioned",
        operator=RuleOperator.in_list,
        value="oxycodone, hydrocodone, fentanyl, morphine",
        severity=RuleSeverity.LOW,
        category=RuleCategory.CLINICAL,
        name="High-risk meds",
    )
    fields = ExtractedFields(
        patient_age=67,
        diagnosis_codes=["I10"],
        procedure_codes=["99213"],
        visit_type="inpatient",
        provider_specialty="cardiology",
        medications_mentioned=["metformin", "oxycodone 5mg PRN"],
        risk_flags_raw=[],
        extraction_confidence=0.9,
    )
    v = check_rule(rule, fields)
    assert v is not None
    assert v.severity == "LOW"
