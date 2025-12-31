"""Visualization functions for the Rosen-Roback spatial equilibrium model.

Provides publication-quality plots for:
- Equilibrium summaries (population, wages, rents)
- Rosen-Roback diagrams (wage-rent scatter)
- Housing supply elasticity effects
- Sensitivity analysis
- Counterfactual comparisons
"""

from typing import Any

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

from src.models.rosen_roback import EquilibriumResult

from .common import (
    COLOR_SEQUENCE,
    COLORS,
    add_value_labels,
    create_figure,
    format_large_number,
)


def plot_equilibrium_summary(
    result: EquilibriumResult,
    title: str | None = None,
    figsize: tuple[float, float] = (14, 4),
) -> plt.Figure:
    """
    Create bar charts showing population, wages, and rents.

    Args:
        result: Equilibrium result to visualize.
        title: Optional figure title.
        figsize: Figure size.

    Returns:
        Matplotlib Figure object.
    """
    fig, axes = create_figure(1, 3, figsize=figsize)

    city_names = result.city_names
    n_cities = len(city_names)
    colors = COLOR_SEQUENCE[:n_cities]

    # Shorten names if needed
    short_names = [
        name[:15] + "..." if len(name) > 18 else name for name in city_names
    ]

    # Population
    bars = axes[0].bar(short_names, np.array(result.population) / 1e6, color=colors)
    axes[0].set_ylabel("Population (millions)")
    axes[0].set_title("Population Distribution")
    axes[0].tick_params(axis="x", rotation=45)

    # Wages
    axes[1].bar(short_names, result.wages, color=colors)
    axes[1].set_ylabel("Wage (index)")
    axes[1].set_title("Wages")
    axes[1].tick_params(axis="x", rotation=45)

    # Rents
    axes[2].bar(short_names, result.rents, color=colors)
    axes[2].set_ylabel("Rent (index)")
    axes[2].set_title("Rents")
    axes[2].tick_params(axis="x", rotation=45)

    if title:
        fig.suptitle(title, y=1.02, fontsize=14)

    plt.tight_layout()
    return fig


def plot_rosen_roback_diagram(
    result: EquilibriumResult,
    color_by: str = "population",
    city_data: pd.DataFrame | None = None,
    color_col: str | None = None,
    label_top_n: int = 5,
    title: str = "Rosen-Roback Diagram",
    figsize: tuple[float, float] = (10, 8),
) -> plt.Figure:
    """
    Create the classic wage-rent scatter plot.

    Points can be colored by population, productivity, or a custom column.

    Args:
        result: Equilibrium result.
        color_by: What to color by ("population", "productivity", or "custom").
        city_data: DataFrame with additional city data (for custom coloring).
        color_col: Column name in city_data for custom coloring.
        label_top_n: Number of extreme points to label.
        title: Plot title.
        figsize: Figure size.

    Returns:
        Matplotlib Figure.
    """
    fig, ax = create_figure(figsize=figsize)

    rents = np.array(result.rents)
    wages = np.array(result.wages)
    population = np.array(result.population)

    # Determine colors
    if color_by == "population":
        colors = population
        cmap = "viridis"
        cbar_label = "Population"
    elif color_by == "productivity" and city_data is not None:
        colors = city_data["productivity"].values
        cmap = "RdYlGn"
        cbar_label = "Productivity"
    elif color_by == "custom" and city_data is not None and color_col:
        colors = city_data[color_col].values
        cmap = "RdYlBu"
        cbar_label = color_col
    else:
        colors = population
        cmap = "viridis"
        cbar_label = "Population"

    # Size by population
    sizes = (population / population.max()) * 200 + 50

    scatter = ax.scatter(
        rents,
        wages,
        c=colors,
        s=sizes,
        cmap=cmap,
        alpha=0.7,
        edgecolors="black",
        linewidths=0.5,
    )

    # Add colorbar
    cbar = plt.colorbar(scatter, ax=ax)
    cbar.set_label(cbar_label)

    # Label extreme points
    if label_top_n > 0:
        # Find points to label (highest/lowest wages and rents)
        indices_to_label = set()

        # Highest wages
        indices_to_label.update(np.argsort(wages)[-label_top_n:])
        # Highest rents
        indices_to_label.update(np.argsort(rents)[-label_top_n:])

        for i in indices_to_label:
            ax.annotate(
                result.city_names[i],
                (rents[i], wages[i]),
                xytext=(5, 5),
                textcoords="offset points",
                fontsize=9,
                alpha=0.8,
            )

    ax.set_xlabel("Rent")
    ax.set_ylabel("Wage")
    ax.set_title(title)

    plt.tight_layout()
    return fig


