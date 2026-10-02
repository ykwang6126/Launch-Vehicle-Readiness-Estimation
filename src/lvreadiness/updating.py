"""Stable binomial importance weights and joint posterior resampling."""

import warnings
import numpy as np

from .validation import validate_evidence


def posterior_weights(q: np.ndarray, n_test: int, k_fail: int) -> np.ndarray:
    """Normalize likelihood in log space, handling q=0/1 and n=0 exactly."""
    validate_evidence(n_test, k_fail)
    q = np.asarray(q, dtype=float)
    if q.ndim != 1 or not len(q) or not np.all(np.isfinite(q) & (q >= 0) & (q <= 1)):
        raise ValueError("Expected a nonempty probability vector in [0, 1].")
    log_l = np.zeros_like(q)
    with np.errstate(divide="ignore"):
        if k_fail > 0:
            log_l += k_fail*np.log(q)
        if n_test > k_fail:
            log_l += (n_test-k_fail)*np.log1p(-q)
    largest = np.max(log_l)
    if not np.isfinite(largest):
        raise ValueError("No prior sample supports the supplied test evidence.")
    weights = np.exp(log_l-largest)
    return weights/weights.sum()


def weighted_moments(values: np.ndarray, weights: np.ndarray) -> tuple[np.ndarray, np.ndarray]:
    """Independent posterior mean and population variance before resampling."""
    mean = np.sum(values*weights[:, None], axis=0)
    variance = np.sum((values-mean)**2*weights[:, None], axis=0)
    return mean, variance


def resample_joint(prior: np.ndarray, weights: np.ndarray, n: int,
                   rng: np.random.Generator) -> tuple[np.ndarray, np.ndarray, float]:
    """Apply one index vector to every node, retaining posterior dependence."""
    ess = float(1/np.sum(weights**2))
    if ess < 0.01*len(weights):
        warnings.warn(f"Low ESS: {ess:.1f} of {len(weights)}. Increase n_prior.", UserWarning, stacklevel=2)
    indices = rng.choice(len(weights), n, replace=True, p=weights)
    return prior[indices, :], indices, ess
