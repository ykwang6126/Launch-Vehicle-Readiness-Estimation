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
p \sim \operatorname{Beta}(\alpha_p,\beta_p).
$$

`mu` is the prior success mean; `strength` ($s$) controls its spread.
There is no confidence multiplier, extra rater weight, or strength floor.

**Example:** $Z_T=3$, $Z_O=2.5$, CDR gives $\mu=0.924$, $s=18.2$,
$\alpha_p=16.8168$, and $\beta_p=1.3832$.

## 3. Pool raters equally within each component

For $R$ profiles, assign $w_r=1/R$ and retain the full mixture:

$$
f(p)=\sum_{r=1}^{R} w_r\,\operatorname{Beta}(p;\alpha_{p,r},\beta_{p,r}).
$$

Sampling selects a rater profile, draws from its Beta, and converts to $q=1-p$.
More indicators do not give a rater more weight.

$$
\bar\mu=\sum_r w_r\mu_r.
$$

$$
V_{\mathrm{within}}=\sum_r w_r\frac{\mu_r(1-\mu_r)}{s_r+1}, \qquad
V_{\mathrm{between}}=\sum_r w_r(\mu_r-\bar\mu)^2.
$$

$$
V_{\mathrm{pool}}=V_{\mathrm{within}}+V_{\mathrm{between}}.
$$

Within variance describes individual rater uncertainty; between variance
captures disagreement. A single moment-matched Beta is shown for comparison:

$$
s_{\mathrm{MM}}=\frac{\bar\mu(1-\bar\mu)}{V_{\mathrm{pool}}}-1.
$$

Its parameters are $\bar\mu s_{\mathrm{MM}}$ and $(1-\bar\mu)s_{\mathrm{MM}}$.
It does not replace the mixture in sampling.

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

Let $M_j=E[p_{\mathrm{top}}^j]$. Independence gives:

$$
M_j=\prod_{c=1}^{7}\left[
\sum_{r=1}^{R_c}w_{c,r}\prod_{\ell=0}^{j-1}
\frac{\alpha_{c,r}+\ell}{\alpha_{c,r}+\beta_{c,r}+\ell}
\right], \qquad M_0=1.
$$

For the reference case $n=3$, $k=1$:

$$
E[q_{\mathrm{top}}]=1-M_1, \qquad
E[q_{\mathrm{top}}\mid k=1,n=3]=\frac{M_2-2M_3+M_4}{M_2-M_3}.
$$

These checks do not depend on a particular random seed. The score mappings remain
model assumptions; implementation verification does not establish predictive calibration.
