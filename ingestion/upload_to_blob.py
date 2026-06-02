import os
from pathlib import Path
from datetime import datetime, timezone
from azure.storage.blob import BlobServiceClient
from dotenv import load_dotenv
from utils import get_logger

load_dotenv(dotenv_path=Path(__file__).parent.parent / ".env")
logger = get_logger(__name__)

ACCOUNT_NAME   = os.getenv("AZURE_STORAGE_ACCOUNT")
ACCOUNT_KEY    = os.getenv("AZURE_STORAGE_KEY")
CONTAINER_NAME = os.getenv("AZURE_CONTAINER_NAME", "raw")


def upload_file_to_blob(local_path: Path, blob_folder: str = "cms") -> str:
    conn_str = (
        f"DefaultEndpointsProtocol=https;"
        f"AccountName={ACCOUNT_NAME};"
        f"AccountKey={ACCOUNT_KEY};"
        f"EndpointSuffix=core.windows.net"
    )

    client         = BlobServiceClient.from_connection_string(conn_str)
    container      = client.get_container_client(CONTAINER_NAME)
    date_partition = datetime.now(timezone.utc).strftime("%Y-%m-%d")
    blob_path      = f"{blob_folder}/{date_partition}/{local_path.name}"

    logger.info(f"Uploading → blob://{CONTAINER_NAME}/{blob_path}")
    with open(local_path, "rb") as data:
        container.upload_blob(name=blob_path, data=data, overwrite=True)

    logger.info("✅ Upload complete")
    return blob_path


if __name__ == "__main__":
    local_file = Path("data/raw/cms_medicare_raw.csv")

    if not local_file.exists():
        raise FileNotFoundError("Run download_cms.py first")

    blob_path = upload_file_to_blob(local_file)
    print(f"File available at: blob://{CONTAINER_NAME}/{blob_path}")