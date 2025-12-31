"""Dataset abstractions for the Rosen-Roback model.

This module provides abstract and concrete dataset classes that encapsulate
data loading, validation, and transformation for use with the spatial
equilibrium model.

The key abstraction is RosenRobackDataset, which any data source must implement
to be usable with the model. This allows swapping between UK, US, or synthetic
data without changing model code.
"""

from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Any

import numpy as np
import pandas as pd

from .parameters import CityParameters


class RosenRobackDataset(ABC):
    """
    Abstract base class for datasets usable with the Rosen-Roback model.

    Implementations must provide methods to extract city parameters and
    total population from the underlying data source.

    Example:
        >>> class MyDataset(RosenRobackDataset):
        ...     @property
        ...     def name(self) -> str:
        ...         return "My Custom Dataset"
        ...
        ...     def get_cities(self) -> list[CityParameters]:
        ...         return [CityParameters("City1", 100), ...]
        ...
        ...     def get_total_population(self) -> float:
        ...         return 1_000_000
    """

    @property
    @abstractmethod
    def name(self) -> str:
        """Human-readable name for this dataset."""

    @abstractmethod
    def get_cities(self) -> list[CityParameters]:
        """
        Extract city parameters from the dataset.

        Returns:
            List of CityParameters, one per city in the dataset.
        """

    @abstractmethod
    def get_total_population(self) -> float:
        """
        Get the total population to distribute across cities.

        Returns:
            Total population (sum across all cities).
        """

    def get_city_names(self) -> list[str]:
        """Get list of city names."""
        return [c.name for c in self.get_cities()]

    def __len__(self) -> int:
        """Number of cities in the dataset."""
        return len(self.get_cities())

    def __repr__(self) -> str:
        return f"{self.__class__.__name__}(name='{self.name}', n_cities={len(self)})"


class DataFrameDataset(RosenRobackDataset):
    """
    Dataset backed by a pandas DataFrame.

    This is the most flexible dataset type, allowing any DataFrame with
    the appropriate columns to be used with the model. Column names are
    configurable to match different data sources.

    Attributes:
        df: The underlying DataFrame.
        name_col: Column containing city names.
        tfp_col: Column containing base TFP values (or None to infer).
        amenity_col: Column containing amenity values (or None for default=1).
        elasticity_col: Column containing housing supply elasticities.
        supply_shifter_col: Column containing supply shifters (or None for default).
        population_col: Column containing population/employment.

    Example:
        >>> df = pd.DataFrame({
        ...     "city": ["London", "Manchester"],
        ...     "wage": [45000, 35000],
        ...     "rent": [20000, 8000],
        ...     "elasticity": [0.8, 2.0],
        ...     "employment": [5_000_000, 2_000_000]
        ... })
        >>> dataset = DataFrameDataset(
        ...     df,
        ...     name="UK Cities",
        ...     name_col="city",
        ...     elasticity_col="elasticity",
        ...     population_col="employment"
        ... )
    """

    def __init__(
        self,
        df: pd.DataFrame,
        name: str,
        name_col: str = "city",
        tfp_col: str | None = None,
        wage_col: str | None = None,
        rent_col: str | None = None,
        amenity_col: str | None = None,
        elasticity_col: str = "elasticity",
        supply_shifter_col: str | None = None,
        population_col: str = "population",
        default_elasticity: float = 2.0,
        default_amenity: float = 1.0,
        default_supply_shifter: float = 1000.0,
    ):
        """
        Initialize a DataFrame-backed dataset.

        Args:
            df: DataFrame containing city data.
            name: Human-readable name for this dataset.
            name_col: Column with city names.
            tfp_col: Column with base TFP (if None, infer from wages/rents).
            wage_col: Column with wages (used to infer TFP if tfp_col is None).
            rent_col: Column with rents (used to infer TFP if tfp_col is None).
            amenity_col: Column with amenities (if None, use default).
            elasticity_col: Column with supply elasticities.
            supply_shifter_col: Column with supply shifters (if None, use default).
            population_col: Column with population/employment.
            default_elasticity: Default elasticity if column missing.
            default_amenity: Default amenity value if column missing.
            default_supply_shifter: Default supply shifter if column missing.
        """
        self._df = df.copy()
        self._name = name
        self._name_col = name_col
        self._tfp_col = tfp_col
        self._wage_col = wage_col
        self._rent_col = rent_col
        self._amenity_col = amenity_col
        self._elasticity_col = elasticity_col
        self._supply_shifter_col = supply_shifter_col
        self._population_col = population_col
        self._default_elasticity = default_elasticity
        self._default_amenity = default_amenity
        self._default_supply_shifter = default_supply_shifter

        self._validate()

    def _validate(self) -> None:
        """Validate that required columns exist."""
        required = [self._name_col, self._population_col]
        missing = [col for col in required if col not in self._df.columns]
        if missing:
            raise ValueError(f"Missing required columns: {missing}")

        # Need either TFP directly or wages/rents to infer it
        if self._tfp_col is None and (
            self._wage_col is None or self._rent_col is None
        ):
            raise ValueError(
                "Must provide either tfp_col or both wage_col and rent_col"
            )

    @property
    def name(self) -> str:
        return self._name

    @property
    def df(self) -> pd.DataFrame:
        """Access the underlying DataFrame."""
        return self._df

    def get_cities(self) -> list[CityParameters]:
        """Extract city parameters from the DataFrame."""
        cities = []

        for _, row in self._df.iterrows():
            # Get base TFP - either directly or infer from wages/rents
            if self._tfp_col and self._tfp_col in self._df.columns:
                base_tfp = float(row[self._tfp_col])
            else:
                # Infer TFP from wages and rents using spatial equilibrium
                # Z = W / P^beta (using beta=0.33)
                wage = float(row[self._wage_col])
                rent = float(row[self._rent_col])
                beta = 0.33
                base_tfp = wage / (rent**beta)

            # Get amenity
            if self._amenity_col and self._amenity_col in self._df.columns:
                amenity = float(row[self._amenity_col])
            else:
                amenity = self._default_amenity

            # Get elasticity
            if self._elasticity_col in self._df.columns:
                elasticity = float(row[self._elasticity_col])
            else:
                elasticity = self._default_elasticity

            # Get supply shifter
            if (
                self._supply_shifter_col
                and self._supply_shifter_col in self._df.columns
            ):
                supply_shifter = float(row[self._supply_shifter_col])
            else:
                supply_shifter = self._default_supply_shifter

            cities.append(
                CityParameters(
                    name=str(row[self._name_col]),
                    base_tfp=base_tfp,
                    amenity=amenity,
                    supply_elasticity=elasticity,
                    supply_shifter=supply_shifter,
                )
            )

        return cities

    def get_total_population(self) -> float:
        """Sum of population across all cities."""
        return float(self._df[self._population_col].sum())


