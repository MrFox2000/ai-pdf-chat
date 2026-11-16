"""FastAPI entry point for the AI PDF Chat backend."""

from __future__ import annotations

import json
import uuid
from typing import AsyncIterator

from fastapi import FastAPI, File, HTTPException, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse

from .config import get_settings
from .embeddings import build_embedder
from .ingest import chunk_pages, extract_pages
from .rag import build_answer_messages, build_graph
from .schemas import ChatRequest, DocumentOut, HealthOut
from .store import Chunk, Document, DocumentStore

settings = get_settings()
embedder = build_embedder(settings)
store = DocumentStore()
graph = build_graph(store, embedder, settings)

app = FastAPI(
    title=settings.app_name,
    version="1.0.0",
    description=(
        "Upload a PDF and ask questions about it. Answers stream token by token "
        "and cite the page they came from."
    ),
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.origins,
    allow_methods=["GET", "POST", "DELETE"],
    allow_headers=["*"],
)


async def _sse(event: dict) -> str:
    return f"data: {json.dumps(event, ensure_ascii=False)}\n\n"


@app.get("/health", response_model=HealthOut)
async def health() -> HealthOut:
    return HealthOut(status="ok", offline=settings.offline, documents=len(store))


@app.post("/api/documents", response_model=DocumentOut, status_code=201)
async def upload_document(file: UploadFile = File(...)) -> DocumentOut:
    filename = file.filename or "document.pdf"
    if not filename.lower().endswith(".pdf"):
        raise HTTPException(status_code=415, detail="Only PDF files are supported")

    data = await file.read()
    if not data:
        raise HTTPException(status_code=400, detail="The uploaded file is empty")
    if len(data) > settings.max_upload_mb * 1024 * 1024:
        raise HTTPException(
            status_code=413,
            detail=f"File is larger than the {settings.max_upload_mb} MB limit",
        )

    try:
        pages = extract_pages(data)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    except Exception as exc:
        raise HTTPException(status_code=422, detail="Could not parse the PDF") from exc

    pieces = chunk_pages(pages, settings.chunk_size, settings.chunk_overlap)
    if not pieces:
        raise HTTPException(
            status_code=422,
            detail="No extractable text found. Scanned PDFs need OCR first.",
        )

    doc_id = uuid.uuid4().hex[:12]
    chunks = [
        Chunk(id=f"{doc_id}-{piece.index}", page=piece.page, text=piece.text)
        for piece in pieces
    ]
    vectors = await embedder.embed([chunk.text for chunk in chunks])

    store.add(
        Document(id=doc_id, filename=filename, pages=len(pages), chunks=chunks),
        vectors,
    )
    return DocumentOut(id=doc_id, filename=filename, pages=len(pages), chunks=len(chunks))


@app.get("/api/documents/{doc_id}", response_model=DocumentOut)
async def get_document(doc_id: str) -> DocumentOut:
    document = store.get(doc_id)
    if document is None:
        raise HTTPException(status_code=404, detail="Document not found")
    return DocumentOut(
        id=document.id,
        filename=document.filename,
        pages=document.pages,
        chunks=len(document.chunks),
    )


async def _offline_answer(context: str) -> AsyncIterator[str]:
    """Extractive stand-in used when no OpenAI key is configured."""
    lead = context.split("\n\n")[0]
    yield "Running without an API key, so here is the most relevant passage instead of a generated answer.\n\n"
    yield lead


async def _answer_tokens(question: str, context: str) -> AsyncIterator[str]:
    if settings.offline:
        async for piece in _offline_answer(context):
            yield piece
        return

    from langchain_openai import ChatOpenAI

    model = ChatOpenAI(
        model=settings.chat_model,
        api_key=settings.openai_api_key,
        temperature=0.1,
        streaming=True,
    )
    async for chunk in model.astream(build_answer_messages(question, context)):
        content = chunk.content
        if isinstance(content, str):
            if content:
                yield content
            continue
        for block in content:  # multimodal content blocks
            if isinstance(block, dict) and block.get("type") == "text":
                text = block.get("text", "")
                if text:
                    yield text


async def _event_stream(request: ChatRequest) -> AsyncIterator[str]:
    state = await graph.ainvoke({"doc_id": request.doc_id, "question": request.question})
    sources = state.get("sources", [])
    context = state.get("context", "")

    yield await _sse({"type": "sources", "sources": sources})

    if not context:
        yield await _sse({"type": "token", "text": "This document does not contain anything relevant to that question."})
        yield await _sse({"type": "done"})
        return

    try:
        async for piece in _answer_tokens(request.question, context):
            yield await _sse({"type": "token", "text": piece})
    except Exception as exc:  # pragma: no cover - network dependent
        yield await _sse({"type": "error", "message": f"Answer generation failed: {exc}"})
    yield await _sse({"type": "done"})


@app.post("/api/chat")
async def chat(request: ChatRequest) -> StreamingResponse:
    if store.get(request.doc_id) is None:
        raise HTTPException(status_code=404, detail="Document not found")

    return StreamingResponse(
        _event_stream(request),
        media_type="text/event-stream",
        headers={"Cache-Control": "no-cache", "X-Accel-Buffering": "no"},
    )
