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
    fig = Figure(figsize=(8, 5), layout="constrained")
    FigureCanvasAgg(fig)
    ax = fig.subplots()
    ax.grid(alpha=.2)
    ax.set_ylabel("Probability density")
    return fig, ax


def _save(fig: Figure, directory: Path, name: str) -> None:
    fig.savefig(directory / (name+".png"), dpi=300)
    fig.clear()


def plot_results(profiles: pd.DataFrame, pools: pd.DataFrame, prior: np.ndarray,
                  posterior: np.ndarray, legacy_prior: np.ndarray,
                  n_test: int, k_fail: int, directory: Path) -> None:
    """Export profile mixtures and top-event prior/posterior/likelihood plots."""
    directory.mkdir(exist_ok=False)
    x = np.linspace(.001, .999, 1500)
    for component in COMPONENTS:
        fig, ax = _figure()
        rows = profiles.loc[profiles.Component.eq(component)]
        pool = pools.loc[pools.Component.eq(component)].iloc[0]
        density = np.zeros_like(x)
        for row in rows.itertuples():
            pdf = beta.pdf(x, row.alpha_p, row.beta_p)
            density += row.WeightWithinComponent*pdf
            ax.plot(x, pdf, lw=1, label=row.RaterID)
        ax.plot(x, density, "k-", lw=2.5, label="Exact equal-weight linear pool")
        if np.isfinite(pool.MomentMatchedAlpha):
            ax.plot(x, beta.pdf(x, pool.MomentMatchedAlpha, pool.MomentMatchedBeta), "k--",
                    lw=1.8, label="Moment-matched Beta (approx.)")
        ax.axvline(pool.PoolMeanP, ls=":", color="gray", label="Pool mean")
        ax.set(xlabel="Readiness probability p", title=f"{component}: mean = {pool.PoolMeanP:.3f}, variance = {pool.PoolVariance:.4f}")
        ax.legend(fontsize=8)
        _save(fig, directory, "pool_"+re.sub(r"[^a-z0-9]+", "_", component.lower()).strip("_"))
    for name, values, title in (("01_prior_q_top", prior, f"Prior of q_top (N={len(prior)})"),
                                 ("02_posterior_q_top", posterior, f"Posterior q_top (k={k_fail}, n={n_test})")):
        fig, ax = _figure()
        ax.hist(values, bins=200, density=True)
        ax.set(xlabel="Top-event failure probability q_top", title=title)
        _save(fig, directory, name)
    for name, likelihood in (("03_prior_vs_posterior", False), ("04_prior_posterior_likelihood", True)):
        fig, ax = _figure()
        ax.hist(prior, bins=200, density=True, alpha=.4, label="Prior")
        ax.hist(posterior, bins=200, density=True, alpha=.4, label="Posterior")
        if likelihood:
            grid = np.linspace(0, 1, 2000)
            density = posterior_weights(grid, n_test, k_fail)
            # numpy 1.x and 2.x compatibility.
            area = np.trapezoid(density, grid) if hasattr(np, 'trapezoid') else np.trapz(density, grid)
            ax.plot(grid, density/area, "k-", lw=2, label="Normalized likelihood")
            ax.set_ylabel("Density / normalized likelihood")
        ax.set(xlabel="Top-event failure probability q_top", title=f"Prior and posterior: k={k_fail}, n={n_test}")
        ax.legend()
        _save(fig, directory, name)
    fig, ax = _figure()
    ax.hist(legacy_prior, bins=200, density=True, alpha=.5, label="Scores averaged across profiles")
    ax.hist(prior, bins=200, density=True, alpha=.5, label="Exact equal-weight linear pool")
    ax.set(xlabel="Top-event failure probability q_top", title="Score aggregation and exact linear pool")
    ax.legend()
    _save(fig, directory, "05_legacy_vs_exact_pool")
