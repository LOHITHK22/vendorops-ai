from pathlib import Path

from app.parsers.csv_parser import parse_csv_file
from app.parsers.email_parser import parse_email_file
from app.parsers.models import ParsedDocument, ParserError
from app.parsers.pdf_parser import parse_pdf_file
from app.parsers.text_parser import parse_text_file


def parse_file(path: str | Path) -> ParsedDocument:
    resolved_path = Path(path)
    if not resolved_path.exists():
        raise ParserError(f"File does not exist: {resolved_path}")

    suffix = resolved_path.suffix.lower()
    if suffix == ".csv":
        return parse_csv_file(resolved_path)
    if suffix == ".eml":
        return parse_email_file(resolved_path)
    if suffix == ".pdf":
        return parse_pdf_file(resolved_path)
    if suffix == ".txt":
        return parse_text_file(resolved_path)

    raise ParserError(f"Unsupported parser file type: {suffix}")

