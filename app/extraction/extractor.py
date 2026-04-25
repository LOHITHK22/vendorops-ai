import json
import re
from datetime import date

from openai import AsyncOpenAI

from app.config.settings import Settings
from app.extraction.prompts import SYSTEM_PROMPT, build_extraction_prompt
from app.extraction.schemas import (
    ExtractedBusinessRecord,
    ExtractedRecordType,
    ExtractionResult,
    SourceEvidence,
)
from app.parsers.models import ParsedDocument


class ExtractionError(Exception):
    """Raised when structured extraction fails."""


def get_extractor(settings: Settings) -> "BaseExtractor":
    if settings.openai_api_key:
        return OpenAIExtractor(settings.openai_api_key, settings.openai_model)
    return MockExtractor()


class BaseExtractor:
    provider: str
    model: str

    async def extract(self, parsed_document: ParsedDocument) -> ExtractionResult:
        raise NotImplementedError


class MockExtractor(BaseExtractor):
    provider = "mock"
    model = "rule-based-mock-v1"

    async def extract(self, parsed_document: ParsedDocument) -> ExtractionResult:
        text = parsed_document.text
        record_type = infer_record_type(parsed_document.file_type, text)
        document_id = first_match(
            text,
            [
                r"invoice\s*(?:number|#|no\.?)\s*[:#-]?\s*([A-Z0-9-]+)",
                r"\b(INV-[A-Z0-9-]+)\b",
                r"agreement\s*(?:number|#|id)?\s*[:#-]?\s*([A-Z0-9-]+)",
            ],
        )
        vendor_name = first_match(
            text,
            [
                r"vendor\s*[:#-]?\s*([^\n\r]+)",
                r"from\s*[:#-]?\s*([^\n\r<]+)",
                r"between\s+(.+?)\s+and\s+",
            ],
        )
        total_amount = extract_amount(text)
        currency = extract_currency(text)
        document_date = extract_date(text, ["invoice date", "date", "effective date"])
        due_date = extract_date(text, ["due date"])
        confidence = calculate_mock_confidence(document_id, vendor_name, total_amount, text)
        evidence = build_mock_evidence(text, document_id, vendor_name, total_amount, confidence)

        record = ExtractedBusinessRecord(
            record_type=record_type,
            vendor_name=clean_optional(vendor_name),
            document_id=clean_optional(document_id),
            document_date=document_date,
            due_date=due_date,
            total_amount=total_amount,
            currency=currency,
            summary=build_summary(record_type, vendor_name, document_id, total_amount, currency),
            source_evidence=evidence,
            confidence=confidence,
            needs_review=confidence < 0.75,
            raw_fields={
                "file_type": parsed_document.file_type,
                "metadata": parsed_document.metadata,
                "extractor": self.model,
            },
        )
        return ExtractionResult(provider=self.provider, model=self.model, record=record)


class OpenAIExtractor(BaseExtractor):
    provider = "openai"

    def __init__(self, api_key: str, model: str) -> None:
        self.model = model
        self.client = AsyncOpenAI(api_key=api_key)

    async def extract(self, parsed_document: ParsedDocument) -> ExtractionResult:
        schema = ExtractedBusinessRecord.model_json_schema()
        try:
            response = await self.client.responses.create(
                model=self.model,
                input=[
                    {"role": "system", "content": SYSTEM_PROMPT},
                    {
                        "role": "user",
                        "content": build_extraction_prompt(
                            parsed_document.file_type,
                            parsed_document.text,
                        ),
                    },
                ],
                text={
                    "format": {
                        "type": "json_schema",
                        "name": "business_document_extraction",
                        "schema": schema,
                        "strict": True,
                    }
                },
            )
        except Exception as exc:
            raise ExtractionError("OpenAI extraction request failed.") from exc

        output_text = getattr(response, "output_text", None)
        if not output_text:
            raise ExtractionError("OpenAI response did not include output_text.")

        try:
            payload = json.loads(output_text)
            record = ExtractedBusinessRecord.model_validate(payload)
        except Exception as exc:
            raise ExtractionError("OpenAI response failed schema validation.") from exc

        return ExtractionResult(provider=self.provider, model=self.model, record=record)


def infer_record_type(file_type: str, text: str) -> ExtractedRecordType:
    lowered = text.lower()
    if "invoice" in lowered or "amount due" in lowered or "due date" in lowered:
        return ExtractedRecordType.invoice
    if "agreement" in lowered or "contract" in lowered or "term" in lowered:
        return ExtractedRecordType.contract
    if file_type == "eml" or "subject:" in lowered:
        return ExtractedRecordType.email
    if file_type == "csv":
        return ExtractedRecordType.csv
    return ExtractedRecordType.unknown


def first_match(text: str, patterns: list[str]) -> str | None:
    for pattern in patterns:
        match = re.search(pattern, text, flags=re.IGNORECASE)
        if match:
            return match.group(1).strip()
    return None


def extract_amount(text: str) -> float | None:
    match = re.search(
        r"(?:total|amount due|contract value)\s*[:#-]?\s*\$?\s*([0-9][0-9,]*(?:\.[0-9]{2})?)",
        text,
        flags=re.IGNORECASE,
    )
    if not match:
        return None
    return float(match.group(1).replace(",", ""))


def extract_currency(text: str) -> str | None:
    match = re.search(r"\b(USD|EUR|GBP|CAD|AUD)\b", text, flags=re.IGNORECASE)
    if match:
        return match.group(1).upper()
    if "$" in text:
        return "USD"
    return None


def extract_date(text: str, labels: list[str]) -> date | None:
    for label in labels:
        match = re.search(
            rf"{re.escape(label)}\s*[:#-]?\s*(\d{{4}}-\d{{2}}-\d{{2}})",
            text,
            flags=re.IGNORECASE,
        )
        if match:
            return date.fromisoformat(match.group(1))
    return None


def calculate_mock_confidence(
    document_id: str | None,
    vendor_name: str | None,
    total_amount: float | None,
    text: str,
) -> float:
    score = 0.45
    if document_id:
        score += 0.15
    if vendor_name:
        score += 0.15
    if total_amount is not None:
        score += 0.15
    if len(text.strip()) > 25:
        score += 0.10
    return min(score, 0.98)


def build_mock_evidence(
    text: str,
    document_id: str | None,
    vendor_name: str | None,
    total_amount: float | None,
    confidence: float,
) -> list[SourceEvidence]:
    evidence: list[SourceEvidence] = []
    for field_name, value in [
        ("document_id", document_id),
        ("vendor_name", vendor_name),
        ("total_amount", total_amount),
    ]:
        if value is None:
            continue
        evidence_text = find_line_containing(text, str(value))
        evidence.append(
            SourceEvidence(
                field_name=field_name,
                evidence_text=evidence_text,
                confidence=confidence,
            )
        )
    return evidence


def find_line_containing(text: str, value: str) -> str:
    for line in text.splitlines():
        if value.lower() in line.lower():
            return line.strip()
    return value


def clean_optional(value: str | None) -> str | None:
    if value is None:
        return None
    cleaned = value.strip()
    return cleaned or None


def build_summary(
    record_type: ExtractedRecordType,
    vendor_name: str | None,
    document_id: str | None,
    total_amount: float | None,
    currency: str | None,
) -> str:
    subject = vendor_name or "Unknown vendor"
    identifier = f" document {document_id}" if document_id else " document"
    amount = (
        f" totaling {total_amount:.2f} {currency or ''}".strip()
        if total_amount is not None
        else ""
    )
    return f"Extracted {record_type.value}{identifier} for {subject}{amount}."
