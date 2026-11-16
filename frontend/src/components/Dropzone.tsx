"use client";

import { useCallback, useRef, useState } from "react";

type DropzoneProps = {
  onFile: (file: File) => void;
  busy?: boolean;
  error?: string | null;
};

export function Dropzone({ onFile, busy = false, error }: DropzoneProps) {
  const inputRef = useRef<HTMLInputElement>(null);
  const [dragging, setDragging] = useState(false);

  const accept = useCallback(
    (file: File | undefined) => {
      if (!file) return;
      onFile(file);
    },
    [onFile],
  );

  return (
    <div className="w-full max-w-2xl">
      <div
        role="button"
        tabIndex={0}
        aria-label="Upload a PDF"
        onClick={() => !busy && inputRef.current?.click()}
        onKeyDown={(event) => {
          if (event.key === "Enter" || event.key === " ") inputRef.current?.click();
        }}
        onDragOver={(event) => {
          event.preventDefault();
          setDragging(true);
        }}
        onDragLeave={() => setDragging(false)}
        onDrop={(event) => {
          event.preventDefault();
          setDragging(false);
          accept(event.dataTransfer.files[0]);
        }}
        className={[
          "group relative flex cursor-pointer flex-col items-center justify-center gap-4 rounded-3xl border-2 border-dashed px-8 py-16 text-center transition",
          dragging
            ? "border-accent bg-accent/10"
            : "border-line bg-panel/60 hover:border-accent/60 hover:bg-panel",
          busy ? "pointer-events-none opacity-60" : "",
        ].join(" ")}
      >
        <input
          ref={inputRef}
          type="file"
          accept="application/pdf"
          className="hidden"
          onChange={(event) => accept(event.target.files?.[0])}
        />

        <span className="flex size-14 items-center justify-center rounded-2xl bg-accent/15 text-accent-soft">
          <svg viewBox="0 0 24 24" fill="none" className="size-7" aria-hidden>
            <path
              d="M12 16V4m0 0L7.5 8.5M12 4l4.5 4.5M4 15v3a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2v-3"
              stroke="currentColor"
              strokeWidth="1.7"
              strokeLinecap="round"
              strokeLinejoin="round"
            />
          </svg>
        </span>

        <div className="space-y-1">
          <p className="text-base font-medium text-white">
            {busy ? "Reading your document…" : "Drop a PDF here, or click to browse"}
          </p>
          <p className="text-sm text-zinc-400">
            Answers cite the exact page. Up to 20 MB, text-based PDFs only.
          </p>
        </div>
      </div>

      {error ? (
        <p className="mt-3 rounded-xl border border-red-500/30 bg-red-500/10 px-4 py-2.5 text-sm text-red-300">
          {error}
        </p>
      ) : null}
    </div>
  );
}
