from email import policy
from email.parser import BytesParser
from pathlib import Path

from app.parsers.models import ParsedDocument


def parse_email_file(path: Path) -> ParsedDocument:
    message = BytesParser(policy=policy.default).parsebytes(path.read_bytes())

    body_parts: list[str] = []
    if message.is_multipart():
        for part in message.walk():
            content_type = part.get_content_type()
            disposition = part.get_content_disposition()
            if content_type == "text/plain" and disposition != "attachment":
                body_parts.append(part.get_content())
    else:
        body_parts.append(message.get_content())

    text = "\n\n".join(part.strip() for part in body_parts if part and part.strip())
    headers = {
        "subject": message.get("subject"),
        "from": message.get("from"),
        "to": message.get("to"),
        "date": message.get("date"),
    }

    return ParsedDocument(
        source_path=str(path),
        file_type="eml",
        text=text,
        metadata={
            "filename": path.name,
            "headers": headers,
            "attachment_count": sum(
                1 for part in message.walk() if part.get_content_disposition() == "attachment"
            ),
        },
    )

