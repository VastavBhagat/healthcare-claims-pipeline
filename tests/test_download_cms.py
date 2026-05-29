import json
import os
import tempfile
from pathlib import Path
from unittest.mock import patch, MagicMock

import pytest

import sys
sys.path.insert(0, str(Path(__file__).parent.parent / "ingestion"))

import download_cms


def test_fetch_page_calls_correct_url(mocker):
    mock_resp = MagicMock()
    mock_resp.json.return_value = [{"npi": "123"}]
    mocker.patch("download_cms.requests.get", return_value=mock_resp)

    os.environ["CMS_DATASET_UUID"] = "test-uuid"
    result = download_cms.fetch_page(offset=0)

    assert result == [{"npi": "123"}]
    mock_resp.raise_for_status.assert_called_once()


def test_fetch_page_raises_on_http_error(mocker):
    import requests
    mock_resp = MagicMock()
    mock_resp.raise_for_status.side_effect = requests.HTTPError("404")
    mocker.patch("download_cms.requests.get", return_value=mock_resp)

    os.environ["CMS_DATASET_UUID"] = "test-uuid"
    with pytest.raises(requests.HTTPError):
        download_cms.fetch_page(offset=0)


def test_validate_download_passes_with_sufficient_rows(tmp_path, sample_cms_record):
    file_path = tmp_path / "test.jsonl"
    with open(file_path, "w") as f:
        for _ in range(2000):
            f.write(json.dumps(sample_cms_record) + "\n")

    result = download_cms.validate_download(file_path)
    assert result["row_count"] == 2000
    assert "checksum" in result


def test_validate_download_fails_below_minimum(tmp_path, sample_cms_record):
    file_path = tmp_path / "test.jsonl"
    with open(file_path, "w") as f:
        for _ in range(10):
            f.write(json.dumps(sample_cms_record) + "\n")

    with pytest.raises(RuntimeError, match="below the minimum"):
        download_cms.validate_download(file_path)
