"use client";
import { useState } from "react";
import { Citation } from "@/types";

export function CitationBadge({ citation, index }: { citation: Citation; index: number }) {
    const [open, setOpen] = useState(false);
    const score = Math.round(citation.score * 100);
    const scoreColor = citation.score >= 0.8 ? "#10b981" : citation.score >= 0.6 ? "#f59e0b" : "#ef4444";

    return (
        <div>
            <button onClick={() => setOpen((o) => !o)} style={{
                display: "inline-flex", alignItems: "center", gap: "0.3rem",
                fontSize: "0.72rem", padding: "0.2rem 0.6rem",
                background: "rgba(59,130,246,0.12)", border: "1px solid rgba(59,130,246,0.3)",
                color: "#60a5fa", borderRadius: "20px", cursor: "pointer",
                fontFamily: "monospace", transition: "all 0.15s",
            }}>
                📎 [{index + 1}] {citation.doc_title}{citation.section ? ` › ${citation.section}` : ""}
            </button>
            {open && (
                <div style={{
                    marginTop: "0.5rem", padding: "0.75rem",
                    background: "#1a2236", border: "1px solid #2d4a6e",
                    borderRadius: "8px", fontSize: "0.78rem",
                    animation: "slideIn 0.15s ease",
                }}>
                    <div style={{ display: "flex", justifyContent: "space-between", marginBottom: "0.4rem" }}>
                        <div>
                            <div style={{ fontWeight: 600, color: "#f1f5f9" }}>{citation.doc_title}</div>
                            {citation.section && <div style={{ color: "#94a3b8", fontSize: "0.72rem" }}>§ {citation.section}</div>}
                        </div>
                        <span style={{
                            fontFamily: "monospace", fontSize: "0.68rem", color: scoreColor,
                            background: `${scoreColor}18`, padding: "0.1rem 0.4rem", borderRadius: "4px"
                        }}>
                            {score}%
                        </span>
                    </div>
                    <a href={citation.path_or_url} target="_blank" rel="noopener noreferrer"
                        style={{ color: "#3b82f6", fontSize: "0.72rem", textDecoration: "none" }}>
                        🔗 {citation.path_or_url}
                    </a>
                </div>
            )}
        </div>
    );
}
