import type { ChatMessage, DocumentInfo, Source, StreamHandlers } from "./types";

export const API_BASE = process.env.NEXT_PUBLIC_API_URL ?? "http://127.0.0.1:8000";

async function readError(response: Response): Promise<string> {
  try {
    const payload = (await response.json()) as { detail?: string };
    return payload.detail ?? response.statusText;
  } catch {
    return response.statusText || `Request failed with ${response.status}`;
  }
}

export async function uploadPdf(file: File): Promise<DocumentInfo> {
  const body = new FormData();
  body.append("file", file);

  const response = await fetch(`${API_BASE}/api/documents`, {
    method: "POST",
    body,
  });

  if (!response.ok) {
    throw new Error(await readError(response));
  }
  return (await response.json()) as DocumentInfo;
}

type StreamEvent =
  | { type: "sources"; sources: Source[] }
  | { type: "token"; text: string }
  | { type: "error"; message: string }
  | { type: "done" };

/**
 * Posts the question and consumes the server-sent event stream.
 * `fetch` is used instead of `EventSource` because the request needs a body.
 */
export async function streamAnswer(
  docId: string,
  question: string,
  handlers: StreamHandlers,
): Promise<void> {
  const response = await fetch(`${API_BASE}/api/chat`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ doc_id: docId, question }),
  });

  if (!response.ok) {
    throw new Error(await readError(response));
  }
  if (!response.body) {
    throw new Error("This browser cannot read streamed responses.");
  }

  const reader = response.body.getReader();
  const decoder = new TextDecoder();
  let buffer = "";

  while (true) {
    const { done, value } = await reader.read();
    if (done) break;

    buffer += decoder.decode(value, { stream: true });
    const frames = buffer.split("\n\n");
    buffer = frames.pop() ?? "";

    for (const frame of frames) {
      const line = frame.split("\n").find((part) => part.startsWith("data: "));
      if (!line) continue;

      const event = JSON.parse(line.slice(6)) as StreamEvent;
      if (event.type === "sources") handlers.onSources(event.sources);
      else if (event.type === "token") handlers.onToken(event.text);
      else if (event.type === "error") handlers.onError(event.message);
    }
  }
}

export function newMessage(
  role: ChatMessage["role"],
  content: string,
  extra: Partial<ChatMessage> = {},
): ChatMessage {
  return {
    id: `${role}-${Date.now()}-${Math.random().toString(36).slice(2, 8)}`,
    role,
    content,
    ...extra,
  };
}
