# Data Sources Reference

Quick reference for all datasets needed for the Cooped Up / Hsieh-Moretti replication.

---

## UK Data Sources (for Cooped Up replication)

### 1. Wages: ONS ASHE Table 8

| Item              | Details                                                                                                                                   |
| ----------------- | ----------------------------------------------------------------------------------------------------------------------------------------- |
| **Description**   | Annual Survey of Hours and Earnings by place of residence                                                                                 |
| **Geography**     | Local Authority                                                                                                                           |
| **Years**         | 1997-present                                                                                                                              |
| **Key variables** | Median weekly earnings, number of jobs                                                                                                    |
| **URL**           | https://www.ons.gov.uk/employmentandlabourmarket/peopleinwork/earningsandworkinghours/datasets/placeofresidencebylocalauthorityashetable8 |
| **Format**        | ZIP containing Excel files                                                                                                                |
| **Notes**         | Table 8.7a has median earnings. Also see Tables 11/12 for TTWA-level data directly.                                                       |

### 2. Rental Prices: ONS PIPR

| Item              | Details                                                                                                           |
| ----------------- | ----------------------------------------------------------------------------------------------------------------- |
| **Description**   | Price Index of Private Rents                                                                                      |
| **Geography**     | Local Authority (England & Wales), BRMA (Scotland & NI)                                                           |
| **Frequency**     | Monthly                                                                                                           |
| **Key variables** | Median rent by bedroom count                                                                                      |
| **URL**           | https://www.ons.gov.uk/economy/inflationandpriceindices/datasets/priceindexofprivaterentsukmonthlypricestatistics |
| **Format**        | Excel                                                                                                             |
| **Notes**         | Replaced PRMS in March 2024. City of London and Isles of Scilly excluded.                                         |

### 3. Census Demographics: ONS Census 2021

| Item                | Details                                |
| ------------------- | -------------------------------------- |
| **Description**     | Census 2021 population characteristics |
| **Geography**       | Local Authority and below              |
| **Key variables**   | Education, ethnicity, age              |
| **Portal**          | https://www.nomisweb.co.uk/            |
| **API**             | https://www.nomisweb.co.uk/api/v01/    |
| **Custom datasets** | https://www.ons.gov.uk/datasets/create |

**Specific tables needed:**

| Variable  | Nomis Dataset | Description                 |
| --------- | ------------- | --------------------------- |
| Education | TS067         | Highest qualification by LA |
| Ethnicity | TS021         | Ethnic group by LA          |
| Age       | TS007         | Age by single year          |

### 4. Geographic Lookups: ONS Open Geography Portal

| Item            | Details                              |
| --------------- | ------------------------------------ |
| **Description** | Geographic boundary and lookup files |
| **Portal**      | https://geoportal.statistics.gov.uk/ |
| **Key files**   | LA to TTWA lookup, LA boundaries     |

**Specific files:**

| File                                       | URL/Search term                                              |
| ------------------------------------------ | ------------------------------------------------------------ |
| LA to TTWA lookup (2021 LAs to 2011 TTWAs) | Search: "Output Area 2021 to TTWAs 2011 to LAD 2022 Lookup"  |
| LA boundaries (GeoJSON)                    | Search: "Local Authority Districts December 2023 Boundaries" |
| TTWA boundaries                            | Search: "Travel to Work Areas December 2011 Boundaries"      |

**Direct lookup file:**
https://www.ons.gov.uk/peoplepopulationandcommunity/populationandmigration/populationestimates/adhocs/13386listingof2021uklocalauthoritiesbycomponent2011traveltoworkareasbasedonmid2019smallareapopulationestimates

### 5. Construction Costs: Costmodelling.com

| Item                 | Details                                         |
| -------------------- | ----------------------------------------------- |
| **Description**      | UK construction cost data                       |
| **Building costs**   | https://costmodelling.com/building-costs        |
| **Regional factors** | https://costmodelling.com/regional-variations   |
| **Price indices**    | https://costmodelling.com/construction-indices  |
| **Notes**            | Need to scrape; no API. Data updated quarterly. |

**Key building types for Cooped Up:**

- "Flats (apartments) 6+ storeys high-rise with lifts"
- Current cost: ~£2,605/m² (as of Q3 2025)

### 6. EPC Data (for rent per sqm)

| Item              | Details                              |
| ----------------- | ------------------------------------ |
| **Description**   | Energy Performance Certificates      |
| **Geography**     | Individual property level            |
| **Key variables** | Floor area, tenure, bedrooms         |
| **URL**           | https://epc.opendatacommunities.org/ |
| **Format**        | Bulk CSV download (~6GB)             |
| **Notes**         | Already implemented in existing repo |

---

## US Data Sources (for Hsieh-Moretti replication)

### 1. Wages & Employment: County Business Patterns

