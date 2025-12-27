"""US American Community Survey (ACS) dataset processing.

Provides housing costs, demographics, and worker characteristics by MSA.
Sources:
- Census API: https://api.census.gov/data.html
- data.census.gov: https://data.census.gov/
- IPUMS: https://usa.ipums.org/
"""

from pathlib import Path
from typing import Any

import pandas as pd

from src.core.config import processed_path as get_processed_path
from src.core.config import raw_path
from src.datasets.base import Dataset

# ACS variable codes for housing and demographics
# See: https://api.census.gov/data/2022/acs/acs5/variables.html
ACS_VARIABLES = {
    # Housing costs
    "B25064_001E": "median_gross_rent",
    "B25077_001E": "median_home_value",
    "B25071_001E": "median_gross_rent_pct_income",
    # Population
    "B01003_001E": "total_population",
    # Education (population 25+)
    "B15003_001E": "pop_25_plus",
    "B15003_022E": "bachelors_degree",
    "B15003_023E": "masters_degree",
    "B15003_024E": "professional_degree",
    "B15003_025E": "doctorate_degree",
    # Employment
    "B23025_001E": "pop_16_plus",
    "B23025_002E": "labor_force",
    "B23025_004E": "employed",
    "B23025_005E": "unemployed",
    # Income
    "B19013_001E": "median_household_income",
    "B19301_001E": "per_capita_income",
}