def plot_supply_elasticity_effect(
    populations: np.ndarray | list[float],
    elasticities: list[float],
    labels: list[str] | None = None,
    supply_shifter: float = 1_000_000,
    title: str = "How Housing Supply Elasticity Affects Rent",
    figsize: tuple[float, float] = (10, 6),
) -> plt.Figure:
    """
    Show how different elasticities affect rent response to population.

    Demonstrates the key insight that inelastic supply causes rent spikes.

    Args:
        populations: Array of population values for x-axis.
        elasticities: List of elasticity values to compare.
        labels: Optional labels for each elasticity (e.g., city names).
        supply_shifter: Housing supply shifter parameter.
        title: Plot title.
        figsize: Figure size.

    Returns:
        Matplotlib Figure.
    """
    fig, ax = create_figure(figsize=figsize)

    populations = np.array(populations)

    for i, gamma in enumerate(elasticities):
        rents = (populations / supply_shifter) ** (1 / gamma)
        label = labels[i] if labels else f"gamma={gamma}"
        ax.plot(
            populations / 1e6,
            rents,
            label=label,
            linewidth=2,
            color=COLOR_SEQUENCE[i % len(COLOR_SEQUENCE)],
        )

    ax.set_xlabel("Population (millions)")
    ax.set_ylabel("Equilibrium rent (index)")
    ax.set_title(title)
    ax.legend()

    plt.tight_layout()
    return fig


def plot_sensitivity_analysis(
    parameter_values: list[float],
    gdp_changes: list[float],
    parameter_name: str,
    reference_value: float | None = None,
    title: str | None = None,
    figsize: tuple[float, float] = (8, 5),
) -> plt.Figure:
    """
    Plot sensitivity of GDP loss to a model parameter.

    Args:
        parameter_values: Parameter values tested.
        gdp_changes: GDP change (%) for each parameter value.
        parameter_name: Name of parameter (for axis label).
        reference_value: Optional reference value to highlight.
        title: Plot title.
        figsize: Figure size.

    Returns:
        Matplotlib Figure.
    """
    fig, ax = create_figure(figsize=figsize)

    ax.plot(
        parameter_values,
        gdp_changes,
        "o-",
        linewidth=2,
        markersize=8,
        color=COLORS["primary"],
    )

    if reference_value is not None:
        ax.axvline(
            x=reference_value,
            color=COLORS["secondary"],
            linestyle="--",
            label=f"Reference ({parameter_name}={reference_value})",
        )
        ax.legend()

    ax.set_xlabel(parameter_name)
    ax.set_ylabel("GDP change from constraints (%)")
    ax.set_title(title or f"Sensitivity to {parameter_name}")

    ax.axhline(y=0, color="black", linestyle="-", alpha=0.3)

    plt.tight_layout()
    return fig


