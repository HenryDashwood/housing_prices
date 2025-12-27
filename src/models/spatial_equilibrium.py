"""Spatial equilibrium model based on Hsieh-Moretti (2019).

Implements the core framework for calculating GDP costs of housing constraints.
"""

from dataclasses import dataclass
from typing import Any

import numpy as np
import pandas as pd


@dataclass
class ModelParameters:
    """
    Hsieh-Moretti spatial equilibrium model parameters.

    These control the key elasticities in the model.
    """

    # Production parameters
    alpha: float = 0.65  # Labour share in production

    # Agglomeration
    eta: float = 0.25  # Agglomeration elasticity (productivity increases with density)

    # Labour mobility
    theta: float = 2.0  # Inverse Fréchet shape parameter (higher = more mobile)

    # Housing
    gamma_median: float = 1.75  # Median housing supply elasticity
    housing_share: float = 0.33  # Share of expenditure on housing

    @property
    def beta(self) -> float:
        """Housing price exponent in utility."""
        return self.housing_share / (1 - self.housing_share)


# Default parameters from Hsieh-Moretti (2019)
HSIEH_MORETTI_PARAMS = ModelParameters(
    alpha=0.65,
    eta=0.25,
    theta=2.0,
    gamma_median=1.75,
)

# UK-specific parameters from Cooped Up
COOPED_UP_PARAMS = ModelParameters(
    alpha=0.65,
    eta=0.25,
    theta=2.0,
    gamma_median=1.75,
    housing_share=0.33,
)


class SpatialEquilibriumModel:
    """
    Hsieh-Moretti spatial equilibrium model.

    Key equations:
    - Labour supply: L_i = (V * Z_i / P_i^beta)^theta * L_bar
    - Housing price: P_i = c * L_i^(1/gamma_i)
    - Productivity: W_i = A_i * L_i^(eta-1)
    - Aggregate output: Y = sum(A_i * L_i^eta)
    """

    def __init__(self, params: ModelParameters | None = None):
        """
        Initialize the spatial equilibrium model.

        Args:
            params: Model parameters (defaults to Hsieh-Moretti values)
        """
        self.params = params or HSIEH_MORETTI_PARAMS

    def calculate_productivity(
        self,
        wages: np.ndarray,
        rents: np.ndarray,
    ) -> np.ndarray:
        """
        Back out city TFP from observed wages and rents.

        From spatial equilibrium condition:
        Z_i = W_i / P_i^beta

        Args:
            wages: Array of wages by city
            rents: Array of rents by city

        Returns:
            Array of implied productivities
        """
        return wages / np.power(rents, self.params.beta)

    def calculate_utility(
        self,
        wages: np.ndarray,
        rents: np.ndarray,
    ) -> np.ndarray:
        """
        Calculate indirect utility in each city.

        V_i = W_i / P_i^beta

        Args:
            wages: Array of wages by city
            rents: Array of rents by city

        Returns:
            Array of utilities
        """
        return wages / np.power(rents, self.params.beta)

    def calculate_counterfactual_employment(
        self,
        current_employment: np.ndarray,
        current_rents: np.ndarray,
        counterfactual_rents: np.ndarray,
        productivity: np.ndarray,
    ) -> np.ndarray:
        """
        Calculate employment distribution under counterfactual rents.

        Args:
            current_employment: Current employment by city
            current_rents: Current rents by city
            counterfactual_rents: Rents under counterfactual policy
            productivity: City productivities

        Returns:
            Counterfactual employment by city
        """
        # Calculate utility change from rent change
        utility_ratio = np.power(
            current_rents / counterfactual_rents,
            self.params.beta * self.params.theta,
        )

        # New employment proportional to utility raised to theta
        new_employment = current_employment * utility_ratio

        # Normalize to preserve total employment
        total_employment = current_employment.sum()
        new_employment = new_employment * (total_employment / new_employment.sum())

        return new_employment

    def calculate_gdp(
        self,
        employment: np.ndarray,
        productivity: np.ndarray,
    ) -> float:
        """
        Calculate aggregate GDP.

        Y = sum(A_i * L_i^eta)

        Args:
            employment: Employment by city
            productivity: Productivity by city

        Returns:
            Aggregate GDP
        """
        return float(np.sum(productivity * np.power(employment, self.params.eta)))

    def calculate_gdp_impact(
        self,
        current_employment: np.ndarray,
        counterfactual_employment: np.ndarray,
        productivity: np.ndarray,
    ) -> dict[str, float]:
        """
        Calculate GDP change from employment reallocation.

        Args:
            current_employment: Current employment by city
            counterfactual_employment: Counterfactual employment
            productivity: City productivities

        Returns:
            Dictionary with GDP impact metrics
        """
        current_gdp = self.calculate_gdp(current_employment, productivity)
        counterfactual_gdp = self.calculate_gdp(counterfactual_employment, productivity)

        gdp_change = counterfactual_gdp - current_gdp
        gdp_change_pct = (gdp_change / current_gdp) * 100

        return {
            "current_gdp": current_gdp,
            "counterfactual_gdp": counterfactual_gdp,
            "gdp_change": gdp_change,
            "gdp_change_pct": gdp_change_pct,
        }


def run_spatial_equilibrium_analysis(
    data: pd.DataFrame,
    wage_col: str = "wage",
    rent_col: str = "rent",
    employment_col: str = "employment",
    params: ModelParameters | None = None,
    counterfactual_rent: float | None = None,
) -> dict[str, Any]:
    """
    Run full spatial equilibrium analysis.

    Args:
        data: DataFrame with city-level data
        wage_col: Column name for wages
        rent_col: Column name for rents
        employment_col: Column name for employment
        params: Model parameters
        counterfactual_rent: Target rent for counterfactual (e.g., construction cost)

    Returns:
        Dictionary with analysis results
    """
    model = SpatialEquilibriumModel(params)

    wages = data[wage_col].values
    rents = data[rent_col].values
    employment = data[employment_col].values

    # Calculate implied productivities
    productivity = model.calculate_productivity(wages, rents)

    results: dict[str, Any] = {
        "productivity": productivity,
        "current_gdp": model.calculate_gdp(employment, productivity),
    }

    # Run counterfactual if target rent provided
    if counterfactual_rent is not None:
        counterfactual_rents = np.full_like(rents, counterfactual_rent)
        counterfactual_employment = model.calculate_counterfactual_employment(
            employment, rents, counterfactual_rents, productivity
        )

        gdp_impact = model.calculate_gdp_impact(employment, counterfactual_employment, productivity)

        results.update(
            {
                "counterfactual_employment": counterfactual_employment,
                **gdp_impact,
            }
        )

    return results
