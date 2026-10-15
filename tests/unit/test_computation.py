"""Check the calculation/report boundary independently of file generation."""

import numpy as np
import pandas as pd

from lvreadiness.config import NODES, TOP_NODE_INDEX
from lvreadiness.pipeline import ComputedAnalysis, compute_analysis
from lvreadiness.input_validation import validate_input


def test_computation_keeps_inputs_and_joint_samples(assessment, monkeypatch):
    """Pure computation needs no exporters and retains coherent posterior rows."""
    _, profiles, settings, _ = validate_input(assessment)
    original_profiles = profiles.copy(deep=True)

    def unexpected_report(*args, **kwargs):
        raise AssertionError("Numerical computation must not generate reports")

    monkeypatch.setattr("lvreadiness.pipeline.plot_results", unexpected_report)
    monkeypatch.setattr("lvreadiness.pipeline.export_results", unexpected_report)
    result = compute_analysis(profiles, settings, 3000, 1000, seed=1)

    assert isinstance(result, ComputedAnalysis)
    pd.testing.assert_frame_equal(profiles, original_profiles)
    assert result.prior_samples.shape == (3000, len(NODES))
    assert result.posterior_samples.shape == (1000, len(NODES))
    np.testing.assert_array_equal(
        result.posterior_samples, result.prior_samples[result.posterior_indices]
    )
    np.testing.assert_allclose(
        result.weighted_mean,
        result.likelihood_weights @ result.prior_samples,
    )
    assert result.node_summary.Node.tolist() == list(NODES)
    assert result.node_summary.iloc[TOP_NODE_INDEX].Node == "q_top"
