# Housing Economics Replication Pipeline Plan

## Overview

This plan extends the existing `housing_prices` repo (which calculates rent per square metre by local authority) to support full replication of:

1. **"Cooped Up" (McClements & Hausenloy, 2024)** - UK adaptation of Hsieh-Moretti
2. **Hsieh-Moretti (2019)** - "Housing Constraints and Spatial Misallocation"

The goal is to quantify the GDP cost of Britain's planning restrictions using spatial equilibrium models.

---

## Current Repo Structure

```
housing_prices/
├── src/
│   ├── config.py
│   ├── process_epc.py
│   ├── process_pipr.py
│   └── calculate_rent_per_sqm.py
├── data/
│   ├── raw/
│   ├── intermediate/
│   └── output/
├── notebooks/
├── plots/
├── pyproject.toml
└── uv.lock
```

---

## Proposed Extended Structure

```
housing_prices/
├── src/
│   ├── config.py                    # Extended with new paths
│   │
│   ├── # ===== EXISTING (rent/sqm pipeline) =====
│   ├── process_epc.py
│   ├── process_pipr.py
│   ├── calculate_rent_per_sqm.py
│   │
│   ├── # ===== NEW: DATA INGESTION =====
│   ├── ingest/
│   │   ├── __init__.py
│   │   ├── download_ashe.py         # Download ASHE wage data
│   │   ├── download_pipr.py         # Download PIPR rental data
│   │   ├── download_census.py       # Download Census 2021 data
│   │   ├── download_ttwa.py         # Download TTWA lookups
│   │   └── download_construction.py # Scrape construction costs
│   │
│   ├── # ===== NEW: DATA PROCESSING =====
│   ├── process/
│   │   ├── __init__.py
│   │   ├── process_wages.py         # ASHE wage processing
│   │   ├── process_rents.py         # Refactored PIPR processing
│   │   ├── process_census.py        # Census demographics
│   │   ├── process_geography.py     # LA to TTWA mapping
│   │   └── process_construction.py  # Construction cost indices
│   │
│   ├── # ===== NEW: ANALYSIS =====
│   ├── analysis/
│   │   ├── __init__.py
│   │   ├── wage_regression.py       # Residual wage calculation
│   │   ├── spatial_equilibrium.py   # Core Hsieh-Moretti model
│   │   ├── counterfactual.py        # GDP impact scenarios
│   │   └── sensitivity.py           # Parameter sensitivity
│   │
│   ├── # ===== NEW: OUTPUTS =====
│   ├── outputs/
│   │   ├── __init__.py
│   │   ├── tables.py                # Generate result tables
│   │   └── figures.py               # Generate publication figures
│   │
│   └── # ===== ORCHESTRATION =====
│   ├── pipelines/
│   │   ├── __init__.py
│   │   ├── rent_per_sqm.py          # Existing pipeline (refactored)
│   │   ├── cooped_up.py             # Full Cooped Up replication
│   │   └── full_analysis.py         # Combined pipeline
│   │
│   └── utils/
│       ├── __init__.py
│       ├── download.py              # HTTP/FTP download utilities
│       ├── excel.py                 # Excel parsing utilities
│       └── geography.py             # Geographic code utilities
│
├── data/
│   ├── raw/
│   │   ├── epc/                     # EPC certificates (existing)
│   │   ├── pipr/                    # PIPR rental data
│   │   ├── ashe/                    # ASHE wage tables
│   │   ├── census/                  # Census 2021 tables
│   │   ├── geography/               # Lookups and boundaries
│   │   └── construction/            # Construction cost data
│   │
│   ├── intermediate/
│   │   ├── floor_areas.parquet      # EPC floor areas
│   │   ├── rental_prices.parquet    # PIPR by LA/bedroom
│   │   ├── wages_raw.parquet        # ASHE wages by LA
│   │   ├── wages_adjusted.parquet   # Regression-adjusted wages
│   │   ├── demographics.parquet     # Census characteristics
│   │   ├── ttwa_mapping.parquet     # LA to TTWA crosswalk
│   │   └── construction_costs.parquet
│   │
│   └── output/
│       ├── rent_per_sqm/            # Existing outputs
│       ├── spatial_analysis/        # Hsieh-Moretti outputs
│       │   ├── ttwa_summary.csv
│       │   ├── gdp_impact.csv
│       │   └── counterfactuals.csv
│       └── figures/
│
├── notebooks/
│   ├── visualise_results.ipynb      # Existing
│   ├── 01_data_exploration.ipynb    # New: explore raw data
│   ├── 02_wage_analysis.ipynb       # New: wage patterns
│   ├── 03_spatial_equilibrium.ipynb # New: model walkthrough
│   └── 04_counterfactuals.ipynb     # New: policy scenarios
│
├── tests/
│   ├── __init__.py
│   ├── test_process_wages.py
│   ├── test_wage_regression.py
│   └── test_spatial_equilibrium.py
│
├── docs/
│   ├── data_sources.md              # This document expanded
│   ├── methodology.md               # Model documentation
│   └── replication_notes.md         # Differences from papers
│
├── pyproject.toml                   # Updated dependencies
├── uv.lock
└── README.md                        # Updated
```

