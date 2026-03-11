"""Tests for LLM extractor with mocked Claude responses."""

import json
from unittest.mock import AsyncMock, patch

import pytest

from models.schemas import ExtractedFields
from services.extractor import extract_fields


@pytest.mark.asyncio
async def test_extract_fields_success():
    """Extractor returns valid ExtractedFields from mocked Claude response."""
    mock_response = {
        "patient_age": 67,
        "diagnosis_codes": ["I10", "E11.9"],
        "procedure_codes": ["99213"],
        "visit_type": "inpatient",
        "provider_specialty": "cardiology",
        "medications_mentioned": ["metformin", "lisinopril", "oxycodone"],
        "risk_flags_raw": ["Elevated BP", "Opioid prescribed"],
        "extraction_confidence": 0.92,
    }

    mock_block = type("Block", (), {"text": json.dumps(mock_response)})()
    mock_message = AsyncMock()
    mock_message.content = [mock_block]

    with patch(
        "services.extractor.AsyncAnthropic",
    ) as mock_anthropic:
        mock_client = AsyncMock()
        mock_client.messages.create = AsyncMock(return_value=mock_message)
        mock_anthropic.return_value = mock_client

        result = await extract_fields(
            "Patient 67yo male, chest pain. Metformin, lisinopril."
        )

    assert isinstance(result, ExtractedFields)
    assert result.patient_age == 67
    assert result.diagnosis_codes == ["I10", "E11.9"]
    assert result.procedure_codes == ["99213"]
    assert result.visit_type == "inpatient"
    assert result.extraction_confidence == 0.92
