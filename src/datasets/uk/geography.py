"""UK geographic data: Local Authority boundaries, TTWA lookups, etc.

Provides boundary files and geographic code crosswalks.
Source: https://geoportal.statistics.gov.uk/
"""

import json
from pathlib import Path
from typing import Any

import pandas as pd

from src.core.config import raw_path
from src.core.download import fetch_with_retry
from src.datasets.base import Dataset

# BGC = Generalised Clipped (smaller, faster than BFE Full Extent)
ARCGIS_URL_BGC = (
    "https://services1.arcgis.com/ESMARspQHYMw9BZ9/arcgis/rest/services/"
    "Local_Authority_Districts_May_2024_Boundaries_UK_BGC/FeatureServer/0/query"
)

# BSC = Super Generalised (fallback, even smaller)
ARCGIS_URL_BSC = (
    "https://services1.arcgis.com/ESMARspQHYMw9BZ9/arcgis/rest/services/"
    "Local_Authority_Districts_May_2024_Boundaries_UK_BSC/FeatureServer/0/query"
)


class UKGeographyDataset(Dataset):
    """
    UK geographic boundary and lookup data.

    Provides:
    - Local Authority District boundaries (GeoJSON)
    - LA to TTWA lookup tables
    - LA code change history
    """

    name = "geography"
    country = "uk"

    def download(self, output_dir: Path | None = None, **kwargs: Any) -> Path:
        """
        Download UK geographic data from ONS ArcGIS FeatureServer.

        Args:
            output_dir: Directory to save downloaded files

        Returns:
            Path to downloaded GeoJSON file
        """
        target_dir = output_dir or raw_path("uk", "geography")
        target_dir.mkdir(parents=True, exist_ok=True)

        output_file = target_dir / "la_boundaries_2024.geojson"
        fetch_lad_boundaries_2024(output_file)

        return output_file

    def process(
        self,
        raw_path: Path | None = None,
        output_path: Path | None = None,
        **kwargs: Any,
    ) -> pd.DataFrame:
        """
        Process geographic data into a lookup table.

        Args:
            raw_path: Path to GeoJSON boundary file
            output_path: Path to save processed data

        Returns:
            DataFrame with LA codes and names
        """
        import geopandas as gpd

        from src.core.config import raw_path as get_raw_path

        geojson_path = raw_path or get_raw_path("uk", "geography") / "la_boundaries_2024.geojson"

        gdf = gpd.read_file(geojson_path)

        # Extract just the code and name
        df = pd.DataFrame(
            {
                "la_code": gdf["LAD24CD"],
                "la_name": gdf["LAD24NM"],
            }
        )

        if output_path:
            output_path = Path(output_path)
            output_path.parent.mkdir(parents=True, exist_ok=True)
            df.to_csv(output_path, index=False)
            print(f"Saved to {output_path}")

        return df

    def load(self, path: Path | None = None) -> pd.DataFrame:
        """
        Load geographic boundary data as GeoDataFrame.

        Args:
            path: Path to GeoJSON file

        Returns:
            GeoDataFrame with LA boundaries
        """
        import geopandas as gpd

        from src.core.config import raw_path as get_raw_path

        path = path or get_raw_path("uk", "geography") / "la_boundaries_2024.geojson"
        return gpd.read_file(path)


def fetch_lad_boundaries_2024(output_path: Path | None = None) -> dict[str, Any]:
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
        ("Generalised Clipped (BGC)", ARCGIS_URL_BGC),
        ("Super Generalised (BSC)", ARCGIS_URL_BSC),
    ]

    import requests

    for name, url in urls_to_try:
        try:
            print(f"  Trying {name} boundaries...")
            all_features: list[dict[str, Any]] = []
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

                data = fetch_with_retry(url, params)
                features = data.get("features", [])
                if not features:
                    break

                all_features.extend(features)
                print(f"  Fetched {len(all_features)} boundaries...")

                if len(features) < batch_size:
                    break
                offset += batch_size

            if all_features:
                geojson: dict[str, Any] = {
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


# Module-level instance for convenience
uk_geography_dataset = UKGeographyDataset()


if __name__ == "__main__":
    from src.core.config import raw_path

    output_file = raw_path("uk", "geography") / "la_boundaries_2024.geojson"
    fetch_lad_boundaries_2024(output_file)