---

## Data Sources and Download Scripts

### 1. Wages: ASHE Table 8 (`src/ingest/download_ashe.py`)

**Source:** ONS Annual Survey of Hours and Earnings
**URL Pattern:** `https://www.ons.gov.uk/file?uri=/employmentandlabourmarket/peopleinwork/earningsandworkinghours/datasets/placeofresidencebylocalauthorityashetable8/...`

**Data needed:**

- Median weekly earnings by local authority (Table 8.7a)
- Number of jobs by local authority
- Available from 1997 onwards

**Script tasks:**

```python
# download_ashe.py
def download_ashe_table8(year: int, output_dir: Path) -> Path:
    """Download ASHE Table 8 for a given year."""
    # 1. Navigate to ONS ASHE page
    # 2. Find correct zip file URL for year
    # 3. Download and extract
    # 4. Return path to extracted files

def get_available_years() -> list[int]:
    """Return list of years with ASHE data available."""
    return list(range(1997, 2025))
```

**Output:** `data/raw/ashe/table8_{year}.xlsx`

---

### 2. Rental Prices: PIPR (`src/ingest/download_pipr.py`)

**Source:** ONS Price Index of Private Rents
**URL:** `https://www.ons.gov.uk/economy/inflationandpriceindices/datasets/priceindexofprivaterentsukmonthlypricestatistics`

**Data needed:**

- Monthly rent levels by local authority
- By bedroom category (1, 2, 3, 4+ bed)

**Script tasks:**

```python
# download_pipr.py
def download_pipr_latest(output_dir: Path) -> Path:
    """Download latest PIPR dataset."""
    # 1. Scrape ONS page for latest file URL
    # 2. Download Excel file
    # 3. Return path

def download_pipr_historical(output_dir: Path) -> Path:
    """Download historical PIPR series."""
    pass
```

**Output:** `data/raw/pipr/priceindexofprivaterents_{date}.xlsx`

---

### 3. Census Demographics (`src/ingest/download_census.py`)

**Source:** ONS Census 2021 via Nomis API
**API:** `https://www.nomisweb.co.uk/api/v01/`

**Data needed by local authority:**

- Age distribution (for working-age population)
- Educational attainment (highest qualification)
- Ethnic group composition

**Script tasks:**

```python
# download_census.py
NOMIS_DATASETS = {
    "education": "NM_2091_1",  # Highest qualification
    "ethnicity": "NM_2041_1",  # Ethnic group
    "age": "NM_2021_1",        # Age by single year
}

def download_census_table(
    dataset_id: str,
    geography: str = "TYPE464",  # Local authorities
    output_dir: Path
) -> Path:
    """Download Census 2021 table via Nomis API."""
    pass

def download_all_census_tables(output_dir: Path) -> dict[str, Path]:
    """Download all required Census tables."""
    pass
```

