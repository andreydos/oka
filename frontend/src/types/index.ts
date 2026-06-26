export type DocumentStatus = "pending" | "processing" | "indexed" | "failed" | "archived";

export interface Document {
  id: string;
  title: string;
  filename: string;
  mime_type: string;
  version: number;
  status: DocumentStatus;
  chunk_count: number;
  created_at: string;
  updated_at: string;
}

export interface Citation {
  document_id: string;
  document_name: string;
  chunk_id: string;
  page: number | null;
  section: string | null;
  quote: string;
}

export interface ChatMessage {
  id: string;
  role: "user" | "assistant";
  content: string;
  created_at: string;
  citations: Citation[];
}

export interface ChatSession {
  id: string;
  title: string;
  created_at: string;
  messages?: ChatMessage[];
}

export interface SendMessageResponse {
  user_message: ChatMessage;
  assistant_message: ChatMessage;
}

export interface HealthStatus {
  status: string;
  database: string;
  qdrant: string;
  ollama: string;
  ollama_busy: boolean;
}
