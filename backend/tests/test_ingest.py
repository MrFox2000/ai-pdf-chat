from __future__ import annotations

from app.ingest import chunk_pages, extract_pages
from pdf_factory import build_pdf

PAGE_ONE = (
    "Retrieval augmented generation combines a search step with a language model. "
    "The retriever returns the passages that are most similar to the question. "
    "The generator then writes an answer grounded in those passages only."
)
PAGE_TWO = "Chunking matters. Small chunks retrieve precisely but lose surrounding context."


def test_extract_pages_keeps_page_order() -> None:
    pages = extract_pages(build_pdf([PAGE_ONE, PAGE_TWO]))

    assert len(pages) == 2
    assert "Retrieval augmented generation" in pages[0]
    assert "Chunking matters" in pages[1]


def test_chunk_pages_attaches_page_numbers() -> None:
    chunks = chunk_pages([PAGE_ONE, PAGE_TWO], chunk_size=120, chunk_overlap=20)

    assert chunks, "expected at least one chunk"
    assert all(chunk.page in (1, 2) for chunk in chunks)
    assert chunks[0].page == 1
    assert chunks[-1].page == 2
    assert [chunk.index for chunk in chunks] == list(range(len(chunks)))


def test_chunk_size_is_respected() -> None:
    chunks = chunk_pages([PAGE_ONE], chunk_size=100, chunk_overlap=10)

    assert all(len(chunk.text) <= 100 for chunk in chunks)


def test_blank_pages_are_skipped() -> None:
    chunks = chunk_pages(["", "   ", PAGE_TWO], chunk_size=200, chunk_overlap=0)

    assert chunks
    assert all(chunk.page == 3 for chunk in chunks)
