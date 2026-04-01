#!/usr/bin/env python3
"""
Fetch docket data using mirrulations-fetch and ingest it into PostgreSQL.

This script combines mirrulations-fetch (to download docket data) with the 
ingest_docket module to load data into the database.

Usage:
    python db/ingest.py FAA-2025-0618
    python db/ingest.py --help
"""
from __future__ import annotations

import argparse
import logging
import sys
import subprocess
from pathlib import Path

# Allow `python db/ingest.py` from repo root without PYTHONPATH.
_ROOT = Path(__file__).resolve().parent.parent
_src = _ROOT / "src"
if _src.is_dir() and str(_src) not in sys.path:
    sys.path.insert(0, str(_src))

try:
    from dotenv import load_dotenv
except ImportError:
    load_dotenv = None

from mirrsearch.db import get_opensearch_connection

from ingest_docket import (
    ingest_docket_and_documents,
    ingest_comments,
    _ingest_summary,
    _require_ingest_schema,
    _ensure_comments_document_fk,
)
import psycopg2

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
)
log = logging.getLogger(__name__)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Fetch docket data using mirrulations-fetch and ingest into PostgreSQL."
    )
    parser.add_argument(
        "docket_id",
        help="Docket ID (e.g., FAA-2025-0618)",
    )
    parser.add_argument(
        "--output-dir",
        default=".",
        help="Output directory for fetched data (default: current directory)",
    )
    parser.add_argument(
        "--skip-fetch",
        action="store_true",
        help="Skip the fetch step (data already exists)",
    )
    parser.add_argument(
        "--skip-comments-ingest",
        action="store_true",
        help="Skip ingesting comments",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Dry run — validate data without writing to database",
    )
    parser.add_argument(
        "--host",
        default="localhost",
        help="PostgreSQL host (default: localhost)",
    )
    parser.add_argument(
        "--port",
        type=int,
        default=5432,
        help="PostgreSQL port (default: 5432)",
    )
    parser.add_argument(
        "--dbname",
        default="mirrulations",
        help="PostgreSQL database name (default: mirrulations)",
    )
    parser.add_argument(
        "--user",
        default="postgres",
        help="PostgreSQL user (default: postgres)",
    )
    parser.add_argument(
        "--password",
        help="PostgreSQL password",
    )
    return parser.parse_args()


def fetch_docket(docket_id: str, output_dir: str) -> Path:
    """Use mirrulations-fetch to download docket data."""
    log.info("Fetching docket data for %s using mirrulations-fetch...", docket_id)
    try:
        result = subprocess.run(
            ["mirrulations-fetch", docket_id],
            cwd=output_dir,
            capture_output=True,
            text=True,
            check=True,
        )
        log.info("Fetch completed successfully")
        docket_path = Path(output_dir) / docket_id
        if not docket_path.exists():
            log.error("Expected docket directory not found: %s", docket_path)
            sys.exit(1)
        return docket_path
    except subprocess.CalledProcessError as e:
        log.error("Fetch failed: %s", e.stderr)
        sys.exit(1)
    except FileNotFoundError:
        log.error("mirrulations-fetch not found. Install it via: pip install mirrulations-fetch")
        sys.exit(1)


def main():
    if load_dotenv:
        load_dotenv(Path(__file__).resolve().parent.parent / ".env")

    args = parse_args()
    docket_id = args.docket_id.strip().upper()

    # Fetch data if not skipping
    if not args.skip_fetch:
        docket_dir = fetch_docket(docket_id, args.output_dir)
    else:
        docket_dir = Path(args.output_dir) / docket_id
        if not docket_dir.exists():
            log.error("Docket directory not found: %s (use --skip-fetch=false to fetch)", docket_dir)
            sys.exit(1)

    log.info("Using docket directory: %s", docket_dir)

    if args.dry_run:
        ingest_into_postgresql_dry_run(docket_dir, args)
    else:
        ingest_into_postgresql(docket_dir, args)
    ingest_htm_files(docket_dir, get_opensearch_connection())

