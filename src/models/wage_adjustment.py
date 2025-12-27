"""Wage adjustment model for controlling for workforce composition.

Following the methodology in Cooped Up (McClements & Hausenloy, 2024),
this module adjusts raw wages for demographic composition differences
across geographic areas.
"""

from dataclasses import dataclass

import numpy as np
import pandas as pd


@dataclass
class WageCoefficients:
    """
    Coefficients for wage adjustment regression.

    These represent the returns to various worker characteristics,
    used to calculate composition-adjusted wages.
    """

    # Educational attainment (relative to no qualifications)
    level_1_2: float = 0.15  # GCSE equivalent
    level_3: float = 0.25  # A-level equivalent
    level_4_plus: float = 0.45  # Degree and above

    # Demographics
    nonwhite: float = -0.05
    age: float = 0.002  # Per year of age

    # Can add more coefficients as needed


# Default coefficients from Cooped Up paper (approximate from Figure 1)
COOPED_UP_COEFFICIENTS = WageCoefficients(
    level_1_2=0.15,
    level_3=0.25,
    level_4_plus=0.45,
    nonwhite=-0.05,
    age=0.002,
)


def calculate_predicted_wage(
    demographics: pd.DataFrame,
    coefficients: WageCoefficients | None = None,
) -> pd.Series:
    """
    Calculate predicted wage based on workforce composition.

    Args:
        demographics: DataFrame with columns:
            - share_level_1_2: Share with GCSE-equivalent
            - share_level_3: Share with A-level equivalent
            - share_level_4_plus: Share with degree+
            - share_nonwhite: Share non-white
            - median_age: Median age

        coefficients: Wage coefficients to use

    Returns:
        Series of predicted log wages
    """
    if coefficients is None:
        coefficients = COOPED_UP_COEFFICIENTS

    # Calculate predicted log wage
    predicted = (
        coefficients.level_1_2 * demographics.get("share_level_1_2", 0)
        + coefficients.level_3 * demographics.get("share_level_3", 0)
        + coefficients.level_4_plus * demographics.get("share_level_4_plus", 0)
        + coefficients.nonwhite * demographics.get("share_nonwhite", 0)
        + coefficients.age * demographics.get("median_age", 40)
    )

    return predicted


def calculate_residual_wage(
    actual_wage: pd.Series,
    demographics: pd.DataFrame,
    coefficients: WageCoefficients | None = None,
    log_transform: bool = True,
) -> pd.Series:
    """
    Calculate residual wage (adjusted for composition).

    residual_wage = actual_wage - predicted_wage

    where predicted_wage is based on workforce characteristics.

    Args:
        actual_wage: Series of actual wages
        demographics: DataFrame with demographic characteristics
        coefficients: Wage coefficients to use
        log_transform: Whether to use log wages (default True)

    Returns:
        Series of residual wages
    """
    if log_transform:
        log_wage = np.log(actual_wage)
    else:
        log_wage = actual_wage

    predicted = calculate_predicted_wage(demographics, coefficients)
    residual = log_wage - predicted

    return pd.Series(residual, index=actual_wage.index)


def estimate_coefficients(
    individual_data: pd.DataFrame,
    wage_col: str = "wage",
    log_transform: bool = True,
) -> WageCoefficients:
    """
    Estimate wage coefficients from individual-level data.

    Runs OLS regression: log(wage) ~ education + ethnicity + age + ...

    Args:
        individual_data: DataFrame with individual workers
        wage_col: Column name for wages
        log_transform: Whether to use log wages

    Returns:
        Estimated WageCoefficients

    Note:
        Implementation pending - requires individual-level survey data
        like Labour Force Survey (UK) or CPS (US).
    """
    raise NotImplementedError(
        "Coefficient estimation requires individual-level data.\n"
        "For UK: Labour Force Survey\n"
        "For US: Current Population Survey\n"
        "Use COOPED_UP_COEFFICIENTS as default."
    )