class SyntheticDataset(RosenRobackDataset):
    """
    Generate synthetic cities for testing and teaching.

    Creates a set of cities with varying productivity, amenities, and
    housing supply elasticities drawn from specified distributions.
    Useful for demonstrating model behavior without real data.

    Example:
        >>> dataset = SyntheticDataset(n_cities=10, seed=42)
        >>> cities = dataset.get_cities()
        >>> len(cities)
        10
    """

    def __init__(
        self,
        n_cities: int = 10,
        total_population: float = 10_000_000,
        tfp_range: tuple[float, float] = (70, 130),
        amenity_range: tuple[float, float] = (0.7, 1.3),
        elasticity_range: tuple[float, float] = (0.5, 3.0),
        supply_shifter: float = 1000.0,
        seed: int | None = None,
    ):
        """
        Initialize a synthetic dataset.

        Args:
            n_cities: Number of cities to generate.
            total_population: Total population to distribute.
            tfp_range: (min, max) for uniform TFP distribution.
            amenity_range: (min, max) for uniform amenity distribution.
            elasticity_range: (min, max) for uniform elasticity distribution.
            supply_shifter: Common supply shifter for all cities.
            seed: Random seed for reproducibility.
        """
        self._n_cities = n_cities
        self._total_population = total_population
        self._tfp_range = tfp_range
        self._amenity_range = amenity_range
        self._elasticity_range = elasticity_range
        self._supply_shifter = supply_shifter
        self._seed = seed

        # Generate cities
        self._cities = self._generate_cities()

    def _generate_cities(self) -> list[CityParameters]:
        """Generate random city parameters."""
        rng = np.random.default_rng(self._seed)

        cities = []
        for i in range(self._n_cities):
            cities.append(
                CityParameters(
                    name=f"City_{i + 1}",
                    base_tfp=rng.uniform(*self._tfp_range),
                    amenity=rng.uniform(*self._amenity_range),
                    supply_elasticity=rng.uniform(*self._elasticity_range),
                    supply_shifter=self._supply_shifter,
                )
            )

        return cities

    @property
    def name(self) -> str:
        return f"Synthetic ({self._n_cities} cities)"

    def get_cities(self) -> list[CityParameters]:
        return self._cities

    def get_total_population(self) -> float:
        return self._total_population


