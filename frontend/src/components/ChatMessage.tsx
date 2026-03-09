"use client";
import { ChatMessage as Msg } from "@/types";
import { CitationBadge } from "./CitationBadge";

export function ChatMessageBubble({ message }: { message: Msg }) {
    const isUser = message.role === "user";
    const time = new Date(message.timestamp).toLocaleTimeString([], { hour: "2-digit", minute: "2-digit" });

    return (
        <div style={{
            display: "flex", gap: "0.75rem", flexDirection: isUser ? "row-reverse" : "row",
            alignSelf: isUser ? "flex-end" : "flex-start", maxWidth: "820px", width: "100%"
        }}>
            <div style={{
                width: 32, height: 32, borderRadius: 8, flexShrink: 0, display: "flex",
                alignItems: "center", justifyContent: "center", fontSize: 14, marginTop: 2,
                background: isUser ? "linear-gradient(135deg,#3b82f6,#8b5cf6)" : "linear-gradient(135deg,#10b981,#3b82f6)"
            }}>
                {isUser ? "👤" : "🤖"}
            </div>
            <div style={{ display: "flex", flexDirection: "column", gap: "0.3rem", maxWidth: "calc(100% - 44px)" }}>
                <div style={{
                    padding: "0.875rem 1.125rem", borderRadius: 12, fontSize: "0.9rem", lineHeight: 1.65,
                    background: isUser ? "#1e3a5f" : "#111827",
                    border: `1px solid ${isUser ? "#2d4a7a" : "#1e293b"}`,
                    borderBottomRightRadius: isUser ? 4 : 12, borderBottomLeftRadius: isUser ? 12 : 4,
                    color: "#f1f5f9",
                }}>
                    <div style={{ whiteSpace: "pre-wrap", wordBreak: "break-word" }}>{message.content}</div>

                    {message.low_confidence && !isUser && (
                        <div style={{
                            display: "inline-flex", alignItems: "center", gap: "0.3rem",
                            fontSize: "0.72rem", padding: "0.2rem 0.6rem", marginTop: "0.5rem",
                            background: "rgba(245,158,11,0.1)", border: "1px solid rgba(245,158,11,0.3)",
                            color: "#f59e0b", borderRadius: 20
                        }}>
                            ⚠️ Low confidence — verify in source docs
                        </div>
                    )}

                    {message.citations && message.citations.length > 0 && (
                        <div style={{
                            display: "flex", flexWrap: "wrap", gap: "0.4rem",
                            marginTop: "0.75rem", paddingTop: "0.75rem", borderTop: "1px solid #1e293b"
                        }}>
                            {message.citations.map((c, i) => <CitationBadge key={c.chunk_id} citation={c} index={i} />)}
                        </div>
                    )}
                </div>
                <div style={{ fontSize: "0.68rem", color: "#475569", textAlign: isUser ? "right" : "left" }}>
                    {time}
                    {message.confidence !== undefined && !isUser && (
                        <span style={{ marginLeft: "0.4rem" }}>
                            · <span style={{
                                fontFamily: "monospace",
                                color: message.confidence >= 0.8 ? "#10b981" : message.confidence >= 0.6 ? "#f59e0b" : "#ef4444"
                            }}>
                                {Math.round(message.confidence * 100)}%
                            </span>
                        </span>
                    )}
                </div>
            </div>
        </div>
    );
}

export function TypingIndicator() {
    return (
        <div style={{ display: "flex", gap: "0.75rem", alignSelf: "flex-start" }}>
            <div style={{
                width: 32, height: 32, borderRadius: 8, display: "flex", alignItems: "center",
                justifyContent: "center", fontSize: 14, background: "linear-gradient(135deg,#10b981,#3b82f6)"
            }}>🤖</div>
            <div style={{
                display: "flex", gap: 4, padding: "0.75rem 1rem", background: "#111827",
                border: "1px solid #1e293b", borderRadius: "12px 12px 12px 4px", width: "fit-content"
            }}>
                {[0, 200, 400].map((delay, i) => (
                    <div key={i} style={{
                        width: 6, height: 6, background: "#475569", borderRadius: "50%",
                        animation: `bounce 1.2s ${delay}ms infinite`
                    }} />
                ))}
            </div>
        </div>
    );
}
