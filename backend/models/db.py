"""SQLAlchemy database models."""

import enum
import uuid
from datetime import datetime
from typing import Any

from sqlalchemy import JSON, Boolean, DateTime, Enum, ForeignKey, Integer, String, Text
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship


class Base(DeclarativeBase):
    """Base class for all models."""

    pass


class RiskLevel(str, enum.Enum):
    """Risk level classification."""

    LOW = "LOW"
    MEDIUM = "MEDIUM"
    HIGH = "HIGH"
    CRITICAL = "CRITICAL"


class RuleSeverity(str, enum.Enum):
    """Compliance rule severity."""

    LOW = "LOW"
    MEDIUM = "MEDIUM"
    HIGH = "HIGH"
    CRITICAL = "CRITICAL"


class RuleCategory(str, enum.Enum):
    """Compliance rule category."""

    BILLING = "BILLING"
    CLINICAL = "CLINICAL"
    COMPLIANCE = "COMPLIANCE"


class RuleOperator(str, enum.Enum):
    """Rule evaluation operator."""

    equals = "equals"
    contains = "contains"
    not_null = "not_null"
    gt = "gt"
    lt = "lt"
    in_list = "in_list"


class ClinicalNote(Base):
    """Stores raw clinical note input."""

    __tablename__ = "clinical_notes"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    raw_text: Mapped[str] = mapped_column(Text, nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime, default=datetime.utcnow, nullable=False
    )
    metadata_: Mapped[dict[str, Any] | None] = mapped_column(
        "metadata", JSONB, nullable=True
    )

    audits: Mapped[list["AuditResult"]] = relationship(
        "AuditResult", back_populates="note", cascade="all, delete-orphan"
    )


class AuditResult(Base):
    """Stores audit results for a clinical note."""

    __tablename__ = "audit_results"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    note_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("clinical_notes.id"), nullable=False
    )
    extracted_fields: Mapped[dict[str, Any]] = mapped_column(JSONB, nullable=False)
    violations: Mapped[list[dict[str, Any]]] = mapped_column(JSONB, nullable=False)
    risk_score: Mapped[int] = mapped_column(Integer, nullable=False)
    risk_level: Mapped[RiskLevel] = mapped_column(
        Enum(RiskLevel), nullable=False
    )
    processing_time_ms: Mapped[int] = mapped_column(Integer, nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime, default=datetime.utcnow, nullable=False
    )

    note: Mapped["ClinicalNote"] = relationship(
        "ClinicalNote", back_populates="audits"
    )


class ComplianceRule(Base):
    """Configurable compliance rules."""

    __tablename__ = "compliance_rules"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[str] = mapped_column(Text, nullable=False)
    field: Mapped[str] = mapped_column(String(100), nullable=False)
    operator: Mapped[RuleOperator] = mapped_column(
        Enum(RuleOperator), nullable=False
    )
    value: Mapped[str | None] = mapped_column(String(500), nullable=True)
    severity: Mapped[RuleSeverity] = mapped_column(
        Enum(RuleSeverity), nullable=False
    )
    category: Mapped[RuleCategory] = mapped_column(
        Enum(RuleCategory), nullable=False
    )
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime, default=datetime.utcnow, nullable=False
    )
