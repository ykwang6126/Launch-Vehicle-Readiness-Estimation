import numpy as np
import pytest

from lvreadiness.fault_tree import fault_tree_nodes
from lvreadiness.pooling import mixture_moments, sample_components, success_product_moments
from lvreadiness.priors import parameters, build_priors
from lvreadiness.summary import summarize_nodes
from lvreadiness.updating import posterior_weights, resample_joint, weighted_moments
from lvreadiness.validation import validate_input


def test_mapping_reference():
    p = parameters(3, 2.5, 1.3)
    np.testing.assert_allclose([p[k] for k in ('mu', 'strength', 'alpha_p', 'beta_p')],
                               [.924, 18.2, 16.8168, 1.3832], atol=1e-10, rtol=0)
    assert p['alpha_p']+p['beta_p'] == p['strength']
    assert parameters(4, 4, 2)['mu'] == .99
    assert parameters(0, 0, .7)['strength'] == pytest.approx(2.8)


def test_mixture_reference():
    mean, within, between = mixture_moments([2,8], [8,2], [.5,.5])
    assert mean == .5
    assert within+between == pytest.approx(.1045454545, abs=1e-10)
    assert between == pytest.approx(.09)
    assert mixture_moments([2], [8], [1])[2] == 0
    with pytest.raises(ValueError):
        mixture_moments([2,8], [8,2], [.4,.4])


def test_synthetic_tree_and_sample_moments(assessment):
    profiles = build_priors(validate_input(assessment)[1], 1.3)
    moments = success_product_moments(profiles, 4)
    assert profiles.mu.iloc[0] == pytest.approx(.7725)
    assert 1-moments[1] == pytest.approx(.8358316563, abs=1e-10)
    q = sample_components(profiles, 200000, np.random.default_rng(1))
    top = fault_tree_nodes(q)[:, -1]
    mu = 1-moments[1]
    var = moments[2]-moments[1]**2
    assert abs(top.mean()-mu) < 5*np.sqrt(var/len(top))
    # Variance MC error uses the exact fourth central moment of the product.
    fourth = moments[4]-4*moments[1]*moments[3]+6*moments[1]**2*moments[2]-3*moments[1]**4
    assert abs(top.var()-var) < 5*np.sqrt((fourth-var**2)/len(top))
    assert np.all(fault_tree_nodes(np.zeros((1,7))) == 0)
    assert np.all(fault_tree_nodes(np.ones((1,7))) == 1)
    for col in range(7):
        q = np.zeros((1,7)); q[0,col] = 1
        assert fault_tree_nodes(q)[0,-1] == 1


@pytest.mark.parametrize('n,k,expected', [(0,0,[1/3]*3), (3,0,[8/9,1/9,0]), (3,3,[0,1/9,8/9])])
def test_endpoint_weights(n,k,expected):
    np.testing.assert_allclose(posterior_weights(np.array([0,.5,1]),n,k), expected, atol=1e-15)


def test_log_weights_and_zero_support():
    q = np.array([.1,.3,.5,.9])
    weights = posterior_weights(q,3,1)
    expected = q*(1-q)**2; expected /= expected.sum()
    np.testing.assert_allclose(weights,expected,atol=1e-15)
    assert np.isfinite(posterior_weights(q,1000000,300000)).all()
    with pytest.raises(ValueError, match='No prior sample'):
        posterior_weights(np.array([0.,1.]), 2,1)
    with pytest.raises(ValueError):
        posterior_weights(q, 2, 3)


def test_joint_resampling_and_weighted_moments():
    prior = np.arange(33).reshape(3,11)/33
    weights = np.array([.2,.3,.5])
    posterior, indices, ess = resample_joint(prior, weights, 500, np.random.default_rng(1))
    np.testing.assert_array_equal(posterior, prior[indices])
    assert ess == pytest.approx(1/.38)
    mean, var = weighted_moments(prior, weights)
    np.testing.assert_allclose(mean, weights @ prior)
    np.testing.assert_allclose(var, weights @ prior**2-mean**2)
    with pytest.warns(UserWarning, match='Low ESS'):
        resample_joint(np.zeros((200,11)),np.r_[1.,np.zeros(199)],10,np.random.default_rng(1))


def test_matlab_percentiles_population_std_threshold():
    prior = np.tile(np.arange(1,11)[:,None]/10,(1,11))
    table = summarize_nodes(prior,prior,.5)
    assert table.PriorP95.iloc[-1] == 1  # MATLAB midpoint / Hazen, not NumPy's default.
    assert table.PriorP025.iloc[-1] == .1
    assert table.PriorStd.iloc[-1] == pytest.approx(np.sqrt(.0825))
    assert table.PriorPmeet.iloc[-1] == .5
    assert table.PriorPexc.iloc[:-1].isna().all()
