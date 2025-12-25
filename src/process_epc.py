"""Process EPC data to get median floor area by local authority and bedroom count."""

from pathlib import Path

import pandas as pd

from src.config import EPC_AGGREGATED_FILE, EPC_DIR


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
    def bedroom_category(beds):
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


def process_epc_data() -> pd.DataFrame:
    """Main function to process EPC data."""
    print("=" * 60)
    print("Processing EPC Data")
    print("=" * 60)

    # Load all certificates
    raw = load_all_epc_certificates(EPC_DIR)

    # Clean and filter
    cleaned = clean_and_filter_epc(raw)

    # Aggregate
    aggregated = aggregate_floor_area(cleaned)

    return aggregated


if __name__ == "__main__":
    result = process_epc_data()

    # Save intermediate output
    result.to_csv(EPC_AGGREGATED_FILE, index=False)
    print(f"\nSaved to {EPC_AGGREGATED_FILE}")
    print("\nSample output:")
    print(result.head(10).to_string())
