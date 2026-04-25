import csv
import json
from pathlib import Path
from typing import Any
from uuid import uuid4


def write_json_report(reports_dir: Path, payload: dict[str, Any]) -> Path:
    reports_dir.mkdir(parents=True, exist_ok=True)
    path = reports_dir / f"report-{uuid4()}.json"
    path.write_text(json.dumps(payload, indent=2), encoding="utf-8")
    return path


def write_csv_report(reports_dir: Path, rows: list[dict[str, Any]]) -> Path:
    reports_dir.mkdir(parents=True, exist_ok=True)
    path = reports_dir / f"report-{uuid4()}.csv"
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
    with path.open("w", encoding="utf-8", newline="") as file:
        writer = csv.DictWriter(file, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)
    return path

