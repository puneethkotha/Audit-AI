"""LLM extraction service using Claude API."""

import json
import re
import time
from typing import Any

from anthropic import AsyncAnthropic
from pydantic import ValidationError

from core.config import settings
from core.metrics import extraction_latency_seconds
from models.schemas import ExtractedFields


EXTRACTION_SYSTEM_PROMPT = """You are a medical documentation specialist. Extract structured fields from clinical notes for compliance auditing.

Return ONLY valid JSON with no preamble, markdown, or explanation. Use this exact schema:
{
  "patient_age": <int or null>,
  "diagnosis_codes": [<list of ICD-10 codes or empty array>],
  "procedure_codes": [<list of CPT codes or empty array>],
  "visit_type": "<inpatient|outpatient|telehealth or null>",
  "provider_specialty": "<string or null>",
  "medications_mentioned": [<list of medication names or empty array>],
  "risk_flags_raw": [<list of strings: anything clinically unusual, billing concerns, or documentation gaps>],
  "extraction_confidence": <float 0.0-1.0>
}

Rules:
- Extract ICD-10 codes (format like I10, E11.9, etc.) and CPT codes where present
- Use null for any field that cannot be determined from the note
- In risk_flags_raw, flag: missing critical documentation, unusual medication combinations, vital anomalies, unclear diagnoses, incomplete procedure documentation
- Set extraction_confidence based on clarity and completeness of the note (0.0 = unreadable, 1.0 = fully clear)"""


class ExtractionError(Exception):
    """Raised when LLM extraction fails."""

    pass


async def extract_fields(note_text: str) -> ExtractedFields:
    """
    Extract structured compliance fields from clinical note using Claude.
    Tracks extraction latency via Prometheus histogram.
    """
    if not settings.anthropic_api_key:
        raise ExtractionError("ANTHROPIC_API_KEY is not configured")

    client = AsyncAnthropic(api_key=settings.anthropic_api_key)
    start = time.perf_counter()

    try:
        response = await client.messages.create(
            model=settings.anthropic_model,
            max_tokens=1024,
            system=EXTRACTION_SYSTEM_PROMPT,
            messages=[
                {
                    "role": "user",
                    "content": f"Extract structured fields from this clinical note:\n\n{note_text}",
                }
            ],
        )

        elapsed = time.perf_counter() - start
        extraction_latency_seconds.observe(elapsed)

        text = ""
        for block in response.content:
            if hasattr(block, "text"):
                text += block.text

        # Parse JSON, handling potential markdown code blocks
        text = text.strip()
        json_match = re.search(r"\{[\s\S]*\}", text)
        if json_match:
            text = json_match.group(0)

        data: dict[str, Any] = json.loads(text)

        # Normalize and validate
        if "extraction_confidence" in data and data["extraction_confidence"] is None:
            data["extraction_confidence"] = 0.0
        if "diagnosis_codes" not in data:
            data["diagnosis_codes"] = []
        if "procedure_codes" not in data:
            data["procedure_codes"] = []
        if "medications_mentioned" not in data:
            data["medications_mentioned"] = []
        if "risk_flags_raw" not in data:
            data["risk_flags_raw"] = []

        return ExtractedFields.model_validate(data)

    except json.JSONDecodeError as e:
        raise ExtractionError(f"Invalid JSON from LLM: {e}") from e
    except ValidationError as e:
        raise ExtractionError(f"Schema validation failed: {e}") from e
    except Exception as e:
        elapsed = time.perf_counter() - start
        extraction_latency_seconds.observe(elapsed)
        raise ExtractionError(f"LLM extraction failed: {e}") from e
