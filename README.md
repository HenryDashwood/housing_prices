# Urban Economics Replication Pipeline

A modular framework for replicating urban economics research on housing constraints and spatial misallocation. This repository hosts datasets and models that can be mixed and matched to replicate various papers and run custom analyses.

## Goal

Quantify how much richer we could be with more liberal planning laws by:

1. Hosting standardised datasets for UK and US housing/labor markets
2. Implementing reusable analytical models (rent calculation, wage adjustment, spatial equilibrium)
3. Providing paper replication pipelines that wire datasets to models

## Project Structure

```
housing_prices/
├── src/
│   ├── datasets/                    # Data ingestion + processing
│   │   ├── base.py                  # Abstract Dataset class
│   │   ├── uk/
│   │   │   ├── epc.py               # Energy Performance Certificates (floor areas)
│   │   │   ├── pipr.py              # Price Index of Private Rents
│   │   │   ├── ashe.py              # Annual Survey of Hours and Earnings
│   │   │   ├── census.py            # Census 2021 demographics
│   │   │   ├── geography.py         # LA boundaries, TTWA lookups
│   │   │   └── construction.py      # Construction costs
│   │   └── us/
│   │       ├── cbp.py               # County Business Patterns
│   │       ├── acs.py               # American Community Survey
│   │       ├── saiz.py              # Housing supply elasticities
│   │       └── geography.py         # MSA crosswalks
│   │
│   ├── models/                      # Reusable analytical models
│   │   ├── rent_per_sqm.py          # Rent per square metre calculation
│   │   ├── wage_adjustment.py       # Composition-adjusted wages
│   │   └── spatial_equilibrium.py   # Hsieh-Moretti framework
│   │
│   ├── replications/                # Paper-specific pipelines
│   │   ├── yimby_rent_map.py        # YIMBY Alliance rent analysis
│   │   ├── cooped_up.py             # UK GDP cost (McClements 2024)
│   │   └── hsieh_moretti.py         # US GDP cost (Hsieh-Moretti 2019)
│   │
│   └── core/                        # Shared utilities
│       ├── config.py                # Paths and configuration
│       ├── download.py              # HTTP download utilities
│       └── geo.py                   # Geographic code utilities
│
├── data/
│   ├── raw/                         # Downloaded source data
│   │   ├── uk/                      # UK datasets by source
│   │   └── us/                      # US datasets by source
│   ├── processed/                   # Cleaned, analysis-ready data
│   └── output/                      # Results by replication
│       ├── yimby_rent_map/
│       ├── cooped_up/
│       └── hsieh_moretti/
│
├── notebooks/                       # Analysis notebooks
├── plots/                           # Generated visualisations
├── tests/                           # Test suite
└── docs/                            # Documentation
```

## Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                        DATASETS LAYER                            │
├─────────────────────────────────────────────────────────────────┤
│  UK: EPC │ PIPR │ ASHE │ Census │ Geography │ Construction      │
│  US: CBP │ ACS  │ Saiz │ Geography                              │
└─────────────────────┬───────────────────────────────────────────┘
                      │
                      ▼
┌─────────────────────────────────────────────────────────────────┐
│                         MODELS LAYER                             │
├─────────────────────────────────────────────────────────────────┤
│  Rent per sqm  │  Wage Adjustment  │  Spatial Equilibrium       │
└─────────────────────┬───────────────────────────────────────────┘
                      │
                      ▼
┌─────────────────────────────────────────────────────────────────┐
│                      REPLICATIONS LAYER                          │
├─────────────────────────────────────────────────────────────────┤
│  YIMBY Rent Map  │  Cooped Up (UK)  │  Hsieh-Moretti (US)       │
└─────────────────────────────────────────────────────────────────┘
```

## Quick Start

### Setup

Requires Python 3.13+ and [uv](https://docs.astral.sh/uv/).

```bash
uv sync
```

### Running the YIMBY Rent Map Replication

This is the currently implemented pipeline. It calculates rent per square metre by UK local authority.

```bash
# Run the full pipeline
uv run python -m src.replications.yimby_rent_map

# Or from Python
from src.replications.yimby_rent_map import run_pipeline
result = run_pipeline()
```

### Data Preparation

1. **EPC Data** (required for YIMBY rent map):

   - Visit https://epc.opendatacommunities.org/
   - Register and download all domestic certificates (~6GB)
   - Extract to `data/raw/uk/epc/`

2. **PIPR Data** (required for YIMBY rent map):
   - Download from [ONS PIPR page](https://www.ons.gov.uk/economy/inflationandpriceindices/datasets/priceindexofprivaterentsukmonthlypricestatistics)
   - Save to `data/raw/uk/pipr/`

## Implemented Features

### ✅ Datasets

| Dataset              | Country | Status         |
| -------------------- | ------- | -------------- |
| EPC (floor areas)    | UK      | ✅ Implemented |
| PIPR (rental prices) | UK      | ✅ Implemented |
| LA Boundaries        | UK      | ✅ Implemented |
| ASHE (wages)         | UK      | 🔲 Stub only   |
| Census 2021          | UK      | 🔲 Stub only   |
| Construction costs   | UK      | 🔲 Stub only   |
| CBP (employment)     | US      | 🔲 Stub only   |
| ACS (housing)        | US      | 🔲 Stub only   |
| Saiz elasticities    | US      | 🔲 Stub only   |

### ✅ Models

| Model               | Status             |
| ------------------- | ------------------ |
| Rent per sqm        | ✅ Implemented     |
| Wage adjustment     | ✅ Framework ready |
| Spatial equilibrium | ✅ Framework ready |

### ✅ Replications

| Paper                | Status         |
| -------------------- | -------------- |
| YIMBY Rent Map       | ✅ Implemented |
| Cooped Up (2024)     | 🔲 Stub only   |
| Hsieh-Moretti (2019) | 🔲 Stub only   |

## Sample Results (YIMBY Rent Map)

| Local Authority        | Rent per sqm (£/month) |
| ---------------------- | ---------------------- |
| Westminster            | £52.56                 |
| Kensington and Chelsea | £51.75                 |
| Camden                 | £43.79                 |
| ...                    | ...                    |
| County Durham          | £9.22                  |
| Powys                  | £9.05                  |
| Hartlepool             | £8.75                  |

## Documentation

- [DATA_SOURCES.md](docs/DATA_SOURCES.md) - All data sources with download links
- [REPLICATION_PLAN.md](REPLICATION_PLAN.md) - Detailed implementation plan

## References

1. **YIMBY Alliance Rent Map** - https://yimbyalliance.org/2025/12/18/how-much-space-can-you-afford-to-rent

2. **Cooped Up** (McClements & Hausenloy, 2024) - Quantifying the Cost of Housing Restrictions. Adam Smith Institute.

3. **Hsieh & Moretti** (2019) - Housing Constraints and Spatial Misallocation. _American Economic Journal: Macroeconomics_, 11(2), 1-39.

## License

MIT
