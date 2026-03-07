"use client";
import { useState, useRef, useEffect, KeyboardEvent } from "react";
import { ChatMessageBubble, TypingIndicator } from "@/components/ChatMessage";
import { sendMessage } from "@/lib/api";
import { getOrCreateSessionId, clearSession } from "@/lib/session";
import { ChatMessage } from "@/types";

const SUGGESTIONS = [
  "How do I deploy to staging?",
  "What is the rollback procedure?",
  "How do I configure the database?",
  "Where are the API docs?",
];

export default function ChatPage() {
  const [messages, setMessages] = useState<ChatMessage[]>([]);
  const [input, setInput] = useState("");
  const [loading, setLoading] = useState(false);
  const [backendOk, setBackendOk] = useState<boolean | null>(null);
  const [sessionId] = useState(() => getOrCreateSessionId());
  const bottomRef = useRef<HTMLDivElement>(null);
  const textareaRef = useRef<HTMLTextAreaElement>(null);

  useEffect(() => {
    fetch(`${process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000"}/health`)
      .then(r => setBackendOk(r.ok)).catch(() => setBackendOk(false));
  }, []);

  useEffect(() => { bottomRef.current?.scrollIntoView({ behavior: "smooth" }); }, [messages, loading]);

  useEffect(() => {
    if (textareaRef.current) {
      textareaRef.current.style.height = "auto";
      textareaRef.current.style.height = `${textareaRef.current.scrollHeight}px`;
    }
  }, [input]);

  async function handleSend(text?: string) {
    const query = (text ?? input).trim();
    if (!query || loading) return;
    setMessages(p => [...p, { id: crypto.randomUUID(), role: "user", content: query, timestamp: Date.now() }]);
    setInput("");
    setLoading(true);
    try {
      const res = await sendMessage(sessionId, query);
      setMessages(p => [...p, {
        id: crypto.randomUUID(), role: "assistant",
        content: res.answer, citations: res.citations,
        confidence: res.confidence, low_confidence: res.low_confidence, timestamp: Date.now()
      }]);
    } catch (err) {
      setMessages(p => [...p, {
        id: crypto.randomUUID(), role: "assistant",
        content: `⚠️ ${err instanceof Error ? err.message : "Backend unreachable"}`, timestamp: Date.now()
      }]);
    } finally {
      setLoading(false);
      textareaRef.current?.focus();
    }
  }

  return (
    <div style={{ display: "flex", flexDirection: "column", height: "100vh", overflow: "hidden" }}>
      {/* Header */}
      <div style={{
        padding: "0.875rem 1.5rem", borderBottom: "1px solid var(--border)",
        background: "var(--bg-surface)", display: "flex", alignItems: "center",
        justifyContent: "space-between", flexShrink: 0
      }}>
        <div style={{ display: "flex", alignItems: "center", gap: "0.75rem" }}>
          <span style={{ fontWeight: 600, fontSize: "0.95rem" }}>Documentation Assistant</span>
          {backendOk !== null && (
            <div style={{ display: "flex", alignItems: "center", gap: "0.375rem" }}>
              <div style={{
                width: 7, height: 7, borderRadius: "50%",
                background: backendOk ? "var(--success)" : "var(--danger)",
                boxShadow: `0 0 5px ${backendOk ? "var(--success)" : "var(--danger)"}`
              }} />
              <span style={{ fontSize: "0.72rem", color: "var(--text-muted)" }}>
                {backendOk ? "Backend ready" : "Backend offline"}
              </span>
            </div>
          )}
        </div>
        <button onClick={() => { clearSession(); setMessages([]); window.location.reload(); }}
          style={{
            background: "none", border: "1px solid var(--border)", borderRadius: 8,
            padding: "0.3rem 0.7rem", color: "var(--text-secondary)", fontSize: "0.78rem", cursor: "pointer"
          }}>
          New session
        </button>
      </div>

      {/* Messages */}
      <div style={{
        flex: 1, overflowY: "auto", padding: "1.5rem",
        display: "flex", flexDirection: "column", gap: "1.25rem"
      }}>
        {messages.length === 0 ? (
          <div style={{
            flex: 1, display: "flex", flexDirection: "column", alignItems: "center",
            justifyContent: "center", gap: "1rem", textAlign: "center", padding: "2rem"
          }}>
            <div style={{
              width: 60, height: 60, background: "linear-gradient(135deg,#3b82f6,#8b5cf6)",
              borderRadius: 18, display: "flex", alignItems: "center", justifyContent: "center",
              fontSize: 26, boxShadow: "0 8px 32px rgba(59,130,246,0.2)"
            }}>📚</div>
            <h2 style={{ margin: 0, fontSize: "1.2rem", fontWeight: 600 }}>Ask anything about your docs</h2>
            <p style={{ margin: 0, color: "var(--text-secondary)", fontSize: "0.875rem", maxWidth: 360 }}>
              I search your indexed documentation and give grounded answers with citations to the source.
            </p>
            <div style={{ display: "flex", flexWrap: "wrap", gap: "0.5rem", justifyContent: "center", maxWidth: 440 }}>
              {SUGGESTIONS.map(s => (
                <button key={s} onClick={() => handleSend(s)} style={{
                  padding: "0.375rem 0.875rem", background: "var(--bg-elevated)",
                  border: "1px solid var(--border)", borderRadius: 20, fontSize: "0.78rem",
                  color: "var(--text-secondary)", cursor: "pointer", transition: "all 0.15s"
                }}>
                  {s}
                </button>
              ))}
            </div>
          </div>
        ) : (
          <>
            {messages.map(m => <ChatMessageBubble key={m.id} message={m} />)}
            {loading && <TypingIndicator />}
          </>
        )}
        <div ref={bottomRef} />
      </div>

      {/* Input */}
      <div style={{
        padding: "0.875rem 1.5rem", borderTop: "1px solid var(--border)",
        background: "var(--bg-surface)", flexShrink: 0
      }}>
        <div style={{ display: "flex", gap: "0.75rem", alignItems: "flex-end" }}>
          <div style={{
            flex: 1, background: "var(--bg-elevated)", border: "1px solid var(--border)",
            borderRadius: 12, display: "flex", alignItems: "center", padding: "0 0.25rem 0 1rem",
            transition: "border-color 0.15s"
          }}>
            <textarea ref={textareaRef} value={input} onChange={e => setInput(e.target.value)}
              onKeyDown={(e: KeyboardEvent<HTMLTextAreaElement>) => { if (e.key === "Enter" && !e.shiftKey) { e.preventDefault(); handleSend(); } }}
              placeholder="Ask a question about your docs..." rows={1} disabled={loading}
              style={{
                flex: 1, background: "transparent", border: "none", outline: "none",
                color: "var(--text-primary)", fontSize: "0.9rem", fontFamily: "inherit",
                padding: "0.625rem 0", resize: "none", minHeight: 44, maxHeight: 120
              }} />
          </div>
          <button onClick={() => handleSend()} disabled={loading || !input.trim()}
            style={{
              width: 40, height: 40, borderRadius: 10, background: "var(--accent)", border: "none",
              color: "white", cursor: "pointer", display: "flex", alignItems: "center", justifyContent: "center",
              opacity: loading || !input.trim() ? 0.4 : 1, transition: "all 0.15s", flexShrink: 0
            }}>
            <svg width="15" height="15" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
              <line x1="22" y1="2" x2="11" y2="13" /><polygon points="22 2 15 22 11 13 2 9 22 2" />
            </svg>
          </button>
        </div>
        <div style={{ fontSize: "0.68rem", color: "var(--text-muted)", marginTop: "0.4rem", textAlign: "center" }}>
          Enter to send · Shift+Enter new line · session: <code>{sessionId.slice(0, 20)}…</code>
        </div>
      </div>
    </div>
  );
}
