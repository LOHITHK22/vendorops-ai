from collections import Counter, defaultdict
from datetime import UTC, datetime
from typing import Any

from app.db.models import ExtractedRecord, ValidationError


def build_summary_report(
    records: list[ExtractedRecord],
    validation_errors: list[ValidationError],
) -> dict[str, Any]:
    total_amount_by_vendor: dict[str, float] = defaultdict(float)
    records_by_type = Counter(record.record_type for record in records)
    findings_by_severity = Counter(error.severity for error in validation_errors)
    findings_by_type = Counter(error.error_type for error in validation_errors)

    for record in records:
        vendor = record.vendor_name or "Unknown vendor"
        total_amount = record.normalized_payload.get("total_amount")
        if isinstance(total_amount, int | float):
            total_amount_by_vendor[vendor] += float(total_amount)

    return {
        "generated_at": datetime.now(UTC).isoformat(),
        "record_count": len(records),
        "validation_finding_count": len(validation_errors),
        "records_by_type": dict(records_by_type),
        "findings_by_severity": dict(findings_by_severity),
        "findings_by_type": dict(findings_by_type),
        "vendor_totals": [
            {"vendor_name": vendor, "total_amount": round(total, 2)}
            for vendor, total in sorted(total_amount_by_vendor.items())
        ],
        "records": [
            {
                "record_id": record.id,
                "record_type": record.record_type,
                "vendor_name": record.vendor_name,
                "external_reference": record.external_reference,
                "confidence": record.confidence,
                "total_amount": record.normalized_payload.get("total_amount"),
                "currency": record.normalized_payload.get("currency"),
                "created_at": record.created_at.isoformat(),
            }
            for record in records
        ],
    }


def build_records_csv_rows(records: list[ExtractedRecord]) -> list[dict[str, Any]]:
    return [
        {
            "record_id": record.id,
            "file_id": record.file_id,
            "job_id": record.job_id,
            "record_type": record.record_type,
            "vendor_name": record.vendor_name,
            "external_reference": record.external_reference,
            "confidence": record.confidence,
            "total_amount": record.normalized_payload.get("total_amount"),
            "currency": record.normalized_payload.get("currency"),
            "created_at": record.created_at.isoformat(),
        }
        for record in records
    ]

