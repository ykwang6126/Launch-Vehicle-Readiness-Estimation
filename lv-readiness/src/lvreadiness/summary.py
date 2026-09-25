"""MATLAB-compatible percentile convention and population standard deviations."""

import numpy as np
import pandas as pd

from .config import NODES


def summarize_nodes(prior: np.ndarray, posterior: np.ndarray, q_req: float) -> pd.DataFrame:
    """Return MATLAB v13's 19-column NodeSummary, including all 11 nodes."""
    data = dict(Node=list(NODES), PriorNSamples=np.full(11, len(prior)), PostNSamples=np.full(11, len(posterior)))
    for prefix, values in (("Prior", prior), ("Post", posterior)):
        quantiles = np.quantile(values, [0.025, 0.95, 0.975], axis=0, method="hazen")
        exceed = np.full(11, np.nan)
        exceed[-1] = np.mean(values[:, -1] > q_req)
        for name, v in (("Mean", values.mean(axis=0)), ("Std", values.std(axis=0, ddof=0)),
                        ("Median", np.median(values, axis=0)), ("P025", quantiles[0]),
                        ("P95", quantiles[1]), ("P975", quantiles[2]),
                        ("Pexc", exceed), ("Pmeet", 1-exceed)):
            data[prefix+name] = v
    return pd.DataFrame(data)


def pooling_comparison(prior: np.ndarray, posterior: np.ndarray,
                       legacy_prior: np.ndarray, legacy_posterior: np.ndarray) -> pd.DataFrame:
    """Compare average-score and exact-pool top-event summaries."""
    rows = []
    for name, before, after in (("Scores averaged across profiles", legacy_prior, legacy_posterior),
                                ("Exact equal-weight linear pool", prior, posterior)):
        rows.append(dict(Method=name, PriorMean=float(before.mean()), PriorStd=float(before.std(ddof=0)),
                         PriorP95=float(np.quantile(before, .95, method="hazen")),
                         PostMean=float(after.mean()), PostP95=float(np.quantile(after, .95, method="hazen"))))
    return pd.DataFrame(rows)
