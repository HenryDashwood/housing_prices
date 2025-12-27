"""Rent per square metre calculation model.

This module contains the core analytical logic for calculating rent per square metre
by joining floor area data with rental price data.

Can be used with any country's data that provides:
- Floor area by geographic unit and bedroom category
- Rental prices by geographic unit and bedroom category
"""

import numpy as np
import pandas as pd


def join_floor_area_and_rents(
    floor_area_df: pd.DataFrame,
    rental_df: pd.DataFrame,
    floor_area_geo_col: str = "LOCAL_AUTHORITY",
    rental_geo_col: str = "la_code",
) -> pd.DataFrame:
    """
    Join floor area data with rental price data.

    Args:
        floor_area_df: DataFrame with floor areas by geographic unit and bedroom category
        rental_df: DataFrame with rental prices by geographic unit and bedroom category
        floor_area_geo_col: Column name for geographic identifier in floor area data
        rental_geo_col: Column name for geographic identifier in rental data

    Returns:
        Merged DataFrame
    """
    print("\n" + "=" * 60)
    print("Joining Floor Area and Rental Data")
    print("=" * 60)

    merged = rental_df.merge(
        floor_area_df,
        left_on=rental_geo_col,
        right_on=floor_area_geo_col,
        how="left",
    )

    print(f"  Rental locations: {len(rental_df)}")
    print(f"  Floor area locations: {len(floor_area_df)}")
    print(f"  Matched: {merged[floor_area_geo_col].notna().sum()}")

    # Drop the duplicate geo column if different
    if floor_area_geo_col != rental_geo_col and floor_area_geo_col in merged.columns:
        merged = merged.drop(columns=[floor_area_geo_col])

    return merged


def calculate_rent_per_sqm(
    df: pd.DataFrame,
    bedroom_categories: list[str] | None = None,
    rent_col_pattern: str = "rent_{cat}bed",
    sqm_col_pattern: str = "median_sqm_{cat}bed",
    count_col_pattern: str = "count_{cat}bed",
) -> pd.DataFrame:
    """
    Calculate rent per square metre for each bedroom category.

    Args:
        df: DataFrame with rent and floor area columns
        bedroom_categories: List of bedroom categories (default: ["1", "2", "3", "4+"])
        rent_col_pattern: Pattern for rent column names, {cat} replaced with category
        sqm_col_pattern: Pattern for floor area column names
        count_col_pattern: Pattern for observation count columns (for weighting)

    Returns:
        DataFrame with rent_per_sqm columns added
    """
    print("\nCalculating rent per square metre...")

    if bedroom_categories is None:
        bedroom_categories = ["1", "2", "3", "4+"]

    result = df.copy()

    # Calculate rent per sqm for each bedroom category
    for cat in bedroom_categories:
        # Handle special case for 4+ bedrooms
        if cat == "4+":
            rent_col = "rent_4bed_plus"
        else:
            rent_col = rent_col_pattern.format(cat=cat)

        sqm_col = sqm_col_pattern.format(cat=cat)
        output_col = f"rent_per_sqm_{cat}bed"

        if rent_col in result.columns and sqm_col in result.columns:
            result[output_col] = result[rent_col] / result[sqm_col]
            valid_count = result[output_col].notna().sum()
            print(f"  {output_col}: {valid_count} valid values")

    return result