**Output:** `data/raw/census/{table_name}.csv`

---

### 4. Geographic Lookups (`src/ingest/download_ttwa.py`)

**Source:** ONS Open Geography Portal
**URL:** `https://geoportal.statistics.gov.uk/`

**Data needed:**

- Local Authority to TTWA lookup
- LA boundary files (for mapping)
- LA code changes over time

**Script tasks:**

```python
# download_ttwa.py
def download_la_to_ttwa_lookup(output_dir: Path) -> Path:
    """Download LA to TTWA best-fit lookup."""
    # URL: OA21 to TTWA11 to LAD22 lookup
    pass

def download_la_boundaries(output_dir: Path) -> Path:
    """Download LA boundary GeoJSON."""
    pass

def download_la_code_changes(output_dir: Path) -> Path:
    """Download LA code change history."""
    pass
```

**Output:** `data/raw/geography/la_ttwa_lookup.csv`, `data/raw/geography/la_boundaries.geojson`

---

### 5. Construction Costs (`src/ingest/download_construction.py`)

**Source:** Costmodelling.com
**URL:** `https://costmodelling.com/building-costs`, `https://costmodelling.com/regional-variations`

**Data needed:**

- Cost per sqm by building type (6+ storey flats)
- Regional adjustment factors

**Script tasks:**

```python
# download_construction.py
def scrape_building_costs() -> pd.DataFrame:
    """Scrape current building costs from costmodelling.com."""
    # Note: May need manual update if site changes
    pass

def scrape_regional_factors() -> pd.DataFrame:
    """Scrape regional cost adjustment factors."""
    pass
```

**Output:** `data/raw/construction/building_costs.csv`, `data/raw/construction/regional_factors.csv`

---

## Data Processing Scripts

### 1. Process Wages (`src/process/process_wages.py`)

```python
# process_wages.py

def load_ashe_table8(filepath: Path) -> pd.DataFrame:
    """Load and parse ASHE Table 8 Excel file."""
    # Handle ONS formatting quirks
    # Extract median weekly earnings
    # Extract number of jobs
    pass

def process_wages_by_la(year: int) -> pd.DataFrame:
    """
    Process ASHE data for a single year.

    Returns:
        DataFrame with columns:
        - la_code: ONS LA code
        - la_name: LA name
        - median_weekly_earnings: £
        - n_jobs: Number of employee jobs
        - year: Data year
    """
    pass

def aggregate_wages_to_ttwa(
    wages_df: pd.DataFrame,
    la_ttwa_lookup: pd.DataFrame
) -> pd.DataFrame:
    """
    Aggregate LA-level wages to TTWA level.

    Uses employment-weighted average:
    ttwa_wage = sum(la_wage * la_jobs) / sum(la_jobs)
    """
    pass
```

---

### 2. Process Census Demographics (`src/process/process_census.py`)

```python
# process_census.py

def process_education_data(raw_path: Path) -> pd.DataFrame:
    """
    Process Census education data.

    Returns share of population at each qualification level:
    - no_qualifications
    - level_1_2 (GCSE equivalent)
    - level_3 (A-level equivalent)
    - level_4_plus (degree and above)
    """
    pass

def process_ethnicity_data(raw_path: Path) -> pd.DataFrame:
    """
    Process Census ethnicity data.

    Returns share by ethnic group:
    - white
    - asian
    - black
    - mixed
    - other
    """
    pass

def process_age_data(raw_path: Path) -> pd.DataFrame:
    """
    Process Census age data.

    Returns:
    - median_age
    - share_working_age (16-64)
    - share_by_age_band
    """
    pass

def merge_demographics(
    education: pd.DataFrame,
    ethnicity: pd.DataFrame,
    age: pd.DataFrame
) -> pd.DataFrame:
    """Merge all demographic variables by LA."""
    pass
```

