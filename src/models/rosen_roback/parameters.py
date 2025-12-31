"""Parameter dataclasses for the Rosen-Roback spatial equilibrium model.

This module defines the configuration objects used throughout the model:
- ModelParameters: Global model parameters (elasticities, shares)
- CityParameters: Per-city parameters (productivity, amenities, housing supply)
"""

from dataclasses import dataclass, field
from typing import ClassVar


@dataclass(frozen=True)
class ModelParameters:
    """
    Global parameters for the Rosen-Roback spatial equilibrium model.

    These control the key elasticities and shares in the model. Default values
    are based on standard estimates from the urban economics literature.

    Attributes:
        alpha: Labour share in production (typically 0.6-0.7).
        eta: Agglomeration elasticity - how much productivity increases with
             city size. Standard estimates: 0.02-0.08. Cooped Up uses 0.25.
        beta: Housing expenditure share - fraction of income spent on housing.
        theta: Labour mobility (Fréchet shape parameter). Higher values mean
               workers respond more strongly to utility differences.
               - theta=3: ~15% utility spread (significant moving costs)
               - theta=10: ~6% utility spread (moderate mobility)
               - theta=20+: <3% spread (high mobility, classic R-R)

    Example:
        >>> params = ModelParameters()  # Use defaults
        >>> params = ModelParameters(eta=0.06)  # Override agglomeration
    """

    alpha: float = 0.65
    eta: float = 0.04
    beta: float = 0.33
    theta: float = 10.0  # Default to moderate mobility for intuitive results

    # Named parameter sets
    STANDARD: ClassVar["ModelParameters"]
    HSIEH_MORETTI: ClassVar["ModelParameters"]
    COOPED_UP: ClassVar["ModelParameters"]

    def __post_init__(self) -> None:
        """Validate parameters are in reasonable ranges."""
        if not 0 < self.alpha < 1:
            raise ValueError(f"alpha must be in (0, 1), got {self.alpha}")
        if self.eta < 0:
            raise ValueError(f"eta must be non-negative, got {self.eta}")
        if not 0 < self.beta < 1:
            raise ValueError(f"beta must be in (0, 1), got {self.beta}")
        if self.theta <= 0:
            raise ValueError(f"theta must be positive, got {self.theta}")

    def with_updates(self, **kwargs) -> "ModelParameters":
        """Create a new ModelParameters with some values updated."""
        return ModelParameters(
            alpha=kwargs.get("alpha", self.alpha),
            eta=kwargs.get("eta", self.eta),
            beta=kwargs.get("beta", self.beta),
            theta=kwargs.get("theta", self.theta),
        )


# Standard academic estimates with moderate mobility
ModelParameters.STANDARD = ModelParameters(
    alpha=0.65,
    eta=0.04,
    beta=0.33,
    theta=10.0,  # ~6% utility spread
)

# Hsieh-Moretti (2019) calibration
ModelParameters.HSIEH_MORETTI = ModelParameters(
    alpha=0.65,
    eta=0.25,
    beta=0.33,
    theta=2.0,  # Original paper value
)

# Cooped Up paper calibration
ModelParameters.COOPED_UP = ModelParameters(
    alpha=0.65,
    eta=0.25,
    beta=0.32,
    theta=3.33,  # Original paper value
)

# High mobility (classic Rosen-Roback with nearly equal utilities)
ModelParameters.HIGH_MOBILITY = ModelParameters(
    alpha=0.65,
    eta=0.04,
    beta=0.33,
    theta=50.0,  # ~1.5% utility spread
)


