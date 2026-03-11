"""Pydantic request/response schemas."""

from uuid import UUID

from pydantic import BaseModel, Field


# --- Audit ---

class AuditRequest(BaseModel):
    """Request schema for audit endpoint."""

    note_text: str = Field(..., min_length=50)


class ExtractedFields(BaseModel):
    """Structured fields extracted from clinical note by LLM."""

    patient_age: int | None = None
    diagnosis_codes: list[str] = Field(default_factory=list)
    procedure_codes: list[str] = Field(default_factory=list)
    visit_type: str | None = None
    provider_specialty: str | None = None
    medications_mentioned: list[str] = Field(default_factory=list)
    risk_flags_raw: list[str] = Field(default_factory=list)
    extraction_confidence: float = 0.0


class RuleViolation(BaseModel):
    """A single rule violation from the audit."""

    rule_id: int
    rule_name: str
    severity: str
    category: str
    field_checked: str
    expected: str | None
    actual: str | None
    recommendation: str


class AuditResultSchema(BaseModel):
    """Response schema for audit endpoint."""

    audit_id: UUID
    risk_score: int
    risk_level: str
    extracted_fields: ExtractedFields
    violations: list[RuleViolation]
    processing_time_ms: int
    total_violations: int
    critical_count: int
    high_count: int


# --- Rules ---

class ComplianceRuleCreate(BaseModel):
    """Schema for creating a compliance rule."""

    name: str = Field(..., min_length=1, max_length=255)
    description: str = Field(..., min_length=1)
    field: str = Field(..., min_length=1, max_length=100)
    operator: str = Field(
        ...,
        pattern="^(equals|contains|not_null|gt|lt|in_list)$",
    )
    value: str | None = None
    severity: str = Field(
        ...,
        pattern="^(LOW|MEDIUM|HIGH|CRITICAL)$",
    )
    category: str = Field(
        ...,
        pattern="^(BILLING|CLINICAL|COMPLIANCE)$",
    )
    is_active: bool = True


class ComplianceRuleResponse(BaseModel):
    """Response schema for compliance rule."""

    id: int
    name: str
    description: str
    field: str
    operator: str
    value: str | None
    severity: str
    category: str
    is_active: bool
