"use client";
import { useEffect, useState } from "react";
import { getAdminStats, getRecentQueries } from "@/lib/api";
import { AdminStats, QueryLog } from "@/types";

export default function AdminPage() {
    const [stats, setStats] = useState<AdminStats | null>(null);
    const [logs, setLogs] = useState<QueryLog[]>([]);
    const [error, setError] = useState<string | null>(null);

    useEffect(() => {
        Promise.all([getAdminStats(), getRecentQueries(20)])
            .then(([s, l]) => { setStats(s); setLogs(l); })
            .catch(e => setError(e instanceof Error ? e.message : "Error loading data"));
    }, []);

    const scoreColor = (s: number | null) =>
        !s ? "#ef4444" : s >= 0.8 ? "#10b981" : s >= 0.6 ? "#f59e0b" : "#ef4444";

    return (
        <div style={{ padding: "2rem", overflowY: "auto", height: "100vh" }}>
            <h1 style={{ fontSize: "1.4rem", fontWeight: 700, margin: "0 0 1.5rem", color: "var(--text-primary)" }}>
                📊 Admin Dashboard
            </h1>

            {error && (
                <div style={{
                    color: "#ef4444", padding: "1rem", background: "rgba(239,68,68,0.1)",
                    borderRadius: 8, marginBottom: "1.5rem"
                }}>
                    ⚠️ {error} — Make sure the backend is running at {process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000"}
                </div>
            )}

            {/* Stats */}
            <div style={{ display: "grid", gridTemplateColumns: "repeat(3,1fr)", gap: "1rem", marginBottom: "2rem" }}>
                {[
                    { label: "Documents Indexed", value: stats?.document_count ?? "—", sub: "Across all sources" },
                    { label: "Chunks in Vector DB", value: stats?.chunk_count ?? "—", sub: "Chroma embeddings" },
                    {
                        label: "Last Indexed", value: stats?.last_indexed_at ? new Date(stats.last_indexed_at).toLocaleString() : "Never",
                        sub: "Run: make index", big: false
                    },
                ].map(({ label, value, sub, big = true }) => (
                    <div key={label} style={{
                        background: "var(--bg-surface)", border: "1px solid var(--border)",
                        borderRadius: 12, padding: "1.25rem"
                    }}>
                        <div style={{
                            fontSize: "0.72rem", color: "var(--text-muted)", textTransform: "uppercase",
                            letterSpacing: "0.05em", marginBottom: "0.4rem"
                        }}>{label}</div>
                        <div style={{
                            fontSize: big ? "2rem" : "1rem", fontWeight: 700, fontFamily: "var(--font-geist-mono, monospace)",
                            color: "var(--text-primary)", marginTop: big ? 0 : "0.5rem"
                        }}>{value}</div>
                        <div style={{ fontSize: "0.72rem", color: "var(--text-secondary)", marginTop: "0.25rem" }}>{sub}</div>
                    </div>
                ))}
            </div>

            {/* Query log */}
            <h2 style={{ fontSize: "1rem", fontWeight: 600, margin: "0 0 0.75rem", color: "var(--text-primary)" }}>
                Recent Queries
            </h2>
            {logs.length === 0 ? (
                <p style={{ color: "var(--text-muted)", fontSize: "0.875rem" }}>
                    No queries yet — ask questions in the Chat page to see them here.
                </p>
            ) : (
                <div style={{ background: "var(--bg-surface)", border: "1px solid var(--border)", borderRadius: 12, overflow: "hidden" }}>
                    <table style={{ width: "100%", borderCollapse: "collapse", fontSize: "0.82rem" }}>
                        <thead>
                            <tr>
                                {["Query", "Confidence", "Latency", "Time", "Chunks"].map(h => (
                                    <th key={h} style={{
                                        textAlign: "left", padding: "0.5rem 1rem", color: "var(--text-muted)",
                                        fontSize: "0.7rem", textTransform: "uppercase", letterSpacing: "0.05em",
                                        borderBottom: "1px solid var(--border)"
                                    }}>{h}</th>
                                ))}
                            </tr>
                        </thead>
                        <tbody>
                            {logs.map(log => (
                                <tr key={log.id}>
                                    <td style={{
                                        padding: "0.625rem 1rem", fontWeight: 500, color: "var(--text-primary)",
                                        maxWidth: 360, borderBottom: "1px solid var(--border)"
                                    }}>{log.query}</td>
                                    <td style={{ padding: "0.625rem 1rem", borderBottom: "1px solid var(--border)" }}>
                                        <span style={{
                                            fontFamily: "monospace", fontSize: "0.7rem", padding: "0.1rem 0.4rem",
                                            borderRadius: 4, color: scoreColor(log.confidence),
                                            background: `${scoreColor(log.confidence)}18`
                                        }}>
                                            {log.confidence ? `${Math.round(log.confidence * 100)}%` : "—"}
                                        </span>
                                    </td>
                                    <td style={{
                                        padding: "0.625rem 1rem", fontFamily: "monospace", fontSize: "0.72rem",
                                        color: "var(--text-secondary)", borderBottom: "1px solid var(--border)"
                                    }}>
                                        {log.latency_ms ? `${Math.round(log.latency_ms)}ms` : "—"}
                                    </td>
                                    <td style={{
                                        padding: "0.625rem 1rem", color: "var(--text-secondary)", whiteSpace: "nowrap",
                                        fontSize: "0.78rem", borderBottom: "1px solid var(--border)"
                                    }}>
                                        {new Date(log.created_at).toLocaleTimeString()}
                                    </td>
                                    <td style={{
                                        padding: "0.625rem 1rem", fontFamily: "monospace", fontSize: "0.7rem",
                                        color: "var(--text-muted)", borderBottom: "1px solid var(--border)"
                                    }}>
                                        {log.top_chunks?.length ?? 0}
                                    </td>
                                </tr>
                            ))}
                        </tbody>
                    </table>
                </div>
            )}
        </div>
    );
}
