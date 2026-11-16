from __future__ import annotations

import json

import pytest
from fastapi.testclient import TestClient

from app.main import app
from pdf_factory import build_pdf

CONTENT = (
    "Invoice total is 4200 EUR and the payment is due on 30 June 2026. "
    "The late fee is two percent per month."
)


@pytest.fixture(scope="module")
def client() -> TestClient:
    with TestClient(app) as test_client:
        yield test_client


@pytest.fixture(scope="module")
def document(client: TestClient) -> dict:
    response = client.post(
        "/api/documents",
        files={"file": ("invoice.pdf", build_pdf([CONTENT]), "application/pdf")},
    )
    assert response.status_code == 201, response.text
    return response.json()


def test_health(client: TestClient) -> None:
    body = client.get("/health").json()

    assert body["status"] == "ok"
    assert isinstance(body["offline"], bool)


def test_upload_returns_document_metadata(document: dict) -> None:
    assert len(document["id"]) == 12
    assert document["filename"] == "invoice.pdf"
    assert document["pages"] == 1
    assert document["chunks"] >= 1


def test_rejects_non_pdf(client: TestClient) -> None:
    response = client.post(
        "/api/documents",
        files={"file": ("notes.txt", b"hello", "text/plain")},
    )

    assert response.status_code == 415


def test_rejects_empty_file(client: TestClient) -> None:
    response = client.post(
        "/api/documents",
        files={"file": ("empty.pdf", b"", "application/pdf")},
    )

    assert response.status_code == 400


def test_rejects_unparsable_pdf(client: TestClient) -> None:
    response = client.post(
        "/api/documents",
        files={"file": ("broken.pdf", b"not a pdf at all", "application/pdf")},
    )

    assert response.status_code in (400, 422)


def test_unknown_document_returns_404(client: TestClient) -> None:
    assert client.get("/api/documents/doesnotexist").status_code == 404
    assert client.post("/api/chat", json={"doc_id": "nope", "question": "hi"}).status_code == 404


def test_chat_streams_sources_before_the_answer(client: TestClient, document: dict) -> None:
    response = client.post(
        "/api/chat",
        json={"doc_id": document["id"], "question": "When is the payment due?"},
    )

    assert response.status_code == 200
    assert response.headers["content-type"].startswith("text/event-stream")

    events = [
        json.loads(line.removeprefix("data: "))
        for line in response.text.splitlines()
        if line.startswith("data: ")
    ]
    assert events[0]["type"] == "sources"
    assert events[0]["sources"], "retrieval should return at least one passage"
    assert events[0]["sources"][0]["page"] == 1
    assert events[-1]["type"] == "done"


def test_chat_rejects_empty_question(client: TestClient, document: dict) -> None:
    response = client.post("/api/chat", json={"doc_id": document["id"], "question": ""})

    assert response.status_code == 422
