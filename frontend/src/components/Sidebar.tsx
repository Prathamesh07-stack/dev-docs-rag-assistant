"use client";

export function Sidebar() {
    return (
        <aside style={{
            background: "var(--bg-surface)", borderRight: "1px solid var(--border)",
            display: "flex", flexDirection: "column", padding: "1.25rem 0.875rem", gap: "0.25rem",
        }}>
            <div style={{ display: "flex", alignItems: "center", gap: "0.5rem", padding: "0.5rem", marginBottom: "1rem" }}>
                <div style={{
                    width: 30, height: 30, borderRadius: 8, fontSize: 14,
                    background: "linear-gradient(135deg,#3b82f6,#8b5cf6)", display: "flex",
                    alignItems: "center", justifyContent: "center"
                }}>📚</div>
                <span style={{ fontSize: "0.85rem", fontWeight: 700, letterSpacing: "-0.01em", color: "var(--text-primary)" }}>
                    Doc Assistant
                </span>
            </div>

            <NavLink href="/" icon="💬" label="Chat" />
            <NavLink href="/admin" icon="📊" label="Admin" />

            <div style={{ marginTop: "auto", padding: "0.5rem", fontSize: "0.7rem", color: "var(--text-muted)" }}>
                Powered by BAAI/bge + Ollama
            </div>
        </aside>
    );
}

function NavLink({ href, icon, label }: { href: string; icon: string; label: string }) {
    const isActive = typeof window !== "undefined" && window.location.pathname === href;
    return (
        <a href={href} style={{
            display: "flex", alignItems: "center", gap: "0.6rem",
            padding: "0.5rem 0.75rem", borderRadius: 8, textDecoration: "none",
            fontSize: "0.875rem", fontWeight: 500,
            color: isActive ? "#3b82f6" : "var(--text-secondary)",
            background: isActive ? "var(--bg-elevated)" : "transparent",
            transition: "all 0.15s",
        }}
            onMouseEnter={e => {
                const el = e.currentTarget as HTMLElement;
                el.style.background = "var(--bg-elevated)";
                el.style.color = "var(--text-primary)";
            }}
            onMouseLeave={e => {
                const el = e.currentTarget as HTMLElement;
                el.style.background = isActive ? "var(--bg-elevated)" : "transparent";
                el.style.color = isActive ? "#3b82f6" : "var(--text-secondary)";
            }}>
            <span>{icon}</span> {label}
        </a>
    );
}
