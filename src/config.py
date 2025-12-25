"""Configuration and paths for the rent per sqm pipeline."""

from pathlib import Path

# Project root
PROJECT_ROOT = Path(__file__).parent.parent

# Data directories
DATA_DIR = PROJECT_ROOT / "data"
RAW_DATA_DIR = DATA_DIR / "raw"
INTERMEDIATE_DIR = DATA_DIR / "intermediate"
OUTPUT_DIR = DATA_DIR / "output"

# Raw data files
EPC_DIR = RAW_DATA_DIR / "all-domestic-certificates"
PIPR_FILE = RAW_DATA_DIR / "priceindexofprivaterentsukmonthlypricestatistics6.xlsx"
BOUNDARIES_FILE = RAW_DATA_DIR / "la_boundaries.geojson"

# Intermediate files
EPC_AGGREGATED_FILE = INTERMEDIATE_DIR / "epc_floor_areas.csv"
PIPR_PROCESSED_FILE = INTERMEDIATE_DIR / "pipr_rental_prices.csv"

# Output files
RENT_PSQM_FULL_FILE = OUTPUT_DIR / "rent_per_sqm_by_la.csv"
RENT_PSQM_MODEL_FILE = OUTPUT_DIR / "rent_per_sqm_for_models.csv"

# Plots directory
PLOTS_DIR = PROJECT_ROOT / "plots"
