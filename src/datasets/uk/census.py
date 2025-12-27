"""UK Census 2021 dataset processing.

Provides demographic data by local authority: education, ethnicity, age.
Source: https://www.nomisweb.co.uk/ (Nomis API)
"""

from pathlib import Path
from typing import Any

import pandas as pd

from src.core.config import processed_path as get_processed_path
from src.core.config import raw_path
from src.datasets.base import Dataset

# Nomis API dataset IDs for Census 2021
NOMIS_DATASETS = {
    "education": "TS067",  # Highest qualification by LA
    "ethnicity": "TS021",  # Ethnic group by LA
    "age": "TS007",  # Age by single year
}


class CensusDataset(Dataset):
    """
    UK Census 2021 dataset.

    Provides demographic characteristics by local authority:
    - Educational attainment
    - Ethnic group composition
    - Age distribution
    """

    name = "census"
    country = "uk"

    def download(
        self,
        output_dir: Path | None = None,
        tables: list[str] | None = None,
        **kwargs: Any,
    ) -> Path:
        """
        Download Census 2021 data from Nomis API.

        Args:
            output_dir: Directory to save downloaded files
            tables: List of tables to download (default: all)

        Returns:
            Path to download directory
        """
        target_dir = output_dir or raw_path("uk", "census")
        target_dir.mkdir(parents=True, exist_ok=True)

        if tables is None:
            tables = list(NOMIS_DATASETS.keys())

        raise NotImplementedError(
            "Census download not yet implemented.\n"
            "The Nomis API requires specific query construction.\n"
            f"Tables to download: {tables}\n"
            f"See: https://www.nomisweb.co.uk/api/v01/"
        )

    def process(
        self,
        raw_path: Path | None = None,
        output_path: Path | None = None,
        **kwargs: Any,
    ) -> pd.DataFrame:
        """
        Process Census data into demographic variables.

        Args:
            raw_path: Path to Census CSV files
            output_path: Path to save processed data

        Returns:
            DataFrame with demographic variables by LA

        Note:
            Implementation pending - needs Census file format analysis.
        """
        raise NotImplementedError(
            "Census processing not yet implemented. See REPLICATION_PLAN.md for the planned structure."
        )

    def load(self, path: Path | None = None) -> pd.DataFrame:
        """
        Load processed Census demographic data.

        Args:
            path: Path to processed CSV file

        Returns:
            DataFrame with demographic data
        """
        path = path or get_processed_path("uk", "census") / "demographics_by_la.csv"
        return pd.read_csv(path)


# Module-level instance for convenience
census_dataset = CensusDataset()