def plot_counterfactual_comparison(
    baseline: EquilibriumResult,
    counterfactual: EquilibriumResult,
    scenario_name: str = "Counterfactual",
    variables: list[str] | None = None,
    figsize: tuple[float, float] = (14, 5),
) -> plt.Figure:
    """
    Compare baseline and counterfactual equilibria side by side.

    Args:
        baseline: Baseline equilibrium.
        counterfactual: Counterfactual equilibrium.
        scenario_name: Name for the counterfactual scenario.
        variables: Which variables to plot (default: population, wages, rents).
        figsize: Figure size.

    Returns:
        Matplotlib Figure.
    """
    if variables is None:
        variables = ["population", "wages", "rents"]

    n_vars = len(variables)
    fig, axes = create_figure(1, n_vars, figsize=figsize)
    if n_vars == 1:
        axes = [axes]

    city_names = baseline.city_names
    n_cities = len(city_names)
    x = np.arange(n_cities)
    width = 0.35

    short_names = [
        name[:12] + "..." if len(name) > 15 else name for name in city_names
    ]

    for i, var in enumerate(variables):
        baseline_vals = np.array(getattr(baseline, var))
        cf_vals = np.array(getattr(counterfactual, var))

        # Normalize for display
        if var == "population":
            baseline_vals = baseline_vals / 1e6
            cf_vals = cf_vals / 1e6
            ylabel = "Population (millions)"
        else:
            ylabel = var.capitalize()

        axes[i].bar(
            x - width / 2,
            baseline_vals,
            width,
            label="Baseline",
            color=COLORS["primary"],
            alpha=0.8,
        )
        axes[i].bar(
            x + width / 2,
            cf_vals,
            width,
            label=scenario_name,
            color=COLORS["secondary"],
            alpha=0.8,
        )

        axes[i].set_ylabel(ylabel)
        axes[i].set_title(var.capitalize())
        axes[i].set_xticks(x)
        axes[i].set_xticklabels(short_names, rotation=45, ha="right")
        axes[i].legend()

    # Add GDP comparison in suptitle
    gdp_change = (
        (counterfactual.total_gdp - baseline.total_gdp) / baseline.total_gdp * 100
    )
    fig.suptitle(
        f"Baseline vs {scenario_name} (GDP change: {gdp_change:+.2f}%)",
        y=1.02,
        fontsize=14,
    )

    plt.tight_layout()
    return fig


def plot_gdp_by_scenario(
    scenario_names: list[str],
    gdp_changes: list[float],
    title: str = "GDP Impact by Scenario",
    figsize: tuple[float, float] = (10, 6),
) -> plt.Figure:
    """
    Bar chart comparing GDP changes across scenarios.

    Args:
        scenario_names: Names of scenarios.
        gdp_changes: GDP change (%) for each scenario.
        title: Plot title.
        figsize: Figure size.

    Returns:
        Matplotlib Figure.
    """
    fig, ax = create_figure(figsize=figsize)

    colors = [
        COLORS["success"] if x > 0 else COLORS["secondary"] for x in gdp_changes
    ]

    bars = ax.bar(scenario_names, gdp_changes, color=colors, alpha=0.8)
    add_value_labels(ax, bars, fmt=".2f")

    ax.axhline(y=0, color="black", linestyle="-", linewidth=0.5)
    ax.set_ylabel("GDP change (%)")
    ax.set_title(title)
    ax.tick_params(axis="x", rotation=45)

    plt.tight_layout()
    return fig


def plot_utility_convergence(
    result: EquilibriumResult,
    figsize: tuple[float, float] = (10, 6),
) -> plt.Figure:
    """
    Show how utilities compare across cities (should be approximately equal).

    Args:
        result: Equilibrium result.
        figsize: Figure size.

    Returns:
        Matplotlib Figure.
    """
    fig, ax = create_figure(figsize=figsize)

    utilities = np.array(result.utilities)
    mean_utility = utilities.mean()

    # Deviation from mean
    deviations = (utilities - mean_utility) / mean_utility * 100

    colors = [COLORS["success"] if d >= 0 else COLORS["secondary"] for d in deviations]

    bars = ax.bar(result.city_names, deviations, color=colors, alpha=0.8)

    ax.axhline(y=0, color="black", linestyle="-", linewidth=1)
    ax.set_ylabel("Deviation from mean utility (%)")
    ax.set_title("Utility Convergence (should be near zero in equilibrium)")
    ax.tick_params(axis="x", rotation=45)

    # Add spread annotation
    spread = (utilities.max() - utilities.min()) / mean_utility * 100
    ax.annotate(
        f"Max spread: {spread:.2f}%",
        xy=(0.95, 0.95),
        xycoords="axes fraction",
        ha="right",
        va="top",
        fontsize=10,
        bbox=dict(boxstyle="round", facecolor="wheat", alpha=0.5),
    )

    plt.tight_layout()
    return fig