class ThreeCityDataset(RosenRobackDataset):
    """
    Simple three-city dataset for pedagogical examples.

    Creates three cities: High Productivity, Medium, and Low Productivity,
    with configurable parameters. Ideal for teaching basic model behavior.

    Example:
        >>> dataset = ThreeCityDataset()
        >>> cities = dataset.get_cities()
        >>> [c.name for c in cities]
        ['High Productivity', 'Medium', 'Low Productivity']
    """

    def __init__(
        self,
        high_tfp: float = 120,
        medium_tfp: float = 100,
        low_tfp: float = 80,
        high_elasticity: float = 1.5,
        medium_elasticity: float = 2.0,
        low_elasticity: float = 3.0,
        total_population: float = 3_000_000,
    ):
        """
        Initialize a three-city dataset.

        Args:
            high_tfp: TFP of high-productivity city.
            medium_tfp: TFP of medium city.
            low_tfp: TFP of low-productivity city.
            high_elasticity: Housing elasticity of high-productivity city.
            medium_elasticity: Housing elasticity of medium city.
            low_elasticity: Housing elasticity of low-productivity city.
            total_population: Total population to distribute.
        """
        self._total_population = total_population
        self._cities = [
            CityParameters(
                name="High Productivity",
                base_tfp=high_tfp,
                amenity=1.0,
                supply_elasticity=high_elasticity,
                supply_shifter=1000,
            ),
            CityParameters(
                name="Medium",
                base_tfp=medium_tfp,
                amenity=1.0,
                supply_elasticity=medium_elasticity,
                supply_shifter=1000,
            ),
            CityParameters(
                name="Low Productivity",
                base_tfp=low_tfp,
                amenity=1.0,
                supply_elasticity=low_elasticity,
                supply_shifter=1000,
            ),
        ]

    @property
    def name(self) -> str:
        return "Three Cities (HP/M/LP)"

    def get_cities(self) -> list[CityParameters]:
        return self._cities

    def get_total_population(self) -> float:
        return self._total_population

    def with_constrained_hp(self, elasticity: float) -> "ThreeCityDataset":
        """
        Create a copy with modified high-productivity elasticity.

        Useful for counterfactual analysis.
        """
        new_dataset = ThreeCityDataset(
            high_tfp=self._cities[0].base_tfp,
            medium_tfp=self._cities[1].base_tfp,
            low_tfp=self._cities[2].base_tfp,
            high_elasticity=elasticity,
            medium_elasticity=self._cities[1].supply_elasticity,
            low_elasticity=self._cities[2].supply_elasticity,
            total_population=self._total_population,
        )
        return new_dataset


@dataclass
class CounterfactualScenario:
    """
    Defines a counterfactual scenario for policy analysis.

    A scenario specifies how housing supply elasticities change from
    baseline to counterfactual, allowing comparison of outcomes.

    Attributes:
        name: Scenario name (e.g., "Reform", "Full Liberalisation").
        description: Human-readable description.
        elasticity_changes: Dict mapping city names to new elasticities.
            Cities not in the dict keep their baseline elasticity.

    Example:
        >>> scenario = CounterfactualScenario(
        ...     name="London Reform",
        ...     description="Increase London's elasticity to 2.0",
        ...     elasticity_changes={"London": 2.0}
        ... )
    """

    name: str
    description: str
    elasticity_changes: dict[str, float]

    def apply_to_dataset(
        self, baseline: RosenRobackDataset
    ) -> list[CityParameters]:
        """
        Apply this scenario to a baseline dataset.

        Returns a new list of CityParameters with modified elasticities.
        """
        cities = baseline.get_cities()
        new_cities = []

        for city in cities:
            if city.name in self.elasticity_changes:
                new_elasticity = self.elasticity_changes[city.name]
                new_cities.append(
                    CityParameters(
                        name=city.name,
                        base_tfp=city.base_tfp,
                        amenity=city.amenity,
                        supply_elasticity=new_elasticity,
                        supply_shifter=city.supply_shifter,
                    )
                )
            else:
                new_cities.append(city)

        return new_cities
