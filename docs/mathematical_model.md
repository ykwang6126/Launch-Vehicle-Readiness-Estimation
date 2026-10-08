# Mathematical model

`p` denotes success probability and `q = 1 - p` failure probability.
Each component–rater pair has its own prior. Raters are pooled within a component;
components are then combined into the system model.

## Symbols and indices

| Symbol | Definition |
| --- | --- |
| $p$, $q=1-p$ | Success and failure probability; uncertain model parameters, not binary test outcomes |
| $j=1,\ldots,7$ | Basic-event / component index, in the component table order |
| $r=1,\ldots,R_j$ | Retained rater-profile index within component $j$ |
| $i=1,\ldots,N$ | Prior Monte Carlo sample index: one complete row of sampled component probabilities and calculated nodes |
| $N$ | Number of prior Monte Carlo rows (`n_prior`); not the number of physical tests |
| $N_{\mathrm{post}}$ | Number of resampled posterior rows (`n_posterior`) |
| $a$ | Indicator index within one component-rater category |
| $N_T$, $N_O$ | Counts of scored technical / organizational indicators in one component-rater profile; exclude unassessed rows |
| $N_t$, $K_t$ | Physical test count and observed failure count (`n_test`, `k_fail`); lowercase subscript $t$ distinguishes tests from $N_T$ |
| $\omega_r$ | Rater-pooling weight within one component; $1/R$ for $R$ retained profiles |
| $w_i$ | Normalized likelihood weight of prior sample $i$; not a rater weight |
| $u$ | Dummy prior-sample index in weight-normalization sums |
| $E[\cdot]$, $\mathrm{Var}(\cdot)$ | Distribution mean and variance |
| $f_r(p)$, $f(p)$ | Individual-rater and pooled probability densities; interval probabilities are areas under these curves |

A Monte Carlo sample $i$ is one draw within an analysis run, not a separate
execution of the program. Each row contains seven basic-event values and four
combined nodes. Use $j$ for components and $a$ for indicators; the earlier
document reused $j$ for multiple purposes.

## 1. Average indicators within each rater profile

For scored technical (T) and organizational (O) indicators:

$$
Z_T = \frac{1}{N_T}\sum_{a=1}^{N_T} Z_{T,a}, \qquad
Z_O = \frac{1}{N_O}\sum_{a=1}^{N_O} Z_{O,a}.
$$

Here $Z_{T,a}$ and $Z_{O,a}$ are individual 0-4 scores; $Z_T$ and $Z_O$ are
their separate category means for this component-rater profile.
Require at least one scored indicator in each category. Exclude “Unable to
assess” rows. Keep fractional averages without rounding.

## 2. Map scores to a Beta prior

Interpolate linearly between these lookup values:

| Score | Technical mean $\mu_T$ | Organizational factor $m_O$ | Base strength $s_O$ |
| --- | --- | --- | --- |
| 0 | 0.40 | 0.90 | 4 |
| 1 | 0.60 | 0.99 | 8 |
| 2 | 0.75 | 1.03 | 12 |
| 3 | 0.88 | 1.07 | 16 |
| 4 | 0.96 | 1.10 | 20 |

| Phase | Full name | Strength factor $\lambda$ |
| --- | --- | --- |
| SFR | System Functional Review | 0.7 |
| PDR | Preliminary Design Review | 1.0 |
| CDR | Critical Design Review | 1.3 |
| TRR | Test Readiness Review | 1.6 |
| SVR | System Verification Review | 2.0 |

These names and factors follow Table 6 of the April 2026 prelim document.
One workbook represents one phase. $\lambda$ is its selected strength factor.

$$
\mu = \min(0.99,\max(0.01,\mu_T m_O)), \qquad s = s_O\lambda.
$$

$$
\alpha_p = \mu s, \qquad \beta_p = (1-\mu)s, \qquad
p \sim \mathrm{Beta}(\alpha_p,\beta_p).
$$

| Parameter | Definition |
| --- | --- |
| $\mu_T$ | Success-mean lookup interpolated from technical mean score $Z_T$ |
| $m_O$ | Mean multiplier interpolated from organizational mean score $Z_O$ |
| $s_O$ | Base strength interpolated from $Z_O$ |
| $\mu$ | Clipped success mean (`mu`) |
| $s$ | Beta strength / concentration (`strength`): $s=s_O\lambda=\alpha_p+\beta_p$ |
| $\alpha_p$, $\beta_p$ | Positive shape parameters of the success Beta |

At a fixed mean, larger $s$ gives smaller variance. The subscript $p$ identifies
success-space Beta parameters, not another component.
There is no confidence multiplier, extra rater weight, or strength floor.

**Example:** $Z_T=3$, $Z_O=2.5$, CDR gives $\mu=0.924$, $s=18.2$,
$\alpha_p=16.8168$, and $\beta_p=1.3832$.

## 3. Pool raters equally within each component

Each rater supplies one success-probability distribution for this component.
If there are $R$ raters, each receives equal weight $\omega_r=1/R$.
More indicators do not increase a rater's weight.

