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
import json
import logging
import re
import sys
import subprocess
from pathlib import Path
from typing import Any

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


def document_content_html_paths(docket_dir: Path) -> list[tuple[str, Path]]:
    """
    Return (document_id, path) for each ``*_content.htm`` under ``raw-data/documents/``.

    Pairs with regulations.gov JSON exports named like ``<document_id>.json`` (e.g.
    ``FAA-2025-0618-0001_content.htm`` → document id ``FAA-2025-0618-0001``).
    """
    docs_dir = docket_dir / "raw-data" / "documents"
    if not docs_dir.is_dir():
        return []
    out: list[tuple[str, Path]] = []
    for path in sorted(docs_dir.glob("*_content.htm")):
        doc_id = path.name.removesuffix("_content.htm")
        if doc_id:
            out.append((doc_id, path))
    return out


def read_document_content_html(docket_dir: Path) -> dict[str, str]:
    """Read UTF-8 text from each ``*_content.htm`` file; map ``document_id`` → HTML body."""
    result: dict[str, str] = {}
    for doc_id, path in document_content_html_paths(docket_dir):
        try:
            result[doc_id] = path.read_text(encoding="utf-8")
        except OSError as exc:
            log.warning("Could not read %s: %s", path, exc)
    return result


def extracted_txt_dir(docket_dir: Path) -> Path | None:
    """
    Resolve ``.../extracted_txt`` under ``derived-data`` if present.

    Tries, in order:

    - ``derived-data/mirrulations/extracted_txt`` (common local mirrulations-fetch layout)
    - ``derived-data/<agency>/<docket_id>/extracted_txt`` (S3-style; agency = segment before
      first ``-`` in the docket folder name)
    - Any ``derived-data/**/extracted_txt`` directory (first match)
    """
    candidates: list[Path] = [
        docket_dir / "derived-data" / "mirrulations" / "extracted_txt",
    ]
    did = docket_dir.name
    if "-" in did:
        agency = did.split("-", 1)[0]
        candidates.append(docket_dir / "derived-data" / agency / did / "extracted_txt")
    for p in candidates:
        if p.is_dir():
            return p
    derived = docket_dir / "derived-data"
    if derived.is_dir():
        for p in sorted(derived.rglob("extracted_txt")):
            if p.is_dir():
                return p
    return None


def iter_extracted_txt_json_files(docket_dir: Path) -> list[Path]:
    """Paths to ``*.json`` under the resolved ``extracted_txt`` tree (recursive)."""
    root = extracted_txt_dir(docket_dir)
    if not root:
        return []
    return sorted(p for p in root.rglob("*.json") if p.is_file())


_EXTRACTED_PLAIN_NAME = re.compile(
    r"^(?P<comment_id>.+)_attachment_(?P<attach>\d+)_extracted\.txt$",
    re.IGNORECASE,
)


def iter_extracted_plain_txt_files(docket_dir: Path) -> list[Path]:
    """
    Paths to ``*_extracted.txt`` under ``extracted_txt`` (e.g.
    ``.../extracted_txt/comments_extracted_text/pypdf/FAA-...-0007_attachment_1_extracted.txt``).
    """
    root = extracted_txt_dir(docket_dir)
    if not root:
        return []
    return sorted(p for p in root.rglob("*_extracted.txt") if p.is_file())


def read_derived_extracted_plain_text(docket_dir: Path) -> list[dict[str, Any]]:
    """
    Load plain-text extractions (PDF attachment text). Filenames must look like
    ``<commentId>_attachment_<n>_extracted.txt``. ``extractedMethod`` is taken from the parent
    directory name (e.g. ``pypdf``).
    """
    docket_id = docket_dir.name
    out: list[dict[str, Any]] = []
    for path in iter_extracted_plain_txt_files(docket_dir):
        m = _EXTRACTED_PLAIN_NAME.match(path.name)
        if not m:
            log.warning(
                "Skipping %s (expected <commentId>_attachment_<n>_extracted.txt)",
                path,
            )
            continue
        comment_id = m.group("comment_id")
        attach_n = int(m.group("attach"))
        method = path.parent.name
        try:
            text = path.read_text(encoding="utf-8")
        except OSError as exc:
            log.warning("Could not read %s: %s", path, exc)
            continue
        out.append(
            {
                "docketId": docket_id,
                "commentId": comment_id,
                "attachmentId": f"{comment_id}_attachment_{attach_n}",
                "extractedMethod": method,
                "extractedText": text,
            }
        )
    return out


def read_derived_extracted_text(docket_dir: Path) -> list[dict[str, Any]]:
    """
    Load extracted comment-attachment text from ``derived-data/.../extracted_txt``:

    - ``*.json`` — one object or a JSON array per file
    - ``*_extracted.txt`` — plain text (e.g. under ``comments_extracted_text/pypdf/``)
    """
    records: list[dict[str, Any]] = []
    for path in iter_extracted_txt_json_files(docket_dir):
        try:
            data = json.loads(path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError) as exc:
            log.warning("Could not read or parse %s: %s", path, exc)
            continue
        if isinstance(data, dict):
            records.append(data)
        elif isinstance(data, list):
            records.extend(x for x in data if isinstance(x, dict))
    records.extend(read_derived_extracted_plain_text(docket_dir))
    return records


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

    html_by_doc = read_document_content_html(docket_dir)
    if html_by_doc:
        log.info(
            "Read %d document HTML file(s): %s",
            len(html_by_doc),
            ", ".join(sorted(html_by_doc)),
        )

    extracted_records = read_derived_extracted_text(docket_dir)
    if extracted_records:
        log.info("Read %d derived extracted-text record(s)", len(extracted_records))

    if args.dry_run:
        ingest_into_postgresql_dry_run(docket_dir, args)
    else:
        ingest_into_postgresql(docket_dir, args)
    ingest_htm_files(docket_dir, get_opensearch_connection())

def ingest_into_postgresql_dry_run(docket_dir: Path, args: argparse.Namespace) -> None:
    # Dry run only (no DB connection needed)
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


if __name__ == "__main__":
    main()
