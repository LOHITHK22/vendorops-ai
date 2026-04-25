from pathlib import Path

from app.parsers.models import ParsedDocument


def parse_text_file(path: Path) -> ParsedDocument:
    text = path.read_text(encoding="utf-8-sig")

    return ParsedDocument(
        source_path=str(path),
        file_type=path.suffix.lower().lstrip("."),
        text=text,
        metadata={
            "filename": path.name,
            "character_count": len(text),
            "line_count": len(text.splitlines()),
        },
    )

