"""LLM extraction service using Claude API or mock mode (free)."""

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


def _mock_extract(note_text: str) -> ExtractedFields:
    """Rule-based extraction when no API key. Free, no signup."""
    note_lower = note_text.lower()
    age = None
    age_match = re.search(r"(\d{1,3})\s*[-]?\s*year[- ]old|(\d{1,3})\s*yo\b|age\s*[:=]\s*(\d{1,3})", note_lower, re.I)
    if age_match:
        age = int(next(g for g in age_match.groups() if g))

    meds = []
    for m in ["metformin", "lisinopril", "oxycodone", "hydrocodone", "fentanyl", "morphine", "aspirin", "atorvastatin", "amlodipine", "insulin"]:
        if m in note_lower:
            meds.append(m)

    codes = re.findall(r"\b([A-Z]\d{2}(?:\.\d{2,4})?)\b", note_text) or []
    cpt = re.findall(r"\b(99\d{3})\b", note_text) or []

    vt = None
    if "inpatient" in note_lower or "admitted" in note_lower or "admission" in note_lower:
        vt = "inpatient"
    elif "outpatient" in note_lower or "office" in note_lower or "clinic" in note_lower:
        vt = "outpatient"
    elif "telehealth" in note_lower or "telemedicine" in note_lower or "virtual" in note_lower:
        vt = "telehealth"

    risk = []
    if not codes:
        risk.append("No ICD-10 diagnosis codes found")
    if not cpt:
        risk.append("No CPT procedure codes found")
    if any(op in note_lower for op in ["oxycodone", "hydrocodone", "fentanyl", "morphine"]):
        risk.append("Opioid medication documented")

    conf = 0.85 if (age and (codes or cpt)) else 0.6
    return ExtractedFields(
        patient_age=age,
        diagnosis_codes=codes[:10] or (["I10", "E11.9"] if "hypertension" in note_lower or "diabetes" in note_lower else []),
        procedure_codes=cpt[:10] or (["99213"] if vt else []),
        visit_type=vt or ("inpatient" if "admitted" in note_lower else None),
        provider_specialty="internal medicine" if "cardiac" in note_lower or "chest" in note_lower else None,
        medications_mentioned=meds,
        risk_flags_raw=risk,
        extraction_confidence=conf,
    )


async def extract_fields(note_text: str) -> ExtractedFields:
    """
    Extract structured compliance fields from clinical note using Claude or mock.
    Mock mode (no API key): free, rule-based extraction.
    """
    if settings.use_mock_extractor or not settings.anthropic_api_key:
        time.sleep(0.1)
        extraction_latency_seconds.observe(0.1)
        return _mock_extract(note_text)

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
