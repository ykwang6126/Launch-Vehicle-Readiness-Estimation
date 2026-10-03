"""Twelve PNG diagnostics with MATLAB v13 filenames and mathematical content."""

from pathlib import Path
import re

import numpy as np
import pandas as pd
from matplotlib.figure import Figure
from matplotlib.backends.backend_agg import FigureCanvasAgg
from scipy.stats import beta

from .config import COMPONENTS
from .updating import posterior_weights


def _figure() -> tuple:
    """Create a figure that can be saved without opening a desktop window."""
    figure = Figure(figsize=(8, 5), layout="constrained")
    FigureCanvasAgg(figure)
    axes = figure.subplots()
    axes.grid(alpha=0.2)
    axes.set_ylabel("Probability density")
    return figure, axes


def _save(figure: Figure, directory: Path, name: str) -> None:
    """Write one PNG and release the plotted content."""
    figure.savefig(directory / (name + ".png"), dpi=300)
    figure.clear()


def plot_results(
    profiles: pd.DataFrame,
    pools: pd.DataFrame,
    prior: np.ndarray,
    posterior: np.ndarray,
    legacy_prior: np.ndarray,
    n_test: int,
    k_fail: int,
    directory: Path,
) -> None:
    """Export profile mixtures and top-event prior/posterior/likelihood plots."""
    directory.mkdir(exist_ok=False)
    probability_grid = np.linspace(0.001, 0.999, 1500)
    # Seven component plots show individual success priors and their mixture.
    for component in COMPONENTS:
        figure, axes = _figure()
        component_profiles = profiles.loc[profiles.Component.eq(component)]
        component_pool = pools.loc[pools.Component.eq(component)].iloc[0]
        pooled_density = np.zeros_like(probability_grid)
        for row in component_profiles.itertuples():
            profile_density = beta.pdf(probability_grid, row.alpha_p, row.beta_p)
            pooled_density += row.WeightWithinComponent * profile_density
            axes.plot(probability_grid, profile_density, lw=1, label=row.RaterID)
        axes.plot(
            probability_grid,
            pooled_density,
            "k-",
            lw=2.5,
            label="Exact equal-weight linear pool",
        )
        if np.isfinite(component_pool.MomentMatchedAlpha):
            axes.plot(
                probability_grid,
                beta.pdf(
                    probability_grid,
                    component_pool.MomentMatchedAlpha,
                    component_pool.MomentMatchedBeta,
                ),
                "k--",
                lw=1.8,
                label="Moment-matched Beta (approx.)",
            )
        axes.axvline(component_pool.PoolMeanP, ls=":", color="gray", label="Pool mean")
        axes.set(
            xlabel="Readiness probability p",
            title=f"{component}: mean = {component_pool.PoolMeanP:.3f}, variance = {component_pool.PoolVariance:.4f}",
        )
        axes.legend(fontsize=8)
        _save(
            figure,
            directory,
            "pool_" + re.sub(r"[^a-z0-9]+", "_", component.lower()).strip("_"),
        )
    # The remaining five figures describe top-event failure probabilities.
    for name, values, title in (
        ("01_prior_q_top", prior, f"Prior of q_top (N={len(prior)})"),
        ("02_posterior_q_top", posterior, f"Posterior q_top (k={k_fail}, n={n_test})"),
    ):
        figure, axes = _figure()
        axes.hist(values, bins=200, density=True)
        axes.set(xlabel="Top-event failure probability q_top", title=title)
        _save(figure, directory, name)
    for name, show_likelihood in (
        ("03_prior_vs_posterior", False),
        ("04_prior_posterior_likelihood", True),
    ):
        figure, axes = _figure()
        axes.hist(prior, bins=200, density=True, alpha=0.4, label="Prior")
        axes.hist(posterior, bins=200, density=True, alpha=0.4, label="Posterior")
        if show_likelihood:
            likelihood_grid = np.linspace(0, 1, 2000)
            # Reuse the likelihood formula, then normalize its area over q for
            # display. This curve is a likelihood, not a posterior density.
            pooled_density = posterior_weights(likelihood_grid, n_test, k_fail)
            # numpy 1.x and 2.x compatibility.
            likelihood_area = (
                np.trapezoid(pooled_density, likelihood_grid)
                if hasattr(np, "trapezoid")
                else np.trapz(pooled_density, likelihood_grid)
            )
            axes.plot(
                likelihood_grid,
                pooled_density / likelihood_area,
                "k-",
                lw=2,
                label="Normalized likelihood",
            )
            axes.set_ylabel("Density / normalized likelihood")
        axes.set(
            xlabel="Top-event failure probability q_top",
            title=f"Prior and posterior: k={k_fail}, n={n_test}",
        )
        axes.legend()
        _save(figure, directory, name)
    figure, axes = _figure()
    axes.hist(
        legacy_prior,
        bins=200,
        density=True,
        alpha=0.5,
        label="Scores averaged across profiles",
    )
    axes.hist(
        prior,
        bins=200,
        density=True,
        alpha=0.5,
        label="Exact equal-weight linear pool",
    )
    axes.set(
        xlabel="Top-event failure probability q_top",
        title="Score aggregation and exact linear pool",
    )
    axes.legend()
    _save(figure, directory, "05_legacy_vs_exact_pool")
