"""Visualization utilities for housing price analysis.

This module provides reusable plotting functions for the Rosen-Roback
spatial equilibrium model and other housing analysis.

Example:
    >>> from src.visualization import plot_equilibrium_summary
    >>> from src.models.rosen_roback import RosenRobackModel, ThreeCityDataset
    >>>
    >>> model = RosenRobackModel()
    >>> result = model.solve(ThreeCityDataset())
    >>> fig = plot_equilibrium_summary(result)
    >>> fig.savefig("equilibrium.png")
"""

from .common import (
    COLOR_SEQUENCE,
    COLORS,
    FIGURE_SIZES,
    add_value_labels,
    create_figure,
    format_large_number,
    save_figure,
    set_style,
)
from .rosen_roback import (
    plot_counterfactual_comparison,
    plot_equilibrium_summary,
    plot_gdp_by_scenario,
    plot_rosen_roback_diagram,
    plot_sensitivity_analysis,
    plot_supply_elasticity_effect,
    plot_utility_convergence,
)

__all__ = [
    # Common utilities
    "set_style",
    "create_figure",
    "save_figure",
    "format_large_number",
    "add_value_labels",
    "COLORS",
    "COLOR_SEQUENCE",
    "FIGURE_SIZES",
    # Rosen-Roback plots
    "plot_equilibrium_summary",
    "plot_rosen_roback_diagram",
    "plot_supply_elasticity_effect",
    "plot_sensitivity_analysis",
    "plot_counterfactual_comparison",
    "plot_gdp_by_scenario",
    "plot_utility_convergence",
]
