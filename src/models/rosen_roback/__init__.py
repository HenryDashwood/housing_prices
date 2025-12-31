"""Rosen-Roback Spatial Equilibrium Model.

A reusable implementation of the Rosen-Roback model for analyzing
spatial equilibrium and the economic costs of housing constraints.

Quick Start:
    >>> from src.models.rosen_roback import RosenRobackModel, ThreeCityDataset
    >>>
    >>> # Create model and dataset
    >>> model = RosenRobackModel()
    >>> dataset = ThreeCityDataset()
    >>>
    >>> # Solve for equilibrium
    >>> result = model.solve(dataset)
    >>> print(result.summary())
    >>>
    >>> # Run counterfactual
    >>> from src.models.rosen_roback import CounterfactualScenario
    >>> scenario = CounterfactualScenario(
    ...     name="Reform",
    ...     description="Increase high-productivity city elasticity",
    ...     elasticity_changes={"High Productivity": 3.0}
    ... )
    >>> baseline, reform, gdp = model.run_counterfactual(dataset, scenario)
    >>> print(f"GDP gain from reform: {gdp['gdp_change_pct']:.2f}%")

Key Classes:
    - RosenRobackModel: Main model class for solving equilibrium
    - ModelParameters: Global model parameters (alpha, eta, beta, theta)
    - CityParameters: Per-city parameters (TFP, amenity, elasticity)
    - RosenRobackDataset: Abstract base for datasets
    - DataFrameDataset: Dataset from pandas DataFrame
    - SyntheticDataset: Generated test data
    - ThreeCityDataset: Simple pedagogical example
    - CounterfactualScenario: Defines policy scenarios
    - EquilibriumResult: Container for equilibrium outcomes
"""

from .datasets import (
    CounterfactualScenario,
    DataFrameDataset,
    RosenRobackDataset,
    SyntheticDataset,
    ThreeCityDataset,
)
from .equilibrium import EquilibriumSolver, calculate_gdp_change
from .model import RosenRobackModel, ScenarioComparison, run_multiple_scenarios
from .parameters import CityParameters, EquilibriumResult, ModelParameters

__all__ = [
    # Main model
    "RosenRobackModel",
    # Parameters
    "ModelParameters",
    "CityParameters",
    "EquilibriumResult",
    # Datasets
    "RosenRobackDataset",
    "DataFrameDataset",
    "SyntheticDataset",
    "ThreeCityDataset",
    # Scenarios
    "CounterfactualScenario",
    "ScenarioComparison",
    # Functions
    "run_multiple_scenarios",
    "calculate_gdp_change",
    # Solver (for advanced use)
    "EquilibriumSolver",
]
