"""Cooped Up replication pipeline (McClements & Hausenloy, 2024).

UK adaptation of Hsieh-Moretti to quantify the GDP cost of housing restrictions.
Paper: https://www.adamsmith.org/research/cooped-up-quantifying-the-cost-of-housing-restrictions
"""

from pathlib import Path
from typing import Any

import pandas as pd

from src.core.config import output_path


def run_pipeline(
    output_dir: Path | None = None,
    scenario: str = "central",
) -> dict[str, Any]:
    """
    Run the Cooped Up replication pipeline.

    Args:
        output_dir: Directory to save outputs
        scenario: Scenario to run ("conservative", "central", or "stretch")

    Returns:
        Dictionary with analysis results

    Note:
        Implementation pending - requires:
        - ASHE wage data
        - Census demographic data
        - PIPR rental data
        - Geographic lookups (LA to TTWA)
        - Construction cost data
    """
    if output_dir is None:
        output_dir = output_path("cooped_up")

    output_dir.mkdir(parents=True, exist_ok=True)

    raise NotImplementedError(
        "Cooped Up replication not yet implemented.\n\n"
        "Required data pipelines:\n"
        "  1. ASHE wages (src/datasets/uk/ashe.py)\n"
        "  2. Census demographics (src/datasets/uk/census.py)\n"
        "  3. PIPR rents (src/datasets/uk/pipr.py) ✓\n"
        "  4. LA-TTWA geography (src/datasets/uk/geography.py)\n"
        "  5. Construction costs (src/datasets/uk/construction.py)\n\n"
        "Required models:\n"
        "  1. Wage adjustment (src/models/wage_adjustment.py) ✓\n"
        "  2. Spatial equilibrium (src/models/spatial_equilibrium.py) ✓\n\n"
        "See REPLICATION_PLAN.md for full implementation details."
    )


def run_conservative_scenario(ttwa_data: pd.DataFrame) -> dict[str, Any]:
    """
    Run conservative scenario.

    - Project size: £1m
    - Project levies: 150%
    - Supply elasticity: 1.75

    Args:
        ttwa_data: DataFrame with TTWA-level data

    Returns:
        Scenario results
    """
    raise NotImplementedError("Conservative scenario not yet implemented")


def run_central_scenario(ttwa_data: pd.DataFrame) -> dict[str, Any]:
    """
    Run central scenario.

    - Project size: £10m
    - Project levies: 100%
    - Supply elasticity: 10

    Args:
        ttwa_data: DataFrame with TTWA-level data

    Returns:
        Scenario results
    """
    raise NotImplementedError("Central scenario not yet implemented")


def run_stretch_scenario(ttwa_data: pd.DataFrame) -> dict[str, Any]:
    """
    Run stretch scenario.

    - Project size: £100m
    - Project levies: 0%
    - Supply elasticity: infinite
    - Price convergence to population-weighted mean

    Args:
        ttwa_data: DataFrame with TTWA-level data

    Returns:
        Scenario results
    """
    raise NotImplementedError("Stretch scenario not yet implemented")


if __name__ == "__main__":
    run_pipeline()
