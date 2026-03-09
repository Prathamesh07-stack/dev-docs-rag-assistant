// ── API Types ────────────────────────────────────────────────────────────────

export interface Citation {
    chunk_id: string;
    doc_id: string;
    doc_title: string;
    section: string | null;
    path_or_url: string;
    score: number;
}

export interface ChatMessage {
    id: string;
    role: "user" | "assistant";
    content: string;
    citations?: Citation[];
    confidence?: number;
    low_confidence?: boolean;
    timestamp: number;
}

export interface ChatResponse {
    answer: string;
    citations: Citation[];
    confidence: number;
    low_confidence: boolean;
}

export interface SearchResult {
    chunk_id: string;
    content: string;
    score: number;
    doc_id: string;
    doc_title: string;
    section: string | null;
    path_or_url: string;
    low_confidence: boolean;
}

export interface AdminStats {
    document_count: number;
    chunk_count: number;
    last_indexed_at: string | null;
}

export interface QueryLog {
    id: number;
    session_id: string;
    query: string;
    top_chunks: string[];
    confidence: number | null;
    latency_ms: number | null;
    created_at: string;
}
