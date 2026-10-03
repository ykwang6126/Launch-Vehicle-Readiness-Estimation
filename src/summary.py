"""MATLAB-compatible percentile convention and population standard deviations."""

import numpy as np
import pandas as pd

from .config import NODES


def summarize_nodes(
    prior: np.ndarray, posterior: np.ndarray, q_req: float
) -> pd.DataFrame:
    """Return MATLAB v13's 19-column NodeSummary, including all 11 nodes."""
    summary_columns = dict(
        Node=list(NODES),
        PriorNSamples=np.full(11, len(prior)),
        PostNSamples=np.full(11, len(posterior)),
    )
    # Prefixes preserve the MATLAB workbook schema (PriorMean, PostMean, etc.).
    for prefix, values in (("Prior", prior), ("Post", posterior)):
        # Hazen quantiles match MATLAB's percentile convention. ddof=0 below
        # uses population standard deviation rather than the sample estimate.
        quantiles = np.quantile(values, [0.025, 0.95, 0.975], axis=0, method="hazen")
        # The requirement applies only to q_top (last column). Leave other
        # nodes blank in Excel by storing NaN in their threshold statistics.
        exceedance_probability = np.full(11, np.nan)
        exceedance_probability[-1] = np.mean(values[:, -1] > q_req)
        for name, statistics in (
            ("Mean", values.mean(axis=0)),
            ("Std", values.std(axis=0, ddof=0)),
            ("Median", np.median(values, axis=0)),
            ("P025", quantiles[0]),
            ("P95", quantiles[1]),
            ("P975", quantiles[2]),
            ("Pexc", exceedance_probability),
            ("Pmeet", 1 - exceedance_probability),
        ):
            summary_columns[prefix + name] = statistics
    return pd.DataFrame(summary_columns)


def pooling_comparison(
    prior: np.ndarray,
    posterior: np.ndarray,
    legacy_prior: np.ndarray,
    legacy_posterior: np.ndarray,
) -> pd.DataFrame:
    """Compare average-score and exact-pool top-event summaries."""
    comparison_records = []
    for name, prior_values, posterior_values in (
        ("Scores averaged across profiles", legacy_prior, legacy_posterior),
        ("Exact equal-weight linear pool", prior, posterior),
    ):
        comparison_records.append(
            dict(
                Method=name,
                PriorMean=float(prior_values.mean()),
                PriorStd=float(prior_values.std(ddof=0)),
                PriorP95=float(np.quantile(prior_values, 0.95, method="hazen")),
                PostMean=float(posterior_values.mean()),
                PostP95=float(np.quantile(posterior_values, 0.95, method="hazen")),
            )
        )
    return pd.DataFrame(comparison_records)
