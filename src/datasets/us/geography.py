"""US Geographic data: MSA/CBSA definitions, county crosswalks.

Provides boundary files and geographic code crosswalks for US metropolitan areas.
Source: https://www.census.gov/geographies/reference-files.html
"""

from pathlib import Path
from typing import Any

import pandas as pd

from src.core.config import processed_path as get_processed_path
from src.core.config import raw_path
from src.core.download import download_file
from src.datasets.base import Dataset

# Census Bureau delineation file URLs
# These are updated periodically - using 2023 delineations
CBSA_DELINEATION_URL = (
    "https://www2.census.gov/programs-surveys/metro-micro/geographies/"
    "reference-files/2023/delineation-files/list1_2023.xls"
)

# County-level FIPS codes
COUNTY_FIPS_URL = "https://www2.census.gov/geo/docs/reference/codes2020/national_county2020.txt"


class USGeographyDataset(Dataset):
    """
    US Geographic boundary and lookup data.

    Provides:
    - CBSA (Core Based Statistical Area) definitions
    - County to MSA/CBSA crosswalk
    - FIPS code lookups
    - MSA population data

    CBSA terminology:
    - Metropolitan Statistical Area (MSA): ≥50,000 population
    - Micropolitan Statistical Area: 10,000-50,000 population
    """

    name = "geography"
    country = "us"

    def download(self, output_dir: Path | None = None, **kwargs: Any) -> Path:
        """
        Download US geographic crosswalk files from Census Bureau.

        Downloads:
        1. CBSA delineation file (county to MSA mapping)
        2. County FIPS codes

        Args:
            output_dir: Directory to save downloaded files

        Returns:
            Path to download directory
        """
        target_dir = output_dir or raw_path("us", "geography")
        target_dir.mkdir(parents=True, exist_ok=True)

        print("Downloading US geographic data from Census Bureau...")

        # Download CBSA delineation file
        cbsa_file = target_dir / "cbsa_delineation_2023.xls"
        if not cbsa_file.exists():
            print("  Downloading CBSA delineation file...")
            try:
                download_file(CBSA_DELINEATION_URL, cbsa_file)
                print(f"  Saved: {cbsa_file}")
            except Exception as e:
                print(f"  Failed to download CBSA file: {e}")
                print(f"  Manual download: {CBSA_DELINEATION_URL}")
        else:
            print(f"  CBSA file already exists: {cbsa_file}")

        # Download county FIPS codes
        fips_file = target_dir / "county_fips_2020.txt"
        if not fips_file.exists():
            print("  Downloading county FIPS codes...")
            try:
                download_file(COUNTY_FIPS_URL, fips_file)
                print(f"  Saved: {fips_file}")
            except Exception as e:
                print(f"  Failed to download FIPS file: {e}")
                print(f"  Manual download: {COUNTY_FIPS_URL}")
        else:
            print(f"  FIPS file already exists: {fips_file}")

        return target_dir

    def process(
        self,
        raw_path: Path | None = None,
        output_path: Path | None = None,
        **kwargs: Any,
    ) -> pd.DataFrame:
        """
        Process US geographic data into a county-MSA crosswalk.

        Args:
            raw_path: Path to directory containing downloaded files
            output_path: Path to save processed data

        Returns:
            DataFrame with county-MSA crosswalk
        """
        from src.core.config import raw_path as get_raw_path

        data_dir = raw_path or get_raw_path("us", "geography")

        cbsa_file = data_dir / "cbsa_delineation_2023.xls"

        if cbsa_file.exists():
            print(f"Processing CBSA delineation file: {cbsa_file}")
            result = self._process_cbsa_delineation(cbsa_file)
        else:
            print("CBSA file not found. Run download() first or provide data manually.")
            raise FileNotFoundError(f"Expected file at: {cbsa_file}")

        if output_path:
            output_path = Path(output_path)
            output_path.parent.mkdir(parents=True, exist_ok=True)
            result.to_csv(output_path, index=False)
            print(f"Saved processed data to: {output_path}")

        return result

    def _process_cbsa_delineation(self, filepath: Path) -> pd.DataFrame:
        """Process Census CBSA delineation Excel file."""
        # The file has headers starting at row 2 (0-indexed)
        df = pd.read_excel(filepath, skiprows=2)

        # Standardize column names
        df.columns = df.columns.str.strip().str.lower().str.replace(" ", "_")

        # Key columns (names may vary slightly by year)
        rename_map = {
            "cbsa_code": "cbsa_code",
            "cbsa_title": "cbsa_name",
            "metropolitan/micropolitan_statistical_area": "cbsa_type",
            "metropolitan_division_code": "metro_division_code",
            "metropolitan_division_title": "metro_division_name",
            "csa_code": "csa_code",
            "csa_title": "csa_name",
            "county/county_equivalent": "county_name",
            "state_name": "state_name",
            "fips_state_code": "state_fips",
            "fips_county_code": "county_fips",
            "central/outlying_county": "county_type",
        }

        # Apply renames for columns that exist
        for old, new in rename_map.items():
            if old in df.columns:
                df = df.rename(columns={old: new})

        # Create full FIPS code (state + county)
        if "state_fips" in df.columns and "county_fips" in df.columns:
            df["state_fips"] = df["state_fips"].astype(str).str.zfill(2)
            df["county_fips"] = df["county_fips"].astype(str).str.zfill(3)
            df["fips"] = df["state_fips"] + df["county_fips"]

        # Filter to Metropolitan Statistical Areas only (for Hsieh-Moretti)
        if "cbsa_type" in df.columns:
            msa_df = df[df["cbsa_type"].str.contains("Metropolitan", case=False, na=False)].copy()
            print(f"  Filtered to {len(msa_df)} counties in Metropolitan Statistical Areas")
        else:
            msa_df = df.copy()

        return msa_df

    def load(self, path: Path | None = None) -> pd.DataFrame:
        """
        Load county-MSA crosswalk data.

        Args:
            path: Path to processed CSV file

        Returns:
            DataFrame with crosswalk data
        """
        path = path or get_processed_path("us", "geography") / "county_msa_crosswalk.csv"
        return pd.read_csv(path)

    def get_msa_counties(self, cbsa_code: str) -> pd.DataFrame:
        """
        Get all counties in a specific MSA.

        Args:
            cbsa_code: CBSA code for the MSA

        Returns:
            DataFrame with counties in the MSA
        """
        df = self.load()
        return df[df["cbsa_code"] == cbsa_code]

    def get_county_msa(self, fips: str) -> str | None:
        """
        Get the MSA for a specific county.

        Args:
            fips: 5-digit county FIPS code

        Returns:
            CBSA code or None if not in an MSA
        """
        df = self.load()
        match = df[df["fips"] == fips]
        if len(match) > 0:
            return match.iloc[0]["cbsa_code"]
        return None


# Module-level instance for convenience
us_geography_dataset = USGeographyDataset()


if __name__ == "__main__":
    from src.core.config import processed_path

    # Download data
    us_geography_dataset.download()

    # Process and save
    output_file = processed_path("us", "geography") / "county_msa_crosswalk.csv"
    df = us_geography_dataset.process(output_path=output_file)
    print(f"\nProcessed {len(df)} county-MSA mappings")
    print(f"Unique MSAs: {df['cbsa_code'].nunique()}")
    print(df.head(10))
