# Exact moments: verification appendix

## Purpose

Monte Carlo results vary slightly with the seed. Analytical moments give expected
means without drawing samples, so we can check whether that variation is reasonable.
They are not additional assessment inputs or another updating method.

| Index / symbol | Definition |
| --- | --- |
| $j=1,\ldots,7$ | Component / basic-event index |
| $r=1,\ldots,R_j$ | Rater within component $j$ |
| $h$ | Nonnegative integer moment order; not a component index |
| $\ell$ | Auxiliary product index from 0 to $h-1$ |
| $B_{j,h}$ | Moment of order $h$ for component $j$'s pooled success distribution |
| $M_h$ | Moment of order $h$ for system success probability |
| $\omega_{j,r}$ | Equal rater weight within component $j$ |
| $\alpha$, $\beta$ | Positive success-Beta shape parameters |

## 1. One rater's Beta prior

For success probability $p$ with Beta parameters $\alpha$ and $\beta$:

$$
E[p]=\frac{\alpha}{\alpha+\beta}.
$$

$$
E[p^2]=\frac{\alpha(\alpha+1)}{(\alpha+\beta)(\alpha+\beta+1)}.
$$

More generally, for integer $h\ge1$:

$$
E[p^h]=\prod_{\ell=0}^{h-1}\frac{\alpha+\ell}{\alpha+\beta+\ell}.
$$

For $h=0$, the moment is 1. These are raw moments: $E[p^2]$ is not
$E[p]^2$, and variance is $E[p^2]-E[p]^2$.

## 2. One component's rater mixture

Let $B_{j,h}$ denote the $h$th success moment for component $j$.
Average each rater's moment using the same pooling weights:

$$
B_{j,h}=\sum_{r=1}^{R_j}\omega_{j,r} E[p_{j,r}^h].
$$

$R_j$ is the number of retained rater profiles for component $j$;
$\omega_{j,r}=1/R_j$ in v0.1. $p_{j,r}$ follows that rater's success Beta.

## 3. System success

The fixed OR failure tree means all seven components must succeed:

$$
p_{\mathrm{top}}=\prod_{j=1}^{7}p_j.
$$

With independent component priors, the moments multiply:

$$
M_h=E[p_{\mathrm{top}}^h]=\prod_{j=1}^{7}B_{j,h},\qquad M_0=1.
$$

Therefore:

$$
E[q_{\mathrm{top}}]=1-M_1.
$$

$$
\mathrm{Var}(q_{\mathrm{top}})=M_2-M_1^2.
$$

**Simple example:** seven independent components each have Beta(2, 2) success
priors. Then $B_{j,1}=0.5$, $B_{j,2}=0.3$, $M_1=0.5^7=0.0078125$,
and $M_2=0.3^7=0.0002187$. Mean system failure is 0.9921875.
This deliberately simple example checks arithmetic; it is not a realistic vehicle.

## 4. Special posterior check: three tests, one failure

Write $P=p_{\mathrm{top}}$ and $q=1-P$. For $n=3$, $k=1$, likelihood is
proportional to $(1-P)P^2$. Bayes' rule gives the posterior mean failure:

$$
E[q\mid n=3,k=1]=\frac{E[(1-P)^2P^2]}{E[(1-P)P^2]}.
$$

Expand the numerator and denominator:

$$
E[q\mid n=3,k=1]=\frac{M_2-2M_3+M_4}{M_2-M_3}.
$$

This requires nonzero evidence probability. It is specific to three tests and
one failure. The general update remains the likelihood-weighting method in
[`updating.py`](../src/lvreadiness/updating.py).

## Code and reference

[`success_product_moments`](../src/lvreadiness/pooling.py) calculates the prior moments.
The optional historical regression uses them for the special posterior check.
The fictional workbook's saved analytical means are:

| Quantity | Exact mean failure probability |
| --- | --- |
| Prior | 0.8358316562692756 |
| Posterior, 3 tests / 1 failure | 0.7986232147953535 |

Monte Carlo means need not match every digit. Use sampling-error tolerances.
The product formula assumes independent component priors; it does not assert
independence of the components after conditioning on system tests.
