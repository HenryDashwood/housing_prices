"""YIMBY Alliance Rent per Square Metre replication pipeline.

Replicates: https://yimbyalliance.org/2025/12/18/how-much-space-can-you-afford-to-rent

This pipeline combines UK EPC floor area data with PIPR rental prices
to calculate rent per square metre by local authority.
"""

from pathlib import Path

import numpy as np
import pandas as pd

from src.core.config import INTERMEDIATE_DIR, output_path
from src.datasets.uk.epc import process_epc_data
from src.datasets.uk.pipr import process_pipr_data
from src.models.rent_per_sqm import (
    calculate_rent_per_sqm,
    calculate_weighted_average_rent_per_sqm,
    join_floor_area_and_rents,
    summarize_results,
    validate_against_reference,
)


def create_outputs(df: pd.DataFrame, output_dir: Path | None = None) -> None:
    """
    Create the output files for the YIMBY rent map replication.

    Args:
        df: DataFrame with rent per sqm results
        output_dir: Directory to save outputs
    """
    if output_dir is None:
        output_dir = output_path("yimby_rent_map")

    output_dir.mkdir(parents=True, exist_ok=True)

    print("\n" + "=" * 60)
    print("Creating Output Files")
    print("=" * 60)

    # Primary output: full detail by LA
    primary_cols = [
        "la_code",
        "la_name",
        "region",
        "rent_1bed",
        "median_sqm_1bed",
        "rent_per_sqm_1bed",
        "rent_2bed",
        "median_sqm_2bed",
        "rent_per_sqm_2bed",
        "rent_3bed",
        "median_sqm_3bed",
        "rent_per_sqm_3bed",
        "rent_4bed_plus",
        "median_sqm_4+bed",
        "rent_per_sqm_4+bed",
        "overall_rent_per_sqm",
        "n_epc_obs",
        "data_date",
    ]

    # Only include columns that exist
    available_cols = [c for c in primary_cols if c in df.columns]
    primary = df[available_cols].copy()

    # Sort by overall rent per sqm descending
    primary = primary.sort_values("overall_rent_per_sqm", ascending=False)

    primary_file = output_dir / "rent_per_sqm_by_la.csv"
    primary.to_csv(primary_file, index=False)
    print(f"  Primary output: {primary_file}")

    # Secondary output: simplified for models
    model_cols = ["la_code", "la_name", "overall_rent_per_sqm"]
    model_df = df[model_cols].copy()
    model_df["log_rent_per_sqm"] = np.log(model_df["overall_rent_per_sqm"])
    model_df["rent_per_sqm_annual"] = model_df["overall_rent_per_sqm"] * 12
    model_df = model_df.sort_values("overall_rent_per_sqm", ascending=False)

    model_file = output_dir / "rent_per_sqm_for_models.csv"
    model_df.to_csv(model_file, index=False)
    print(f"  Model output: {model_file}")


def run_pipeline(
    use_cached: bool = True,
    output_dir: Path | None = None,
) -> pd.DataFrame:
    """
    Run the full YIMBY rent per sqm replication pipeline.

    Args:
        use_cached: If True, use cached intermediate files if available
        output_dir: Directory to save outputs

    Returns:
        DataFrame with rent per sqm by local authority
    """
    print("\n" + "=" * 60)
    print("YIMBY RENT PER SQUARE METRE REPLICATION")
    print("https://yimbyalliance.org/2025/12/18/how-much-space-can-you-afford-to-rent")
    print("=" * 60)

    # Step 1: Get EPC floor area data
    epc_cache = INTERMEDIATE_DIR / "epc_floor_areas.csv"
    if use_cached and epc_cache.exists():
        print(f"\nLoading cached EPC data from {epc_cache}")
        epc_df = pd.read_csv(epc_cache)
    else:
        epc_df = process_epc_data()
        epc_cache.parent.mkdir(parents=True, exist_ok=True)
        epc_df.to_csv(epc_cache, index=False)
        print(f"Cached EPC data to {epc_cache}")

    # Step 2: Get PIPR rental data
    pipr_cache = INTERMEDIATE_DIR / "pipr_rental_prices.csv"
    if use_cached and pipr_cache.exists():
        print(f"\nLoading cached PIPR data from {pipr_cache}")
        pipr_df = pd.read_csv(pipr_cache)
    else:
        pipr_df = process_pipr_data()
        pipr_cache.parent.mkdir(parents=True, exist_ok=True)
        pipr_df.to_csv(pipr_cache, index=False)
        print(f"Cached PIPR data to {pipr_cache}")

    # Step 3: Join datasets
    merged = join_floor_area_and_rents(epc_df, pipr_df)

    # Step 4: Calculate rent per sqm
    result = calculate_rent_per_sqm(merged)
    result = calculate_weighted_average_rent_per_sqm(result)

    # Step 5: Create outputs
    create_outputs(result, output_dir)

    # Step 6: Validate and summarize
    validate_against_reference(result)
    summarize_results(result)

    print("\n" + "=" * 60)
    print("Pipeline Complete!")
    print("=" * 60)

    return result


def main() -> None:
    """Entry point for running the YIMBY rent map replication."""
    run_pipeline(use_cached=True)


if __name__ == "__main__":
    main()
