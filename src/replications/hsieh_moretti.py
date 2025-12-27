"""Hsieh-Moretti (2019) replication pipeline.

"Housing Constraints and Spatial Misallocation"
Original US analysis of GDP costs from housing supply constraints.
Paper: https://www.aeaweb.org/articles?id=10.1257/mac.20170388
"""

from pathlib import Path
from typing import Any

import pandas as pd

from src.core.config import output_path


def run_pipeline(output_dir: Path | None = None, start_year: int = 1964, end_year: int = 2009) -> dict[str, Any]:
    """
    Run the Hsieh-Moretti replication pipeline.

    Args:
        output_dir: Directory to save outputs
        start_year: Start year for analysis (1964 in original)
        end_year: End year for analysis (2009 in original)

    Returns:
        Dictionary with analysis results

    Note:
        Implementation pending - requires:
        - County Business Patterns data
        - ACS/Census housing data
        - Saiz supply elasticities
        - MSA geographic crosswalks
    """
    if output_dir is None:
        output_dir = output_path("hsieh_moretti")

    output_dir.mkdir(parents=True, exist_ok=True)

    raise NotImplementedError(
        "Hsieh-Moretti replication not yet implemented.\n\n"
        "Required data pipelines:\n"
        "  1. CBP employment data (src/datasets/us/cbp.py)\n"
        "  2. ACS housing costs (src/datasets/us/acs.py)\n"
        "  3. Saiz elasticities (src/datasets/us/saiz.py)\n"
        "  4. MSA geography (src/datasets/us/geography.py)\n\n"
        "Required models:\n"
        "  1. Wage adjustment (src/models/wage_adjustment.py) ✓\n"
        "  2. Spatial equilibrium (src/models/spatial_equilibrium.py) ✓\n\n"
        "See REPLICATION_PLAN.md for full implementation details."
    )


def calculate_counterfactual_1964_2009(
    msa_data: pd.DataFrame, target_cities: list[str] | None = None
) -> dict[str, Any]:
    """
    Calculate counterfactual GDP if NYC/SF had average housing constraints.

    This is the core Hsieh-Moretti exercise: what if housing supply
    in New York and San Francisco had been as elastic as the median city?

    Args:
        msa_data: DataFrame with MSA-level data over time
        target_cities: Cities to relax constraints for (default: NYC, SF)

    Returns:
        Dictionary with counterfactual results
    """
    if target_cities is None:
        target_cities = ["New York-Newark-Jersey City", "San Francisco-Oakland-Berkeley"]

    raise NotImplementedError(
        "Counterfactual calculation not yet implemented.\n"
        "Key finding from original: relaxing constraints in NYC/SF would have "
        "raised US GDP by 8.9% from 1964-2009."
    )


if __name__ == "__main__":
    run_pipeline()
