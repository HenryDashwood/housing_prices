"""Process ONS PIPR rental price data to get rents by local authority and bedroom count."""

import pandas as pd

from src.config import PIPR_FILE, PIPR_PROCESSED_FILE

# ONS PIPR data has some incorrect LA codes - map to correct 2024 codes
LA_CODE_FIXES = {
    "E08000039": "E08000019",  # Sheffield (typo in ONS data)
    "E08000038": "E08000016",  # Barnsley (typo in ONS data)
}


def load_pipr_data() -> pd.DataFrame:
    """Load PIPR rental price data from Excel file."""
    print(f"Loading PIPR data from {PIPR_FILE.name}...")

    df = pd.read_excel(PIPR_FILE, sheet_name="Table 1", header=2)

    print(f"  Loaded {len(df):,} rows")
    return df


def filter_to_local_authorities(df: pd.DataFrame) -> pd.DataFrame:
    """Filter to local authority level data only."""
    print("\nFiltering to local authorities...")

    # LA codes start with E06, E07, E08, E09 (England) or W06 (Wales)
    la_pattern = r"^E0[6-9]|^W06"
    la_mask = df["Area code"].astype(str).str.match(la_pattern)

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
    fixed_count = result["la_code"].isin(LA_CODE_FIXES.keys()).sum()
    if fixed_count > 0:
        result["la_code"] = result["la_code"].replace(LA_CODE_FIXES)
        print(f"  Fixed {fixed_count} incorrect LA codes")

    return result


def process_pipr_data() -> pd.DataFrame:
    """Main function to process PIPR data."""
    print("=" * 60)
    print("Processing PIPR Rental Price Data")
    print("=" * 60)

    # Load data
    raw = load_pipr_data()

    # Filter to LAs
    la_data = filter_to_local_authorities(raw)

    # Get latest prices
    latest = get_latest_rental_prices(la_data)

    return latest


if __name__ == "__main__":
    result = process_pipr_data()

    # Save intermediate output
    result.to_csv(PIPR_PROCESSED_FILE, index=False)
    print(f"\nSaved to {PIPR_PROCESSED_FILE}")
    print("\nSample output:")
    print(result.head(10).to_string())
