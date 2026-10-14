# Reading the calculation code

Start with `pipeline.run_analysis`: it validates inputs, calls `compute_analysis`,
and sends its `ComputedAnalysis` result to `generate_report`. Open a helper only
when you need the details of that stage.

## Tables and arrays

A DataFrame is a table with named columns. A profile is one rater's assessment
of one component. `Z_T` and `Z_O` are that profile's average technical and
organizational scores, not individual indicator scores.

In `build_priors`, `.to_numpy()` extracts a column's values for numerical work.
The parameter function returns a name/value dictionary; `.items()` pairs each
new column name with its values. Rows keep their original alignment.

`groupby("Component").Component.transform("size")` repeats each component's
profile count on all rows for that component. Taking its reciprocal assigns
equal rater weights: three profiles each get 1/3, even if they scored different
numbers of indicators.

In sampling, `rng.choice` draws profile indices with replacement. A Boolean mask
then identifies which draws use each profile's Beta distribution. Each matrix
row contains a possible set of failure probabilities, not a simulated launch
outcome. Full sample columns follow `config.NODES`.

## Scientific names

| Name | Meaning |
| --- | --- |
| `p`, `q` | Success probability and failure probability; `q = 1 - p` |
| `mu_T`, `m_O` | Technical baseline success mean and organizational multiplier |
| `s_O`, `lambda_phase` | Organizational strength and lifecycle strength factor |
| `mu`, `strength` | Adjusted success mean and concentration of the prior |
| `alpha_p`, `beta_p` | Beta parameters for success probability, not real test counts |
| `likelihood_weights` | How well each prior row explains the observed test counts |
| `posterior_indices` | Prior rows selected to form the posterior sample |

The top-event requirement is evaluated only for `q_top`. The fraction of samples
meeting that failure-risk limit describes uncertainty about meeting a requirement;
it is different from the mission's success probability.

## Details worth preserving during edits

The single random generator is consumed in a fixed order, including the separate
average-score comparison after the main posterior. Reordering random calls can
change seeded results even if the underlying mathematics is equivalent.

Weights are calculated in log space for numerical stability. Whole rows are
resampled together so component values remain paired with the system probability
calculated from them. Direct weighted moments avoid resampling noise; the
workbook summaries describe the finite resampled posterior.

Field names such as `PriorMean` and the filename `05_legacy_vs_exact_pool.png`
are retained for output compatibility. Internally, the comparison method is
called the average-score method. The exact mixture drives the primary analysis;
moment-matched Beta parameters are reporting approximations only.
