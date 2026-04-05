"""
Tests for the ingest.py module - Testing OpenSearch ingest, PostgreSQL ingest, and file fetching.
"""
import sys
import tempfile
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

# Add db directory to path for imports BEFORE importing ingest module
sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "db"))

# pylint: disable=wrong-import-position,import-error
from ingest import (
    get_htm_files,
    ingest_htm_files,
    fetch_docket,
    get_docket_ID,
    get_document_ID,
)
# pylint: enable=wrong-import-position,import-error


class TestFetchDocket:
    """Test docket file fetching functionality."""

    @patch('ingest.subprocess.run')
    def test_fetch_docket_success(self, mock_run):
        """Successfully fetch docket using mirrulations-fetch."""
        mock_run.return_value = MagicMock(returncode=0)

        with tempfile.TemporaryDirectory() as tmpdir:
            # Create the expected docket directory
            docket_dir = Path(tmpdir) / "FAA-2025-0618"
            docket_dir.mkdir()

            result = fetch_docket("FAA-2025-0618", tmpdir)

            # Verify subprocess was called correctly
            mock_run.assert_called_once()
            args = mock_run.call_args
            assert "mirrulations-fetch" in args[0][0]
            assert "FAA-2025-0618" in args[0][0]
            assert result == docket_dir

    @patch('ingest.subprocess.run')
    def test_fetch_docket_not_found(self, mock_run):
        """Handle missing docket directory after fetch."""
        mock_run.return_value = MagicMock(returncode=0)

        with tempfile.TemporaryDirectory() as tmpdir:
            # Don't create the directory - simulate fetch failure
            with pytest.raises(SystemExit):
                fetch_docket("MISSING-2025-0001", tmpdir)

    @patch('ingest.subprocess.run')
    def test_fetch_docket_subprocess_error(self, mock_run):
        """Handle subprocess errors during fetch."""
        mock_run.side_effect = FileNotFoundError("mirrulations-fetch not found")

        with tempfile.TemporaryDirectory() as tmpdir:
            with pytest.raises(SystemExit):
                fetch_docket("FAA-2025-0618", tmpdir)

    @patch('ingest.subprocess.run')
    def test_fetch_docket_calculates_correct_path(self, mock_run):
        """Verify fetch_docket returns correct path."""
        mock_run.return_value = MagicMock(returncode=0)

        with tempfile.TemporaryDirectory() as tmpdir:
            docket_dir = Path(tmpdir) / "CMS-2025-0240"
            docket_dir.mkdir()

            result = fetch_docket("CMS-2025-0240", tmpdir)

            assert result.name == "CMS-2025-0240"
            assert result.parent == Path(tmpdir)


