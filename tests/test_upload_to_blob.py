import os
import tempfile
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

import sys
sys.path.insert(0, str(Path(__file__).parent.parent / "ingestion"))

import upload_to_blob


def test_upload_file_calls_blob_client(mock_blob_service, tmp_path):
    test_file = tmp_path / "test.jsonl"
    test_file.write_text("test content")
    os.environ["AZURE_STORAGE_CONNECTION_STRING"] = "fake-conn-string"
    os.environ["AZURE_CONTAINER_RAW"] = "raw"

    mock_blob_client = MagicMock()
    mock_blob_client.url = "https://fake.blob.core.windows.net/raw/test.jsonl"
    mock_blob_service.get_blob_client.return_value = mock_blob_client

    url = upload_to_blob.upload_file(str(test_file), zone="raw")

    assert url == "https://fake.blob.core.windows.net/raw/test.jsonl"
    mock_blob_client.upload_blob.assert_called_once()


def test_upload_file_rejects_invalid_zone(tmp_path):
    test_file = tmp_path / "test.jsonl"
    test_file.write_text("x")

    with pytest.raises(ValueError, match="zone must be one of"):
        upload_to_blob.upload_file(str(test_file), zone="invalid")


def test_upload_file_raises_without_connection_string(tmp_path, monkeypatch):
    monkeypatch.delenv("AZURE_STORAGE_CONNECTION_STRING", raising=False)
    test_file = tmp_path / "test.jsonl"
    test_file.write_text("x")

    with pytest.raises(EnvironmentError):
        upload_to_blob.upload_file(str(test_file), zone="raw")