class ACSDataset(Dataset):
    """
    US American Community Survey dataset.

    Provides:
    - Median rent by MSA
    - Median home values
    - Educational attainment
    - Employment statistics
    - Income measures

    Data can be obtained via:
    1. Census API (requires free API key)
    2. data.census.gov (manual download)
    3. IPUMS USA (requires account)
    """

    name = "acs"
    country = "us"

    def __init__(self, api_key: str | None = None):
        """
        Initialize ACS dataset handler.

        Args:
            api_key: Census API key (get free at https://api.census.gov/data/key_signup.html)
        """
        self.api_key = api_key

    def download(
        self,
        output_dir: Path | None = None,
        year: int = 2022,
        survey: str = "acs5",
        **kwargs: Any,
    ) -> Path:
        """
        Download ACS data from Census Bureau API.

        Args:
            output_dir: Directory to save downloaded file
            year: Data year to download
            survey: Survey type ('acs1' for 1-year, 'acs5' for 5-year)

        Returns:
            Path to download directory
        """
        target_dir = output_dir or raw_path("us", "acs")
        target_dir.mkdir(parents=True, exist_ok=True)

        if self.api_key:
            print(f"Downloading ACS {survey} {year} data via Census API...")
            try:
                df = self._download_via_api(year, survey)
                output_file = target_dir / f"acs_{survey}_{year}_msa.csv"
                df.to_csv(output_file, index=False)
                print(f"Saved: {output_file}")
                return target_dir
            except Exception as e:
                print(f"API download failed: {e}")
                print("Falling back to manual download instructions...")

        # Create instructions for manual download
        readme_path = target_dir / "DOWNLOAD_INSTRUCTIONS.md"
        readme_content = f"""# ACS Data Download Instructions

## Option 1: Census API (Recommended)

Get a free API key at: https://api.census.gov/data/key_signup.html

Then either:
- Set environment variable: CENSUS_API_KEY=your_key
- Or pass api_key when creating the dataset:
  ```python
  from src.datasets.us.acs import ACSDataset
  acs = ACSDataset(api_key="your_key")
  acs.download(year={year})
  ```

## Option 2: data.census.gov

1. Visit: https://data.census.gov/
2. Search for "ACS 5-Year Estimates" or "B25064" (median rent)
3. Select geography: Metropolitan Statistical Area
4. Download as CSV
5. Save to this directory as `acs_{survey}_{year}_msa.csv`

## Option 3: IPUMS USA

1. Visit: https://usa.ipums.org/
2. Create an account
3. Select ACS samples for {year}
4. Select variables: RENT, VALUEH, EDUCD, etc.
5. Download and save to this directory

## Required Variables

The following ACS table variables are needed:
- B25064_001E: Median gross rent
- B25077_001E: Median home value
- B01003_001E: Total population
- B19013_001E: Median household income
- B15003_022E-025E: Education (degree holders)
"""
        readme_path.write_text(readme_content)
        print(f"Created download instructions: {readme_path}")

        return target_dir

    def _download_via_api(self, year: int, survey: str) -> pd.DataFrame:
        """Download ACS data using Census Bureau API."""
        import requests

        # API endpoint
        base_url = f"https://api.census.gov/data/{year}/acs/{survey}"

        # Variables to fetch
        var_list = ",".join(ACS_VARIABLES.keys())

        # Fetch for all MSAs (geography code 310)
        params = {
            "get": f"NAME,{var_list}",
            "for": "metropolitan statistical area/micropolitan statistical area:*",
            "key": self.api_key,
        }

        print(f"  Fetching from: {base_url}")
        response = requests.get(base_url, params=params, timeout=60)
        response.raise_for_status()

        data = response.json()

        # First row is headers
        headers = data[0]
        rows = data[1:]

        df = pd.DataFrame(rows, columns=headers)

        # Rename variable codes to readable names
        rename_map = {code: name for code, name in ACS_VARIABLES.items()}
        rename_map["metropolitan statistical area/micropolitan statistical area"] = "cbsa_code"
        rename_map["NAME"] = "cbsa_name"
        df = df.rename(columns=rename_map)

        # Convert numeric columns
        numeric_cols = list(ACS_VARIABLES.values())
        for col in numeric_cols:
            if col in df.columns:
                df[col] = pd.to_numeric(df[col], errors="coerce")

        df["year"] = year
        df["survey"] = survey

        return df

    def process(
        self,
        raw_path: Path | None = None,
        output_path: Path | None = None,
        year: int = 2022,
        survey: str = "acs5",
        **kwargs: Any,
    ) -> pd.DataFrame:
        """
        Process ACS data into analysis-ready format.

        Args:
            raw_path: Path to directory containing ACS CSV files
            output_path: Path to save processed data
            year: Year to process
            survey: Survey type

        Returns:
            DataFrame with housing and demographic variables by MSA
        """
        from src.core.config import raw_path as get_raw_path

        data_dir = raw_path or get_raw_path("us", "acs")
        data_file = data_dir / f"acs_{survey}_{year}_msa.csv"

        if data_file.exists():
            print(f"Loading ACS data: {data_file}")
            df = pd.read_csv(data_file)
        else:
            # Try to download if API key available
            if self.api_key:
                print("Data file not found. Attempting download...")
                self.download(year=year, survey=survey)
                df = pd.read_csv(data_file)
            else:
                raise FileNotFoundError(
                    f"ACS data file not found: {data_file}\n"
                    f"Run download() with an API key, or manually download the data."
                )

        # Process the data
        result = self._process_acs_data(df)

        if output_path:
            output_path = Path(output_path)
            output_path.parent.mkdir(parents=True, exist_ok=True)
            result.to_csv(output_path, index=False)
            print(f"Saved processed data to: {output_path}")

        return result

    def _process_acs_data(self, df: pd.DataFrame) -> pd.DataFrame:
        """Process raw ACS data into analysis-ready format."""
        result = df.copy()

        # Calculate derived variables

        # Share with bachelor's degree or higher
        education_cols = [
            "bachelors_degree",
            "masters_degree",
            "professional_degree",
            "doctorate_degree",
            "pop_25_plus",
        ]
        if all(col in result.columns for col in education_cols):
            result["college_plus"] = (
                result["bachelors_degree"]
                + result["masters_degree"]
                + result["professional_degree"]
                + result["doctorate_degree"]
            )
            result["share_college"] = result["college_plus"] / result["pop_25_plus"]

        # Employment rate
        if "employed" in result.columns and "labor_force" in result.columns:
            result["employment_rate"] = result["employed"] / result["labor_force"]

        # Filter to Metropolitan Statistical Areas only (exclude Micropolitan)
        if "cbsa_name" in result.columns:
            # MSAs typically have larger populations
            # Or we can filter by name pattern
            msa_mask = ~result["cbsa_name"].str.contains("Micro Area", case=False, na=False)
            result = result[msa_mask].copy()
            print(f"  Filtered to {len(result)} Metropolitan Statistical Areas")

        return result

    def load(self, path: Path | None = None) -> pd.DataFrame:
        """
        Load processed ACS data.

        Args:
            path: Path to processed CSV file

        Returns:
            DataFrame with ACS data
        """
        path = path or get_processed_path("us", "acs") / "housing_demographics_by_msa.csv"
        return pd.read_csv(path)


# Module-level instance (without API key - will prompt for download)
acs_dataset = ACSDataset()


def create_acs_dataset(api_key: str | None = None) -> ACSDataset:
    """
    Create an ACS dataset handler with an API key.

    Args:
        api_key: Census API key (get free at https://api.census.gov/data/key_signup.html)
                 Can also be set via CENSUS_API_KEY environment variable.

    Returns:
        ACSDataset instance
    """
    import os

    key = api_key or os.environ.get("CENSUS_API_KEY")
    return ACSDataset(api_key=key)


if __name__ == "__main__":
    import os

    from src.core.config import processed_path

    # Try to get API key from environment
    api_key = os.environ.get("CENSUS_API_KEY")

    if api_key:
        print("Using Census API key from environment")
        acs = ACSDataset(api_key=api_key)
        acs.download(year=2022)
        df = acs.process(year=2022)
    else:
        print("No API key found. Creating download instructions...")
        acs = ACSDataset()
        acs.download(year=2022)
        print("\nSet CENSUS_API_KEY environment variable to enable automatic download.")
