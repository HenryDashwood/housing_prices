"""High-level Rosen-Roback model API.

This module provides the main RosenRobackModel class that users interact with.
It wraps the equilibrium solver and provides convenient methods for running
the model and counterfactual analysis.

Example usage:
    >>> from src.models.rosen_roback import RosenRobackModel, SyntheticDataset
    >>>
    >>> # Create model with default parameters
    >>> model = RosenRobackModel()
    >>>
    >>> # Solve equilibrium
    >>> dataset = SyntheticDataset(n_cities=10)
    >>> result = model.solve(dataset)
    >>> print(result.summary())
    >>>
    >>> # Run counterfactual
    >>> comparison = model.compare_scenarios(
    ...     dataset,
    ...     baseline_elasticity={"High Productivity": 0.5},
    ...     counterfactual_elasticity={"High Productivity": 2.0}
    ... )
"""

from dataclasses import dataclass
from typing import Any

from .datasets import CityParameters, CounterfactualScenario, RosenRobackDataset
from .equilibrium import EquilibriumSolver, calculate_gdp_change
from .parameters import EquilibriumResult, ModelParameters


class RosenRobackModel:
    """
    Multi-city Rosen-Roback spatial equilibrium model.

    This is the main class for running spatial equilibrium analysis.
    It solves for the equilibrium distribution of workers across cities
    and can compare baseline vs counterfactual scenarios.

    The model captures three key forces:
    1. Agglomeration: larger cities are more productive (higher wages)
    2. Housing supply: inelastic supply means population growth raises rents
    3. Worker mobility: workers move toward high-utility cities

    In equilibrium, these forces balance so workers are approximately
    indifferent between locations.

    Attributes:
        params: Model parameters controlling elasticities and shares.

    Example:
        >>> model = RosenRobackModel()
        >>> dataset = ThreeCityDataset()
        >>> result = model.solve(dataset)
        >>> print(f"Total GDP: {result.total_gdp:,.0f}")
    """

    def __init__(self, params: ModelParameters | None = None):
        """
        Initialize the model.

        Args:
            params: Model parameters. If None, uses standard academic estimates.
        """
        self.params = params or ModelParameters.STANDARD

    def solve(
        self,
        dataset: RosenRobackDataset,
        **solver_kwargs: Any,
    ) -> EquilibriumResult:
        """
        Solve for spatial equilibrium.

        Finds the population distribution where workers are approximately
        indifferent between cities, given the dataset's city parameters.

        Args:
            dataset: Dataset providing city parameters and total population.
            **solver_kwargs: Additional arguments passed to the solver
                (tol, max_iter, damping, verbose).

        Returns:
            EquilibriumResult with population, wages, rents, etc.

        Example:
            >>> model = RosenRobackModel()
            >>> result = model.solve(ThreeCityDataset())
            >>> result.to_dataframe()
        """
        cities = dataset.get_cities()
        total_population = dataset.get_total_population()

        solver = EquilibriumSolver(self.params, cities)
        return solver.solve(total_population, **solver_kwargs)

    def solve_with_cities(
        self,
        cities: list[CityParameters],
        total_population: float,
        **solver_kwargs: Any,
    ) -> EquilibriumResult:
        """
        Solve equilibrium given explicit city parameters.

        Lower-level method when you don't have a dataset object.

        Args:
            cities: List of city parameters.
            total_population: Total population to distribute.
            **solver_kwargs: Additional solver arguments.

        Returns:
            EquilibriumResult with equilibrium values.
        """
        solver = EquilibriumSolver(self.params, cities)
        return solver.solve(total_population, **solver_kwargs)

    def run_counterfactual(
        self,
        dataset: RosenRobackDataset,
        scenario: CounterfactualScenario,
        **solver_kwargs: Any,
    ) -> tuple[EquilibriumResult, EquilibriumResult, dict[str, float]]:
        """
        Run a counterfactual analysis.

        Compares baseline equilibrium to a scenario with modified elasticities.

        Args:
            dataset: Baseline dataset.
            scenario: Counterfactual scenario specifying elasticity changes.
            **solver_kwargs: Additional solver arguments.

        Returns:
            Tuple of (baseline_result, counterfactual_result, gdp_comparison).

        Example:
            >>> scenario = CounterfactualScenario(
            ...     name="Reform",
            ...     description="Increase London elasticity",
            ...     elasticity_changes={"London": 2.0}
            ... )
            >>> baseline, counterfactual, gdp = model.run_counterfactual(
            ...     dataset, scenario
            ... )
            >>> print(f"GDP change: {gdp['gdp_change_pct']:.2f}%")
        """
        # Solve baseline
        baseline = self.solve(dataset, **solver_kwargs)

        # Apply scenario to get counterfactual cities
        counterfactual_cities = scenario.apply_to_dataset(dataset)

        # Solve counterfactual
        counterfactual = self.solve_with_cities(
            counterfactual_cities,
            dataset.get_total_population(),
            **solver_kwargs,
        )

        # Calculate GDP change
        gdp_comparison = calculate_gdp_change(baseline, counterfactual)

        return baseline, counterfactual, gdp_comparison

    def compare_elasticities(
        self,
        dataset: RosenRobackDataset,
        city_name: str,
        elasticities: list[float],
        **solver_kwargs: Any,
    ) -> list[tuple[float, EquilibriumResult]]:
        """
        Compare outcomes across different elasticity values for one city.

        Useful for sensitivity analysis on housing supply elasticity.

        Args:
            dataset: Baseline dataset.
            city_name: Name of city to vary.
            elasticities: List of elasticity values to try.
            **solver_kwargs: Additional solver arguments.

        Returns:
            List of (elasticity, result) tuples.

        Example:
            >>> results = model.compare_elasticities(
            ...     dataset,
            ...     city_name="London",
            ...     elasticities=[0.5, 1.0, 2.0, 3.0]
            ... )
            >>> for gamma, result in results:
            ...     print(f"gamma={gamma}: GDP={result.total_gdp:,.0f}")
        """
        results = []

        for gamma in elasticities:
            # Create modified cities
            modified_cities = []
            for city in dataset.get_cities():
                if city.name == city_name:
                    modified_cities.append(
                        CityParameters(
                            name=city.name,
                            base_tfp=city.base_tfp,
                            amenity=city.amenity,
                            supply_elasticity=gamma,
                            supply_shifter=city.supply_shifter,
                        )
                    )
                else:
                    modified_cities.append(city)

            result = self.solve_with_cities(
                modified_cities,
                dataset.get_total_population(),
                **solver_kwargs,
            )
            results.append((gamma, result))

        return results

    def sensitivity_analysis(
        self,
        dataset: RosenRobackDataset,
        parameter: str,
        values: list[float],
        constrained_city: str | None = None,
        constrained_elasticity: float = 0.5,
        **solver_kwargs: Any,
    ) -> list[tuple[float, float]]:
        """
        Analyze sensitivity of GDP loss to model parameters.

        Computes GDP loss from housing constraints for different parameter values.

        Args:
            dataset: Baseline dataset.
            parameter: Parameter to vary ("eta", "theta", "alpha", "beta").
            values: List of parameter values to try.
            constrained_city: Name of city to constrain (if None, uses first city).
            constrained_elasticity: Elasticity for constrained scenario.
            **solver_kwargs: Additional solver arguments.

        Returns:
            List of (parameter_value, gdp_loss_pct) tuples.

        Example:
            >>> results = model.sensitivity_analysis(
            ...     dataset,
            ...     parameter="eta",
            ...     values=[0.02, 0.04, 0.06, 0.08]
            ... )
        """
        if constrained_city is None:
            constrained_city = dataset.get_city_names()[0]

        results = []

        for value in values:
            # Create model with modified parameter
            params_dict = {
                "alpha": self.params.alpha,
                "eta": self.params.eta,
                "beta": self.params.beta,
                "theta": self.params.theta,
            }
            params_dict[parameter] = value
            modified_model = RosenRobackModel(ModelParameters(**params_dict))

            # Solve baseline (elastic supply)
            baseline = modified_model.solve(dataset, **solver_kwargs)

            # Solve constrained
            scenario = CounterfactualScenario(
                name="Constrained",
                description=f"Constrain {constrained_city}",
                elasticity_changes={constrained_city: constrained_elasticity},
            )
            _, constrained, gdp = modified_model.run_counterfactual(
                dataset, scenario, **solver_kwargs
            )

            results.append((value, gdp["gdp_change_pct"]))

        return results


