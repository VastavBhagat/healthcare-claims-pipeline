"""
Uploads a local file to Azure Blob Storage.
Supports routing to raw/, staging/, or archive/ zones.
"""

import os
from pathlib import Path

from azure.storage.blob import BlobServiceClient
from dotenv import load_dotenv

from utils import get_logger

load_dotenv()

logger = get_logger(__name__)

ZONES = {"raw", "staging", "archive"}


def get_blob_client() -> BlobServiceClient:
    conn_str = os.getenv("AZURE_STORAGE_CONNECTION_STRING")
    if not conn_str:
        raise EnvironmentError("AZURE_STORAGE_CONNECTION_STRING is not set")
    return BlobServiceClient.from_connection_string(conn_str)


def upload_file(file_path: str, zone: str, blob_name: str = None) -> str:
    if zone not in ZONES:
        raise ValueError(f"zone must be one of {ZONES}, got '{zone}'")

    container = os.getenv(f"AZURE_CONTAINER_{zone.upper()}", zone)
    blob_name = blob_name or Path(file_path).name

    client = get_blob_client()
    blob_client = client.get_blob_client(container=container, blob=blob_name)

    with open(file_path, "rb") as data:
        blob_client.upload_blob(data, overwrite=True)

    url = blob_client.url
    logger.info(f"Uploaded {file_path} -> {container}/{blob_name}")
    return url


def move_to_archive(blob_name: str) -> None:
    """Copy a blob from raw to archive then delete the raw copy."""
    client = get_blob_client()
    raw_container = os.getenv("AZURE_CONTAINER_RAW", "raw")
    archive_container = os.getenv("AZURE_CONTAINER_ARCHIVE", "archive")

    source = client.get_blob_client(container=raw_container, blob=blob_name)
    dest = client.get_blob_client(container=archive_container, blob=blob_name)

    dest.start_copy_from_url(source.url)
    source.delete_blob()

    logger.info(f"Archived {blob_name} from {raw_container} to {archive_container}")


if __name__ == "__main__":
    import sys
    file_path = sys.argv[1]
    zone = sys.argv[2] if len(sys.argv) > 2 else "raw"
    url = upload_file(file_path, zone)
    print(f"Uploaded to: {url}")