Let $f_r(p)$ be rater $r$'s Beta density. Pool the **densities**, keeping each
rater's mean and uncertainty:

$$
f(p)=\sum_{r=1}^{R}\omega_r f_r(p).
$$

For each Monte Carlo draw, select one rater with these weights, draw success
probability $p$ from that rater's Beta, then store failure probability $q=1-p$.
This selection is repeated independently for each component.

### Mean and variance

The following equations describe one component, so its $j$ index is omitted.
For rater $r$, $\mu_r$ is the success mean, $s_r=\alpha_{p,r}+\beta_{p,r}$ is
the Beta strength, and $V_r$ is the variance of that rater's success prior.
The pool mean is $\bar\mu$.

The standard Beta variance is:

$$
V_r=\frac{\alpha_{p,r}\beta_{p,r}}{(\alpha_{p,r}+\beta_{p,r})^2(\alpha_{p,r}+\beta_{p,r}+1)}
=\frac{\mu_r(1-\mu_r)}{s_r+1}.
$$

Source: [NIST/SEMATECH e-Handbook, Beta distribution, Common Statistics](https://www.itl.nist.gov/div898/handbook/eda/section3/eda366h.htm).
NIST gives the standard deviation; squaring it gives the variance above.
The second form substitutes $\mu_r=\alpha_{p,r}/s_r$ and $s_r=\alpha_{p,r}+\beta_{p,r}$.

$$
\bar\mu=\sum_{r=1}^{R}\omega_r\mu_r.
$$

$$
V_{\mathrm{within}}=\sum_{r=1}^{R}\omega_r V_r=\sum_{r=1}^{R}\omega_r\frac{\mu_r(1-\mu_r)}{s_r+1}.
$$

$$
V_{\mathrm{between}}=\sum_{r=1}^{R}\omega_r(\mu_r-\bar\mu)^2.
$$

$$
V_{\mathrm{pool}}=V_{\mathrm{within}}+V_{\mathrm{between}}.
$$

| Quantity | Meaning |
| --- | --- |
| Within-rater variance | Average uncertainty in the individual priors |
| Between-rater variance | Disagreement between rater means |
| Pool variance | Both sources combined; not divided by the number of raters |

**Worked example** (illustrative Beta parameters, not T/O mapping outputs):

| Rater | Success prior | Mean | Variance | Weight |
| --- | --- | --- | --- | --- |
| A | Beta(2, 8) | 0.20 | 0.014545 | 0.50 |
| B | Beta(8, 2) | 0.80 | 0.014545 | 0.50 |

The pool mean is 0.50. Within variance is 0.014545; between variance is 0.09;
total variance is 0.104545. The mixture retains two peaks despite its mean of 0.50.
See the [pooling plot](review_diagrams.md#2-equal-rater-pooling).

Here, “linear opinion pool” means a weighted average of the rater densities.
Rater assessments are alternative judgments, not extra successful or failed tests.
For two identical rater priors, their equal-weight mixture equals that same prior;
its variance does not halve. When means disagree, the between-rater term adds spread.
This preserves disagreement without claiming that the assessments are independent
measurements of the true probability.

### Comparison Beta: a moment-matched approximation

The exact mixture can have several peaks. To show what a single-distribution
approximation would look like, calculate one Beta with the same pool mean and
variance. Matching these two moments does not match the entire shape or tails.
The approximation strength is $s_{\mathrm{MM}}$ (“MM” means moment matched):

$$
s_{\mathrm{MM}}=\frac{\bar\mu(1-\bar\mu)}{V_{\mathrm{pool}}}-1.
$$

Its shape parameters are:

$$
\alpha_{\mathrm{MM}}=\bar\mu s_{\mathrm{MM}},\qquad
\beta_{\mathrm{MM}}=(1-\bar\mu)s_{\mathrm{MM}}.
$$

For the two-rater example, $s_{\mathrm{MM}}=1.391304$ and both shape parameters
are 0.695652. This Beta has a different shape from the two-peaked exact mixture.
The method-of-moments equations also appear in the NIST reference above.
It does not replace the mixture used in the main calculation.
It is shown as the dashed comparison curve in the component plots and as
`MomentMatchedStrength`, `MomentMatchedAlpha`, and `MomentMatchedBeta` in PoolSummary.
This is different from the average-score comparison: that method first averages
T/O scores across raters, then maps those scores to one Beta. Neither approximation
drives the main analysis.

## 4. Combine components through the fault tree

| Symbol | Component |
| --- | --- |
| $q_C$ | Concept |
| $q_{Vd}$ | Design Verification |
| $q_M$ | Manufacturing |
| $q_I$ | Assembly and Integration |
| $q_{Vi}$ | Implementation Verification |
| $q_S$ | Operation Setup |
| $q_E$ | Operation Execution |

$$
\begin{aligned}
q_{\mathrm{dsgn}} &= 1-(1-q_C)(1-q_{Vd}),\\
q_{\mathrm{impl}} &= 1-(1-q_M)(1-q_I)(1-q_{Vi}),\\
q_{\mathrm{op}} &= 1-(1-q_S)(1-q_E),\\
q_{\mathrm{top}} &= 1-(1-q_{\mathrm{dsgn}})(1-q_{\mathrm{impl}})(1-q_{\mathrm{op}}).
\end{aligned}
$$

For Monte Carlo row $i$, apply these equations to the seven component draws
$q_j^{(i)}$. The displayed branch symbols omit $(i)$ for readability.
The prior model assumes independent components. Common causes and prior
cross-component dependence are outside v0.1.

## 5. Update with system-level test evidence

Assume binary test outcomes, independent tests conditional on a constant failure
probability, and comparable design / test conditions. There are $N_t$ physical
tests and $K_t$ observed failures. For prior Monte Carlo sample $i$, the full
binomial likelihood is the prelim document's equation (23):

$$
L_i=\Pr(K_t\mid N_t,q_{\mathrm{top}}^{(i)})
=\binom{N_t}{K_t}(q_{\mathrm{top}}^{(i)})^{K_t}(1-q_{\mathrm{top}}^{(i)})^{N_t-K_t}.
$$

Here $q_{\mathrm{top}}^{(i)}$ is the calculated system failure probability in
prior row $i$. Define the coefficient-free likelihood used in code:

$$
\ell_i=(q_{\mathrm{top}}^{(i)})^{K_t}(1-q_{\mathrm{top}}^{(i)})^{N_t-K_t}.
$$

The normalized weight is the prelim equation (24), with $u$ used as the summation
index to avoid confusing it with a failure count or component index:

$$
w_i=\frac{L_i}{\sum_{u=1}^{N}L_u}=\frac{\ell_i}{\sum_{u=1}^{N}\ell_u}.
$$

The coefficient $\binom{N_t}{K_t}$ is the same for every sample, so it cancels.
For three tests and one failure it is 3: multiplying every likelihood by 3 leaves
all normalized weights unchanged. The earlier shorthand used $n=N_t$ and $k=K_t$.

`posterior_weights` computes $\ell_i$ in log space, skips zero exponents at
endpoints, and rejects evidence supported by no draws. With $N_t=0$, weights are
$1/N$. The weights sum to 1; they are not rater-pooling weights.

### Weighted estimates and resampling

The direct weighted posterior mean matches the prelim equation (25):

$$
\widehat\mu_{\mathrm{post}}=\sum_{i=1}^{N}w_i q_{\mathrm{top}}^{(i)}.
$$

This is the estimated posterior mean failure probability, not a Beta mapping mean.
The pipeline also calculates weighted variance as in prelim equation (26).
These diagnostics appear in `WeightedPosteriorMean` and `WeightedPosteriorVariance`.

The code then resamples $N_{\mathrm{post}}$ **complete rows** using $w_i$.
Updating can induce dependence, so all eleven nodes share the selected prior-row
index. Exported node statistics use that resample and include its sampling noise;
they need not exactly equal the direct weighted estimates. Resampling is a numerical
representation of the same posterior, not another set of physical tests.

### Effective sample size (ESS)

$$
\mathrm{ESS}=\frac{1}{\sum_{i=1}^{N}w_i^2}.
$$

ESS measures how broadly the likelihood weights are spread over the prior samples.
It ranges from 1 to $N$: uniform weights give $N$; one nonzero weight gives 1.
It is not the physical test count or the posterior-resample count. Resampling
more rows does not increase this ESS. The code warns below 1% of $N$; that is a
computational diagnostic threshold, not a system readiness criterion.

## 6. Interpret results

$$
P_{\mathrm{meet}}=P(q_{\mathrm{top}}\le q_{\mathrm{req}}), \qquad
P_{\mathrm{exc}}=P(q_{\mathrm{top}}>q_{\mathrm{req}}).
$$

Here $q_{\mathrm{req}}$ is the maximum acceptable system failure probability
(`q_req`); $P_{\mathrm{meet}}$ and $P_{\mathrm{exc}}$ are probability mass at or
below / above that threshold in the distribution being summarized.
These quantify confidence in meeting the failure-probability requirement.
Estimated mission success is a different quantity:

$$
E[p_{\mathrm{top}}]=1-E[q_{\mathrm{top}}].
$$

Summaries use population standard deviations and Hazen percentiles to match
MATLAB v13. Threshold statistics are reported only for the top event.

## Exact moments for verification

An exact moment is a mean of a power, calculated analytically rather than from
random draws. Here $M_1$ is the system success mean and $M_2$ is the mean of
squared system success probability. These are optional numerical checks.

The [verification appendix](exact_moments.md) derives them from the component
Beta mixtures and explains the special three-test, one-failure check.
They do not change the model or update algorithm. The special formula does not
apply unchanged to other test counts.

The score mappings and independence assumptions still require research review;
agreement with exact moments verifies calculation, not predictive calibration.
