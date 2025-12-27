"""US Housing Supply Elasticity dataset (Saiz 2010).

Provides MSA-level housing supply elasticities used in Hsieh-Moretti (2019).

Sources:
- Original: https://urbaneconomics.mit.edu/research/data
- Hsieh-Moretti replication: https://www.openicpsr.org/openicpsr/project/114161
"""

from pathlib import Path
from typing import Any

import pandas as pd

from src.core.config import processed_path as get_processed_path
from src.core.config import raw_path
from src.datasets.base import Dataset

# Key MSAs and their elasticities from Saiz (2010) / Hsieh-Moretti (2019)
# These are the elasticities used in the counterfactual calculations
SAIZ_ELASTICITIES = {
    # High-productivity, low-elasticity metros (constrained)
    "New York-Newark-Jersey City, NY-NJ-PA": 0.76,
    "San Francisco-Oakland-Hayward, CA": 0.66,
    "San Jose-Sunnyvale-Santa Clara, CA": 0.76,
    "Los Angeles-Long Beach-Anaheim, CA": 0.63,
    "Boston-Cambridge-Newton, MA-NH": 1.16,
    "Seattle-Tacoma-Bellevue, WA": 1.08,
    "San Diego-Carlsbad, CA": 0.67,
    "Washington-Arlington-Alexandria, DC-VA-MD-WV": 1.47,
    # Medium elasticity metros
    "Chicago-Naperville-Elgin, IL-IN-WI": 1.54,
    "Philadelphia-Camden-Wilmington, PA-NJ-DE-MD": 1.62,
    "Miami-Fort Lauderdale-West Palm Beach, FL": 0.60,
    "Denver-Aurora-Lakewood, CO": 1.53,
    "Minneapolis-St. Paul-Bloomington, MN-WI": 2.07,
    "Detroit-Warren-Dearborn, MI": 2.54,
    # High elasticity metros (unconstrained)
    "Dallas-Fort Worth-Arlington, TX": 2.44,
    "Houston-The Woodlands-Sugar Land, TX": 2.46,
    "Atlanta-Sandy Springs-Roswell, GA": 2.46,
    "Phoenix-Mesa-Scottsdale, AZ": 2.04,
    "Las Vegas-Henderson-Paradise, NV": 1.43,
}