| Item                       | Details                                                        |
| -------------------------- | -------------------------------------------------------------- |
| **Description**            | Employment and payroll by county and industry                  |
| **Years**                  | 1964-present                                                   |
| **Main page**              | https://www.census.gov/programs-surveys/cbp.html               |
| **Data downloads**         | https://www.census.gov/programs-surveys/cbp/data/datasets.html |
| **Historical (1964-1974)** | https://fpeckert.me/cbp/ (digitised by Fabian Eckert)          |

### 2. Housing Costs: Census/ACS

| Item                | Details                                             |
| ------------------- | --------------------------------------------------- |
| **Description**     | Median rent by MSA                                  |
| **Source**          | Census of Population (1960, 1970) and ACS (2008-09) |
| **IPUMS**           | https://usa.ipums.org/usa/                          |
| **data.census.gov** | https://data.census.gov/                            |

### 3. Worker Characteristics: Census/CPS

| Item            | Details                             |
| --------------- | ----------------------------------- |
| **Description** | Education, race, age, gender by MSA |
| **CPS**         | https://cps.ipums.org/cps/          |
| **Census**      | https://usa.ipums.org/usa/          |

### 4. Housing Supply Elasticity: Saiz (2010)

| Item              | Details                                                          |
| ----------------- | ---------------------------------------------------------------- |
| **Description**   | MSA-level housing supply elasticities                            |
| **Data download** | https://urbaneconomics.mit.edu/research/data                     |
| **Format**        | Stata (.dta)                                                     |
| **Variables**     | Supply elasticity, land unavailability, Wharton regulation index |

### 5. Union Density: Hirsch-Macpherson

| Item                         | Details                                              |
| ---------------------------- | ---------------------------------------------------- |
| **Description**              | Union membership and coverage by state/MSA           |
| **Main site**                | http://www.unionstats.com/                           |
| **Documentation**            | http://unionstats.gsu.edu/CPS%20Documentation.htm    |
| **State-level 1964-present** | https://unionstats.com/MonthlyLaborReviewArticle.htm |

### 6. Geographic Crosswalks

| Item            | Details                                                                                    |
| --------------- | ------------------------------------------------------------------------------------------ |
| **Description** | County to MSA crosswalk                                                                    |
| **Source**      | Census Bureau                                                                              |
| **URL**         | https://www.census.gov/geographies/reference-files/time-series/geo/relationship-files.html |

---

## Cooped Up Replication Code

| Item       | Details                                                                                   |
| ---------- | ----------------------------------------------------------------------------------------- |
| **GitHub** | https://github.com/DuncanMcClements/ASI_housing_code                                      |
| **Paper**  | https://www.adamsmith.org/research/cooped-up-quantifying-the-cost-of-housing-restrictions |

---

## Summary: Minimum Data for UK Replication

| Data               | Source        | Geography | Critical?                    |
| ------------------ | ------------- | --------- | ---------------------------- |
| Wages              | ASHE Table 8  | LA → TTWA | ✅ Yes                       |
| Rents              | PIPR          | LA → TTWA | ✅ Yes                       |
| Education          | Census 2021   | LA → TTWA | ✅ Yes (for wage adjustment) |
| Ethnicity          | Census 2021   | LA → TTWA | ⚠️ Optional                  |
| Age                | Census 2021   | LA → TTWA | ⚠️ Optional                  |
| LA-TTWA lookup     | ONS Geography | -         | ✅ Yes                       |
| Construction costs | Costmodelling | Region    | ✅ Yes (for counterfactual)  |
| Floor areas        | EPC           | LA        | ⚠️ Only if using rent/sqm    |

---

## Download Commands (examples)

```bash
# ASHE Table 8 (manual - need to find correct year's URL)
curl -o data/raw/ashe/table8_2023.zip "https://www.ons.gov.uk/file?uri=..."

# PIPR (need to find current URL from page)
curl -o data/raw/pipr/pipr_latest.xlsx "https://www.ons.gov.uk/file?uri=..."

# Nomis API example (education by LA)
curl "https://www.nomisweb.co.uk/api/v01/dataset/NM_2091_1.data.csv?geography=TYPE464&measures=20100" \
  -o data/raw/census/education_by_la.csv

# LA boundaries
curl -o data/raw/geography/la_boundaries.geojson \
  "https://services1.arcgis.com/ESMARspQHYMw9BZ9/arcgis/rest/services/Local_Authority_Districts_December_2023_Boundaries_UK_BFC/FeatureServer/0/query?where=1%3D1&outFields=*&f=geojson"
```

---

## Notes on Data Quality

1. **ASHE**: Sample survey, so small LAs may have suppressed data. Table 8 is by residence (where workers live), Table 7 is by workplace.

2. **PIPR**: New methodology from March 2024. Historical comparison requires chain-linking to old IPHRP series.

3. **Census**: 2021 Census conducted during COVID, may affect some variables (e.g., travel to work patterns).

4. **TTWA boundaries**: Based on 2011 Census commuting patterns. May not reflect post-COVID work patterns.

5. **Construction costs**: From private company, may not be fully comprehensive. Cross-check with BCIS if possible.
