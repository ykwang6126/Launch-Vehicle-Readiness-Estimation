"""Exact linear mixtures, separate within/between variance, and MC sampling."""

import numpy as np
import pandas as pd

from .config import BASIC_EVENTS, COMPONENTS
from .priors import parameters


def mixture_moments(alpha: np.ndarray, beta: np.ndarray, weights: np.ndarray) -> tuple[float, float, float]:
    """Return mixture mean, within-profile variance, between-profile variance."""
    alpha, beta, weights = (np.asarray(x, dtype=float) for x in (alpha, beta, weights))
    if alpha.ndim != 1 or alpha.shape != beta.shape or alpha.shape != weights.shape or not len(alpha):
        raise ValueError("Mixture arrays must have equal, nonempty one-dimensional shapes.")
    if not all(np.isfinite(x).all() for x in (alpha, beta, weights)) or (alpha <= 0).any() or (beta <= 0).any():
        raise ValueError("Beta parameters must be finite and positive.")
    if (weights < 0).any() or not np.isclose(weights.sum(), 1, atol=1e-12, rtol=0):
        raise ValueError("Mixture weights must be nonnegative and sum to one.")
    means = alpha / (alpha + beta)
    mean = float(weights @ means)
    within = float(weights @ (alpha*beta/((alpha+beta)**2*(alpha+beta+1))))
    between = float(weights @ (means-mean)**2)
    return mean, within, between


def summarize_pools(profiles: pd.DataFrame) -> pd.DataFrame:
    """Report exact mixture moments; moment matching never drives sampling."""
    result = []
    for component, event in zip(COMPONENTS, BASIC_EVENTS):
        rows = profiles.loc[profiles.Component.eq(component)]
        weights = rows.WeightWithinComponent.to_numpy()
        mean, within, between = mixture_moments(rows.alpha_p, rows.beta_p, weights)
        variance = within + between
        strength = mean*(1-mean)/variance-1
        if strength <= 0:
            strength = np.nan
        result.append(dict(BasicEvent=event, Branch=rows.Branch.iloc[0], Component=component,
                           NProfiles=len(rows), PoolMeanP=mean, WithinRaterVariance=within,
                           BetweenRaterVariance=between, PoolVariance=variance,
                           MomentMatchedStrength=strength, MomentMatchedAlpha=mean*strength,
                           MomentMatchedBeta=(1-mean)*strength,
                           MeanZT=float(weights @ rows.Z_T), MeanZO=float(weights @ rows.Z_O)))
    return pd.DataFrame(result)


def sample_components(profiles: pd.DataFrame, n: int, rng: np.random.Generator) -> np.ndarray:
    """Select a rater, sample its success Beta, then convert p to q."""
    q = np.empty((n, 7))
    for col, component in enumerate(COMPONENTS):
        rows = profiles.loc[profiles.Component.eq(component)]
        selected = rng.choice(len(rows), size=n, p=rows.WeightWithinComponent.to_numpy())
        for local, row in enumerate(rows.itertuples()):
            mask = selected == local
            q[mask, col] = 1-rng.beta(row.alpha_p, row.beta_p, size=int(mask.sum()))
    return q


def sample_averaged_scores(profiles: pd.DataFrame, lambda_phase: float, n: int,
                           rng: np.random.Generator) -> np.ndarray:
    """MATLAB's legacy comparison: equal-profile scores, same strength formula."""
    q = np.empty((n, 7))
    for col, component in enumerate(COMPONENTS):
        rows = profiles.loc[profiles.Component.eq(component)]
        par = parameters(rows.Z_T.mean(), rows.Z_O.mean(), lambda_phase)
        q[:, col] = 1-rng.beta(par['alpha_p'], par['beta_p'], n)
    return q


def success_product_moments(profiles: pd.DataFrame, max_order: int) -> np.ndarray:
    """Exact moments E[P_top**r] for independent finite component mixtures."""
    moments = np.ones(max_order+1)
    for component in COMPONENTS:
        rows = profiles.loc[profiles.Component.eq(component)]
        raw = np.ones(len(rows))
        for order in range(1, max_order+1):
            raw *= (rows.alpha_p.to_numpy()+order-1)/(rows.alpha_p.to_numpy()+rows.beta_p.to_numpy()+order-1)
            moments[order] *= rows.WeightWithinComponent.to_numpy() @ raw
    return moments