@dataclass
class ScenarioComparison:
    """
    Container for comparing multiple scenarios.

    Attributes:
        baseline: Baseline equilibrium.
        scenarios: Dict mapping scenario names to results.
        gdp_impacts: Dict mapping scenario names to GDP impact metrics.
    """

    baseline: EquilibriumResult
    scenarios: dict[str, EquilibriumResult]
    gdp_impacts: dict[str, dict[str, float]]

    def summary_table(self) -> "pd.DataFrame":
        """Create a summary DataFrame of all scenarios."""
        import pandas as pd

        rows = []
        for name, result in self.scenarios.items():
            impact = self.gdp_impacts[name]
            rows.append(
                {
                    "Scenario": name,
                    "Total GDP": result.total_gdp,
                    "GDP Change (%)": impact["gdp_change_pct"],
                    "Converged": result.converged,
                }
            )

        return pd.DataFrame(rows)


def run_multiple_scenarios(
    model: RosenRobackModel,
    dataset: RosenRobackDataset,
    scenarios: list[CounterfactualScenario],
    **solver_kwargs: Any,
) -> ScenarioComparison:
    """
    Run multiple counterfactual scenarios and compare results.

    Args:
        model: RosenRobackModel instance.
        dataset: Baseline dataset.
        scenarios: List of scenarios to run.
        **solver_kwargs: Additional solver arguments.

    Returns:
        ScenarioComparison with all results.
    """
    baseline = model.solve(dataset, **solver_kwargs)

    scenario_results = {}
    gdp_impacts = {}

    for scenario in scenarios:
        _, result, gdp = model.run_counterfactual(
            dataset, scenario, **solver_kwargs
        )
        scenario_results[scenario.name] = result
        gdp_impacts[scenario.name] = gdp

    return ScenarioComparison(
        baseline=baseline,
        scenarios=scenario_results,
        gdp_impacts=gdp_impacts,
    )
