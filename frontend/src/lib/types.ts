export type Source = {
  index: number;
  page: number;
  score: number;
  text: string;
};

export type DocumentInfo = {
  id: string;
  filename: string;
  pages: number;
  chunks: number;
};

export type ChatMessage = {
  id: string;
  role: "user" | "assistant";
  content: string;
  sources?: Source[];
  pending?: boolean;
  failed?: boolean;
};

export type StreamHandlers = {
  onSources: (sources: Source[]) => void;
  onToken: (text: string) => void;
  onError: (message: string) => void;
};
