import type {
  ChatSession,
  Document,
  HealthStatus,
  SendMessageResponse,
} from "../types";

const API_BASE = "/api/v1";

async function request<T>(path: string, options?: RequestInit): Promise<T> {
  const response = await fetch(`${API_BASE}${path}`, options);
  if (!response.ok) {
    const text = await response.text();
    throw new Error(text || `Request failed: ${response.status}`);
  }
  if (response.status === 204) {
    return undefined as T;
  }
  return response.json();
}

export const api = {
  health: () => request<HealthStatus>("/health"),

  listDocuments: () => request<Document[]>("/documents"),

  getDocument: (id: string) => request<Document>(`/documents/${id}`),

  documentFileUrl: (id: string, page?: number | null) => {
    const url = `${API_BASE}/documents/${id}/file`;
    return page != null ? `${url}#page=${page}` : url;
  },

  uploadDocument: async (file: File, title?: string) => {
    const form = new FormData();
    form.append("file", file);
    if (title) form.append("title", title);
    return request<Document>("/documents", { method: "POST", body: form });
  },

  deleteDocument: (id: string) =>
    request<void>(`/documents/${id}`, { method: "DELETE" }),

  reindexDocument: (id: string) =>
    request<Document>(`/documents/${id}/reindex`, { method: "POST" }),

  createSession: () =>
    request<ChatSession>("/chat/sessions", { method: "POST" }),

  listSessions: () => request<ChatSession[]>("/chat/sessions"),

  getSession: (id: string) => request<ChatSession>(`/chat/sessions/${id}`),

  sendMessage: (sessionId: string, content: string) =>
    request<SendMessageResponse>(`/chat/sessions/${sessionId}/messages`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ content }),
    }),
};
