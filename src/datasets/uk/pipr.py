"""UK Price Index of Private Rents (PIPR) dataset processing.

Provides rental prices by local authority and bedroom count.
Source: https://www.ons.gov.uk/economy/inflationandpriceindices/datasets/priceindexofprivaterentsukmonthlypricestatistics
"""

from pathlib import Path
from typing import Any

import pandas as pd

from src.core.config import processed_path as get_processed_path
from src.core.config import raw_path
from src.core.geo import fix_la_code, is_england_wales_la
from src.datasets.base import Dataset


class PIPRDataset(Dataset):
    """
    UK Price Index of Private Rents dataset.

    Provides monthly rental prices by local authority and bedroom category.
    """

    name = "pipr"
    country = "uk"

    def download(self, output_dir: Path | None = None, **kwargs: Any) -> Path:
        """
        Download PIPR data from ONS.

        Note: The URL changes with each release. This method provides
        the pattern but may need manual URL update.

        Args:
            output_dir: Directory to save downloaded file

        Returns:
            Path to downloaded file
        """
        from src.core.download import download_file

        target_dir = output_dir or raw_path("uk", "pipr")
        target_dir.mkdir(parents=True, exist_ok=True)

        # URL pattern - this changes with each release
        url = (
            "https://www.ons.gov.uk/file?uri=/economy/inflationandpriceindices/"
            "datasets/priceindexofprivaterentsukmonthlypricestatistics/"
            "current/priceindexofprivaterentsukmonthlypricestatistics.xlsx"
        )

        output_file = target_dir / "priceindexofprivaterentsukmonthlypricestatistics.xlsx"

        print("Downloading PIPR data from ONS...")
        print("Note: If this fails, visit the ONS page to get the current URL.")

        return download_file(url, output_file)

    def process(
        self,
        raw_path: Path | None = None,
        output_path: Path | None = None,
        **kwargs: Any,
    ) -> pd.DataFrame:
        """
        Process PIPR data to get rental prices by LA and bedroom count.

        Args:
            raw_path: Path to PIPR Excel file
            output_path: Path to save processed data
            **kwargs: Additional processing options

        Returns:
            DataFrame with rental prices by LA and bedroom category
        """
        result = process_pipr_data(raw_path)

        if output_path:
            output_path = Path(output_path)
            output_path.parent.mkdir(parents=True, exist_ok=True)
            result.to_csv(output_path, index=False)
            print(f"Saved to {output_path}")

        return result

    def load(self, path: Path | None = None) -> pd.DataFrame:
        """
        Load processed PIPR rental price data.

        Args:
            path: Path to processed CSV file

        Returns:
            DataFrame with rental price data
        """
        from src.core.config import INTERMEDIATE_DIR

        path = path or INTERMEDIATE_DIR / "pipr_rental_prices.csv"
        return pd.read_csv(path)


def load_pipr_data(pipr_file: Path | None = None) -> pd.DataFrame:
    """Load PIPR rental price data from Excel file."""
    from src.core.config import raw_path

    if pipr_file is None:
        # Try to find the file in the raw directory
        pipr_dir = raw_path("uk", "pipr")
        xlsx_files = list(pipr_dir.glob("*.xlsx"))
        if xlsx_files:
            pipr_file = xlsx_files[0]
        else:
            # Fall back to legacy location
            from src.core.config import DATA_DIR

            legacy_path = DATA_DIR / "raw" / "priceindexofprivaterentsukmonthlypricestatistics6.xlsx"
            if legacy_path.exists():
                pipr_file = legacy_path
            else:
                raise FileNotFoundError(f"No PIPR Excel file found in {pipr_dir} or legacy location")

    print(f"Loading PIPR data from {pipr_file.name}...")

    df = pd.read_excel(pipr_file, sheet_name="Table 1", header=2)

    print(f"  Loaded {len(df):,} rows")
    return df


def filter_to_local_authorities(df: pd.DataFrame) -> pd.DataFrame:
    """Filter to local authority level data only."""
    print("\nFiltering to local authorities...")

    # Use the geo utility to filter to England & Wales LAs
    la_mask = df["Area code"].astype(str).apply(is_england_wales_la)

    la_data = df[la_mask].copy()
    print(f"  Found {la_data['Area code'].nunique()} unique local authorities")

    return la_data


def get_latest_rental_prices(df: pd.DataFrame) -> pd.DataFrame:
    """Extract the latest month of rental price data."""
    print("\nExtracting latest rental prices...")

    # Get latest time period
    latest_date = df["Time period"].max()
    print(f"  Latest data: {latest_date}")

    latest = df[df["Time period"] == latest_date].copy()
    print(f"  {len(latest)} local authorities with data")

    # Select relevant columns
    cols = [
        "Area code",
        "Area name",
        "Region or country name",
        "Rental price",
        "Rental price one bed",
        "Rental price two bed",
        "Rental price three bed",
        "Rental price four or more bed",
    ]

    result = latest[cols].copy()

    # Rename columns for easier joining
    result.columns = [
        "la_code",
        "la_name",
        "region",
        "rent_overall",
        "rent_1bed",
        "rent_2bed",
        "rent_3bed",
        "rent_4bed_plus",
    ]

    # Store the data date
    result["data_date"] = latest_date.strftime("%Y-%m")

    # Fix incorrect LA codes from ONS source data
    original_codes = result["la_code"].copy()
    result["la_code"] = result["la_code"].apply(fix_la_code)
    fixed_count = (result["la_code"] != original_codes).sum()
    if fixed_count > 0:
        print(f"  Fixed {fixed_count} incorrect LA codes")

    return result


def process_pipr_data(pipr_file: Path | None = None) -> pd.DataFrame:
    """
    Main function to process PIPR data.

    Args:
        pipr_file: Path to PIPR Excel file (optional, will search default locations)

    Returns:
        DataFrame with rental prices by LA and bedroom category
    """
    print("=" * 60)
    print("Processing PIPR Rental Price Data")
    print("=" * 60)

    # Load data
    raw = load_pipr_data(pipr_file)

    # Filter to LAs
    la_data = filter_to_local_authorities(raw)

    # Get latest prices
    latest = get_latest_rental_prices(la_data)

    return latest


# Module-level instance for convenience
pipr_dataset = PIPRDataset()


if __name__ == "__main__":
    from src.core.config import INTERMEDIATE_DIR

    result = process_pipr_data()

    # Save intermediate output
    output_file = INTERMEDIATE_DIR / "pipr_rental_prices.csv"
    output_file.parent.mkdir(parents=True, exist_ok=True)
    result.to_csv(output_file, index=False)
    print(f"\nSaved to {output_file}")
    print("\nSample output:")
    print(result.head(10).to_string())
