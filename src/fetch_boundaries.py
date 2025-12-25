"""Fetch Local Authority District boundaries from ONS ArcGIS FeatureServer."""

import json
import time
from pathlib import Path

import requests

# BGC = Generalised Clipped (smaller, faster than BFE Full Extent)
ARCGIS_URL = (
    "https://services1.arcgis.com/ESMARspQHYMw9BZ9/arcgis/rest/services/"
    "Local_Authority_Districts_May_2024_Boundaries_UK_BGC/FeatureServer/0/query"
)

# Fallback to Super Generalised if BGC fails
ARCGIS_URL_FALLBACK = (
    "https://services1.arcgis.com/ESMARspQHYMw9BZ9/arcgis/rest/services/"
    "Local_Authority_Districts_May_2024_Boundaries_UK_BSC/FeatureServer/0/query"
)


def _fetch_with_retry(url: str, params: dict, max_retries: int = 3) -> dict:
    """Fetch data with retry logic for transient failures."""
    for attempt in range(max_retries):
        try:
            response = requests.get(url, params=params, timeout=120)
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


def fetch_lad_boundaries_2024(output_path: Path | None = None) -> dict:
    """
    Fetch LAD May 2024 boundaries from ONS ArcGIS FeatureServer.

    Uses Generalised Clipped (BGC) boundaries which are smaller and faster
    than Full Extent (BFE). Falls back to Super Generalised (BSC) if needed.

    Args:
        output_path: Optional path to save GeoJSON file

    Returns:
        GeoJSON FeatureCollection dict
    """
    print("Fetching LAD 2024 boundaries from ONS ArcGIS...")

    # Try BGC first, then BSC as fallback
    urls_to_try = [
        ("Generalised Clipped (BGC)", ARCGIS_URL),
        ("Super Generalised (BSC)", ARCGIS_URL_FALLBACK),
    ]

    for name, url in urls_to_try:
        try:
            print(f"  Trying {name} boundaries...")
            all_features = []
            offset = 0
            batch_size = 500  # Smaller batches for reliability

            while True:
                params = {
                    "where": "1=1",
                    "outFields": "LAD24CD,LAD24NM",
                    "f": "geojson",
                    "outSR": "4326",  # WGS84 for GeoJSON compatibility
                    "resultOffset": offset,
                    "resultRecordCount": batch_size,
                }

                data = _fetch_with_retry(url, params)
                features = data.get("features", [])
                if not features:
                    break

                all_features.extend(features)
                print(f"  Fetched {len(all_features)} boundaries...")

                if len(features) < batch_size:
                    break
                offset += batch_size

            if all_features:
                geojson = {
                    "type": "FeatureCollection",
                    "features": all_features,
                }
                print(f"Total: {len(all_features)} LAD boundaries fetched using {name}")

                if output_path:
                    output_path = Path(output_path)
                    output_path.parent.mkdir(parents=True, exist_ok=True)
                    with open(output_path, "w") as f:
                        json.dump(geojson, f)
                    print(f"Saved to {output_path}")

                return geojson

        except requests.exceptions.RequestException as e:
            print(f"  Failed with {name}: {e}")
            continue

    raise RuntimeError("Failed to fetch boundaries from all available sources")


if __name__ == "__main__":
    from config import BOUNDARIES_FILE

    fetch_lad_boundaries_2024(BOUNDARIES_FILE)
