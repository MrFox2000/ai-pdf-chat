"use client";

import { useCallback, useState } from "react";

import { Chat } from "@/components/Chat";
import { Dropzone } from "@/components/Dropzone";
import { newMessage, streamAnswer, uploadPdf } from "@/lib/api";
import type { ChatMessage, DocumentInfo } from "@/lib/types";

const SUGGESTIONS = [
  "Summarise this document in five bullets",
  "What are the key dates mentioned?",
  "List every amount of money and what it is for",
];

export default function Home() {
  const [document, setDocument] = useState<DocumentInfo | null>(null);
  const [messages, setMessages] = useState<ChatMessage[]>([]);
  const [uploading, setUploading] = useState(false);
  const [uploadError, setUploadError] = useState<string | null>(null);
  const [answering, setAnswering] = useState(false);

  const handleFile = useCallback(async (file: File) => {
    setUploading(true);
    setUploadError(null);
    try {
      const info = await uploadPdf(file);
      setDocument(info);
      setMessages([]);
    } catch (error) {
      setUploadError(error instanceof Error ? error.message : "Upload failed");
    } finally {
      setUploading(false);
    }
  }, []);

  const ask = useCallback(
    async (question: string) => {
      if (!document || answering) return;

      const userMessage = newMessage("user", question);
      const assistantMessage = newMessage("assistant", "", { pending: true, sources: [] });
      setMessages((previous) => [...previous, userMessage, assistantMessage]);
      setAnswering(true);

      const patch = (changes: Partial<ChatMessage>) =>
        setMessages((previous) =>
          previous.map((message) =>
            message.id === assistantMessage.id ? { ...message, ...changes } : message,
          ),
        );

      try {
        await streamAnswer(document.id, question, {
          onSources: (sources) => patch({ sources }),
          onToken: (text) =>
            setMessages((previous) =>
              previous.map((message) =>
                message.id === assistantMessage.id
                  ? { ...message, content: message.content + text, pending: false }
                  : message,
              ),
            ),
          onError: (message) => patch({ content: message, pending: false, failed: true }),
        });
      } catch (error) {
        patch({
          content: error instanceof Error ? error.message : "Could not get an answer",
          pending: false,
          failed: true,
        });
      } finally {
        setAnswering(false);
        setMessages((previous) =>
          previous.map((message) =>
            message.id === assistantMessage.id ? { ...message, pending: false } : message,
          ),
        );
      }
    },
    [answering, document],
  );

  return (
    <main className="mx-auto flex h-dvh w-full max-w-6xl flex-col px-4 py-6 sm:px-6">
      <header className="flex items-center justify-between gap-4 pb-5">
        <div className="flex items-center gap-3">
          <span className="flex size-9 items-center justify-center rounded-xl bg-accent/15 text-accent-soft">
            <svg viewBox="0 0 24 24" fill="none" className="size-5" aria-hidden>
              <path
                d="M7 3.5h7l4 4V19a1.5 1.5 0 0 1-1.5 1.5h-9A1.5 1.5 0 0 1 6 19V5A1.5 1.5 0 0 1 7.5 3.5Z"
                stroke="currentColor"
                strokeWidth="1.6"
                strokeLinejoin="round"
              />
              <path d="M13.5 3.75V8h4.25" stroke="currentColor" strokeWidth="1.6" strokeLinejoin="round" />
            </svg>
          </span>
          <div>
            <h1 className="text-sm font-semibold tracking-tight text-white">AI PDF Chat</h1>
            <p className="text-xs text-zinc-500">Grounded answers with page citations</p>
          </div>
        </div>

        {document ? (
          <div className="flex items-center gap-3">
            <div className="hidden text-right sm:block">
              <p className="max-w-[220px] truncate text-xs font-medium text-zinc-200">{document.filename}</p>
              <p className="text-[11px] text-zinc-500">
                {document.pages} pages · {document.chunks} chunks indexed
              </p>
            </div>
            <button
              type="button"
              onClick={() => {
                setDocument(null);
                setMessages([]);
                setUploadError(null);
              }}
              className="rounded-lg border border-line bg-panel px-3 py-1.5 text-xs text-zinc-300 transition hover:border-accent/60 hover:text-white"
            >
              New document
            </button>
          </div>
        ) : null}
      </header>

      <section className="flex min-h-0 flex-1 flex-col overflow-hidden rounded-3xl border border-line bg-panel/40 shadow-2xl shadow-black/40 backdrop-blur">
        {document ? (
          <Chat messages={messages} busy={answering} onAsk={ask} suggestions={SUGGESTIONS} />
        ) : (
          <div className="flex flex-1 items-center justify-center px-6 py-10">
            <Dropzone onFile={handleFile} busy={uploading} error={uploadError} />
          </div>
        )}
      </section>

      <footer className="pt-4 text-center text-[11px] text-zinc-600">
        FastAPI · LangGraph · Next.js — answers are limited to the uploaded document
      </footer>
    </main>
  );
}
