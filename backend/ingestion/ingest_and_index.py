"""
Full pipeline entry point: ingest → chunk → embed → index.

This is what `make index` calls.

Usage:
  python -m ingestion.ingest_and_index --source-config config/sources.yaml
  python -m ingestion.ingest_and_index --force   # re-index everything
"""

import argparse
import asyncio

import structlog
import yaml

from db.database import init_db
from ingestion.ingest import run_ingestion
from ingestion.indexer import index_all_docs

logger = structlog.get_logger()


async def run_pipeline(source_config: str, force: bool = False):
    """Run ingestion then indexing end-to-end."""
    await init_db()

    print("\n📥 Step 1/2 — Ingestion")
    print("─" * 40)
    await run_ingestion(source_config)

    print("\n🔢 Step 2/2 — Embedding & Indexing")
    print("─" * 40)
    await index_all_docs(force=force)


def main():
    parser = argparse.ArgumentParser(
        description="Full RAG pipeline: ingest + chunk + embed + index"
    )
    parser.add_argument(
        "--source-config",
        default="config/sources.yaml",
        help="Path to sources.yaml",
    )
    parser.add_argument(
        "--force",
        action="store_true",
        help="Re-index all docs even if unchanged",
    )
    args = parser.parse_args()
    asyncio.run(run_pipeline(args.source_config, force=args.force))


if __name__ == "__main__":
    main()
