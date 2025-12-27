"""Base class for dataset ingestion and processing."""

from abc import ABC, abstractmethod
from pathlib import Path
from typing import Any

import pandas as pd


class Dataset(ABC):
    """
    Abstract base class for dataset handlers.

    Each dataset module should implement this interface to provide
    consistent download, processing, and loading functionality.
    """

    name: str  # Dataset identifier (e.g., "epc", "pipr", "ashe")
    country: str  # Country code (e.g., "uk", "us")

    @abstractmethod
    def download(self, output_dir: Path, **kwargs: Any) -> Path:
        """
        Download raw data from source.

        Args:
            output_dir: Directory to save downloaded files
            **kwargs: Additional download options

        Returns:
            Path to downloaded file(s)
        """
        pass

    @abstractmethod
    def process(self, raw_path: Path, output_path: Path, **kwargs: Any) -> pd.DataFrame:
        """
        Process raw data into analysis-ready format.

        Args:
            raw_path: Path to raw data file(s)
            output_path: Path to save processed data
            **kwargs: Additional processing options

        Returns:
            Processed DataFrame
        """
        pass

    @abstractmethod
    def load(self, path: Path | None = None) -> pd.DataFrame:
        """
        Load processed data.

        Args:
            path: Path to processed data file (uses default if None)

        Returns:
            DataFrame with processed data
        """
        pass

    def __repr__(self) -> str:
        return f"{self.__class__.__name__}(country={self.country!r}, name={self.name!r})"
