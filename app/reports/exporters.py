import csv
import json
from dataclasses import dataclass
from typing import Any
from uuid import uuid4

from app.storage.backends import ObjectStorageBackend


@dataclass(frozen=True)
class StoredReportArtifact:
    uri: str
    filename: str
    content_type: str


def write_json_report(
    storage: ObjectStorageBackend,
    payload: dict[str, Any],
) -> StoredReportArtifact:
    filename = f"report-{uuid4()}.json"
    stored_object = storage.put_bytes(
        key=f"reports/{filename}",
        content=json.dumps(payload, indent=2).encode("utf-8"),
        content_type="application/json",
    )
    return StoredReportArtifact(
        uri=stored_object.uri,
        filename=filename,
        content_type=stored_object.content_type,
    )


def write_csv_report(
    storage: ObjectStorageBackend,
    rows: list[dict[str, Any]],
) -> StoredReportArtifact:
    filename = f"report-{uuid4()}.csv"
    fieldnames = [
        "record_id",
        "file_id",
        "job_id",
        "record_type",
        "vendor_name",
        "external_reference",
        "confidence",
        "total_amount",
        "currency",
        "created_at",
    ]
    buffer = _CsvStringBuffer()
    writer = csv.DictWriter(buffer, fieldnames=fieldnames)
    writer.writeheader()
    writer.writerows(rows)
    stored_object = storage.put_bytes(
        key=f"reports/{filename}",
        content=buffer.value.encode("utf-8"),
        content_type="text/csv",
    )
    return StoredReportArtifact(
        uri=stored_object.uri,
        filename=filename,
        content_type=stored_object.content_type,
    )


class _CsvStringBuffer:
    def __init__(self) -> None:
        self.value = ""

    def write(self, value: str) -> int:
        self.value += value
        return len(value)
