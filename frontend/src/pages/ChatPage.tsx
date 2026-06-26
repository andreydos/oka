import { FormEvent, useEffect, useRef, useState } from "react";
import { Link, useNavigate, useParams } from "react-router-dom";
import { api } from "../api/client";
import { CitationList } from "../components/CitationList";
import { MessageContent } from "../components/MessageContent";
import type { ChatMessage, ChatSession } from "../types";

export function ChatPage() {
  const { sessionId } = useParams();
  const navigate = useNavigate();
  const [sessions, setSessions] = useState<ChatSession[]>([]);
  const [messages, setMessages] = useState<ChatMessage[]>([]);
  const [input, setInput] = useState("");
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const messagesEndRef = useRef<HTMLDivElement>(null);
  const activeSessionIdRef = useRef<string | undefined>(sessionId);
  const skipSessionLoadRef = useRef<string | null>(null);

  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages, loading]);

  useEffect(() => {
    api.listSessions().then(setSessions).catch(() => setSessions([]));
  }, []);

  useEffect(() => {
    activeSessionIdRef.current = sessionId;

    if (!sessionId) {
      setMessages([]);
      return;
    }

    if (skipSessionLoadRef.current === sessionId) {
      skipSessionLoadRef.current = null;
      return;
    }

    let cancelled = false;
    api
      .getSession(sessionId)
      .then((s) => {
        if (!cancelled) setMessages(s.messages ?? []);
      })
      .catch((e) => {
        if (!cancelled) setError(e.message);
      });

    return () => {
      cancelled = true;
    };
  }, [sessionId]);

  const startNewChat = () => {
    activeSessionIdRef.current = undefined;
    skipSessionLoadRef.current = null;
    setMessages([]);
    setError(null);
    navigate("/chat");
  };

  const ensureSession = async (): Promise<string> => {
    if (activeSessionIdRef.current) {
      return activeSessionIdRef.current;
    }

    const session = await api.createSession();
    activeSessionIdRef.current = session.id;
    skipSessionLoadRef.current = session.id;
    navigate(`/chat/${session.id}`, { replace: true });
    setSessions(await api.listSessions());
    return session.id;
  };

  const send = async (e: FormEvent) => {
    e.preventDefault();
    if (!input.trim() || loading) return;

    setLoading(true);
    setError(null);
    const question = input.trim();
    setInput("");

    const optimisticUser: ChatMessage = {
      id: `temp-${Date.now()}`,
      role: "user",
      content: question,
      created_at: new Date().toISOString(),
      citations: [],
    };
    setMessages((prev) => [...prev, optimisticUser]);

    try {
      const activeId = await ensureSession();
      const result = await api.sendMessage(activeId, question);
      setMessages((prev) => [
        ...prev.filter((m) => m.id !== optimisticUser.id),
        result.user_message,
        result.assistant_message,
      ]);
      setSessions(await api.listSessions());
    } catch (e) {
      setMessages((prev) => prev.filter((m) => m.id !== optimisticUser.id));
      setError(e instanceof Error ? e.message : "Failed to send message");
      setInput(question);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="flex gap-6 h-[calc(100vh-8rem)]">
      <aside className="w-64 shrink-0 flex flex-col gap-2">
        <button
          type="button"
          onClick={startNewChat}
          className="rounded-lg bg-slate-800 px-4 py-2 text-sm text-white hover:bg-slate-700"
        >
          New chat
        </button>
        <div className="flex-1 overflow-y-auto space-y-1">
          {sessions.map((s) => (
            <Link
              key={s.id}
              to={`/chat/${s.id}`}
              className={`block rounded-lg px-3 py-2 text-sm truncate ${
                sessionId === s.id
                  ? "bg-slate-200 font-medium"
                  : "text-slate-600 hover:bg-slate-100"
              }`}
            >
              {s.title}
            </Link>
          ))}
        </div>
      </aside>

      <div className="flex-1 flex flex-col rounded-xl border border-slate-200 bg-white">
        <div className="flex-1 overflow-y-auto p-6 space-y-6">
          {!sessionId && messages.length === 0 && (
            <p className="text-slate-500 text-center mt-12">
              Ask a question about your indexed documents. Answers include citations.
            </p>
          )}
          {messages.map((msg) => (
            <div
              key={msg.id}
              className={`max-w-3xl ${msg.role === "user" ? "ml-auto text-right" : ""}`}
            >
              <div
                className={`inline-block rounded-2xl px-4 py-3 text-sm ${
                  msg.role === "user"
                    ? "bg-slate-800 text-white"
                    : "bg-slate-100 text-slate-800"
                }`}
              >
                {msg.role === "user" ? msg.content : <MessageContent content={msg.content} />}
              </div>
              {msg.role === "assistant" && <CitationList citations={msg.citations} />}
            </div>
          ))}
          {loading && (
            <div className="text-sm text-slate-500 animate-pulse">Generating answer…</div>
          )}
          <div ref={messagesEndRef} />
        </div>

        {error && (
          <div className="mx-6 mb-2 rounded-lg bg-red-50 p-3 text-sm text-red-700">{error}</div>
        )}

        <form onSubmit={send} className="border-t border-slate-200 p-4 flex gap-2">
          <input
            type="text"
            value={input}
            onChange={(e) => setInput(e.target.value)}
            placeholder="Ask a question…"
            className="flex-1 rounded-lg border border-slate-300 px-4 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-slate-400"
            disabled={loading}
          />
          <button
            type="submit"
            disabled={loading || !input.trim()}
            className="rounded-lg bg-slate-800 px-4 py-2 text-sm text-white hover:bg-slate-700 disabled:opacity-50"
          >
            Send
          </button>
        </form>
      </div>
    </div>
  );
}
