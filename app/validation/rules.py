from collections import Counter
from dataclasses import dataclass
from enum import StrEnum

from app.extraction.schemas import ExtractedBusinessRecord, ExtractedRecordType


class ValidationSeverity(StrEnum):
    info = "info"
    warning = "warning"
    error = "error"


@dataclass(frozen=True)
class ValidationFinding:
    field_name: str | None
    error_type: str
    message: str
    severity: ValidationSeverity = ValidationSeverity.error


def validate_extracted_record(record: ExtractedBusinessRecord) -> list[ValidationFinding]:
    findings: list[ValidationFinding] = []

    findings.extend(validate_required_fields(record))
    findings.extend(validate_confidence(record))
    findings.extend(validate_amounts(record))
    findings.extend(validate_source_evidence(record))
    findings.extend(validate_line_items(record))

    return findings


def validate_required_fields(record: ExtractedBusinessRecord) -> list[ValidationFinding]:
    findings: list[ValidationFinding] = []

    if record.record_type == ExtractedRecordType.invoice:
        required_fields = {
            "vendor_name": record.vendor_name,
            "document_id": record.document_id,
            "total_amount": record.total_amount,
            "currency": record.currency,
        }
    elif record.record_type == ExtractedRecordType.contract:
        required_fields = {
            "vendor_name": record.vendor_name,
            "document_id": record.document_id,
        }
    else:
        required_fields = {"summary": record.summary}

    for field_name, value in required_fields.items():
        if value is None or value == "":
            findings.append(
                ValidationFinding(
                    field_name=field_name,
                    error_type="required_field_missing",
                    message=f"Required field '{field_name}' is missing.",
                )
            )

    return findings


def validate_confidence(record: ExtractedBusinessRecord) -> list[ValidationFinding]:
    if record.confidence >= 0.75:
        return []

    return [
        ValidationFinding(
            field_name="confidence",
            error_type="low_confidence",
            message=(
                f"Extraction confidence {record.confidence:.2f} is below "
                "the 0.75 review threshold."
            ),
            severity=ValidationSeverity.warning,
        )
    ]


def validate_amounts(record: ExtractedBusinessRecord) -> list[ValidationFinding]:
    findings: list[ValidationFinding] = []

    if record.total_amount is not None and record.total_amount < 0:
        findings.append(
            ValidationFinding(
                field_name="total_amount",
                error_type="invalid_amount",
                message="Total amount cannot be negative.",
            )
        )

    return findings


def validate_source_evidence(record: ExtractedBusinessRecord) -> list[ValidationFinding]:
    important_fields = [
        field_name
        for field_name, value in {
            "vendor_name": record.vendor_name,
            "document_id": record.document_id,
            "total_amount": record.total_amount,
        }.items()
        if value is not None
    ]
    evidence_counter = Counter(evidence.field_name for evidence in record.source_evidence)

    findings = []
    for field_name in important_fields:
        if evidence_counter[field_name] == 0:
            findings.append(
                ValidationFinding(
                    field_name=field_name,
                    error_type="source_evidence_missing",
                    message=f"Field '{field_name}' has a value but no source evidence.",
                    severity=ValidationSeverity.warning,
                )
            )

    return findings


def validate_line_items(record: ExtractedBusinessRecord) -> list[ValidationFinding]:
    findings: list[ValidationFinding] = []

    for index, line_item in enumerate(record.line_items):
        if line_item.amount is not None and line_item.amount < 0:
            findings.append(
                ValidationFinding(
                    field_name=f"line_items[{index}].amount",
                    error_type="invalid_line_item_amount",
                    message="Line item amount cannot be negative.",
                )
            )

    return findings
