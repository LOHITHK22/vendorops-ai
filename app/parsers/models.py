from pathlib import Path
from typing import Any

from pydantic import BaseModel, Field


class ParsedPage(BaseModel):
    page_number: int
    text: str


class ParsedTable(BaseModel):
    name: str
    columns: list[str]
    rows: list[dict[str, Any]]


class ParsedDocument(BaseModel):
    source_path: str
    file_type: str
    text: str
    metadata: dict[str, Any] = Field(default_factory=dict)
    pages: list[ParsedPage] = Field(default_factory=list)
    tables: list[ParsedTable] = Field(default_factory=list)

    @property
    def filename(self) -> str:
        return Path(self.source_path).name


class ParserError(Exception):
    """Raised when a file cannot be parsed into normalized document text."""

