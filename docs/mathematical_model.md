# Mathematical model

`p` denotes success probability and `q = 1 - p` failure probability.
Each component–rater pair has its own prior. Raters are pooled within a component;
components are then combined into the system model.

## 1. Average indicators within each rater profile

For scored technical (T) and organizational (O) indicators:

$$
Z_T = \frac{1}{N_T}\sum_{j=1}^{N_T} Z_{T,j}, \qquad
Z_O = \frac{1}{N_O}\sum_{j=1}^{N_O} Z_{O,j}.
$$

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

| Lifecycle phase | SFR | PDR | CDR | TRR | SVR |
| --- | --- | --- | --- | --- | --- |
| Strength factor $\lambda$ | 0.7 | 1.0 | 1.3 | 1.6 | 2.0 |

$$
\mu = \min(0.99,\max(0.01,\mu_T m_O)), \qquad s = s_O\lambda.
$$

$$
\alpha_p = \mu s, \qquad \beta_p = (1-\mu)s, \qquad
p \sim \mathrm{Beta}(\alpha_p,\beta_p).
$$

`mu` is the prior success mean; `strength` ($s$) controls its spread.
There is no confidence multiplier, extra rater weight, or strength floor.

**Example:** $Z_T=3$, $Z_O=2.5$, CDR gives $\mu=0.924$, $s=18.2$,
$\alpha_p=16.8168$, and $\beta_p=1.3832$.

## 3. Pool raters equally within each component

Each rater supplies one success-probability distribution for this component.
If there are $R$ raters, each receives weight $w_r=1/R$.
More indicators do not increase a rater's weight.

Let $f_r(p)$ be rater $r$'s Beta density. Pool the **densities**, keeping each
rater's mean and uncertainty:

$$
f(p)=\sum_{r=1}^{R}w_r f_r(p).
$$

For each Monte Carlo draw, select one rater with these weights, draw success
probability $p$ from that rater's Beta, then store failure probability $q=1-p$.
This selection is repeated independently for each component.

### Mean and variance

For rater $r$, $\mu_r$ is the success mean and $s_r$ is Beta strength.

$$
\bar\mu=\sum_{r=1}^{R}w_r\mu_r.
$$

$$
V_{\mathrm{within}}=\sum_{r=1}^{R}w_r\frac{\mu_r(1-\mu_r)}{s_r+1}.
$$

$$
V_{\mathrm{between}}=\sum_{r=1}^{R}w_r(\mu_r-\bar\mu)^2.
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

This is a linear opinion pool. It does not treat the raters as independent
observations that automatically increase statistical precision.

### Comparison Beta

A single Beta with the same mean and variance is exported for comparison:

$$
s_{\mathrm{MM}}=\frac{\bar\mu(1-\bar\mu)}{V_{\mathrm{pool}}}-1.
$$

Its parameters are $\bar\mu s_{\mathrm{MM}}$ and $(1-\bar\mu)s_{\mathrm{MM}}$.
It does not replace the mixture used in the main calculation.
The separate average-score comparison also does not drive the main calculation.

## 4. Combine components through the fault tree

| Symbol | Component |
| --- | --- |
| $q_C$ | Concept |
| $q_{Vd}$ | Design Verification |
| $q_M$ | Manufacturing |
| $q_I$ | Assembly and Integration |
| $q_{Vi}$ | Impl. Verification |
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

The prior model assumes independent components. Common causes and prior
cross-component dependence are outside v0.1.

## 5. Update with system-level test evidence

For $n$ independent comparable tests and $k$ failures, prior draw $i$ receives:

$$
L_i \propto q_{\mathrm{top},i}^{k}(1-q_{\mathrm{top},i})^{n-k}, \qquad
\widetilde w_i=\frac{L_i}{\sum_j L_j}.
$$

The common binomial coefficient cancels. The implementation uses log likelihoods,
skips zero exponents at endpoints, and rejects evidence supported by no draws.
With $n=0$, weights are uniform.

Resample **complete rows** using $\widetilde w_i$. Updating can induce dependence
between components, so all eleven nodes must share the same selected row index.

$$
\mathrm{ESS}=\frac{1}{\sum_i\widetilde w_i^2}.
$$

Warn when ESS is below 1% of prior draws. Direct weighted moments provide a check;
exported node summaries use the posterior resample and include its sampling noise.

## 6. Interpret results

$$
P_{\mathrm{meet}}=P(q_{\mathrm{top}}\le q_{\mathrm{req}}), \qquad
P_{\mathrm{exc}}=P(q_{\mathrm{top}}>q_{\mathrm{req}}).
$$

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