---

### 3. Geographic Processing (`src/process/process_geography.py`)

```python
# process_geography.py

def load_la_ttwa_lookup(filepath: Path) -> pd.DataFrame:
    """Load and clean LA to TTWA lookup."""
    pass

def handle_la_code_changes(
    data: pd.DataFrame,
    code_changes: pd.DataFrame
) -> pd.DataFrame:
    """
    Handle LA boundary/code changes over time.

    Key changes to handle:
    - 2019: Bournemouth + Poole + Christchurch = BCP
    - 2019: Suffolk Coastal + Waveney = East Suffolk
    - etc.
    """
    pass

def create_ttwa_summary(
    la_ttwa_lookup: pd.DataFrame,
    la_data: pd.DataFrame
) -> pd.DataFrame:
    """
    Create TTWA-level summary from LA data.

    Handles LAs that span multiple TTWAs using
    population-weighted allocation.
    """
    pass
```

---

## Analysis Scripts

### 1. Wage Regression (`src/analysis/wage_regression.py`)

Following Cooped Up methodology: adjust wages for workforce composition.

```python
# wage_regression.py

def estimate_wage_coefficients(
    individual_data: pd.DataFrame  # If available, e.g., from LFS
) -> dict[str, float]:
    """
    Estimate returns to characteristics from individual-level data.

    Regression: log(wage) ~ education + ethnicity + age + ...

    Returns dict of coefficients.
    """
    # If individual data not available, use Cooped Up coefficients
    pass

def calculate_residual_wages(
    wages: pd.DataFrame,
    demographics: pd.DataFrame,
    coefficients: dict[str, float]
) -> pd.DataFrame:
    """
    Calculate residual wages (adjusted for composition).

    residual_wage = actual_wage - predicted_wage

    where predicted_wage = X' * beta
    """
    pass

# Cooped Up coefficients (from paper Figure 1)
COOPED_UP_COEFFICIENTS = {
    "level_4_plus": 0.45,  # Approximate from regression line
    "nonwhite": -0.05,
    "age": 0.002,
    # ... etc
}
```

---

### 2. Spatial Equilibrium Model (`src/analysis/spatial_equilibrium.py`)

Core Hsieh-Moretti framework adapted for UK.

```python
# spatial_equilibrium.py

from dataclasses import dataclass
from typing import Optional
import numpy as np
import pandas as pd

@dataclass
class ModelParameters:
    """Hsieh-Moretti model parameters."""
    alpha: float = 0.65      # Labour share
    eta: float = 0.25        # Agglomeration elasticity
    theta: float = 2.0       # Labour mobility (inverse Frechet shape)
    gamma_median: float = 1.75  # Median housing supply elasticity

    # UK-specific (from Cooped Up)
    housing_share: float = 0.33  # Share of expenditure on housing

@dataclass
class CityData:
    """Data for a single city/TTWA."""
    name: str
    employment: float
    wage: float              # Residual wage
    rent: float              # Rent per sqm or similar
    supply_elasticity: Optional[float] = None

class SpatialEquilibriumModel:
    """
    Hsieh-Moretti spatial equilibrium model.

    Key equations:
    - Labour supply: L_i = (V * Z_i / P_i^beta)^theta * L_bar
    - Housing price: P_i = c * L_i^(1/gamma_i)
    - Productivity: W_i = A_i * L_i^(eta-1)
    - Aggregate output: Y = sum(A_i * L_i^eta)
    """

    def __init__(self, params: ModelParameters):
        self.params = params

    def calculate_productivity(
        self,
        wages: np.ndarray,
        rents: np.ndarray
    ) -> np.ndarray:
        """
        Back out city TFP from wages and rents.

        From spatial equilibrium:
        Z_i = W_i / P_i^beta

        where beta = housing_share / (1 - housing_share)
        """
        pass

    def calculate_counterfactual_employment(
        self,
        current_employment: np.ndarray,
        current_rents: np.ndarray,
        counterfactual_rents: np.ndarray,
        productivity: np.ndarray
    ) -> np.ndarray:
        """
        Calculate employment distribution under counterfactual rents.
        """
        pass

    def calculate_gdp_impact(
        self,
        current_employment: np.ndarray,
        counterfactual_employment: np.ndarray,
        productivity: np.ndarray
    ) -> float:
        """
        Calculate GDP change from reallocation.

        Y_new / Y_old = sum(A_i * L_i_new^eta) / sum(A_i * L_i_old^eta)
        """
        pass

def run_cooped_up_analysis(
    ttwa_data: pd.DataFrame,
    params: ModelParameters,
    counterfactual_rent: float  # Target rent (construction cost)
) -> dict:
    """
    Run full Cooped Up replication.

    Returns:
        - gdp_impact_nominal: Percentage GDP change
        - gdp_impact_real: Real GDP change (adjusted for rent)
        - employment_shifts: DataFrame of employment changes by TTWA
        - welfare_impact: Welfare change estimate
    """
    pass
```