class SaizDataset(Dataset):
    """
    US Housing Supply Elasticity dataset from Saiz (2010).

    Provides:
    - Housing supply elasticity by MSA
    - Land unavailability measures
    - Wharton Residential Land Use Regulation Index

    The elasticities measure how responsive housing supply is to price changes.
    Low elasticity = constrained supply (geographic or regulatory barriers).
    """

    name = "saiz"
    country = "us"

    def download(self, output_dir: Path | None = None, **kwargs: Any) -> Path:
        """
        Download Saiz (2010) supply elasticity data.

        Note: The full dataset requires manual download due to licensing.

        Options:
        1. Hsieh-Moretti replication package (recommended):
           https://www.openicpsr.org/openicpsr/project/114161
           - Requires ICPSR account (free)
           - Contains data3.dta with all variables

        2. Original Saiz data:
           https://urbaneconomics.mit.edu/research/data
           - Stata .dta format

        Args:
            output_dir: Directory to save downloaded file

        Returns:
            Path to download directory
        """
        target_dir = output_dir or raw_path("us", "saiz")
        target_dir.mkdir(parents=True, exist_ok=True)

        # Create a README with download instructions
        readme_path = target_dir / "DOWNLOAD_INSTRUCTIONS.md"
        readme_content = """# Saiz Housing Supply Elasticity Data

## Option 1: Hsieh-Moretti Replication Package (Recommended)

1. Visit: https://www.openicpsr.org/openicpsr/project/114161
2. Create a free ICPSR account if needed
3. Download the replication package
4. Extract `data3.dta` to this directory

## Option 2: Original Saiz (2010) Data

1. Visit: https://urbaneconomics.mit.edu/research/data
2. Download the housing supply elasticity data
3. Save to this directory

## Expected Files

After download, this directory should contain:
- `data3.dta` (from Hsieh-Moretti) OR
- `elasticity_data.dta` (from Saiz website)

## Key Variables

- `msa` or `msaname`: MSA identifier/name
- `elasticity` or `supplyelasticity`: Housing supply elasticity
- `unavailable_share`: Share of land unavailable for development
- `wrluri`: Wharton Residential Land Use Regulation Index
"""
        readme_path.write_text(readme_content)
        print(f"Created download instructions at: {readme_path}")

        # Also create a fallback CSV with key elasticities from the paper
        fallback_path = target_dir / "saiz_elasticities_key_msas.csv"
        fallback_df = pd.DataFrame([{"msa_name": k, "supply_elasticity": v} for k, v in SAIZ_ELASTICITIES.items()])
        fallback_df.to_csv(fallback_path, index=False)
        print(f"Created fallback data with {len(fallback_df)} key MSAs: {fallback_path}")

        return target_dir

    def process(
        self,
        raw_path: Path | None = None,
        output_path: Path | None = None,
        **kwargs: Any,
    ) -> pd.DataFrame:
        """
        Process Saiz supply elasticity data.

        Handles both:
        - Hsieh-Moretti replication data (data3.dta)
        - Original Saiz Stata files
        - Fallback CSV with key MSAs

        Args:
            raw_path: Path to directory containing data files
            output_path: Path to save processed data

        Returns:
            DataFrame with supply elasticities by MSA
        """
        from src.core.config import raw_path as get_raw_path

        data_dir = raw_path or get_raw_path("us", "saiz")

        # Try to find data files in order of preference
        hm_file = data_dir / "data3.dta"
        saiz_file = data_dir / "elasticity_data.dta"
        fallback_file = data_dir / "saiz_elasticities_key_msas.csv"

        if hm_file.exists():
            print(f"Loading Hsieh-Moretti replication data: {hm_file}")
            stata_data = pd.read_stata(hm_file)
            df = stata_data if isinstance(stata_data, pd.DataFrame) else pd.DataFrame(stata_data)
            # Extract relevant columns (adjust based on actual file structure)
            result = self._process_hsieh_moretti_data(df)

        elif saiz_file.exists():
            print(f"Loading original Saiz data: {saiz_file}")
            stata_data = pd.read_stata(saiz_file)
            df = stata_data if isinstance(stata_data, pd.DataFrame) else pd.DataFrame(stata_data)
            result = self._process_saiz_data(df)

        elif fallback_file.exists():
            print(f"Loading fallback data (key MSAs only): {fallback_file}")
            result = pd.read_csv(fallback_file)

        else:
            # Generate fallback from hardcoded values
            print("No data files found. Using hardcoded key MSA elasticities.")
            result = pd.DataFrame([{"msa_name": k, "supply_elasticity": v} for k, v in SAIZ_ELASTICITIES.items()])

        if output_path:
            output_path = Path(output_path)
            output_path.parent.mkdir(parents=True, exist_ok=True)
            result.to_csv(output_path, index=False)
            print(f"Saved processed data to: {output_path}")

        return result

    def _process_hsieh_moretti_data(self, df: pd.DataFrame) -> pd.DataFrame:
        """Process Hsieh-Moretti replication data (data3.dta)."""
        # Map from target column names to possible source column names
        # Order matters - first match wins
        possible_columns = {
            "msa_code": ["msa", "msacode", "cbsa", "cbsacode", "metarea"],
            "msa_name": ["name_msa", "msaname", "msa_name", "metareaname", "cbsaname"],
            "supply_elasticity": ["elasticity", "supplyelasticity", "supply_elasticity", "saiz_elasticity"],
            "land_unavailable_share": ["unaval", "unavailable", "unavailable_share", "land_unavailable"],
            "wrluri": ["WRLURI", "wrluri", "regulation", "regulation_index"],
            "inverse_elasticity": ["inverse"],
            "population": ["populat_saiz", "population", "pop"],
        }

        result_cols = {}
        for target, options in possible_columns.items():
            for opt in options:
                if opt in df.columns:
                    result_cols[target] = df[opt]
                    break

        result = pd.DataFrame(result_cols)

        # Filter to rows with elasticity data
        if "supply_elasticity" in result.columns:
            result = result[result["supply_elasticity"].notna()].copy()

        return result

    def _process_saiz_data(self, df: pd.DataFrame) -> pd.DataFrame:
        """Process original Saiz (2010) data."""
        # Similar logic to above, adjusted for Saiz file format
        return self._process_hsieh_moretti_data(df)

    def load(self, path: Path | None = None) -> pd.DataFrame:
        """
        Load processed Saiz supply elasticity data.

        Args:
            path: Path to processed CSV file

        Returns:
            DataFrame with supply elasticity data
        """
        path = path or get_processed_path("us", "saiz") / "supply_elasticities.csv"

        if path.exists():
            return pd.read_csv(path)

        # Fall back to hardcoded values
        print(f"Processed file not found at {path}. Using hardcoded key MSAs.")
        return pd.DataFrame([{"msa_name": k, "supply_elasticity": v} for k, v in SAIZ_ELASTICITIES.items()])

    def get_elasticity(self, msa_name: str) -> float | None:
        """
        Get supply elasticity for a specific MSA.

        Args:
            msa_name: MSA name (partial match supported)

        Returns:
            Supply elasticity or None if not found
        """
        # Try exact match first
        if msa_name in SAIZ_ELASTICITIES:
            return SAIZ_ELASTICITIES[msa_name]

        # Try partial match
        for key, value in SAIZ_ELASTICITIES.items():
            if msa_name.lower() in key.lower():
                return value

        return None


# Module-level instance for convenience
saiz_dataset = SaizDataset()


if __name__ == "__main__":
    # Create download instructions and fallback data
    saiz_dataset.download()

    # Process whatever data is available
    df = saiz_dataset.process()
    print(f"\nLoaded {len(df)} MSAs with supply elasticities")
    print(df.head(10))
