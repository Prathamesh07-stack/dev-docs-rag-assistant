import { ChatResponse, AdminStats, QueryLog } from "@/types";

const BASE_URL = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

export async function sendMessage(
    sessionId: string,
    message: string,
    topK: number = 5
): Promise<ChatResponse> {
    const res = await fetch(`${BASE_URL}/api/chat`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ session_id: sessionId, message, top_k: topK }),
    });
    if (!res.ok) {
        const err = await res.json().catch(() => ({}));
        throw new Error((err as { detail?: string }).detail || `API error ${res.status}`);
    }
    return res.json();
}

export async function getAdminStats(): Promise<AdminStats> {
    const res = await fetch(`${BASE_URL}/admin/stats`);
    if (!res.ok) throw new Error(`Stats error ${res.status}`);
    return res.json();
}

export async function getRecentQueries(limit = 20): Promise<QueryLog[]> {
    const res = await fetch(`${BASE_URL}/admin/queries?limit=${limit}`);
    if (!res.ok) throw new Error(`Queries error ${res.status}`);
    return res.json();
}