class TestIngestOpenSearch:
    """Test OpenSearch ingestion functionality."""

    def test_ingest_single_htm_file_to_opensearch(self):
        """Ingest a single HTM file into OpenSearch."""
        with tempfile.TemporaryDirectory() as tmpdir:
            docket_dir = Path(tmpdir) / "FAA-2025-0618"
            docs_dir = docket_dir / "raw-data" / "documents"
            docs_dir.mkdir(parents=True)

            # Create test HTM file
            htm_file = docs_dir / "FAA-2025-0618-0001_content.htm"
            htm_file.write_text("<html><body>Airworthiness Directive</body></html>")

            # Mock OpenSearch client
            mock_client = MagicMock()

            ingest_htm_files(docket_dir, mock_client)

            # Verify OpenSearch index was called
            mock_client.index.assert_called_once()
            call_kwargs = mock_client.index.call_args[1]

            assert call_kwargs["index"] == "documents"
            assert call_kwargs["id"] == "FAA-2025-0618-0001_content.htm"
            assert call_kwargs["body"]["docketId"] == "FAA-2025-0618"
            assert call_kwargs["body"]["documentId"] == "FAA-2025-0618-0001_content.htm"
            assert "Airworthiness" in call_kwargs["body"]["documentText"]

    def test_ingest_multiple_htm_files_to_opensearch(self):
        """Ingest multiple HTM files into OpenSearch."""
        with tempfile.TemporaryDirectory() as tmpdir:
            docket_dir = Path(tmpdir) / "CMS-2025-0240"
            docs_dir = docket_dir / "raw-data" / "documents"
            docs_dir.mkdir(parents=True)

            # Create multiple HTM files
            for i in range(1, 4):
                htm_file = docs_dir / f"CMS-2025-0240-000{i}_content.htm"
                htm_file.write_text(f"<html><body>Document {i}</body></html>")

            mock_client = MagicMock()
            ingest_htm_files(docket_dir, mock_client)

            # Verify all documents were indexed
            assert mock_client.index.call_count == 3

            # Verify document IDs are correct
            doc_ids = [call[1]["id"] for call in mock_client.index.call_args_list]
            assert "CMS-2025-0240-0001_content.htm" in doc_ids
            assert "CMS-2025-0240-0002_content.htm" in doc_ids
            assert "CMS-2025-0240-0003_content.htm" in doc_ids

    def test_ingest_handles_missing_opensearch(self):
        """Handle OpenSearch connection errors gracefully."""
        with tempfile.TemporaryDirectory() as tmpdir:
            docket_dir = Path(tmpdir) / "FAIL-2025-0001"
            docs_dir = docket_dir / "raw-data" / "documents"
            docs_dir.mkdir(parents=True)

            htm_file = docs_dir / "doc.htm"
            htm_file.write_text("<html>Test</html>")

            mock_client = MagicMock()
            mock_client.index.side_effect = Exception("OpenSearch connection failed")

            with pytest.raises(Exception):
                ingest_htm_files(docket_dir, mock_client)

    def test_opensearch_document_structure(self):
        """Verify correct document structure for OpenSearch."""
        with tempfile.TemporaryDirectory() as tmpdir:
            docket_dir = Path(tmpdir) / "OSHA-2025-0005"
            docs_dir = docket_dir / "raw-data" / "documents"
            docs_dir.mkdir(parents=True)

            htm_file = docs_dir / "safety_doc.htm"
            htm_file.write_text("<html><body>Safety content</body></html>")

            mock_client = MagicMock()
            ingest_htm_files(docket_dir, mock_client)

            body = mock_client.index.call_args[1]["body"]

            # Verify required fields exist
            assert "docketId" in body
            assert "documentId" in body
            assert "documentText" in body

            # Verify field values
            assert body["docketId"] == "OSHA-2025-0005"
            assert body["documentId"] == "safety_doc.htm"
            assert body["documentText"] == "<html><body>Safety content</body></html>"