@dataclass
class CityParameters:
    """
    Parameters for a single city in the model.

    Each city has its own productivity, amenity value, and housing supply
    characteristics. These determine how wages and rents respond to population.

    Attributes:
        name: City identifier (e.g., "London", "Manchester").
        base_tfp: Base total factor productivity. Higher values mean
                  firms in this city are more productive.
        amenity: Amenity value. Higher values mean workers prefer this city
                 independent of wages and rents.
        supply_elasticity: Housing supply elasticity (gamma). Higher values
                          mean housing supply responds more to rent increases.
                          Examples: San Francisco ~0.7, Houston ~2.5.
        supply_shifter: Housing supply shifter. Affects the level of rents
                       at any given population. Can represent land availability.

    Example:
        >>> london = CityParameters(
        ...     name="London",
        ...     base_tfp=120,
        ...     amenity=1.2,
        ...     supply_elasticity=0.8,
        ...     supply_shifter=1000
        ... )
    """

    name: str
    base_tfp: float
    amenity: float = 1.0
    supply_elasticity: float = 2.0
    supply_shifter: float = 1000.0

    def __post_init__(self) -> None:
        """Validate city parameters."""
        if self.base_tfp <= 0:
            raise ValueError(f"base_tfp must be positive, got {self.base_tfp}")
        if self.amenity <= 0:
            raise ValueError(f"amenity must be positive, got {self.amenity}")
        if self.supply_elasticity <= 0:
            raise ValueError(
                f"supply_elasticity must be positive, got {self.supply_elasticity}"
            )
        if self.supply_shifter <= 0:
            raise ValueError(
                f"supply_shifter must be positive, got {self.supply_shifter}"
            )


@dataclass
class EquilibriumResult:
    """
    Results from solving the spatial equilibrium.

    Contains the equilibrium distribution of population, wages, rents,
    and output across cities, along with convergence information.

    Attributes:
        city_names: List of city names in order.
        population: Equilibrium population in each city.
        wages: Equilibrium wage in each city.
        rents: Equilibrium rent in each city.
        utilities: Worker utility in each city (approximately equal in equilibrium).
        outputs: Total output produced in each city.
        total_gdp: Sum of outputs across all cities.
        converged: Whether the solver converged.
        iterations: Number of iterations taken.
    """

    city_names: list[str]
    population: list[float] = field(default_factory=list)
    wages: list[float] = field(default_factory=list)
    rents: list[float] = field(default_factory=list)
    utilities: list[float] = field(default_factory=list)
    outputs: list[float] = field(default_factory=list)
    total_gdp: float = 0.0
    converged: bool = False
    iterations: int = 0

    def __len__(self) -> int:
        """Number of cities."""
        return len(self.city_names)

    def to_dataframe(self):
        """Convert results to a pandas DataFrame."""
        import pandas as pd

        return pd.DataFrame(
            {
                "city": self.city_names,
                "population": self.population,
                "wage": self.wages,
                "rent": self.rents,
                "utility": self.utilities,
                "output": self.outputs,
            }
        )

    def utility_spread_pct(self) -> float:
        """Calculate percentage spread in utilities (max/min - 1)."""
        if not self.utilities:
            return 0.0
        utils = [u for u in self.utilities if u > 0]
        if not utils:
            return 0.0
        return (max(utils) / min(utils) - 1) * 100

    def summary(self) -> str:
        """Return a formatted summary string."""
        lines = [
            "Spatial Equilibrium Results",
            "=" * 70,
            f"{'City':<25} {'Population':>12} {'Wage':>10} {'Rent':>10} {'Utility':>10}",
            "-" * 70,
        ]
        for i, name in enumerate(self.city_names):
            lines.append(
                f"{name:<25} {self.population[i]:>12,.0f} "
                f"{self.wages[i]:>10.2f} {self.rents[i]:>10.2f} "
                f"{self.utilities[i]:>10.4f}"
            )
        lines.append("-" * 70)
        lines.append(f"Total GDP: {self.total_gdp:,.0f}")
        spread = self.utility_spread_pct()
        lines.append(f"Utility spread: {spread:.1f}% (smaller = closer to classic R-R equilibrium)")
        lines.append(f"Converged: {self.converged} ({self.iterations} iterations)")
        return "\n".join(lines)
