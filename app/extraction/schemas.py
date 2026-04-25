from datetime import date
from enum import StrEnum
from typing import Any

from pydantic import BaseModel, Field, field_validator


class ExtractedRecordType(StrEnum):
    invoice = "invoice"
    contract = "contract"
    email = "email"
    csv = "csv"
    unknown = "unknown"


class SourceEvidence(BaseModel):
    field_name: str
    evidence_text: str
    page_number: int | None = None
    confidence: float = Field(ge=0, le=1)


class ExtractedLineItem(BaseModel):
    description: str
    quantity: float | None = None
    unit_price: float | None = None
    amount: float | None = None


class ExtractedBusinessRecord(BaseModel):
    record_type: ExtractedRecordType
    vendor_name: str | None = None
    document_id: str | None = None
    document_date: date | None = None
    due_date: date | None = None
    total_amount: float | None = None
    currency: str | None = None
    summary: str
    key_terms: list[str] = Field(default_factory=list)
    line_items: list[ExtractedLineItem] = Field(default_factory=list)
    source_evidence: list[SourceEvidence] = Field(default_factory=list)
    confidence: float = Field(ge=0, le=1)
    needs_review: bool = False
    raw_fields: dict[str, Any] = Field(default_factory=dict)

    @field_validator("currency")
    @classmethod
    def normalize_currency(cls, value: str | None) -> str | None:
        if value is None:
            return None
        normalized = value.strip().upper()
        if len(normalized) != 3:
            return normalized
        return normalized


class ExtractionResult(BaseModel):
    provider: str
    model: str
    record: ExtractedBusinessRecord