class TestFileDiscovery:
    """Test HTM file discovery and reading functionality."""

    def test_discover_htm_files_in_documents_directory(self):
        """Discover all HTM files in documents directory."""
        with tempfile.TemporaryDirectory() as tmpdir:
            docket_dir = Path(tmpdir) / "FAA-2025-0618"
            docs_dir = docket_dir / "raw-data" / "documents"
            docs_dir.mkdir(parents=True)

            # Create HTM files
            (docs_dir / "doc1.htm").write_text("<html>1</html>")
            (docs_dir / "doc2.htm").write_text("<html>2</html>")

            files = get_htm_files(docket_dir)

            assert len(files) == 2
            assert all(f["docketId"] == "FAA-2025-0618" for f in files)

    def test_discover_html_files_as_well(self):
        """Discover both .htm and .html file extensions."""
        with tempfile.TemporaryDirectory() as tmpdir:
            docket_dir = Path(tmpdir) / "TEST-2025-0001"
            docs_dir = docket_dir / "raw-data" / "documents"
            docs_dir.mkdir(parents=True)

            (docs_dir / "file1.htm").write_text("<html>HTM</html>")
            (docs_dir / "file2.html").write_text("<html>HTML</html>")

            files = get_htm_files(docket_dir)

            assert len(files) == 2
            doc_ids = [f["documentId"] for f in files]
            assert "file1.htm" in doc_ids
            assert "file2.html" in doc_ids

    def test_discover_nested_documents(self):
        """Discover HTM files in nested subdirectories."""
        with tempfile.TemporaryDirectory() as tmpdir:
            docket_dir = Path(tmpdir) / "NESTED-2025-0001"
            docs_dir = docket_dir / "raw-data" / "documents"
            subdir = docs_dir / "subfolder" / "deepfolder"
            subdir.mkdir(parents=True)

            (subdir / "nested_doc.htm").write_text("<html>Nested</html>")
            (docs_dir / "top_doc.htm").write_text("<html>Top</html>")

            files = get_htm_files(docket_dir)

            assert len(files) == 2
            doc_ids = [f["documentId"] for f in files]
            assert "nested_doc.htm" in doc_ids
            assert "top_doc.htm" in doc_ids

    def test_read_file_content_correctly(self):
        """Verify HTM file content is read correctly."""
        with tempfile.TemporaryDirectory() as tmpdir:
            docket_dir = Path(tmpdir) / "CONTENT-2025-0001"
            docs_dir = docket_dir / "raw-data" / "documents"
            docs_dir.mkdir(parents=True)

            expected_content = (
                "<html><head><title>Test</title></head>"
                "<body>Content</body></html>"
            )
            (docs_dir / "test.htm").write_text(expected_content)

            files = get_htm_files(docket_dir)

            assert len(files) == 1
            assert files[0]["documentHtm"] == expected_content

    def test_handle_non_htm_files(self):
        """Ignore non-HTM/HTML files in documents directory."""
        with tempfile.TemporaryDirectory() as tmpdir:
            docket_dir = Path(tmpdir) / "MIXED-2025-0001"
            docs_dir = docket_dir / "raw-data" / "documents"
            docs_dir.mkdir(parents=True)

            (docs_dir / "document.htm").write_text("<html>HTM</html>")
            (docs_dir / "readme.txt").write_text("Text file")
            (docs_dir / "data.json").write_text('{"key": "value"}')
            (docs_dir / "file.pdf").write_text("PDF content")

            files = get_htm_files(docket_dir)

            assert len(files) == 1
            assert files[0]["documentId"] == "document.htm"


class TestIntegration:
    """Integration tests for full ingest workflow."""

    @patch('ingest.subprocess.run')
    def test_full_workflow_fetch_then_ingest(self, mock_run):
        """Test complete workflow: fetch docket, then ingest HTM files."""
        mock_run.return_value = MagicMock(returncode=0)

        with tempfile.TemporaryDirectory() as tmpdir:
            # Setup: Create docket structure as if fetch succeeded
            docket_dir = Path(tmpdir) / "FAA-2025-0618"
            docs_dir = docket_dir / "raw-data" / "documents"
            docs_dir.mkdir(parents=True)

            # Create HTM file to be ingested
            htm_file = docs_dir / "FAA-2025-0618-0001_content.htm"
            htm_file.write_text("<html><body>Airworthiness</body></html>")

            # Step 1: Fetch the docket
            fetched_path = fetch_docket("FAA-2025-0618", tmpdir)
            assert fetched_path.exists()

            # Step 2: Ingest HTM files to OpenSearch
            mock_client = MagicMock()
            ingest_htm_files(fetched_path, mock_client)

            # Verify ingestion occurred
            assert mock_client.index.called
            assert mock_client.index.call_count == 1

    def test_docket_id_extraction_from_path(self):
        """Verify docket ID extraction from directory path."""
        test_cases = [
            (Path("/path/FAA-2025-0618"), "FAA-2025-0618"),
            (Path("/path/CMS-2025-0240"), "CMS-2025-0240"),
            (Path("/path/OSHA-2025-0005"), "OSHA-2025-0005"),
        ]

        for path, expected_id in test_cases:
            result = get_docket_ID(path)
            assert result == expected_id

    def test_document_id_extraction_from_filename(self):
        """Verify document ID extraction from file path."""
        test_cases = [
            (
                Path("/path/FAA-2025-0618-0001_content.htm"),
                "FAA-2025-0618-0001_content.htm",
            ),
            (Path("/path/doc1.html"), "doc1.html"),
            (Path("/path/test_file.htm"), "test_file.htm"),
        ]

        for path, expected_id in test_cases:
            result = get_document_ID(path)
            assert result == expected_id
