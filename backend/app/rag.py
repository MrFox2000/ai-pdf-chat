"""Retrieval-augmented generation pipeline built on LangGraph."""

from __future__ import annotations

from typing import Any, TypedDict

from langgraph.graph import END, START, StateGraph

SYSTEM_PROMPT = (
    "You are a precise document assistant. Answer using ONLY the numbered "
    "context passages provided. Cite the page of every factual claim in the "
    "form (p. 12). If the context does not contain the answer, say so plainly "
    "and never invent facts. Keep answers short and concrete."
)


class RAGState(TypedDict, total=False):
    """State threaded through the retrieval graph."""

    doc_id: str
    question: str
    context: str
    sources: list[dict[str, Any]]


def build_graph(store, embedder, settings):
    """Compile the retrieval graph: question -> embedded query -> ranked sources."""

    async def retrieve(state: RAGState) -> dict[str, Any]:
        vectors = await embedder.embed([state["question"]])
        hits = store.search(state["doc_id"], vectors[0], settings.top_k)
        if not hits:
            return {"context": "", "sources": []}

        context = "\n\n".join(
            f"[{position}] (page {chunk.page}) {chunk.text}"
            for position, (chunk, _) in enumerate(hits, start=1)
        )
        sources = [
            {
                "index": position,
                "page": chunk.page,
                "score": round(score, 4),
                "text": chunk.text,
            }
            for position, (chunk, score) in enumerate(hits, start=1)
        ]
        return {"context": context, "sources": sources}

    graph = StateGraph(RAGState)
    graph.add_node("retrieve", retrieve)
    graph.add_edge(START, "retrieve")
    graph.add_edge("retrieve", END)
    return graph.compile()


def build_answer_messages(question: str, context: str) -> list[dict[str, str]]:
    return [
        {"role": "system", "content": SYSTEM_PROMPT},
        {
            "role": "user",
            "content": f"Context:\n{context}\n\nQuestion: {question}",
        },
    ]