def ingest_into_postgresql_dry_run(docket_dir: Path, args: argparse.Namespace) -> None:
    # Dry run only (no DB connection needed)
    log.info("DRY RUN — no database writes.")
    ok, n_doc, sk, fetched_docket_id = ingest_docket_and_documents(docket_dir, conn=None, dry_run=True)
    pc, cs = (0, 0)
    if ok and not args.skip_comments_ingest:
        pc, cs = ingest_comments(docket_dir, conn=None, dry_run=True)
    if ok:
        log.info("Done. Documents (this run): %d upserted, %d skipped", n_doc, sk)
        if not args.skip_comments_ingest:
            log.info("Comments (this run): %d processed, %d skipped", pc, cs)
        _ingest_summary(
            docket_dir,
            fetched_docket_id,
            None,
            dry_run=True,
            skip_comments_ingest=args.skip_comments_ingest,
        )
    else:
        sys.exit(1)
    return
    

def ingest_into_postgresql(docket_dir: Path, args: argparse.Namespace) -> None:
    # Connect to database and ingest
    log.info("Connecting to PostgreSQL at %s:%d/%s…", args.host, args.port, args.dbname)
    try:
        conn = psycopg2.connect(
            host=args.host,
            port=args.port,
            dbname=args.dbname,
            user=args.user,
            password=args.password or None,
        )
    except psycopg2.OperationalError as exc:
        log.error("Could not connect to database: %s", exc)
        sys.exit(1)

    _require_ingest_schema(conn, args)
    _ensure_comments_document_fk(conn)

    try:
        ok, n_doc, sk, fetched_docket_id = ingest_docket_and_documents(docket_dir, conn, dry_run=False)
        pc, cs = (0, 0)
        if ok and not args.skip_comments_ingest:
            pc, cs = ingest_comments(docket_dir, conn, dry_run=False)
        if ok:
            log.info("Done. Documents (this run): %d upserted, %d skipped", n_doc, sk)
            if not args.skip_comments_ingest:
                log.info("Comments (this run): %d processed, %d skipped", pc, cs)
            _ingest_summary(
                docket_dir,
                fetched_docket_id,
                conn,
                dry_run=False,
                skip_comments_ingest=args.skip_comments_ingest,
            )
        else:
            sys.exit(1)
    finally:
        conn.close()

def get_htm_files(docket_dir: Path) -> list[dict[str, str]]:
    """Get all .htm or .html files in the docket directory."""
    list_htms = list(docket_dir.glob("raw-data/documents/**/*.htm")) + list(docket_dir.glob("raw-data/documents/**/*.html"))
    htm_texts = []
    for htm_file in list_htms:
        try:
            text = htm_file.read_text(encoding="utf-8", errors="ignore")
            document_id_from_htm = get_document_ID(htm_file)  # Assuming document ID is the parent directory name
            htm_texts.append((text, document_id_from_htm))
        except Exception as e:
            log.warning("Could not read file %s: %s", htm_file, e)
    docket_id = get_docket_ID(docket_dir)
    return [{"docketId": docket_id, "documentHtm": text, "documentId": document_id} for text, document_id in htm_texts]

def get_docket_ID(docket_dir: Path) -> str:
    """Extract docket ID from the directory name."""
    return docket_dir.name.strip()

def get_document_ID(docket_dir: Path) -> str:
    """Extract document ID from the directory name."""
    return docket_dir.name.strip()

def ingest_htm_files(htm_path: Path, client) -> None:
    """Ingest HTM file data into OpenSearch documents index."""
    documents_text = get_htm_files(htm_path)
    
    if not documents_text:
        log.info("No HTM files found in %s", htm_path)
        return
    
    log.info("Ingesting %d HTM document(s) into OpenSearch...", len(documents_text))
    
    try:
        # Bulk ingest documents into the "documents" index
        for idx, doc in enumerate(documents_text, 1):
            doc_id = doc['documentId']
            document = {
                "docketId": doc["docketId"],
                "documentId": doc["documentId"],
                "documentText": doc["documentHtm"],
            }
            client.index(
                index="documents",
                id=doc_id,
                body=document,
            )
            if idx % 10 == 0:
                log.info("Ingested %d/%d documents", idx, len(documents_text))
        
        log.info("Successfully ingested %d HTM document(s) into OpenSearch", len(documents_text))
    except Exception as e:
        log.error("Failed to ingest HTM files into OpenSearch: %s", e)
        raise


if __name__ == "__main__":
    main()
