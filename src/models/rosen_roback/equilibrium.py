"""Equilibrium solver for the Rosen-Roback spatial equilibrium model.

This module implements the iterative algorithm that finds the equilibrium
distribution of workers across cities.

Two equilibrium concepts are supported:

1. **Perfect mobility** (calibrate_amenities=True): Amenities are calibrated
   so that utilities exactly equalize across cities. This is the classic
   Rosen-Roback equilibrium.

2. **Imperfect mobility** (calibrate_amenities=False): Uses a Fréchet/logit
   model where share_i ∝ V_i^θ. Utilities don't perfectly equalize - the
   spread depends on θ (mobility parameter). This represents moving costs
   and heterogeneous preferences.

The solver uses log-space calculations for numerical stability.
"""

import numpy as np
from scipy.special import logsumexp as scipy_logsumexp

from .parameters import CityParameters, EquilibriumResult, ModelParameters


class EquilibriumSolver:
    """
    Iterative solver for spatial equilibrium.

    The solver finds the population distribution where workers are
    (approximately) indifferent between cities. Uses a probabilistic
    model where workers flow toward high-utility cities.

    Algorithm:
        1. Start with equal population distribution
        2. Calculate wages and rents from population
        3. Calculate utility in each city
        4. Update population shares: share_i proportional to utility_i^theta
        5. Repeat until convergence

    The theta parameter controls mobility: higher theta means workers
    respond more strongly to utility differences.

    Attributes:
        params: Model parameters.
        cities: List of city parameters.

    Example:
        >>> solver = EquilibriumSolver(ModelParameters(), cities)
        >>> result = solver.solve(total_population=1_000_000)
        >>> print(result.summary())
    """

    def __init__(self, params: ModelParameters, cities: list[CityParameters]):
        """
        Initialize the solver.

        Args:
            params: Model parameters (elasticities, shares).
            cities: List of city-specific parameters.
        """
        self.params = params
        self.cities = cities
        self.n_cities = len(cities)

        # Pre-compute log of city-specific parameters for efficiency
        self._log_base_tfp = np.array([np.log(c.base_tfp) for c in cities])
        self._log_amenity = np.array([np.log(c.amenity) for c in cities])
        self._supply_elasticity = np.array([c.supply_elasticity for c in cities])
        self._log_supply_shifter = np.array(
            [np.log(c.supply_shifter) for c in cities]
        )

    def log_rent_from_log_population(self, log_pop: np.ndarray) -> np.ndarray:
        """
        Calculate log rents given log population.

        From housing market equilibrium: r = (L/S)^(1/gamma)
        In logs: log(r) = (log(L) - log(S)) / gamma
        """
        return (log_pop - self._log_supply_shifter) / self._supply_elasticity

    def log_wage_from_log_population(self, log_pop: np.ndarray) -> np.ndarray:
        """
        Calculate log wages given log population.

        From production: w = alpha * A * L^(alpha + eta - 1)
        Where A = base_A * L^eta (agglomeration)
        In logs: log(w) = log(alpha) + log(base_A) + (alpha + eta - 1) * log(L)
        """
        p = self.params
        return np.log(p.alpha) + self._log_base_tfp + (p.alpha + p.eta - 1) * log_pop

    def log_utility(
        self, log_wages: np.ndarray, log_rents: np.ndarray
    ) -> np.ndarray:
        """
        Calculate log utility in each city.

        Utility: V = (w / r^beta) * a
        In logs: log(V) = log(w) - beta * log(r) + log(a)
        """
        return log_wages - self.params.beta * log_rents + self._log_amenity

    def log_output(self, log_pop: np.ndarray) -> np.ndarray:
        """
        Calculate log output in each city.

        Output: Y = A * L^alpha where A = base_A * L^eta
        So: Y = base_A * L^(alpha + eta)
        In logs: log(Y) = log(base_A) + (alpha + eta) * log(L)
        """
        return (
            self._log_base_tfp
            + (self.params.alpha + self.params.eta) * log_pop
        )

    def _logsumexp(self, x: np.ndarray) -> float:
        """
        Numerically stable log-sum-exp.

        Computes log(sum(exp(x))) without overflow.
        Uses scipy's implementation for better numerical stability.
        """
        return float(scipy_logsumexp(x))

    def _log_softmax(self, x: np.ndarray) -> np.ndarray:
        """
        Compute log(softmax(x)) in a numerically stable way.

        Returns log probabilities that sum to 1 (in probability space).
        """
        # log_softmax(x) = x - logsumexp(x)
        return x - scipy_logsumexp(x)

    def solve(
        self,
        total_population: float,
        tol: float = 1e-8,
        max_iter: int = 2000,
        damping: float = 0.3,
        verbose: bool = False,
    ) -> EquilibriumResult:
        """
        Solve for spatial equilibrium using the Fréchet/probabilistic model.

        In this model, worker location follows a Fréchet distribution:
            share_i ∝ V_i^θ

        This means utilities don't perfectly equalize - instead, the population
        distribution reflects utility differences scaled by mobility (θ).

        - Higher θ: More mobile workers, utilities converge closer
        - Lower θ: Less mobile workers, larger utility differences persist

        The equilibrium represents a balance where no worker wants to move
        given their idiosyncratic preferences (captured by the Fréchet shocks).

        Args:
            total_population: Total population to distribute across cities.
            tol: Convergence tolerance (max change in population shares).
            max_iter: Maximum iterations before giving up.
            damping: Damping factor for updates (0-1, lower = more stable).
            verbose: If True, print iteration progress.

        Returns:
            EquilibriumResult containing population, wages, rents, etc.
        """
        # Initial guess: equal distribution in log space
        log_total_pop = np.log(total_population)
        log_pop = np.full(self.n_cities, log_total_pop - np.log(self.n_cities))

        # Adaptive damping for high theta (more mobile workers need gentler updates)
        # Use very strong damping for high theta to prevent oscillation
        effective_damping = min(damping, 0.5 / (1.0 + self.params.theta / 5.0))

        converged = False
        iteration = 0
        for iteration in range(max_iter):
            # Calculate wages and rents in log space
            log_rents = self.log_rent_from_log_population(log_pop)
            log_wages = self.log_wage_from_log_population(log_pop)
            log_utilities = self.log_utility(log_wages, log_rents)

            # Workers move toward high-utility cities
            # share_i proportional to utility_i^theta
            # Use log_softmax for numerical stability
            log_shares = self._log_softmax(self.params.theta * log_utilities)

            # Check for numerical issues
            if not np.all(np.isfinite(log_shares)):
                # Fall back to equal shares if numerical issues
                log_shares = np.full(self.n_cities, -np.log(self.n_cities))

            # New population in log space
            new_log_pop = log_shares + log_total_pop

            # Damped update for stability
            new_log_pop = (
                effective_damping * new_log_pop
                + (1 - effective_damping) * log_pop
            )

            # Check convergence on population shares
            old_shares = np.exp(self._log_softmax(log_pop))
            new_shares = np.exp(self._log_softmax(new_log_pop))
            diff = np.abs(new_shares - old_shares).max()

            if verbose and iteration % 100 == 0:
                utilities = np.exp(log_utilities)
                util_spread = (utilities.max() / utilities.min() - 1) * 100
                print(
                    f"Iteration {iteration}: share change = {diff:.2e}, "
                    f"utility spread = {util_spread:.2f}%"
                )

            log_pop = new_log_pop

            if diff < tol:
                converged = True
                break

        # Final calculations (convert back from log space)
        population = np.exp(log_pop)
        # Renormalize to ensure exact total
        population = population * (total_population / population.sum())

        log_pop = np.log(population)
        log_rents = self.log_rent_from_log_population(log_pop)
        log_wages = self.log_wage_from_log_population(log_pop)
        log_utilities = self.log_utility(log_wages, log_rents)
        log_outputs = self.log_output(log_pop)

        rents = np.exp(log_rents)
        wages = np.exp(log_wages)
        utilities = np.exp(log_utilities)
        outputs = np.exp(log_outputs)

        return EquilibriumResult(
            city_names=[c.name for c in self.cities],
            population=population.tolist(),
            wages=wages.tolist(),
            rents=rents.tolist(),
            utilities=utilities.tolist(),
            outputs=outputs.tolist(),
            total_gdp=float(outputs.sum()),
            converged=converged,
            iterations=iteration + 1,
        )


def calculate_gdp_change(
    baseline: EquilibriumResult, counterfactual: EquilibriumResult
) -> dict[str, float]:
    """
    Calculate GDP change between two equilibria.

    Args:
        baseline: Baseline equilibrium result.
        counterfactual: Counterfactual equilibrium result.

    Returns:
        Dictionary with GDP metrics:
        - baseline_gdp: GDP under baseline
        - counterfactual_gdp: GDP under counterfactual
        - gdp_change: Absolute change
        - gdp_change_pct: Percentage change
    """
    gdp_change = counterfactual.total_gdp - baseline.total_gdp
    gdp_change_pct = (gdp_change / baseline.total_gdp) * 100

    return {
        "baseline_gdp": baseline.total_gdp,
        "counterfactual_gdp": counterfactual.total_gdp,
        "gdp_change": gdp_change,
        "gdp_change_pct": gdp_change_pct,
    }
