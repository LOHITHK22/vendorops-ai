from pathlib import Path
from uuid import uuid4

import fitz

from app.parsers.dispatcher import parse_file


def make_test_dir() -> Path:
    test_dir = Path(".test_storage") / str(uuid4())
    test_dir.mkdir(parents=True, exist_ok=True)
    return test_dir


def test_parse_txt_file() -> None:
    parsed = parse_file("tests/fixtures/sample_invoice.txt")

    assert parsed.file_type == "txt"
    assert "Invoice Number: INV-001" in parsed.text
    assert parsed.metadata["line_count"] >= 4


def test_parse_csv_file() -> None:
    csv_path = make_test_dir() / "vendors.csv"
    csv_path.write_text(
        "vendor,invoice,total\nAcme Software,INV-001,100.00\nBeta LLC,INV-002,250.50\n",
        encoding="utf-8",
    )

    parsed = parse_file(csv_path)

    assert parsed.file_type == "csv"
    assert parsed.metadata["row_count"] == 2
    assert parsed.metadata["columns"] == ["vendor", "invoice", "total"]
    assert parsed.tables[0].rows[0]["vendor"] == "Acme Software"


def test_parse_email_file() -> None:
    email_path = make_test_dir() / "renewal.eml"
    email_path.write_text(
        "\n".join(
            [
                "From: vendor@example.com",
                "To: finance@example.com",
                "Subject: Renewal notice",
                "Date: Sat, 25 Apr 2026 09:00:00 -0700",
                "",
                "Your Acme Software contract renews on 2026-06-30.",
            ]
        ),
        encoding="utf-8",
    )

    parsed = parse_file(email_path)

    assert parsed.file_type == "eml"
    assert parsed.metadata["headers"]["subject"] == "Renewal notice"
    assert "contract renews" in parsed.text


def test_parse_pdf_file() -> None:
    pdf_path = make_test_dir() / "contract.pdf"
    document = fitz.open()
    page = document.new_page()
    page.insert_text((72, 72), "Master Services Agreement\nTotal Contract Value: 12000 USD")
    document.save(pdf_path)
    document.close()

    parsed = parse_file(pdf_path)

    assert parsed.file_type == "pdf"
    assert parsed.metadata["page_count"] == 1
    assert parsed.pages[0].page_number == 1
    assert "Master Services Agreement" in parsed.text
