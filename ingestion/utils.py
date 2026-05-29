import hashlib
import logging
import time
from functools import wraps


def get_logger(name: str) -> logging.Logger:
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s  %(levelname)s  %(name)s  %(message)s",
    )
    return logging.getLogger(name)


def compute_checksum(file_path: str) -> str:
    sha256 = hashlib.sha256()
    with open(file_path, "rb") as f:
        for chunk in iter(lambda: f.read(8192), b""):
            sha256.update(chunk)
    return sha256.hexdigest()


def retry(max_attempts: int = 3, backoff: float = 2.0):
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            logger = get_logger(func.__module__)
            for attempt in range(1, max_attempts + 1):
                try:
                    return func(*args, **kwargs)
                except Exception as exc:
                    if attempt == max_attempts:
                        raise
                    wait = backoff ** attempt
                    logger.warning(
                        f"{func.__name__} attempt {attempt} failed: {exc}. "
                        f"Retrying in {wait:.0f}s"
                    )
                    time.sleep(wait)
        return wrapper
    return decorator
