"""HTTP/FTP download utilities for data ingestion."""

import time
from pathlib import Path
from typing import Any

import requests


def fetch_with_retry(
    url: str,
    params: dict[str, Any] | None = None,
    max_retries: int = 3,
    timeout: int = 120,
) -> dict[str, Any]:
    """
    Fetch JSON data from URL with retry logic for transient failures.

    Args:
        url: URL to fetch
        params: Optional query parameters
        max_retries: Maximum number of retry attempts
        timeout: Request timeout in seconds

    Returns:
        Parsed JSON response

    Raises:
        requests.exceptions.RequestException: If all retries fail
    """
    for attempt in range(max_retries):
        try:
            response = requests.get(url, params=params, timeout=timeout)
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            if attempt < max_retries - 1:
                wait_time = 2**attempt  # Exponential backoff: 1, 2, 4 seconds
                print(f"  Request failed, retrying in {wait_time}s... ({e})")
                time.sleep(wait_time)
            else:
                raise
    return {}


def download_file(
    url: str,
    output_path: Path,
    chunk_size: int = 8192,
    timeout: int = 300,
) -> Path:
    """
    Download a file from URL to local path.

    Args:
        url: URL to download from
        output_path: Local path to save file
        chunk_size: Download chunk size in bytes
        timeout: Request timeout in seconds

    Returns:
        Path to downloaded file

    Raises:
        requests.exceptions.RequestException: If download fails
    """
    output_path = Path(output_path)
    output_path.parent.mkdir(parents=True, exist_ok=True)

    response = requests.get(url, stream=True, timeout=timeout)
    response.raise_for_status()

    with open(output_path, "wb") as f:
        for chunk in response.iter_content(chunk_size=chunk_size):
            f.write(chunk)

    return output_path
