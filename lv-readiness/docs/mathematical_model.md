# Mathematical model

For each component–rater profile, compute independent arithmetic means Z_T and
Z_O over scored technical and organizational indicators. Interpolate linearly
at these unrounded means using:

| Score | mu_T | m_O | s_O |
| --- | --- | --- | --- |
| 0 | 0.40 | 0.90 | 4 |
| 1 | 0.60 | 0.99 | 8 |
| 2 | 0.75 | 1.03 | 12 |
| 3 | 0.88 | 1.07 | 16 |
| 4 | 0.96 | 1.10 | 20 |

Phase factors are SFR 0.7, PDR 1.0, CDR 1.3, TRR 1.6, SVR 2.0.
Set mu = clip(mu_T m_O, 0.01, 0.99), s = s_O lambda_phase,
alpha_p = mu s, beta_p = (1-mu)s. Sample success p from Beta(alpha_p,beta_p)
and failure q = 1-p. There is no additional rater adjustment or strength floor.

For R profiles in one component, each weight is 1/R. Draw a profile first and
then draw its Beta. The exact mixture is not replaced by a fitted Beta.
Pool mean is sum(w_r mu_r). Within variance is sum(w_r mu_r(1-mu_r)/(s_r+1));
between variance is sum(w_r (mu_r-pool_mean)^2). Total variance is their sum.
Reporting-only moment matching uses s_MM = mean(1-mean)/variance - 1.

Basic event order is C, Vd, M, I, Vi, S, E. The failure tree is:

```
q_design = 1 - (1-q_C)(1-q_Vd)
q_implementation = 1 - (1-q_M)(1-q_I)(1-q_Vi)
q_operation = 1 - (1-q_S)(1-q_E)
q_top = 1 - (1-q_design)(1-q_implementation)(1-q_operation)
```

These product rules assume independent component priors. Common causes and
cross-component prior dependence are outside v0.1. Updating can induce dependence;
one common posterior index vector is therefore applied to all eleven nodes.

For n independent comparable trials and k failures, sample likelihood is
L_i proportional to q_i^k (1-q_i)^(n-k). Compute log L only for nonzero
exponents, subtract its maximum, exponentiate, and normalize. The common
binomial coefficient cancels. Zero support is an error. n=0 gives uniform
weights, but posterior resampling can still introduce MC noise.

ESS = 1/sum(w_i^2); warn below 0.01 N. Weighted mean and variance are computed
before resampling as a separate diagnostic. Exported summaries use the posterior
resample to match MATLAB. Standard deviations use population normalization.
MATLAB R2024b percentiles use midpoint plotting positions (Hazen/type 5), matched
by NumPy quantile(method="hazen"), not NumPy's default quantile convention.

Pmeet = P(q_top <= q_req), Pexc = P(q_top > q_req). These describe confidence
in meeting a failure-rate requirement. They are not the predictive success
probability, which is 1-E[q_top]. Pmeet/Pexc are blank for all other nodes.

For independent components, exact success-product moments are products of
mixture-weighted Beta moments. Let m_r = E[P_top^r]. The historical n=3,k=1
case has prior mean 1-m_1 and posterior mean
(m_2-2m_3+m_4)/(m_2-m_3). This avoids relying on an MC seed for validation.
