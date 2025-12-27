"""US County Business Patterns (CBP) dataset processing.

Provides employment and payroll data by county, used to construct wage measures.
Source: https://www.census.gov/programs-surveys/cbp.html
"""

from pathlib import Path
from typing import Any

import pandas as pd

from src.core.config import processed_path as get_processed_path
from src.core.config import raw_path
from src.core.download import download_file
from src.datasets.base import Dataset

# CBP data URLs by year
# Format changed over time - modern files are ZIP with CSV inside
CBP_BASE_URL = "https://www2.census.gov/programs-surveys/cbp/datasets"


def get_cbp_url(year: int) -> str:
    """Get download URL for CBP county-level data for a given year."""
    if year >= 2017:
        # Modern format: cbpYYco.zip
        return f"{CBP_BASE_URL}/{year}/cbp{str(year)[2:]}co.zip"
    elif year >= 2008:
        # Older format with different naming
        return f"{CBP_BASE_URL}/{year}/cbp{str(year)[2:]}co.zip"
    else:
        # Very old data may need different sources
        # Historical data (1964-1974) digitized by Fabian Eckert: https://fpeckert.me/cbp/
        return f"{CBP_BASE_URL}/{year}/cbp{str(year)[2:]}co.zip"


class CBPDataset(Dataset):
    """
    US County Business Patterns dataset.

    Provides:
    - Employment by county (number of employees)
    - Annual payroll by county
    - Number of establishments
    - Data by industry (NAICS codes)

    Used to construct:
    - Total employment by MSA
    - Average wages by MSA
    """

    name = "cbp"
    country = "us"

    def download(
        self,
        output_dir: Path | None = None,
        years: list[int] | None = None,
        **kwargs: Any,
    ) -> Path:
        """
        Download CBP data from Census Bureau.

        Args:
            output_dir: Directory to save downloaded files
            years: List of years to download (default: [2021])

        Returns:
            Path to download directory
        """
        target_dir = output_dir or raw_path("us", "cbp")
        target_dir.mkdir(parents=True, exist_ok=True)

        if years is None:
            years = [2021]  # Default to recent year

        print(f"Downloading CBP data for years: {years}")

        for year in years:
            url = get_cbp_url(year)
            filename = f"cbp{str(year)[2:]}co.zip"
            output_file = target_dir / filename

            if output_file.exists():
                print(f"  {year}: Already exists at {output_file}")
                continue

            print(f"  {year}: Downloading from {url}")
            try:
                download_file(url, output_file)
                print(f"  {year}: Saved to {output_file}")
            except Exception as e:
                print(f"  {year}: Failed to download: {e}")
                print(f"        Manual download: {url}")

        return target_dir

    def process(
        self,
        raw_path: Path | None = None,
        output_path: Path | None = None,
        year: int = 2021,
        **kwargs: Any,
    ) -> pd.DataFrame:
        """
        Process CBP data to get employment and wages by county.

        Args:
            raw_path: Path to directory containing CBP ZIP files
            output_path: Path to save processed data
            year: Year to process

        Returns:
            DataFrame with employment and wages by county
        """
        import zipfile

        from src.core.config import raw_path as get_raw_path

        data_dir = raw_path or get_raw_path("us", "cbp")
        zip_file = data_dir / f"cbp{str(year)[2:]}co.zip"

        if not zip_file.exists():
            raise FileNotFoundError(f"CBP file not found: {zip_file}\nRun download(years=[{year}]) first.")

        print(f"Processing CBP data for {year}: {zip_file}")

        # Read directly from ZIP
        with zipfile.ZipFile(zip_file, "r") as z:
            # Find the main data file in the ZIP
            csv_files = [f for f in z.namelist() if f.endswith(".txt") or f.endswith(".csv")]
            if not csv_files:
                raise ValueError(f"No data files found in {zip_file}")

            data_file = csv_files[0]
            print(f"  Reading: {data_file}")

            with z.open(data_file) as f:
                df = pd.read_csv(f, dtype=str, low_memory=False)

        # Process the data
        result = self._process_cbp_data(df, year)

        if output_path:
            output_path = Path(output_path)
            output_path.parent.mkdir(parents=True, exist_ok=True)
            result.to_csv(output_path, index=False)
            print(f"Saved processed data to: {output_path}")

        return result

    def _process_cbp_data(self, df: pd.DataFrame, year: int) -> pd.DataFrame:
        """Process raw CBP data into county-level employment and wage measures."""
        # Standardize column names (they vary by year)
        df.columns = df.columns.str.lower().str.strip()

        # Key columns (names vary by year)
        fipstate_col = next((c for c in df.columns if "fipstate" in c or "fips_state" in c), None)
        fipscty_col = next((c for c in df.columns if "fipscty" in c or "fips_county" in c), None)
        emp_col = next((c for c in df.columns if c in ["emp", "emp_nf", "employment"]), None)
        ap_col = next((c for c in df.columns if c in ["ap", "ap_nf", "annual_payroll"]), None)
        est_col = next((c for c in df.columns if c in ["est", "establishments"]), None)
        naics_col = next((c for c in df.columns if "naics" in c), None)

        if not all([fipstate_col, fipscty_col, emp_col]):
            print(f"  Available columns: {list(df.columns)}")
            raise ValueError("Could not identify required columns in CBP data")

        # Create FIPS code
        df["state_fips"] = df[fipstate_col].astype(str).str.zfill(2)
        df["county_fips"] = df[fipscty_col].astype(str).str.zfill(3)
        df["fips"] = df["state_fips"] + df["county_fips"]

        # Filter to total (all industries) - NAICS = "------" or similar
        if naics_col:
            # Total row has NAICS like "------" or "00" depending on year
            total_mask = df[naics_col].str.contains(r"^-+$|^0+$", regex=True, na=False)
            df_total = df[total_mask].copy()
            print(f"  Filtered to {len(df_total)} county totals (all industries)")
        else:
            df_total = df.copy()

        # Convert numeric columns
        for col in [emp_col, ap_col, est_col]:
            if col and col in df_total.columns:
                # Handle suppressed data (flagged with letters or 'N')
                df_total[col] = pd.to_numeric(df_total[col], errors="coerce")

        # Build result DataFrame
        result = pd.DataFrame(
            {
                "fips": df_total["fips"],
                "state_fips": df_total["state_fips"],
                "county_fips": df_total["county_fips"],
                "year": year,
            }
        )

        if emp_col:
            result["employment"] = df_total[emp_col].values
        if ap_col:
            result["annual_payroll_1000"] = df_total[ap_col].values  # In $1,000s
        if est_col:
            result["establishments"] = df_total[est_col].values

        # Calculate average wage per employee
        if "employment" in result.columns and "annual_payroll_1000" in result.columns:
            # Payroll is in $1,000s, so multiply by 1000 to get dollars
            result["avg_annual_wage"] = (result["annual_payroll_1000"] * 1000) / result["employment"]
            result["avg_weekly_wage"] = result["avg_annual_wage"] / 52

        # Remove rows with missing employment
        result = result.dropna(subset=["employment"])
        print(f"  Final: {len(result)} counties with employment data")

        return result

    def load(self, path: Path | None = None) -> pd.DataFrame:
        """
        Load processed CBP data.

        Args:
            path: Path to processed CSV file

        Returns:
            DataFrame with employment data
        """
        path = path or get_processed_path("us", "cbp") / "employment_by_county.csv"
        return pd.read_csv(path)

    def aggregate_to_msa(
        self,
        county_data: pd.DataFrame,
        geography: pd.DataFrame,
    ) -> pd.DataFrame:
        """
        Aggregate county-level data to MSA level.

        Args:
            county_data: DataFrame with county-level CBP data (must have 'fips' column)
            geography: DataFrame with county-MSA crosswalk (must have 'fips', 'cbsa_code', 'cbsa_name')

        Returns:
            DataFrame with MSA-level employment and wages
        """
        # Merge county data with geography
        merged = county_data.merge(geography[["fips", "cbsa_code", "cbsa_name"]], on="fips", how="inner")

        # Aggregate to MSA level
        msa_data = (
            merged.groupby(["cbsa_code", "cbsa_name"])
            .agg(
                employment=("employment", "sum"),
                annual_payroll_1000=("annual_payroll_1000", "sum"),
                establishments=("establishments", "sum"),
                n_counties=("fips", "count"),
            )
            .reset_index()
        )

        # Recalculate average wage at MSA level
        msa_data["avg_annual_wage"] = (msa_data["annual_payroll_1000"] * 1000) / msa_data["employment"]
        msa_data["avg_weekly_wage"] = msa_data["avg_annual_wage"] / 52

        return msa_data


# Module-level instance for convenience
cbp_dataset = CBPDataset()


if __name__ == "__main__":
    from src.core.config import processed_path

    # Download recent year
    cbp_dataset.download(years=[2021])

    # Process and save
    output_file = processed_path("us", "cbp") / "employment_by_county.csv"
    df = cbp_dataset.process(year=2021, output_path=output_file)

    print(f"\nProcessed {len(df)} counties")
    print(f"Total employment: {df['employment'].sum():,.0f}")
    print(df.head(10))
