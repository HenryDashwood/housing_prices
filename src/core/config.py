"""Configuration and paths for the urban economics pipeline.

Supports multi-country data organization with UK and US datasets.
"""

from pathlib import Path
from typing import Literal

# Country type
Country = Literal["uk", "us"]

# Project root
PROJECT_ROOT = Path(__file__).parent.parent.parent

# Base directories
DATA_DIR = PROJECT_ROOT / "data"
PLOTS_DIR = PROJECT_ROOT / "plots"
NOTEBOOKS_DIR = PROJECT_ROOT / "notebooks"
DOCS_DIR = PROJECT_ROOT / "docs"

# Data subdirectories
RAW_DATA_DIR = DATA_DIR / "raw"
PROCESSED_DATA_DIR = DATA_DIR / "processed"
OUTPUT_DIR = DATA_DIR / "output"


def raw_path(country: Country, dataset: str) -> Path:
    """
    Get path to raw data directory for a country/dataset.

    Args:
        country: Country code ("uk" or "us")
        dataset: Dataset name (e.g., "epc", "pipr", "ashe")

    Returns:
        Path to raw data directory

    Example:
        >>> raw_path("uk", "epc")
        Path(".../data/raw/uk/epc")
    """
    return RAW_DATA_DIR / country / dataset


def processed_path(country: Country, dataset: str) -> Path:
    """
    Get path to processed data directory for a country/dataset.

    Args:
        country: Country code ("uk" or "us")
        dataset: Dataset name

    Returns:
        Path to processed data directory

    Example:
        >>> processed_path("uk", "epc")
        Path(".../data/processed/uk/epc")
    """
    return PROCESSED_DATA_DIR / country / dataset


def output_path(replication: str) -> Path:
    """
    Get path to output directory for a paper replication.

    Args:
        replication: Replication name (e.g., "yimby_rent_map", "cooped_up")

    Returns:
        Path to output directory

    Example:
        >>> output_path("cooped_up")
        Path(".../data/output/cooped_up")
    """
    return OUTPUT_DIR / replication


# ============================================================
# Legacy paths for backwards compatibility
# These will be deprecated once migration is complete
# ============================================================

# UK EPC data
EPC_DIR = raw_path("uk", "epc")

# UK PIPR data
PIPR_FILE = raw_path("uk", "pipr") / "priceindexofprivaterentsukmonthlypricestatistics.xlsx"

# UK boundaries
BOUNDARIES_FILE = raw_path("uk", "geography") / "la_boundaries_2024.geojson"

# Legacy intermediate files (to be migrated to processed/)
INTERMEDIATE_DIR = DATA_DIR / "intermediate"
EPC_AGGREGATED_FILE = INTERMEDIATE_DIR / "epc_floor_areas.csv"
PIPR_PROCESSED_FILE = INTERMEDIATE_DIR / "pipr_rental_prices.csv"

# Legacy output files
RENT_PSQM_FULL_FILE = output_path("yimby_rent_map") / "rent_per_sqm_by_la.csv"
RENT_PSQM_MODEL_FILE = output_path("yimby_rent_map") / "rent_per_sqm_for_models.csv"


def ensure_dirs() -> None:
    """Create all required directories if they don't exist."""
    dirs = [
        RAW_DATA_DIR,
        PROCESSED_DATA_DIR,
        OUTPUT_DIR,
        PLOTS_DIR,
        INTERMEDIATE_DIR,  # Legacy
        # UK raw data
        raw_path("uk", "epc"),
        raw_path("uk", "pipr"),
        raw_path("uk", "ashe"),
        raw_path("uk", "census"),
        raw_path("uk", "geography"),
        raw_path("uk", "construction"),
        # US raw data
        raw_path("us", "cbp"),
        raw_path("us", "acs"),
        raw_path("us", "saiz"),
        raw_path("us", "geography"),
        # Processed data
        processed_path("uk", "epc"),
        processed_path("uk", "pipr"),
        processed_path("us", "cbp"),
        # Outputs
        output_path("yimby_rent_map"),
        output_path("cooped_up"),
        output_path("hsieh_moretti"),
    ]
    for d in dirs:
        d.mkdir(parents=True, exist_ok=True)


if __name__ == "__main__":
    print(f"Project root: {PROJECT_ROOT}")
    print(f"Data dir: {DATA_DIR}")
    print(f"UK EPC raw path: {raw_path('uk', 'epc')}")
    print(f"UK EPC processed path: {processed_path('uk', 'epc')}")
    print(f"Cooped Up output path: {output_path('cooped_up')}")