---

### 3. Counterfactual Scenarios (`src/analysis/counterfactual.py`)

```python
# counterfactual.py

def calculate_construction_cost_rent(
    construction_costs: pd.DataFrame,
    target_density: str = "6_storey_flats"
) -> pd.DataFrame:
    """
    Calculate implied rent if prices = construction costs.

    Following Cooped Up methodology:
    - 80-85% of building is rentable space
    - Cost includes demolition of 2-storey building
    - Regional adjustment factors applied
    """
    pass

def run_conservative_scenario(
    ttwa_data: pd.DataFrame,
    model: SpatialEquilibriumModel
) -> dict:
    """
    Conservative scenario:
    - Project size: £1m
    - Project levies: 150%
    - Supply elasticity: 1.75
    """
    pass

def run_central_scenario(
    ttwa_data: pd.DataFrame,
    model: SpatialEquilibriumModel
) -> dict:
    """
    Central scenario:
    - Project size: £10m
    - Project levies: 100%
    - Supply elasticity: 10
    """
    pass

def run_stretch_scenario(
    ttwa_data: pd.DataFrame,
    model: SpatialEquilibriumModel
) -> dict:
    """
    Stretch scenario:
    - Project size: £100m
    - Project levies: 0%
    - Supply elasticity: infinite
    - Price convergence to population-weighted mean
    """
    pass
```

---

## Pipeline Orchestration

### Main Pipeline (`src/pipelines/cooped_up.py`)

