"""
CLI entry point for the ingestion pipeline.

Usage:
  python -m ingestion.ingest --source-config config/sources.yaml

What it does:
  1. Reads sources.yaml to get configured doc sources
  2. For each enabled source, picks the right loader
  3. Loads and normalizes docs into Document objects
  4. Saves them to the SQLite staging store (skips unchanged docs)
  5. Prints a summary of what was loaded / skipped / failed

Run this before chunking and indexing:
  Pipeline: ingest → chunk → embed → index
"""

import argparse
import asyncio
import sys
import time
from pathlib import Path

import structlog
import yaml

from db.database import init_db
from ingestion.loaders import get_loader
from ingestion.staging import init_staging_store, save_document, get_staged_count
from db.database import AsyncSessionLocal

logger = structlog.get_logger()


def load_config(config_path: str) -> dict:
    """Read and parse sources.yaml."""
    path = Path(config_path)
    if not path.exists():
        logger.error("ingest.config_not_found", path=config_path)
        sys.exit(1)
    with open(path) as f:
        return yaml.safe_load(f)


async def run_ingestion(config_path: str):
    """Main async ingestion loop."""

    # Init DB tables
    await init_db()
    await init_staging_store()

    config = load_config(config_path)
    sources = config.get("sources", [])

    total_loaded = 0
    total_skipped = 0
    total_failed = 0
    start = time.time()

    async with AsyncSessionLocal() as session:
        for source in sources:
            name = source.get("name", "unnamed")
            source_type = source.get("type", "?")
            enabled = source.get("enabled", True)

            if not enabled:
                logger.info("ingest.source_skipped", name=name, reason="disabled in config")
                continue

            logger.info("ingest.source_start", name=name, type=source_type)

            try:
                loader = get_loader(source)
            except ValueError as e:
                logger.error("ingest.loader_error", name=name, error=str(e))
                total_failed += 1
                continue

            source_loaded = 0
            source_skipped = 0

            for doc in loader.load():
                try:
                    was_new_or_updated = await save_document(doc, session)
                    if was_new_or_updated:
                        source_loaded += 1
                        total_loaded += 1
                    else:
                        source_skipped += 1
                        total_skipped += 1
                except Exception as e:
                    logger.error(
                        "ingest.save_error",
                        doc_id=doc.id,
                        title=doc.title,
                        error=str(e),
                    )
                    total_failed += 1

            logger.info(
                "ingest.source_done",
                name=name,
                loaded=source_loaded,
                skipped=source_skipped,
            )

    elapsed = round(time.time() - start, 2)

    # Final summary
    async with AsyncSessionLocal() as session:
        total_in_store = await get_staged_count(session)

    print("\n" + "=" * 50)
    print("  INGESTION COMPLETE")
    print("=" * 50)
    print(f"  ✅ New / updated : {total_loaded}")
    print(f"  ⏭️  Unchanged     : {total_skipped}")
    print(f"  ❌ Failed        : {total_failed}")
    print(f"  📦 Total in store: {total_in_store}")
    print(f"  ⏱️  Time          : {elapsed}s")
    print("=" * 50)
    print("  Next step: make index  (chunk + embed + vectorize)")
    print("=" * 50 + "\n")


def main():
    parser = argparse.ArgumentParser(
        description="RAG ingestion pipeline — loads docs into staging store"
    )
    parser.add_argument(
        "--source-config",
        default="config/sources.yaml",
        help="Path to sources.yaml (default: config/sources.yaml)",
    )
    args = parser.parse_args()
    asyncio.run(run_ingestion(args.source_config))


if __name__ == "__main__":
    main()
