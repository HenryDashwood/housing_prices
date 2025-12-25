"""Main pipeline to calculate rent per square metre by local authority.

Replicates the YIMBY Alliance analysis:
https://yimbyalliance.org/2025/12/18/how-much-space-can-you-afford-to-rent
"""

import numpy as np
import pandas as pd

from src.config import OUTPUT_DIR, RENT_PSQM_FULL_FILE, RENT_PSQM_MODEL_FILE
from src.process_epc import process_epc_data
from src.process_pipr import process_pipr_data


def join_epc_and_pipr(epc_df: pd.DataFrame, pipr_df: pd.DataFrame) -> pd.DataFrame:
    """Join EPC floor area data with PIPR rental price data."""
    print("\n" + "=" * 60)
    print("Joining EPC and PIPR Data")
    print("=" * 60)

    # Join on LA code
    merged = pipr_df.merge(
        epc_df,
        left_on="la_code",
        right_on="LOCAL_AUTHORITY",
        how="left",
    )

    print(f"  PIPR LAs: {len(pipr_df)}")
    print(f"  EPC LAs: {len(epc_df)}")
    print(f"  Matched: {merged['LOCAL_AUTHORITY'].notna().sum()}")

    # Drop the duplicate LA column
    merged = merged.drop(columns=["LOCAL_AUTHORITY"])

    return merged


def calculate_rent_per_sqm(df: pd.DataFrame) -> pd.DataFrame:
    """Calculate rent per square metre for each bedroom category."""
    print("\nCalculating rent per square metre...")

    result = df.copy()

    # Calculate rent per sqm for each bedroom category
    bedroom_cats = ["1", "2", "3", "4+"]

    for cat in bedroom_cats:
        rent_col = f"rent_{cat}bed" if cat != "4+" else "rent_4bed_plus"
        sqm_col = f"median_sqm_{cat}bed"
        output_col = f"rent_per_sqm_{cat}bed"

        if rent_col in result.columns and sqm_col in result.columns:
            result[output_col] = result[rent_col] / result[sqm_col]

    # Calculate weighted average rent per sqm
    # Weight by number of observations in each bedroom category
    count_cols = [f"count_{cat}bed" for cat in bedroom_cats]
    rent_psqm_cols = [f"rent_per_sqm_{cat}bed" for cat in bedroom_cats]

    # Calculate weighted average where we have data
    def weighted_avg(row):
        weights = []
        values = []
        for count_col, val_col in zip(count_cols, rent_psqm_cols):
            if pd.notna(row.get(count_col)) and pd.notna(row.get(val_col)):
                weights.append(row[count_col])
                values.append(row[val_col])
        if weights:
            return np.average(values, weights=weights)
        return np.nan

    result["overall_rent_per_sqm"] = result.apply(weighted_avg, axis=1)

    return result


def create_outputs(df: pd.DataFrame) -> None:
    """Create the output files."""
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

    primary.to_csv(RENT_PSQM_FULL_FILE, index=False)
    print(f"  Primary output: {RENT_PSQM_FULL_FILE}")

    # Secondary output: simplified for models
    model_cols = ["la_code", "la_name", "overall_rent_per_sqm"]
    model_df = df[model_cols].copy()
    model_df["log_rent_per_sqm"] = np.log(model_df["overall_rent_per_sqm"])
    model_df["rent_per_sqm_annual"] = model_df["overall_rent_per_sqm"] * 12
    model_df = model_df.sort_values("overall_rent_per_sqm", ascending=False)

    model_df.to_csv(RENT_PSQM_MODEL_FILE, index=False)
    print(f"  Model output: {RENT_PSQM_MODEL_FILE}")


def validate_results(df: pd.DataFrame) -> None:
    """Validate results against known YIMBY reference values."""
    print("\n" + "=" * 60)
    print("Validation Against YIMBY Reference Values")
    print("=" * 60)

    # Reference values from YIMBY article
    references = {
        "Westminster": 44.60,  # Highest
        "Hartlepool": 7.50,  # One of lowest
    }

    print("\nComparison with YIMBY published values:")
    print("-" * 50)

    for la_name, expected in references.items():
        match = df[df["la_name"].str.contains(la_name, case=False, na=False)]
        if len(match) > 0:
            actual = match["overall_rent_per_sqm"].values[0]
            diff = actual - expected
            pct_diff = (diff / expected) * 100
            print(f"  {la_name}:")
            print(f"    Expected: £{expected:.2f}/sqm")
            print(f"    Actual:   £{actual:.2f}/sqm")
            print(f"    Diff:     £{diff:+.2f} ({pct_diff:+.1f}%)")
        else:
            print(f"  {la_name}: NOT FOUND")

    # Show top and bottom 5
    print("\nTop 5 most expensive (£/sqm/month):")
    print("-" * 50)
    top5 = df.nlargest(5, "overall_rent_per_sqm")[["la_name", "overall_rent_per_sqm"]]
    for _, row in top5.iterrows():
        print(f"  {row['la_name']}: £{row['overall_rent_per_sqm']:.2f}")

    print("\nBottom 5 cheapest (£/sqm/month):")
    print("-" * 50)
    bottom5 = df.nsmallest(5, "overall_rent_per_sqm")[["la_name", "overall_rent_per_sqm"]]
    for _, row in bottom5.iterrows():
        print(f"  {row['la_name']}: £{row['overall_rent_per_sqm']:.2f}")


def main():
    """Run the full pipeline."""
    print("\n" + "=" * 60)
    print("RENT PER SQUARE METRE PIPELINE")
    print("Replicating YIMBY Alliance Analysis")
    print("=" * 60)

    # Process EPC data
    epc_df = process_epc_data()

    # Process PIPR data
    pipr_df = process_pipr_data()

    # Join datasets
    merged = join_epc_and_pipr(epc_df, pipr_df)

    # Calculate rent per sqm
    result = calculate_rent_per_sqm(merged)

    # Create outputs
    create_outputs(result)

    # Validate
    validate_results(result)

    print("\n" + "=" * 60)
    print("Pipeline Complete!")
    print("=" * 60)


if __name__ == "__main__":
    main()
