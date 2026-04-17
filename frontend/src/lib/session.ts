const SESSION_KEY = "rag_session_id";

export function getOrCreateSessionId(): string {
    if (typeof window === "undefined") return "ssr-session";
    let id = localStorage.getItem(SESSION_KEY);
    if (!id) {
        id = `session_${Date.now()}_${Math.random().toString(36).slice(2, 9)}`;
        localStorage.setItem(SESSION_KEY, id);
    }
    return id;
}

export function clearSession(): void {
    if (typeof window === "undefined") return;
    localStorage.removeItem(SESSION_KEY);
}
