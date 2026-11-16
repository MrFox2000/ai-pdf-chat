"""PDF text extraction and page-aware chunking."""

from __future__ import annotations

from dataclasses import dataclass
from io import BytesIO

from langchain_text_splitters import RecursiveCharacterTextSplitter
from pypdf import PdfReader

#: Separators ordered from the most desirable split point to the least.
SEPARATORS = ["\n\n", "\n", ". ", "? ", "! ", "; ", ", ", " ", ""]


@dataclass(frozen=True)
class ParsedChunk:
    """A single retrievable passage with the page it came from."""

    index: int
    page: int
    text: str


def count_pages(data: bytes) -> int:
    return len(PdfReader(BytesIO(data)).pages)


def extract_pages(data: bytes) -> list[str]:
    """Return the plain text of every page, preserving page order."""
    reader = PdfReader(BytesIO(data))
    if reader.is_encrypted:
        try:
            reader.decrypt("")
        except Exception as exc:  # pragma: no cover - depends on the file
            raise ValueError("PDF is password protected") from exc

    pages: list[str] = []
    for page in reader.pages:
        pages.append((page.extract_text() or "").strip())
    return pages


def chunk_pages(
    pages: list[str],
    chunk_size: int = 900,
    chunk_overlap: int = 120,
) -> list[ParsedChunk]:
    """Split page texts into overlapping chunks, keeping page numbers attached."""
    splitter = RecursiveCharacterTextSplitter(
        chunk_size=chunk_size,
        chunk_overlap=chunk_overlap,
        separators=SEPARATORS,
    )

    chunks: list[ParsedChunk] = []
    for page_number, text in enumerate(pages, start=1):
        if not text:
            continue
        for piece in splitter.split_text(text):
            piece = piece.strip()
            if piece:
                chunks.append(ParsedChunk(index=len(chunks), page=page_number, text=piece))
    return chunks
