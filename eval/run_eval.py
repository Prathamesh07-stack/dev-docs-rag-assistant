#!/usr/bin/env python3
"""
Evaluation harness — measures retrieval hit rate on a golden Q&A set.

Usage:
    cd backend
    source venv/bin/activate
    python ../eval/run_eval.py
    python ../eval/run_eval.py --top-k 5 --golden eval/golden_set.json

Output:
    Hit rate @ K=1, K=3, K=5
    Per-question log: query | expected doc | found? | top result
"""

import argparse
import json
import os
import sys
import time
import asyncio

# Add backend to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "backend"))


async def run_eval(golden_path: str, top_k: int = 5):
    from db.database import init_db
    from ingestion.indexer import get_chroma_collection
    from retrieval.retriever import RetrieverService

    await init_db()

    # Load golden set
    with open(golden_path) as f:
        data = json.load(f)

    questions = data.get("questions", [])
    if not questions:
        print("❌ No questions in golden set. Add Q&A pairs to eval/golden_set.json")
        return

    retriever = RetrieverService()
    collection = get_chroma_collection()
    total_chunks = collection.count()

    if total_chunks == 0:
        print("❌ Vector DB is empty. Run `make index` first to index your documents.")
        return

    print(f"\n{'='*60}")
    print(f"  RAG Evaluation Harness")
    print(f"{'='*60}")
    print(f"  Golden set    : {len(questions)} questions")
    print(f"  Chunks in DB  : {total_chunks}")
    print(f"  Top-K         : {top_k}")
    print(f"{'='*60}\n")

    hits_at = {1: 0, 3: 0, 5: 0}
    results_log = []

    for q in questions:
        qid         = q["id"]
        question    = q["question"]
        expected_doc= q.get("expected_doc_title", "").lower()
        expected_sec= q.get("expected_section", "").lower()

        t0 = time.time()
        results = retriever.search(query=question, top_k=max(top_k, 5))
        elapsed_ms = round((time.time() - t0) * 1000, 1)

        found_at = None
        for rank, r in enumerate(results, 1):
            doc_match = expected_doc in r.doc_title.lower() if expected_doc else False
            sec_match = expected_sec in (r.section or "").lower() if expected_sec else False
            if doc_match or sec_match:
                found_at = rank
                break

        # Count hits
        for k in [1, 3, 5]:
            if found_at is not None and found_at <= k:
                hits_at[k] += 1

        top = results[0] if results else None
        status = f"✅ Hit@{found_at}" if found_at else "❌ Miss"

        print(f"  [{qid:02d}] {status:12s}  {question[:55]}")
        if top:
            print(f"          Top: {top.doc_title} §{top.section or 'General'}  score={top.score:.3f}  {elapsed_ms}ms")
        print()

        results_log.append({
            "id": qid,
            "question": question,
            "expected_doc": q.get("expected_doc_title"),
            "expected_section": q.get("expected_section"),
            "found_at": found_at,
            "top_result": {
                "doc_title": top.doc_title,
                "section": top.section,
                "score": top.score,
            } if top else None,
        })

    n = len(questions)
    print(f"{'='*60}")
    print(f"  RESULTS")
    print(f"{'='*60}")
    for k in [1, 3, 5]:
        hits = hits_at[k]
        rate = hits / n * 100
        bar  = "█" * int(rate / 5) + "░" * (20 - int(rate / 5))
        print(f"  Hit Rate @K={k}:  {hits}/{n}  {rate:5.1f}%  {bar}")
    print(f"{'='*60}\n")

    # Save log
    log_path = os.path.join(os.path.dirname(__file__), "eval_results.json")
    with open(log_path, "w") as f:
        json.dump({"summary": {f"hit_rate_at_{k}": hits_at[k]/n for k in [1,3,5]},
                   "results": results_log}, f, indent=2)
    print(f"  Full log saved → {log_path}")
    print(f"  Tip: Improve hit rate by tuning chunk_size, overlap, or top_k\n")


def main():
    parser = argparse.ArgumentParser(description="RAG retrieval evaluation")
    parser.add_argument("--golden", default="eval/golden_set.json")
    parser.add_argument("--top-k", type=int, default=5)
    args = parser.parse_args()

    golden = os.path.join(os.path.dirname(__file__), "..", args.golden)
    asyncio.run(run_eval(golden, args.top_k))


if __name__ == "__main__":
    main()
