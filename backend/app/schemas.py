"""Request and response models."""

from __future__ import annotations

from pydantic import BaseModel, Field


class DocumentOut(BaseModel):
    id: str
    filename: str
    pages: int
    chunks: int


class ChatRequest(BaseModel):
    doc_id: str = Field(min_length=1, max_length=64)
    question: str = Field(min_length=1, max_length=2000)


class Source(BaseModel):
    index: int
    page: int
    score: float
    text: str


class HealthOut(BaseModel):
    status: str
    offline: bool
    documents: int
