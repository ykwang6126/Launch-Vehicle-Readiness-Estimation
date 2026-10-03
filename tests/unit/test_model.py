"""Check mapping, pooling, tree propagation, updating, and reporting against reference values."""

import numpy as np
import pytest

from lvreadiness.fault_tree import fault_tree_nodes
from lvreadiness.pooling import (
    mixture_moments,
    sample_components,
    success_product_moments,
)
from lvreadiness.priors import parameters, build_priors
from lvreadiness.summary import summarize_nodes
from lvreadiness.updating import posterior_weights, resample_joint, weighted_moments
from lvreadiness.validation import validate_input


def test_mapping_reference():
    """Check fractional-score interpolation, Beta parameters, and clipping."""
    beta_parameters = parameters(3, 2.5, 1.3)
    np.testing.assert_allclose(
        [beta_parameters[k] for k in ("mu", "strength", "alpha_p", "beta_p")],
        [0.924, 18.2, 16.8168, 1.3832],
        atol=1e-10,
        rtol=0,
    )
    assert (
        beta_parameters["alpha_p"] + beta_parameters["beta_p"]
        == beta_parameters["strength"]
    )
    assert parameters(4, 4, 2)["mu"] == 0.99
    assert parameters(0, 0, 0.7)["strength"] == pytest.approx(2.8)


def test_mixture_reference():
    """Check within/between variance and reject weights that do not sum to one."""
    mean, within, between = mixture_moments([2, 8], [8, 2], [0.5, 0.5])
    assert mean == 0.5
    assert within + between == pytest.approx(0.1045454545, abs=1e-10)
    assert between == pytest.approx(0.09)
    assert mixture_moments([2], [8], [1])[2] == 0
    with pytest.raises(ValueError):
        mixture_moments([2, 8], [8, 2], [0.4, 0.4])


def test_synthetic_tree_and_sample_moments(assessment):
    """Compare sampled tree moments with exact success-product moments."""
    profiles = build_priors(validate_input(assessment)[1], 1.3)
    moments = success_product_moments(profiles, 4)
    assert profiles.mu.iloc[0] == pytest.approx(0.7725)
    assert 1 - moments[1] == pytest.approx(0.8358316563, abs=1e-10)
    component_failures = sample_components(profiles, 200000, np.random.default_rng(1))
    top_failure = fault_tree_nodes(component_failures)[:, -1]
    expected_mean = 1 - moments[1]
    expected_variance = moments[2] - moments[1] ** 2
    assert abs(top_failure.mean() - expected_mean) < 5 * np.sqrt(
        expected_variance / len(top_failure)
    )
    # Variance MC error uses the exact fourth central moment of the product.
    fourth_central_moment = (
        moments[4]
        - 4 * moments[1] * moments[3]
        + 6 * moments[1] ** 2 * moments[2]
        - 3 * moments[1] ** 4
    )
    assert abs(top_failure.var() - expected_variance) < 5 * np.sqrt(
        (fourth_central_moment - expected_variance**2) / len(top_failure)
    )
    assert np.all(fault_tree_nodes(np.zeros((1, 7))) == 0)
    assert np.all(fault_tree_nodes(np.ones((1, 7))) == 1)
    for component_index in range(7):
        component_failures = np.zeros((1, 7))
        component_failures[0, component_index] = 1
        assert fault_tree_nodes(component_failures)[0, -1] == 1


@pytest.mark.parametrize(
    "n,k,expected",
    [(0, 0, [1 / 3] * 3), (3, 0, [8 / 9, 1 / 9, 0]), (3, 3, [0, 1 / 9, 8 / 9])],
)
def test_endpoint_weights(n, k, expected):
    """Check no-evidence, all-success, and all-failure likelihoods at q=0 and q=1."""
    np.testing.assert_allclose(
        posterior_weights(np.array([0, 0.5, 1]), n, k), expected, atol=1e-15
    )


def test_log_weights_and_zero_support():
    """Check normalized likelihoods, numerical stability, and impossible evidence."""
    component_failures = np.array([0.1, 0.3, 0.5, 0.9])
    weights = posterior_weights(component_failures, 3, 1)
    expected = component_failures * (1 - component_failures) ** 2
    expected /= expected.sum()
    np.testing.assert_allclose(weights, expected, atol=1e-15)
    assert np.isfinite(posterior_weights(component_failures, 1000000, 300000)).all()
    with pytest.raises(ValueError, match="No prior sample"):
        posterior_weights(np.array([0.0, 1.0]), 2, 1)
    with pytest.raises(ValueError):
        posterior_weights(component_failures, 2, 3)


def test_joint_resampling_and_weighted_moments():
    """Verify complete-row resampling, ESS, and direct weighted moments."""
    prior = np.arange(33).reshape(3, 11) / 33
    weights = np.array([0.2, 0.3, 0.5])
    posterior, indices, ess = resample_joint(
        prior, weights, 500, np.random.default_rng(1)
    )
    np.testing.assert_array_equal(posterior, prior[indices])
    assert ess == pytest.approx(1 / 0.38)
    mean, expected_variance = weighted_moments(prior, weights)
    np.testing.assert_allclose(mean, weights @ prior)
    np.testing.assert_allclose(expected_variance, weights @ prior**2 - mean**2)
    with pytest.warns(UserWarning, match="Low ESS"):
        resample_joint(
            np.zeros((200, 11)), np.r_[1.0, np.zeros(199)], 10, np.random.default_rng(1)
        )


def test_matlab_percentiles_population_std_threshold():
    """Check Hazen percentiles, population spread, and top-event threshold reporting."""
    prior = np.tile(np.arange(1, 11)[:, None] / 10, (1, 11))
    table = summarize_nodes(prior, prior, 0.5)
    assert table.PriorP95.iloc[-1] == 1  # MATLAB midpoint / Hazen, not NumPy's default.
    assert table.PriorP025.iloc[-1] == 0.1
    assert table.PriorStd.iloc[-1] == pytest.approx(np.sqrt(0.0825))
    assert table.PriorPmeet.iloc[-1] == 0.5
    assert table.PriorPexc.iloc[:-1].isna().all()
