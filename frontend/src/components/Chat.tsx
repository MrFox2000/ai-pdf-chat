"use client";

import { useEffect, useRef, useState } from "react";

import type { ChatMessage } from "@/lib/types";

type ChatProps = {
  messages: ChatMessage[];
  busy: boolean;
  onAsk: (question: string) => void;
  suggestions: string[];
};

function SourceChips({ message }: { message: ChatMessage }) {
  const [open, setOpen] = useState(false);
  if (!message.sources?.length) return null;

  return (
    <div className="mt-3 space-y-2">
      <button
        type="button"
        onClick={() => setOpen((value) => !value)}
        className="flex items-center gap-2 text-xs font-medium text-zinc-400 transition hover:text-accent-soft"
      >
        <span className="flex flex-wrap gap-1.5">
          {message.sources.map((source) => (
            <span
              key={source.index}
              className="rounded-md border border-line bg-panel-soft px-1.5 py-0.5 text-[11px] text-zinc-300"
            >
              p. {source.page}
            </span>
          ))}
        </span>
        <span>{open ? "hide passages" : "show passages"}</span>
      </button>

      {open ? (
        <ol className="space-y-2">
          {message.sources.map((source) => (
            <li
              key={source.index}
              className="rounded-lg border border-line bg-panel-soft/60 p-3 text-xs leading-relaxed text-zinc-400"
            >
              <span className="mr-1 font-mono text-accent-soft">[{source.index}]</span>
              <span className="text-zinc-500">page {source.page} · score {source.score.toFixed(3)}</span>
              <p className="mt-1 line-clamp-4">{source.text}</p>
            </li>
          ))}
        </ol>
      ) : null}
    </div>
  );
}

export function Chat({ messages, busy, onAsk, suggestions }: ChatProps) {
  const [draft, setDraft] = useState("");
  const endRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    endRef.current?.scrollIntoView({ behavior: "smooth", block: "end" });
  }, [messages]);

  const send = () => {
    const question = draft.trim();
    if (!question || busy) return;
    setDraft("");
    onAsk(question);
  };

  const empty = messages.length === 0;

  return (
    <div className="flex min-h-0 flex-1 flex-col">
      <div className="scroll-area flex-1 overflow-y-auto px-5 py-6 sm:px-8">
        {empty ? (
          <div className="mx-auto max-w-xl space-y-4 py-10 text-center">
            <p className="text-lg font-medium text-white">Ask anything about this document</p>
            <p className="text-sm text-zinc-400">
              Every answer is grounded in the PDF and points back to the page it used.
            </p>
            <div className="flex flex-wrap justify-center gap-2 pt-2">
              {suggestions.map((suggestion) => (
                <button
                  key={suggestion}
                  type="button"
                  onClick={() => onAsk(suggestion)}
                  className="rounded-full border border-line bg-panel px-3.5 py-1.5 text-xs text-zinc-300 transition hover:border-accent/60 hover:text-white"
                >
                  {suggestion}
                </button>
              ))}
            </div>
          </div>
        ) : (
          <ul className="mx-auto flex max-w-3xl flex-col gap-5">
            {messages.map((message) => (
              <li
                key={message.id}
                className={`rise flex ${message.role === "user" ? "justify-end" : "justify-start"}`}
              >
                <div
                  className={[
                    "max-w-[85%] rounded-2xl px-4 py-3 text-sm leading-relaxed",
                    message.role === "user"
                      ? "bg-accent text-white"
                      : "border border-line bg-panel text-zinc-200",
                    message.failed ? "border-red-500/40 text-red-300" : "",
                  ].join(" ")}
                >
                  <p className="whitespace-pre-wrap">
                    {message.content}
                    {message.pending && !message.content ? (
                      <span className="inline-flex gap-1 align-middle">
                        <span className="size-1.5 animate-bounce rounded-full bg-zinc-400 [animation-delay:-0.2s]" />
                        <span className="size-1.5 animate-bounce rounded-full bg-zinc-400 [animation-delay:-0.1s]" />
                        <span className="size-1.5 animate-bounce rounded-full bg-zinc-400" />
                      </span>
                    ) : null}
                  </p>
                  {message.role === "assistant" ? <SourceChips message={message} /> : null}
                </div>
              </li>
            ))}
          </ul>
        )}
        <div ref={endRef} />
      </div>

      <div className="border-t border-line bg-panel/70 px-5 py-4 backdrop-blur sm:px-8">
        <form
          className="mx-auto flex max-w-3xl items-end gap-3"
          onSubmit={(event) => {
            event.preventDefault();
            send();
          }}
        >
          <textarea
            value={draft}
            onChange={(event) => setDraft(event.target.value)}
            onKeyDown={(event) => {
              if (event.key === "Enter" && !event.shiftKey) {
                event.preventDefault();
                send();
              }
            }}
            rows={1}
            placeholder="Ask a question about the document…"
            className="scroll-area max-h-40 min-h-[46px] flex-1 resize-none rounded-xl border border-line bg-surface px-4 py-3 text-sm text-zinc-100 outline-none transition placeholder:text-zinc-500 focus:border-accent/70"
          />
          <button
            type="submit"
            disabled={busy || !draft.trim()}
            className="flex size-[46px] items-center justify-center rounded-xl bg-accent text-white transition hover:bg-accent-soft disabled:cursor-not-allowed disabled:opacity-40"
            aria-label="Send question"
          >
            <svg viewBox="0 0 24 24" fill="none" className="size-5" aria-hidden>
              <path
                d="M5 12h13m0 0-5.5-5.5M18 12l-5.5 5.5"
                stroke="currentColor"
                strokeWidth="1.8"
                strokeLinecap="round"
                strokeLinejoin="round"
              />
            </svg>
          </button>
        </form>
      </div>
    </div>
  );
}
