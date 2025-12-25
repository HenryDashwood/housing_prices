# Rent per Square Metre by Local Authority

Pipeline to calculate rent per square metre across England and Wales local authorities, replicating the [YIMBY Alliance analysis](https://yimbyalliance.org/2025/12/18/how-much-space-can-you-afford-to-rent).

## Project Structure

```
housing_prices/
├── src/                     # Pipeline scripts
│   ├── config.py            # Paths and configuration
│   ├── process_epc.py       # EPC data processing
│   ├── process_pipr.py      # PIPR rental data processing
│   └── calculate_rent_per_sqm.py  # Main pipeline
├── data/
│   ├── raw/                 # Raw input data
│   │   ├── all-domestic-certificates/  # EPC certificates by LA
│   │   ├── priceindexofprivaterentsukmonthlypricestatistics6.xlsx
│   │   └── la_boundaries.geojson
│   ├── intermediate/        # Processed intermediate files
│   │   ├── epc_floor_areas.csv
│   │   └── pipr_rental_prices.csv
│   └── output/              # Final outputs
│       ├── rent_per_sqm_by_la.csv
│       └── rent_per_sqm_for_models.csv
├── plots/                   # Generated visualisations
├── notebooks/               # Jupyter notebooks
│   └── visualise_results.ipynb
├── plan.md                  # Original project plan
└── README.md
```

## Data Sources

1. **Energy Performance Certificates (EPC)** - Floor area data

   - Source: https://epc.opendatacommunities.org
   - Download: Bulk download of all domestic certificates (~6GB)

2. **Price Index of Private Rents (PIPR)** - Monthly rental prices by LA
   - Source: https://www.ons.gov.uk/economy/inflationandpriceindices/datasets/priceindexofprivaterentsukmonthlypricestatistics

## Setup

Requires Python 3.13+ and uv. From the parent directory:

```bash
uv sync
```

## Data Preparation

1. Download EPC bulk data and extract to `data/raw/all-domestic-certificates/`
2. Download PIPR Excel file to `data/raw/priceindexofprivaterentsukmonthlypricestatistics6.xlsx`

## Running the Pipeline

```bash
cd housing_prices/src
uv run python calculate_rent_per_sqm.py
```

Or from the parent directory:

```bash
cd src && uv run python calculate_rent_per_sqm.py
```

## Pipeline Steps

1. **EPC Processing** (`src/process_epc.py`)

   - Loads ~28.7M certificates from 347 LA folders
   - Filters to private rented properties (~5.9M)
   - Removes implausible floor areas (<10 or >800 sqm)
   - Filters to last 5 years (~1.7M records)
   - Maps habitable rooms to bedroom categories (1, 2, 3, 4+)
   - Calculates median floor area by LA and bedroom count

2. **PIPR Processing** (`src/process_pipr.py`)

   - Extracts latest month of rental prices
   - Filters to local authority level (316 LAs)
   - Gets rents by bedroom category

3. **Calculation** (`src/calculate_rent_per_sqm.py`)
   - Joins EPC floor areas with PIPR rents
   - Calculates `rent_per_sqm = monthly_rent / median_floor_area`
   - Computes weighted average across bedroom categories

## Visualisation

Run the notebook to generate charts and maps:

```bash
uv run jupyter lab notebooks/visualise_results.ipynb
```

Generates:

- `plots/rent_psqm_distribution.png` - Histogram
- `plots/rent_psqm_top_bottom.png` - Top/bottom 20 bar charts
- `plots/rent_psqm_by_bedroom.png` - By bedroom count
- `plots/rent_psqm_map.png` - Choropleth map
- `plots/rent_psqm_london.png` - London zoom

## Outputs

### `data/output/rent_per_sqm_by_la.csv`

Full breakdown with 18 columns:

| Column                 | Description                               |
| ---------------------- | ----------------------------------------- |
| `la_code`              | ONS local authority code                  |
| `la_name`              | Local authority name                      |
| `region`               | Region/country                            |
| `rent_Xbed`            | Monthly rent for X bedrooms (£)           |
| `median_sqm_Xbed`      | Median floor area for X bedrooms (sqm)    |
| `rent_per_sqm_Xbed`    | Rent per sqm for X bedrooms (£/sqm/month) |
| `overall_rent_per_sqm` | Weighted average (£/sqm/month)            |
| `n_epc_obs`            | Number of EPC observations                |
| `data_date`            | PIPR data month                           |

### `data/output/rent_per_sqm_for_models.csv`

Simplified output for economic models:

| Column                 | Description          |
| ---------------------- | -------------------- |
| `la_code`              | Local authority code |
| `la_name`              | Local authority name |
| `overall_rent_per_sqm` | £/sqm/month          |
| `log_rent_per_sqm`     | Natural log          |
| `rent_per_sqm_annual`  | Annualised (×12)     |

## Sample Results

| Local Authority        | Rent per sqm (£/month) |
| ---------------------- | ---------------------- |
| Westminster            | 52.56                  |
| Kensington and Chelsea | 51.75                  |
| Camden                 | 43.79                  |
| ...                    | ...                    |
| County Durham          | 9.22                   |
| Powys                  | 9.05                   |
| Hartlepool             | 8.75                   |

## Validation

Results are ~17% higher than YIMBY published figures (Westminster: £44.60, Hartlepool: £7.50), likely due to more recent data (Nov 2025 vs Dec 2025 article baseline).

## References

- YIMBY Alliance article: https://yimbyalliance.org/2025/12/18/how-much-space-can-you-afford-to-rent
- Original code: https://github.com/thicknavyrain/rents_per_sq_ft_uk
- Interactive map: https://maps.yimbyalliance.org/psqm-rents
