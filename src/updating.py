"""Stable binomial importance weights and joint posterior resampling."""

import warnings
import numpy as np

from .validation import validate_evidence


def posterior_weights(q: np.ndarray, n_test: int, k_fail: int) -> np.ndarray:
    """Return one normalized binomial likelihood weight for each prior q_top draw.

    n_test is the number of comparable tests and k_fail the observed failures.
    Calculating in log space avoids underflow for large test counts.
    With no tests all weights are equal; incompatible evidence raises an error.
    """
    validate_evidence(n_test, k_fail)
    q = np.asarray(q, dtype=float)
    if q.ndim != 1 or not len(q) or not np.all(np.isfinite(q) & (q >= 0) & (q <= 1)):
        raise ValueError("Expected a nonempty probability vector in [0, 1].")
    log_likelihood = np.zeros_like(q)
    # Skip zero exponents so endpoint cases never produce 0 * log(0).
    with np.errstate(divide="ignore"):
        if k_fail > 0:
            log_likelihood += k_fail * np.log(q)
        if n_test > k_fail:
            log_likelihood += (n_test - k_fail) * np.log1p(-q)
    largest_log_likelihood = np.max(log_likelihood)
    if not np.isfinite(largest_log_likelihood):
        raise ValueError("No prior sample supports the supplied test evidence.")
    # Subtracting a common maximum leaves the normalized weights unchanged.
    weights = np.exp(log_likelihood - largest_log_likelihood)
    return weights / weights.sum()


def weighted_moments(
    values: np.ndarray, weights: np.ndarray
) -> tuple[np.ndarray, np.ndarray]:
    """Compute posterior mean/variance directly from weighted prior rows.

    values has one row per draw and one column per node. weights[:, None]
    repeats each row weight across columns. This diagnostic avoids the extra
    sampling noise introduced by drawing a finite posterior sample.
    """
    mean = np.sum(values * weights[:, None], axis=0)
    variance = np.sum((values - mean) ** 2 * weights[:, None], axis=0)
    return mean, variance


def resample_joint(
    prior: np.ndarray, weights: np.ndarray, n: int, rng: np.random.Generator
) -> tuple[np.ndarray, np.ndarray, float]:
    """Draw n complete prior rows with replacement using likelihood weights.

    Return the posterior rows, their original indices, and effective sample size
    (ESS). A common row index for all nodes preserves dependence after updating.
    ESS near the prior sample count means weights are spread out; low ESS means
    only a few draws explain the observed tests.
    """
    effective_sample_size = float(1 / np.sum(weights**2))
    if effective_sample_size < 0.01 * len(weights):
        warnings.warn(
            f"Low ESS: {effective_sample_size:.1f} of {len(weights)}. Increase n_prior.",
            UserWarning,
            stacklevel=2,
        )
    indices = rng.choice(len(weights), n, replace=True, p=weights)
    return prior[indices, :], indices, effective_sample_size
