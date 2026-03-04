# RAG Documentation Assistant

> Answer natural-language questions over your engineering docs — with citations to the exact source section.

[![Python 3.11](https://img.shields.io/badge/python-3.11-blue)](https://python.org)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.110-green)](https://fastapi.tiangolo.com)
[![Next.js](https://img.shields.io/badge/Next.js-14-black)](https://nextjs.org)
[![Chroma](https://img.shields.io/badge/VectorDB-Chroma-purple)](https://trychroma.com)

---

## Problem

Docs are scattered across GitHub READMEs, internal wikis, PDFs, and tickets. Engineers waste hours searching and still get inconsistent answers. This system fixes that.

## What It Does

1. **Indexes** your docs (Markdown, HTML, PDF, Git repos) into a vector database
2. **Retrieves** the most semantically relevant chunks for any question
3. **Generates** a grounded answer using an LLM — using *only* the retrieved chunks
4. **Cites** the exact document + section the answer came from

---

## Architecture

![Architecture Diagram](./Architecture_diagram_RAG.png)

See [`docs/architecture.md`](./docs/architecture.md) for full component details.

---

## Tech Stack

| Layer | Choice |
|---|---|
| Backend | Python + FastAPI |
| LLM | Ollama + Llama 3.1 8B (local, free, private) |
| Embeddings | `BAAI/bge-base-en-v1.5` |
| Vector DB | Chroma (embedded) |
| Frontend | Next.js |

---

## Setup & Run

### Prerequisites
- Python 3.11+
- Node.js 18+
- [Ollama](https://ollama.com) installed and running
- Ollama model pulled: `ollama pull llama3.1:8b`

### 1. Install dependencies
```bash
make setup
```

### 2. Configure your doc sources
```bash
cp config/sources.yaml config/sources.local.yaml
# Edit config/sources.local.yaml — add your doc paths
```

### 3. Copy and fill environment variables
```bash
cp backend/.env.example backend/.env
```

### 4. Index your docs
```bash
make index
```

### 5. Start the app
```bash
make dev
```

- Backend: http://localhost:8000
- Frontend: http://localhost:3000
- API docs: http://localhost:8000/docs

---

## API Endpoints

| Method | Path | Description |
|---|---|---|
| `POST` | `/api/chat` | Ask a question — returns answer + citations |
| `GET` | `/api/search` | Semantic search — returns top-K chunks |
| `GET` | `/admin/stats` | Index statistics |
| `GET` | `/admin/queries` | Query audit log |
| `GET` | `/health` | Health check |

---

## Example

**Query:**
```json
POST /api/chat
{
  "session_id": "user-123",
  "message": "How do I deploy service X to staging?"
}
```

**Response:**
```json
{
  "answer": "To deploy service X to staging, run `make deploy ENV=staging`...",
  "citations": [
    { "doc_title": "Runbook", "section": "Deploy", "score": 0.91, "path_or_url": "docs/runbook.md" },
    { "doc_title": "README",  "section": "CI/CD",  "score": 0.87, "path_or_url": "README.md" }
  ],
  "confidence": 0.91,
  "low_confidence": false
}
```

---

## Evaluation

```bash
make eval
# Prints retrieval hit rate @ K=1, K=3, K=5 against golden Q&A set
```

---

## Project Structure

```
/backend        → FastAPI app
  /api          → chat, search, admin routers
  /ingestion    → loaders, chunker, embedder, indexer
  /retrieval    → retriever, context_builder
  /generation   → llm_client, prompt_templates, citation_formatter
  /models       → Document, Chunk, API models
  /db           → SQLite async database

/frontend       → Next.js chat UI
/infra          → Docker Compose
/config         → sources.yaml
/docs           → architecture.md
/eval           → golden_set.json, run_eval.py
/data           → raw docs + vector DB (gitignored)
```