```python
# cooped_up.py

import logging
from pathlib import Path

from src.ingest import (
    download_ashe,
    download_pipr,
    download_census,
    download_ttwa,
    download_construction
)
from src.process import (
    process_wages,
    process_rents,
    process_census,
    process_geography,
    process_construction
)
from src.analysis import (
    wage_regression,
    spatial_equilibrium,
    counterfactual
)
from src.outputs import tables, figures

logger = logging.getLogger(__name__)

def run_data_ingestion(config: dict) -> None:
    """Step 1: Download all raw data."""
    logger.info("Downloading ASHE wage data...")
    download_ashe.download_ashe_table8(
        year=config["year"],
        output_dir=config["raw_dir"] / "ashe"
    )

    logger.info("Downloading PIPR rental data...")
    download_pipr.download_pipr_latest(
        output_dir=config["raw_dir"] / "pipr"
    )

    logger.info("Downloading Census data...")
    download_census.download_all_census_tables(
        output_dir=config["raw_dir"] / "census"
    )

    logger.info("Downloading geographic lookups...")
    download_ttwa.download_la_to_ttwa_lookup(
        output_dir=config["raw_dir"] / "geography"
    )

    logger.info("Downloading construction costs...")
    download_construction.scrape_building_costs()

def run_data_processing(config: dict) -> None:
    """Step 2: Process raw data into analysis-ready format."""
    logger.info("Processing wage data...")
    wages = process_wages.process_wages_by_la(config["year"])

    logger.info("Processing rental data...")
    rents = process_rents.process_pipr_data(config["raw_dir"] / "pipr")

    logger.info("Processing Census demographics...")
    demographics = process_census.process_all_demographics(
        config["raw_dir"] / "census"
    )

    logger.info("Processing geographic mappings...")
    la_ttwa = process_geography.load_la_ttwa_lookup(
        config["raw_dir"] / "geography"
    )

    # Aggregate to TTWA level
    logger.info("Aggregating to TTWA level...")
    ttwa_wages = process_wages.aggregate_wages_to_ttwa(wages, la_ttwa)
    ttwa_rents = process_rents.aggregate_rents_to_ttwa(rents, la_ttwa)
    ttwa_demographics = process_geography.create_ttwa_summary(
        la_ttwa, demographics
    )

    # Merge all TTWA data
    ttwa_data = (
        ttwa_wages
        .merge(ttwa_rents, on="ttwa_code")
        .merge(ttwa_demographics, on="ttwa_code")
    )

    # Save intermediate
    ttwa_data.to_parquet(config["intermediate_dir"] / "ttwa_data.parquet")

def run_analysis(config: dict) -> None:
    """Step 3: Run spatial equilibrium analysis."""
    ttwa_data = pd.read_parquet(
        config["intermediate_dir"] / "ttwa_data.parquet"
    )

    logger.info("Calculating residual wages...")
    ttwa_data = wage_regression.calculate_residual_wages(
        ttwa_data,
        coefficients=wage_regression.COOPED_UP_COEFFICIENTS
    )

    logger.info("Running spatial equilibrium model...")
    params = spatial_equilibrium.ModelParameters()
    model = spatial_equilibrium.SpatialEquilibriumModel(params)

    # Run scenarios
    logger.info("Running counterfactual scenarios...")
    results = {
        "conservative": counterfactual.run_conservative_scenario(ttwa_data, model),
        "central": counterfactual.run_central_scenario(ttwa_data, model),
        "stretch": counterfactual.run_stretch_scenario(ttwa_data, model),
    }

    # Save results
    for scenario, result in results.items():
        pd.DataFrame(result).to_csv(
            config["output_dir"] / f"results_{scenario}.csv"
        )

def run_outputs(config: dict) -> None:
    """Step 4: Generate tables and figures."""
    logger.info("Generating output tables...")
    tables.generate_main_results_table(config["output_dir"])
    tables.generate_ttwa_summary_table(config["output_dir"])

    logger.info("Generating figures...")
    figures.plot_wage_rent_scatter(config["output_dir"])
    figures.plot_employment_shift_map(config["output_dir"])
    figures.plot_gdp_impact_comparison(config["output_dir"])

def main():
    """Run full Cooped Up replication pipeline."""
    config = {
        "year": 2023,
        "raw_dir": Path("data/raw"),
        "intermediate_dir": Path("data/intermediate"),
        "output_dir": Path("data/output/spatial_analysis"),
    }

    run_data_ingestion(config)
    run_data_processing(config)
    run_analysis(config)
    run_outputs(config)

    logger.info("Pipeline complete!")

if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    main()
```

---

## Dependencies to Add (`pyproject.toml`)

