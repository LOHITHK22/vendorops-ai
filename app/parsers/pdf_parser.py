from pathlib import Path

import fitz

from app.parsers.models import ParsedDocument, ParsedPage, ParserError


def parse_pdf_file(path: Path) -> ParsedDocument:
    try:
        document = fitz.open(path)
    except Exception as exc:
        raise ParserError(f"Unable to open PDF '{path.name}'.") from exc

    pages: list[ParsedPage] = []
    for page_index, page in enumerate(document, start=1):
        pages.append(
            ParsedPage(
                page_number=page_index,
                text=page.get_text("text").strip(),
            )
        )

    text = "\n\n".join(page.text for page in pages if page.text)

    return ParsedDocument(
        source_path=str(path),
        file_type="pdf",
        text=text,
        metadata={
            "filename": path.name,
            "page_count": document.page_count,
            "character_count": len(text),
        },
        pages=pages,
    )

