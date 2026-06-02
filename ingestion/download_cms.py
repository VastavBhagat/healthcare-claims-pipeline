import requests
import hashlib
import pandas as pd
from pathlib import Path
from dotenv import load_dotenv
from utils import get_logger

load_dotenv(dotenv_path=Path(__file__).parent.parent / ".env")
logger = get_logger(__name__)

CMS_BASE_URL = "https://data.cms.gov/data-api/v1/dataset"
DATASET_ID   = "9767cb68-8ea9-4f0b-8179-9431abc89f11"
OUTPUT_DIR   = Path("data/raw")
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)


def download_cms_data(limit: int = 5000, offset: int = 0) -> list:
    url    = f"{CMS_BASE_URL}/{DATASET_ID}/data"
    params = {"limit": limit, "offset": offset}

    logger.info(f"Fetching CMS records — offset={offset}, limit={limit}")
    response = requests.get(url, params=params, timeout=30)
    response.raise_for_status()

    records = response.json()
    logger.info(f"Fetched {len(records)} records")
    return records


def save_to_csv(records: list, filename: str) -> Path:
    df       = pd.DataFrame(records)
    filepath = OUTPUT_DIR / filename
    df.to_csv(filepath, index=False)
    logger.info(f"Saved {len(df)} rows → {filepath}")
    return filepath


def compute_checksum(filepath: Path) -> str:
    md5 = hashlib.md5()
    with open(filepath, "rb") as f:
        for chunk in iter(lambda: f.read(8192), b""):
            md5.update(chunk)
    return md5.hexdigest()


if __name__ == "__main__":
    records  = download_cms_data(limit=5000, offset=0)

    if not records:
        logger.error("No records returned from CMS API")
        raise SystemExit(1)

    filepath = save_to_csv(records, "cms_medicare_raw.csv")
    checksum = compute_checksum(filepath)

    logger.info(f"✅ Done — {len(records)} rows | checksum: {checksum}")