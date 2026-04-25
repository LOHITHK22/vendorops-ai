import csv
from pathlib import Path

from app.parsers.models import ParsedDocument, ParsedTable


def parse_csv_file(path: Path) -> ParsedDocument:
    with path.open("r", encoding="utf-8-sig", newline="") as file:
        reader = csv.DictReader(file)
        rows = [dict(row) for row in reader]
        columns = list(reader.fieldnames or [])

    preview_lines = []
    if columns:
        preview_lines.append(", ".join(columns))
    for row in rows[:25]:
        preview_lines.append(", ".join(str(row.get(column, "")) for column in columns))

    text = "\n".join(preview_lines)

    return ParsedDocument(
        source_path=str(path),
        file_type="csv",
        text=text,
        metadata={
            "filename": path.name,
            "row_count": len(rows),
            "column_count": len(columns),
            "columns": columns,
        },
        tables=[
            ParsedTable(
                name=path.stem,
                columns=columns,
                rows=rows,
            )
        ],
    )

