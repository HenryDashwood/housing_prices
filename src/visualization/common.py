"""Common visualization utilities and styling.

Provides consistent styling and helper functions for all plots.
"""

from typing import Any

import matplotlib.pyplot as plt
import numpy as np

# Default color palette
COLORS = {
    "primary": "#2C3E50",
    "secondary": "#E74C3C",
    "tertiary": "#3498DB",
    "success": "#27AE60",
    "warning": "#F39C12",
    "high_productivity": "#E74C3C",
    "medium": "#F39C12",
    "low_productivity": "#27AE60",
}

# Color sequence for multiple categories
COLOR_SEQUENCE = [
    "#E74C3C",
    "#3498DB",
    "#27AE60",
    "#F39C12",
    "#9B59B6",
    "#1ABC9C",
    "#E67E22",
    "#34495E",
]

# Default figure sizes
FIGURE_SIZES = {
    "single": (8, 6),
    "wide": (12, 5),
    "tall": (8, 10),
    "grid_2x2": (12, 10),
    "grid_1x3": (14, 4),
    "grid_1x2": (12, 5),
}


def set_style() -> None:
    """Set consistent matplotlib style for all plots."""
    plt.style.use("seaborn-v0_8-whitegrid")
    plt.rcParams.update(
        {
            "font.size": 11,
            "axes.titlesize": 13,
            "axes.labelsize": 11,
            "xtick.labelsize": 10,
            "ytick.labelsize": 10,
            "legend.fontsize": 10,
            "figure.titlesize": 14,
            "axes.spines.top": False,
            "axes.spines.right": False,
        }
    )


def create_figure(
    nrows: int = 1,
    ncols: int = 1,
    figsize: tuple[float, float] | str | None = None,
    **kwargs: Any,
) -> tuple[plt.Figure, np.ndarray | plt.Axes]:
    """
    Create a figure with consistent styling.

    Args:
        nrows: Number of subplot rows.
        ncols: Number of subplot columns.
        figsize: Either a tuple (width, height) or a key from FIGURE_SIZES.
        **kwargs: Additional arguments passed to plt.subplots.

    Returns:
        Tuple of (figure, axes).
    """
    set_style()

    if figsize is None:
        if nrows == 1 and ncols == 1:
            figsize = FIGURE_SIZES["single"]
        elif nrows == 1:
            figsize = FIGURE_SIZES["wide"]
        else:
            figsize = FIGURE_SIZES["grid_2x2"]
    elif isinstance(figsize, str):
        figsize = FIGURE_SIZES.get(figsize, FIGURE_SIZES["single"])

    fig, axes = plt.subplots(nrows, ncols, figsize=figsize, **kwargs)
    return fig, axes


def format_large_number(x: float, decimals: int = 0) -> str:
    """Format large numbers with K/M/B suffixes."""
    if abs(x) >= 1e9:
        return f"{x / 1e9:.{decimals}f}B"
    elif abs(x) >= 1e6:
        return f"{x / 1e6:.{decimals}f}M"
    elif abs(x) >= 1e3:
        return f"{x / 1e3:.{decimals}f}K"
    else:
        return f"{x:.{decimals}f}"


def add_value_labels(
    ax: plt.Axes,
    bars: Any,
    fmt: str = ".0f",
    offset: float = 0.02,
    fontsize: int = 9,
) -> None:
    """Add value labels above bar charts."""
    for bar in bars:
        height = bar.get_height()
        ax.annotate(
            f"{height:{fmt}}",
            xy=(bar.get_x() + bar.get_width() / 2, height),
            xytext=(0, 3),
            textcoords="offset points",
            ha="center",
            va="bottom",
            fontsize=fontsize,
        )


def save_figure(
    fig: plt.Figure,
    filename: str,
    dpi: int = 150,
    bbox_inches: str = "tight",
) -> None:
    """Save figure with consistent settings."""
    fig.savefig(filename, dpi=dpi, bbox_inches=bbox_inches)
    print(f"Saved: {filename}")
