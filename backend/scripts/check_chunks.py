"""
Sanity-check script for the chunker.

Run from backend/ with venv active:
  python scripts/check_chunks.py

What it does:
  - Creates 3 sample documents (Markdown, multi-section, short)
  - Runs the chunker on each
  - Prints chunk count, token sizes, section titles, and content previews
  - Flags any chunks outside the expected size range

Usage:
  source venv/bin/activate
  python scripts/check_chunks.py
  python scripts/check_chunks.py --file path/to/your.md   # test a real file
"""

import argparse
import sys
from pathlib import Path

# Allow running from backend/ directory
sys.path.insert(0, str(Path(__file__).parent.parent))

from ingestion.chunker import chunk_document, _count_tokens
from models.document import Document


# ── Sample documents for testing ─────────────────────────────────────────────

SAMPLE_MARKDOWN = """# Deployment Guide

This guide explains how to deploy service X to staging and production.

## Prerequisites

Before deploying, ensure you have:
- Docker installed (`docker --version`)
- Access to the staging cluster
- `.env.staging` configured with the correct secrets

## Deploy to Staging

Run the following command from the project root:

```bash
make deploy ENV=staging
```

This will:
1. Build the Docker image
2. Push to the container registry
3. Apply Kubernetes manifests from `infra/k8s/staging/`
4. Wait for rollout to complete

If the rollout fails, the deployment will automatically roll back.

## Deploy to Production

Production deploys require a pull request approval from two senior engineers.

```bash
make deploy ENV=production
```

Monitor the deployment using:
```bash
kubectl rollout status deployment/service-x -n production
```

## Rollback

To rollback to the previous version:
```bash
make rollback ENV=staging
```

Or manually:
```bash
kubectl rollout undo deployment/service-x -n staging
```

## Troubleshooting

### OOMKilled
If pods are getting OOMKilled, increase the memory limit in `infra/k8s/base/deployment.yaml`.

### CrashLoopBackOff
Check pod logs:
```bash
kubectl logs -f deployment/service-x -n staging
```
"""

SAMPLE_NO_HEADINGS = """
This is a plain document with no headings. It has several paragraphs of content.

The chunker should handle this gracefully by splitting purely on token count when the total exceeds 512 tokens.

Lorem ipsum dolor sit amet, consectetur adipiscing elit. Sed do eiusmod tempor incididunt ut labore et dolore magna aliqua. Ut enim ad minim veniam, quis nostrud exercitation ullamco laboris nisi ut aliquip ex ea commodo consequat.

Duis aute irure dolor in reprehenderit in voluptate velit esse cillum dolore eu fugiat nulla pariatur. Excepteur sint occaecat cupidatat non proident, sunt in culpa qui officia deserunt mollit anim id est laborum.

Sed ut perspiciatis unde omnis iste natus error sit voluptatem accusantium doloremque laudantium, totam rem aperiam, eaque ipsa quae ab illo inventore veritatis et quasi architecto beatae vitae dicta sunt explicabo.

Nemo enim ipsam voluptatem quia voluptas sit aspernatur aut odit aut fugit, sed quia consequuntur magni dolores eos qui ratione voluptatem sequi nesciunt.
"""

SAMPLE_SHORT = "# Short Doc\nThis is a very short document."


# ── Helpers ───────────────────────────────────────────────────────────────────

def make_doc(title: str, content: str, source_type: str = "markdown") -> Document:
    return Document(
        title=title,
        content=content,
        source_type=source_type,
        path_or_url=f"test/{title.lower().replace(' ', '_')}.md",
        content_hash="test",
    )


def print_separator(char="─", width=60):
    print(char * width)


def check_doc(doc: Document, chunk_size: int = 512, overlap: int = 64):
    chunks = chunk_document(doc, chunk_size=chunk_size, overlap=overlap)
    total_tokens = _count_tokens(doc.content)

    print_separator("═")
    print(f"  📄 Document : {doc.title}")
    print(f"  Source type : {doc.source_type}")
    print(f"  Total tokens: {total_tokens}")
    print(f"  Chunks      : {len(chunks)}")
    print_separator()

    warnings = 0
    for i, chunk in enumerate(chunks):
        section = chunk.section_title or "(no heading)"
        preview = chunk.content[:80].replace("\n", " ").strip()
        status = ""

        if chunk.token_count > chunk_size * 1.1:
            status = "  ⚠️  OVERSIZED"
            warnings += 1
        elif chunk.token_count < 20:
            status = "  ⚠️  TOO SMALL"
            warnings += 1

        print(
            f"  [{i:02d}] §{section:<25} "
            f"tokens={chunk.token_count:<5} "
            f"pos={chunk.position}{status}"
        )
        print(f"       preview: \"{preview}...\"")

    print_separator()
    if warnings == 0:
        print(f"  ✅ All chunks within expected range ({20}–{int(chunk_size * 1.1)} tokens)")
    else:
        print(f"  ⚠️  {warnings} chunk(s) outside expected range — consider adjusting chunk_size/overlap")
    print()


def check_real_file(file_path: str, chunk_size: int = 512, overlap: int = 64):
    path = Path(file_path)
    if not path.exists():
        print(f"❌ File not found: {file_path}")
        sys.exit(1)
    content = path.read_text(encoding="utf-8", errors="replace")
    source_type = "pdf" if path.suffix == ".pdf" else "markdown"
    doc = make_doc(path.stem, content, source_type)
    check_doc(doc, chunk_size, overlap)


# ── Main ──────────────────────────────────────────────────────────────────────

def main():
    parser = argparse.ArgumentParser(description="Sanity-check the RAG chunker")
    parser.add_argument("--file", help="Path to a real file to chunk (optional)")
    parser.add_argument("--chunk-size", type=int, default=512)
    parser.add_argument("--overlap", type=int, default=64)
    args = parser.parse_args()

    print("\n🔬 RAG Chunker — Sanity Check\n")

    if args.file:
        check_real_file(args.file, args.chunk_size, args.overlap)
    else:
        # Run against all 3 built-in samples
        check_doc(make_doc("Deployment Guide", SAMPLE_MARKDOWN), args.chunk_size, args.overlap)
        check_doc(make_doc("Plain Text Doc", SAMPLE_NO_HEADINGS), args.chunk_size, args.overlap)
        check_doc(make_doc("Short Doc", SAMPLE_SHORT), args.chunk_size, args.overlap)

    print("Done.")


if __name__ == "__main__":
    main()
