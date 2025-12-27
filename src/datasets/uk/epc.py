"""UK Energy Performance Certificate (EPC) dataset processing.

Provides floor area data by local authority and bedroom count for private rented properties.
Source: https://epc.opendatacommunities.org/
"""

from pathlib import Path
from typing import Any

import pandas as pd

from src.core.config import processed_path as get_processed_path
from src.core.config import raw_path
from src.datasets.base import Dataset


class EPCDataset(Dataset):
    """
    UK Energy Performance Certificate dataset.

    Provides median floor area by local authority and bedroom category
    for private rented properties.
    """

    name = "epc"
    country = "uk"

    def download(self, output_dir: Path | None = None, **kwargs: Any) -> Path:
        """
        EPC data requires manual bulk download from the Open Data Communities portal.

        Instructions:
        1. Visit https://epc.opendatacommunities.org/
        2. Register for an account
        3. Download all domestic certificates (bulk download ~6GB)
        4. Extract to data/raw/uk/epc/

        Args:
            output_dir: Directory to save downloaded files (unused for manual download)

        Returns:
            Path to expected download location

        Raises:
            NotImplementedError: EPC data requires manual download
        """
        target_dir = output_dir or raw_path("uk", "epc")
        raise NotImplementedError(
            f"EPC data requires manual download.\n"
            f"1. Visit https://epc.opendatacommunities.org/\n"
            f"2. Register and download all domestic certificates\n"
            f"3. Extract to {target_dir}"
        )

    def process(
        self,
        raw_path: Path | None = None,
        output_path: Path | None = None,
        **kwargs: Any,
    ) -> pd.DataFrame:
        """
        Process EPC data to get median floor area by LA and bedroom count.

        Args:
            raw_path: Path to extracted EPC certificates directory
            output_path: Path to save processed data
            **kwargs: Additional processing options

        Returns:
            DataFrame with median floor areas by LA and bedroom category
        """
        from src.core.config import raw_path as get_raw_path

        epc_dir = raw_path or get_raw_path("uk", "epc")
        result = process_epc_data(epc_dir)

        if output_path:
            output_path = Path(output_path)
            output_path.parent.mkdir(parents=True, exist_ok=True)
            result.to_csv(output_path, index=False)
            print(f"Saved to {output_path}")

        return result

    def load(self, path: Path | None = None) -> pd.DataFrame:
        """
        Load processed EPC floor area data.

        Args:
            path: Path to processed CSV file

        Returns:
            DataFrame with floor area data
        """
        from src.core.config import INTERMEDIATE_DIR

        path = path or INTERMEDIATE_DIR / "epc_floor_areas.csv"
        return pd.read_csv(path)


def load_all_epc_certificates(epc_dir: Path) -> pd.DataFrame:
    """Load all EPC certificates from local authority folders."""
    all_dfs = []
    la_folders = list(epc_dir.glob("domestic-*/"))

    print(f"Found {len(la_folders)} local authority folders")

    for i, folder in enumerate(la_folders):
        cert_file = folder / "certificates.csv"
        if cert_file.exists():
            cols = [
                "LOCAL_AUTHORITY",
                "TENURE",
                "TOTAL_FLOOR_AREA",
                "NUMBER_HABITABLE_ROOMS",
                "PROPERTY_TYPE",
                "LODGEMENT_DATE",
            ]
            df = pd.read_csv(str(cert_file), usecols=cols, low_memory=False)  # type: ignore[call-overload]
            all_dfs.append(df)

        if (i + 1) % 50 == 0:
            print(f"  Loaded {i + 1}/{len(la_folders)} folders...")

    print("Concatenating dataframes...")
    combined = pd.concat(all_dfs, ignore_index=True)
    print(f"Total certificates loaded: {len(combined):,}")
    return combined


