"""Exact linear mixtures, separate within/between variance, and MC sampling."""

import numpy as np
import pandas as pd

from .config import BASIC_EVENTS, COMPONENTS
from .priors import parameters


def mixture_moments(
    alpha: np.ndarray, beta: np.ndarray, weights: np.ndarray
) -> tuple[float, float, float]:
    """Return mixture mean, within-profile variance, between-profile variance."""
    alpha, beta, weights = (np.asarray(x, dtype=float) for x in (alpha, beta, weights))
    if (
        alpha.ndim != 1
        or alpha.shape != beta.shape
        or alpha.shape != weights.shape
        or not len(alpha)
    ):
        raise ValueError(
            "Mixture arrays must have equal, nonempty one-dimensional shapes."
        )
    if (
        not all(np.isfinite(x).all() for x in (alpha, beta, weights))
        or (alpha <= 0).any()
        or (beta <= 0).any()
    ):
        raise ValueError("Beta parameters must be finite and positive.")
    if (weights < 0).any() or not np.isclose(weights.sum(), 1, atol=1e-12, rtol=0):
        raise ValueError("Mixture weights must be nonnegative and sum to one.")
    # @ is a weighted sum here: sum(weight * profile statistic).
    # Within variance describes each rater's uncertainty; between variance
    # describes disagreement between rater means.
    profile_means = alpha / (alpha + beta)
    pool_mean = float(weights @ profile_means)
    profile_variances = alpha * beta / ((alpha + beta) ** 2 * (alpha + beta + 1))
    within_variance = float(weights @ profile_variances)
    between_variance = float(weights @ (profile_means - pool_mean) ** 2)
    return pool_mean, within_variance, between_variance


def summarize_pools(profiles: pd.DataFrame) -> pd.DataFrame:
    """Report exact mixture moments; moment matching never drives sampling."""
    pool_records = []
    for component, event in zip(COMPONENTS, BASIC_EVENTS):
        component_profiles = profiles.loc[profiles.Component.eq(component)]
        weights = component_profiles.WeightWithinComponent.to_numpy()
        pool_mean, within_variance, between_variance = mixture_moments(
            component_profiles.alpha_p, component_profiles.beta_p, weights
        )
        pool_variance = within_variance + between_variance
        # A single Beta with matching mean/variance is exported for comparison.
        # It is never used in sample_components; the full mixture is retained.
        matched_strength = pool_mean * (1 - pool_mean) / pool_variance - 1
        if matched_strength <= 0:
            matched_strength = np.nan
        pool_records.append(
            dict(
                BasicEvent=event,
                Branch=component_profiles.Branch.iloc[0],
                Component=component,
                NProfiles=len(component_profiles),
                PoolMeanP=pool_mean,
                WithinRaterVariance=within_variance,
                BetweenRaterVariance=between_variance,
                PoolVariance=pool_variance,
                MomentMatchedStrength=matched_strength,
                MomentMatchedAlpha=pool_mean * matched_strength,
                MomentMatchedBeta=(1 - pool_mean) * matched_strength,
                MeanZT=float(weights @ component_profiles.Z_T),
                MeanZO=float(weights @ component_profiles.Z_O),
            )
        )
    return pd.DataFrame(pool_records)


def sample_components(
    profiles: pd.DataFrame, n: int, rng: np.random.Generator
) -> np.ndarray:
    """Return n rows of failure probabilities in the seven-component order.

    Each draw selects a profile using its within-component weight, samples that
    profile's success Beta, and stores q = 1 - p. Components are sampled independently.
    rng is supplied by the pipeline so all draws use one reproducible random stream.
    """
    component_failures = np.empty((n, 7))
    for component_index, component in enumerate(COMPONENTS):
        component_profiles = profiles.loc[profiles.Component.eq(component)]
        # First decide which rater supplies each draw for this component.
        # selected_profiles function selects the rater using random number generator
        selected_profiles = rng.choice(
            len(component_profiles),
            #length of array
            size=n,
            #n is the number of Monte Carlo draws, how many you are extracting from the matrix component_profiles
            p=component_profiles.WeightWithinComponent.to_numpy(),
            #function specifies the probability of selecting each option
        )
        for profile_index, profile in enumerate(component_profiles.itertuples()):
            # This Boolean mask locates draws assigned to the current profile.
            profile_draws = selected_profiles == profile_index
            component_failures[profile_draws, component_index] = 1 - rng.beta(
                profile.alpha_p, profile.beta_p, size=int(profile_draws.sum())
            )
    return component_failures


def sample_averaged_scores(
    profiles: pd.DataFrame, lambda_phase: float, n: int, rng: np.random.Generator
) -> np.ndarray:
    """Sample the older average-score method for the comparison table and plot.

    Average T/O scores across profiles before mapping to one Beta per component.
    These samples do not enter the primary prior or posterior calculation.
    """
    component_failures = np.empty((n, 7))
    for component_index, component in enumerate(COMPONENTS):
        component_profiles = profiles.loc[profiles.Component.eq(component)]
        beta_parameters = parameters(
            component_profiles.Z_T.mean(), component_profiles.Z_O.mean(), lambda_phase
        )
        component_failures[:, component_index] = 1 - rng.beta(
            beta_parameters["alpha_p"], beta_parameters["beta_p"], n
        )
    return component_failures


def success_product_moments(profiles: pd.DataFrame, max_order: int) -> np.ndarray:
    """Exact moments E[P_top**r] for independent finite component mixtures."""
    # moments[r] is E[P_top**r]; the zeroth moment is always 1.
    # Independent components let us multiply their success moments.
    moments = np.ones(max_order + 1)
    for component in COMPONENTS:
        component_profiles = profiles.loc[profiles.Component.eq(component)]
        profile_moments = np.ones(len(component_profiles))
        for order in range(1, max_order + 1):
            # Beta raw-moment recurrence: E[p**r] / E[p**(r-1)].
            profile_moments *= (component_profiles.alpha_p.to_numpy() + order - 1) / (
                component_profiles.alpha_p.to_numpy()
                + component_profiles.beta_p.to_numpy()
                + order
                - 1
            )
            moments[order] *= (
                component_profiles.WeightWithinComponent.to_numpy() @ profile_moments
            )
    return moments
