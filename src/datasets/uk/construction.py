"""UK Construction cost dataset processing.

Provides construction costs and regional adjustment factors.
Source: https://costmodelling.com/
"""

from pathlib import Path
from typing import Any

import pandas as pd

from src.core.config import processed_path as get_processed_path
from src.core.config import raw_path
from src.datasets.base import Dataset


class ConstructionDataset(Dataset):
    """
    UK Construction cost dataset.

    Provides:
    - Cost per sqm by building type
    - Regional adjustment factors
    """

    name = "construction"
    country = "uk"

    def download(self, output_dir: Path | None = None, **kwargs: Any) -> Path:
        """
        Scrape construction cost data from costmodelling.com.

        Args:
            output_dir: Directory to save downloaded data

        Returns:
            Path to download directory

        Note:
            Requires web scraping - site structure may change.
        """
        target_dir = output_dir or raw_path("uk", "construction")
        target_dir.mkdir(parents=True, exist_ok=True)

        raise NotImplementedError(
            "Construction cost scraping not yet implemented.\n"
            "Data sources:\n"
            "  - Building costs: https://costmodelling.com/building-costs\n"
            "  - Regional factors: https://costmodelling.com/regional-variations\n"
            f"Save to: {target_dir}"
        )

    def process(
        self,
        raw_path: Path | None = None,
        output_path: Path | None = None,
        **kwargs: Any,
    ) -> pd.DataFrame:
        """
        Process construction cost data.

        Args:
            raw_path: Path to scraped data files
            output_path: Path to save processed data

        Returns:
            DataFrame with construction costs and regional factors

        Note:
            Implementation pending.
        """
        raise NotImplementedError(
            "Construction cost processing not yet implemented. See REPLICATION_PLAN.md for the planned structure."
        )

    def load(self, path: Path | None = None) -> pd.DataFrame:
        """
        Load processed construction cost data.

        Args:
            path: Path to processed CSV file

        Returns:
            DataFrame with construction cost data
        """
        path = path or get_processed_path("uk", "construction") / "construction_costs.csv"
        return pd.read_csv(path)


# Key building type costs (for Cooped Up replication)
# From costmodelling.com, Q3 2025
BUILDING_COSTS_2025 = {
    "flats_6_storey_high_rise": 2605,  # £/m² for 6+ storey flats with lifts
    "flats_3_5_storey_mid_rise": 2250,  # £/m² for 3-5 storey flats
    "houses_terraced": 1750,  # £/m² for terraced houses
}

# Regional adjustment factors (London = 1.0)
REGIONAL_FACTORS = {
    "inner_london": 1.15,
    "outer_london": 1.05,
    "south_east": 0.98,
    "south_west": 0.92,
    "east_of_england": 0.94,
    "east_midlands": 0.88,
    "west_midlands": 0.90,
    "yorkshire_and_humber": 0.87,
    "north_west": 0.88,
    "north_east": 0.85,
    "wales": 0.86,
    "scotland": 0.90,
    "northern_ireland": 0.82,
}


# Module-level instance for convenience
construction_dataset = ConstructionDataset()
