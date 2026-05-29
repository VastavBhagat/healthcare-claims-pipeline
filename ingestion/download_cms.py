"""
Downloads CMS Medicare Provider Utilization data from data.cms.gov.
Paginates through the full dataset, writes to JSONL, and validates row count + checksum.
"""

import json
import os
from pathlib import Path

import requests
from dotenv import load_dotenv

from utils import compute_checksum, get_logger, retry

load_dotenv()

logger = get_logger(__name__)

CMS_API_BASE = os.getenv("CMS_API_BASE_URL", "https://data.cms.gov/data-api/v1")
DATASET_UUID = os.getenv("CMS_DATASET_UUID")
PAGE_SIZE = 5000
MIN_EXPECTED_ROWS = 1000


@retry(max_attempts=3, backoff=2.0)
def fetch_page(offset: int, size: int = PAGE_SIZE) -> list:
    url = f"{CMS_API_BASE}/dataset/{DATASET_UUID}/data"
    resp = requests.get(url, params={"offset": offset, "size": size}, timeout=60)
    resp.raise_for_status()
    return resp.json()


def download_dataset(output_dir: str) -> Path:
    if not DATASET_UUID:
        raise ValueError("CMS_DATASET_UUID is not set in environment")

    output_path = Path(output_dir)
    output_path.mkdir(parents=True, exist_ok=True)
    output_file = output_path / "cms_claims_raw.jsonl"

    total = 0
    offset = 0

    with open(output_file, "w") as f:
        while True:
            page = fetch_page(offset)
            if not page:
                break
            for record in page:
                f.write(json.dumps(record) + "\n")
            total += len(page)
            offset += len(page)
            logger.info(f"Downloaded {total} records")

    logger.info(f"Saved to {output_file}")
    return output_file


def validate_download(file_path: Path) -> dict:
    row_count = sum(1 for _ in open(file_path))
    checksum = compute_checksum(str(file_path))

    if row_count < MIN_EXPECTED_ROWS:
        raise RuntimeError(
            f"Row count {row_count} is below the minimum expected {MIN_EXPECTED_ROWS}"
        )

    logger.info(f"Validation passed: {row_count} rows, checksum {checksum}")
    return {"row_count": row_count, "checksum": checksum, "file": str(file_path)}


if __name__ == "__main__":
    out = download_dataset("data/raw")
    stats = validate_download(out)
    print(stats)