```toml
[project]
dependencies = [
    # Existing
    "pandas>=2.0",
    "numpy>=1.24",
    "openpyxl>=3.1",
    "geopandas>=0.14",
    "matplotlib>=3.8",
    "seaborn>=0.13",
    "jupyter>=1.0",

    # New
    "requests>=2.31",          # HTTP downloads
    "httpx>=0.27",             # Async HTTP
    "beautifulsoup4>=4.12",    # Web scraping
    "lxml>=5.0",               # HTML/XML parsing
    "pyarrow>=15.0",           # Parquet support
    "scipy>=1.12",             # Optimisation
    "statsmodels>=0.14",       # Regression
    "tqdm>=4.66",              # Progress bars
    "pydantic>=2.5",           # Data validation
    "typer>=0.9",              # CLI
]

[project.optional-dependencies]
dev = [
    "pytest>=8.0",
    "pytest-cov>=4.1",
    "black>=24.0",
    "ruff>=0.2",
    "mypy>=1.8",
]
```

---

## Implementation Order

### Phase 1: Data Infrastructure (Week 1)

1. [ ] Set up new directory structure
2. [ ] Implement `download_ashe.py`
3. [ ] Implement `download_census.py` (Nomis API)
4. [ ] Implement `download_ttwa.py`
5. [ ] Implement `download_construction.py`
6. [ ] Add tests for downloaders

### Phase 2: Data Processing (Week 2)

1. [ ] Implement `process_wages.py`
2. [ ] Implement `process_census.py`
3. [ ] Implement `process_geography.py`
4. [ ] Implement LA to TTWA aggregation
5. [ ] Handle LA code changes over time
6. [ ] Add tests for processors

### Phase 3: Analysis (Week 3)

1. [ ] Implement `wage_regression.py`
2. [ ] Implement core `spatial_equilibrium.py` model
3. [ ] Implement `counterfactual.py` scenarios
4. [ ] Validate against Cooped Up results
5. [ ] Add sensitivity analysis

### Phase 4: Outputs & Documentation (Week 4)

1. [ ] Implement table generation
2. [ ] Implement figure generation
3. [ ] Create analysis notebooks
4. [ ] Write methodology documentation
5. [ ] Create README with replication instructions

---

## Validation Checkpoints

### Checkpoint 1: Wage Data

- [ ] Median weekly earnings matches ONS published figures
- [ ] London wage premium ~£200/week above national average
- [ ] Wage ratio between highest/lowest TTWA ~1.5-1.6x (per Cooped Up)

### Checkpoint 2: Rental Data

- [ ] Rent per sqm matches YIMBY Alliance figures (within 20%)
- [ ] London rents ~5-6x higher than cheapest areas

### Checkpoint 3: TTWA Aggregation

- [ ] 228 TTWAs in final dataset
- [ ] London TTWA population ~9-10 million
- [ ] Employment figures sum to UK total

### Checkpoint 4: Model Results

- [ ] GDP impact in range 2.9%-6.1% (matching Cooped Up)
- [ ] Largest employment shifts from Northern TTWAs to London/South East
- [ ] Results sensitive to θ (mobility) and γ (supply elasticity)

---

## Key Differences from Cooped Up

Document these in `docs/replication_notes.md`:

1. **Data vintage**: Using 2023/2024 data vs. 2023 in original
2. **Rent measure**: Rent per sqm vs. raw median rent
3. **LA boundaries**: Using 2023 boundaries (some mergers since original)
4. **Census data**: Using 2021 Census (same as original)
5. **Construction costs**: Updated to 2024 figures

---

## References

1. Hsieh, C. T., & Moretti, E. (2019). Housing constraints and spatial misallocation. _American Economic Journal: Macroeconomics_, 11(2), 1-39.

2. McClements, D., & Hausenloy, J. (2024). Cooped Up: Quantifying the Cost of Housing Restrictions. Adam Smith Institute.

3. Hilber, C. A., & Vermeulen, W. (2016). The impact of supply constraints on house prices in England. _The Economic Journal_, 126(591), 358-405.

4. Saiz, A. (2010). The geographic determinants of housing supply. _The Quarterly Journal of Economics_, 125(3), 1253-1296.