def clean_and_filter_epc(df: pd.DataFrame) -> pd.DataFrame:
    """Filter to private rented and clean floor area data."""
    print("\nFiltering and cleaning EPC data...")

    # Filter to private rented only (handle mixed case)
    tenure_lower = df["TENURE"].str.lower()
    private_rented = df[tenure_lower.isin(["rental (private)", "rented (private)"])].copy()
    print(f"  Private rented properties: {len(private_rented):,}")

    # Convert floor area to numeric, coercing errors
    private_rented["TOTAL_FLOOR_AREA"] = pd.to_numeric(private_rented["TOTAL_FLOOR_AREA"], errors="coerce")

    # Remove implausible floor areas (< 10 sqm or > 800 sqm)
    valid_area = private_rented[
        (private_rented["TOTAL_FLOOR_AREA"] >= 10) & (private_rented["TOTAL_FLOOR_AREA"] <= 800)
    ].copy()
    print(f"  After floor area filter (10-800 sqm): {len(valid_area):,}")

    # Convert habitable rooms to numeric
    valid_area["NUMBER_HABITABLE_ROOMS"] = pd.to_numeric(valid_area["NUMBER_HABITABLE_ROOMS"], errors="coerce")

    # Remove rows with missing rooms
    valid_area = valid_area.dropna(subset=["NUMBER_HABITABLE_ROOMS"])
    print(f"  After removing missing room counts: {len(valid_area):,}")

    # Map habitable rooms to bedroom categories
    # Typically: habitable rooms = bedrooms + living rooms
    # Assume 1 living room, so bedrooms = habitable_rooms - 1
    # But minimum 1 bedroom (studio = 1 bed)
    valid_area["bedrooms"] = (valid_area["NUMBER_HABITABLE_ROOMS"] - 1).clip(lower=1)

    # Create bedroom category matching PIPR categories
    def bedroom_category(beds: float) -> str:
        if beds <= 1:
            return "1"
        elif beds == 2:
            return "2"
        elif beds == 3:
            return "3"
        else:
            return "4+"

    valid_area["bedroom_cat"] = valid_area["bedrooms"].apply(bedroom_category)

    # Filter to recent certificates (last 5 years from latest data)
    valid_area["LODGEMENT_DATE"] = pd.to_datetime(valid_area["LODGEMENT_DATE"], errors="coerce")
    max_date = valid_area["LODGEMENT_DATE"].max()
    cutoff_date = max_date - pd.DateOffset(years=5)
    print(f"  Date range: {valid_area['LODGEMENT_DATE'].min()} to {max_date}")
    print(f"  Using cutoff: {cutoff_date}")
    recent = valid_area[valid_area["LODGEMENT_DATE"] >= cutoff_date]
    print(f"  After filtering to last 5 years: {len(recent):,}")

    return recent


def aggregate_floor_area(df: pd.DataFrame) -> pd.DataFrame:
    """Calculate median floor area by LA and bedroom category."""
    print("\nAggregating floor area by LA and bedroom count...")

    # Group by LA and bedroom category
    grouped = (
        df.groupby(["LOCAL_AUTHORITY", "bedroom_cat"])
        .agg(
            median_sqm=("TOTAL_FLOOR_AREA", "median"),
            mean_sqm=("TOTAL_FLOOR_AREA", "mean"),
            count=("TOTAL_FLOOR_AREA", "count"),
        )
        .reset_index()
    )

    print(f"  Generated {len(grouped)} LA-bedroom combinations")

    # Pivot to wide format for easier joining
    pivot = grouped.pivot(index="LOCAL_AUTHORITY", columns="bedroom_cat", values=["median_sqm", "count"])

    # Flatten column names
    pivot.columns = [f"{col[0]}_{col[1]}bed" for col in pivot.columns]
    pivot = pivot.reset_index()

    # Calculate total observations per LA
    count_cols = [c for c in pivot.columns if c.startswith("count_")]
    pivot["n_epc_obs"] = pivot[count_cols].sum(axis=1)

    print(f"  Final output: {len(pivot)} local authorities")
    return pivot


def process_epc_data(epc_dir: Path | None = None) -> pd.DataFrame:
    """
    Main function to process EPC data.

    Args:
        epc_dir: Path to EPC certificates directory

    Returns:
        DataFrame with median floor areas by LA and bedroom category
    """
    from src.core.config import raw_path

    if epc_dir is None:
        epc_dir = raw_path("uk", "epc")

    print("=" * 60)
    print("Processing EPC Data")
    print("=" * 60)

    # Load all certificates
    raw = load_all_epc_certificates(epc_dir)

    # Clean and filter
    cleaned = clean_and_filter_epc(raw)

    # Aggregate
    aggregated = aggregate_floor_area(cleaned)

    return aggregated


# Module-level instance for convenience
epc_dataset = EPCDataset()


if __name__ == "__main__":
    from src.core.config import INTERMEDIATE_DIR

    result = process_epc_data()

    # Save intermediate output
    output_file = INTERMEDIATE_DIR / "epc_floor_areas.csv"
    output_file.parent.mkdir(parents=True, exist_ok=True)
    result.to_csv(output_file, index=False)
    print(f"\nSaved to {output_file}")
    print("\nSample output:")
    print(result.head(10).to_string())
