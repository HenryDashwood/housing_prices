"""UK Annual Survey of Hours and Earnings (ASHE) dataset processing.

Provides wage data by local authority.
Source: https://www.ons.gov.uk/employmentandlabourmarket/peopleinwork/earningsandworkinghours/datasets/placeofresidencebylocalauthorityashetable8
"""

from pathlib import Path
from typing import Any

import pandas as pd

from src.core.config import processed_path as get_processed_path
from src.core.config import raw_path
from src.datasets.base import Dataset


class ASHEDataset(Dataset):
    """
    UK Annual Survey of Hours and Earnings dataset.

    Provides median weekly earnings and number of jobs by local authority.
    Uses Table 8 (by place of residence).
    """

    name = "ashe"
    country = "uk"

    def download(self, output_dir: Path | None = None, year: int = 2023, **kwargs: Any) -> Path:
        """
        Download ASHE Table 8 data from ONS.

        Args:
            output_dir: Directory to save downloaded file
            year: Data year to download

        Returns:
            Path to downloaded file
        """
        from src.core.download import download_file

        target_dir = output_dir or raw_path("uk", "ashe")
        target_dir.mkdir(parents=True, exist_ok=True)

        # Note: The exact filename varies by year
        output_file = target_dir / f"ashe_table8_{year}.xlsx"

        raise NotImplementedError(
            f"ASHE download not yet implemented.\n"
            f"Please visit the ONS ASHE page and download Table 8 manually:\n"
            f"https://www.ons.gov.uk/employmentandlabourmarket/peopleinwork/"
            f"earningsandworkinghours/datasets/placeofresidencebylocalauthorityashetable8\n"
            f"Save to: {output_file}"
        )

    def process(
        self,
        raw_path: Path | None = None,
        output_path: Path | None = None,
        **kwargs: Any,
    ) -> pd.DataFrame:
        """
        Process ASHE data to get wages by local authority.

        Args:
            raw_path: Path to ASHE Excel file
            output_path: Path to save processed data

        Returns:
            DataFrame with wages by LA

        Note:
            Implementation pending - needs ASHE file format analysis.
        """
        raise NotImplementedError(
            "ASHE processing not yet implemented. See REPLICATION_PLAN.md for the planned structure."
        )

    def load(self, path: Path | None = None) -> pd.DataFrame:
        """
        Load processed ASHE wage data.

        Args:
            path: Path to processed CSV file

        Returns:
            DataFrame with wage data
        """
        path = path or get_processed_path("uk", "ashe") / "wages_by_la.csv"
        return pd.read_csv(path)


# Module-level instance for convenience
ashe_dataset = ASHEDataset()