def calculate_weighted_average_rent_per_sqm(
    df: pd.DataFrame,
    bedroom_categories: list[str] | None = None,
    rent_psqm_col_pattern: str = "rent_per_sqm_{cat}bed",
    count_col_pattern: str = "count_{cat}bed",
    output_col: str = "overall_rent_per_sqm",
) -> pd.DataFrame:
    """
    Calculate weighted average rent per sqm across bedroom categories.

    Weights by number of observations in each bedroom category.

    Args:
        df: DataFrame with rent_per_sqm and count columns
        bedroom_categories: List of bedroom categories
        rent_psqm_col_pattern: Pattern for rent per sqm column names
        count_col_pattern: Pattern for count column names
        output_col: Name of output column

    Returns:
        DataFrame with overall weighted average column added
    """
    if bedroom_categories is None:
        bedroom_categories = ["1", "2", "3", "4+"]

    result = df.copy()

    count_cols = [count_col_pattern.format(cat=cat) for cat in bedroom_categories]
    rent_psqm_cols = [rent_psqm_col_pattern.format(cat=cat) for cat in bedroom_categories]

    # Calculate weighted average where we have data
    def weighted_avg(row: pd.Series) -> float:
        weights = []
        values = []
        for count_col, val_col in zip(count_cols, rent_psqm_cols):
            if pd.notna(row.get(count_col)) and pd.notna(row.get(val_col)):
                weights.append(row[count_col])
                values.append(row[val_col])
        if weights:
            return float(np.average(values, weights=weights))
        return np.nan

    result[output_col] = result.apply(weighted_avg, axis=1)

    valid_count = result[output_col].notna().sum()
    print(f"\n  Calculated {output_col} for {valid_count} locations")

    return result


def validate_against_reference(
    df: pd.DataFrame,
    name_col: str = "la_name",
    value_col: str = "overall_rent_per_sqm",
    references: dict[str, float] | None = None,
) -> None:
    """
    Validate results against known reference values.

    Args:
        df: DataFrame with results
        name_col: Column containing location names
        value_col: Column containing values to validate
        references: Dict mapping location names to expected values
    """
    if references is None:
        # Default YIMBY reference values
        references = {
            "Westminster": 44.60,
            "Hartlepool": 7.50,
        }

    print("\n" + "=" * 60)
    print("Validation Against Reference Values")
    print("=" * 60)

    print("\nComparison with reference values:")
    print("-" * 50)

    for la_name, expected in references.items():
        match = df[df[name_col].str.contains(la_name, case=False, na=False)]
        if len(match) > 0:
            actual = match[value_col].values[0]
            diff = actual - expected
            pct_diff = (diff / expected) * 100
            print(f"  {la_name}:")
            print(f"    Expected: £{expected:.2f}/sqm")
            print(f"    Actual:   £{actual:.2f}/sqm")
            print(f"    Diff:     £{diff:+.2f} ({pct_diff:+.1f}%)")
        else:
            print(f"  {la_name}: NOT FOUND")


def summarize_results(
    df: pd.DataFrame,
    name_col: str = "la_name",
    value_col: str = "overall_rent_per_sqm",
    n_top: int = 5,
    n_bottom: int = 5,
) -> None:
    """
    Print summary statistics of rent per sqm results.

    Args:
        df: DataFrame with results
        name_col: Column containing location names
        value_col: Column containing rent per sqm values
        n_top: Number of top (most expensive) to show
        n_bottom: Number of bottom (cheapest) to show
    """
    print(f"\nTop {n_top} most expensive (£/sqm/month):")
    print("-" * 50)
    top = df.nlargest(n_top, value_col)[[name_col, value_col]]
    for _, row in top.iterrows():
        print(f"  {row[name_col]}: £{row[value_col]:.2f}")

    print(f"\nBottom {n_bottom} cheapest (£/sqm/month):")
    print("-" * 50)
    bottom = df.nsmallest(n_bottom, value_col)[[name_col, value_col]]
    for _, row in bottom.iterrows():
        print(f"  {row[name_col]}: £{row[value_col]:.2f}")

    # Overall statistics
    print("\nOverall statistics:")
    print("-" * 50)
    print(f"  Mean:   £{df[value_col].mean():.2f}/sqm")
    print(f"  Median: £{df[value_col].median():.2f}/sqm")
    print(f"  Std:    £{df[value_col].std():.2f}/sqm")
    print(f"  Min:    £{df[value_col].min():.2f}/sqm")
    print(f"  Max:    £{df[value_col].max():.2f}/sqm")
