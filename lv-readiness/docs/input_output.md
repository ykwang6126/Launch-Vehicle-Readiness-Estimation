# Inputs and outputs

## Excel input

Read only `MATLAB_Input`. No computed Beta or pool parameters are read from Excel.

| Column | Rule |
| --- | --- |
| `Branch` | Must match the component's branch in `config.py` |
| `Component` | One of seven supported components; approved aliases are accepted |
| `Indicator` | Nonblank; unique within each component–rater pair, ignoring case |
| `Cat` | `T` or `O` (letter O); lowercase is accepted |
| `Z` | Finite score in 0–4; fractional historical scores are accepted |
| `RaterID` | Nonblank person ID; may recur across components |
| `Lifecycle Phase` | One consistent supported phase for the workbook |
| `n_test` | Nonnegative integer test count |
| `k_fail` | Integer failure count with `0 <= k_fail <= n_test` |
| `q_req` | Failure-probability requirement in 0–1 |
| `Status` (optional) | `Unable to assess` requires blank `Z` and excludes that row |

- Enter workbook settings once or repeat them identically; blanks are ignored.
- Each component–rater profile needs at least one scored T and one scored O indicator.
- Completely blank assessment rows are ignored. Missing required fields stop the run.
- Status matching ignores case and outside whitespace; other status text is narrative.
- Separate assessment rounds belong in separate workbooks.
- New rubric scores use integers; category averages can be fractional.
- Formula cells use cached values. Save a calculated workbook in Excel first.

Excluded rows are listed by their original Excel row numbers in warnings and
metadata. Supported aliases include `Integration` and `Implementation Verification`.
Historical category labels are not reassigned automatically.

**Open review item V2-01:** Excel TRUE/FALSE is not yet explicitly rejected in
numeric fields. Dhrupath will add rejection checks and tests; use numeric values.

## Output files

Each run creates a unique `run_YYYYMMDD_HHMMSS_SSS` folder.

| File | Contents |
| --- | --- |
| `results.xlsx` | Five worksheets defined below |
| `run_config.yaml` | Resolved settings and mapping constants |
| `run_metadata.json` | Runtime versions, RNG, input SHA-256, Git commit when available, excluded rows, weighted moments |
| `figures/` | Twelve PNG diagnostics; Python does not export MATLAB FIG files |

SHA-256 identifies the exact workbook bytes used. The Git commit identifies the
committed code version; it does not record uncommitted edits. YAML is an output
record, not another required input.

## Result workbook

| Worksheet | Purpose |
| --- | --- |
| `RunInfo` | Settings, model mappings, sample counts, and ESS |
| `RaterParameters` | One row per component–rater profile and its Beta parameters |
| `PoolSummary` | Seven component mixtures and within/between variance |
| `NodeSummary` | Prior/posterior statistics for eleven nodes |
| `PoolingComparison` | Average-score method versus exact equal-weight pooling |

Numeric values remain numeric; unavailable statistics are blank.
The comparison method does not drive the main analysis.

### Column reference

**RunInfo**

- Paths/time: `RunStamp`, `InputFile`, `OutputFolder`.
- Settings: `N` (prior draws), `Mpost` (posterior draws), `n_test`, `k_fail`, `q_req`,
  `phase_name`, `lambda_phase`, `Seed`.
- Model: `InputMode`, `ModelVersion`, `PoolingWeights`, `ScoreLevels`, `MuTLevels`,
  `MOLevels`, `SOLevels`, `PhaseLevels`, `LambdaLevels`, `MeanClipMin`, `MeanClipMax`.
- Diagnostics: `EffectiveSampleSize`, `NInputRows`, `NUsedRows`, `NExcludedRows`,
  `NRaters`, `NProfiles`.

Mapping arrays use MATLAB-compatible strings. `NInputRows` counts retained
assessment rows before excluding unassessed scores.

**RaterParameters**

- Identity/counts: `Branch`, `Component`, `RaterID`, `NInputRows`, `NUsedRows`, `NExcludedRows`.
- Scores: `Z_T`, `Z_O` (separate category means).
- Mapping: `mu_T`, `m_O`, `s_O`, `mu`, `strength`, `alpha_p`, `beta_p`.
- Pooling: `WeightWithinComponent` (equal profile weight within the component).

**PoolSummary**

- Identity: `BasicEvent`, `Branch`, `Component`, `NProfiles`.
- Exact mixture: `PoolMeanP`, `WithinRaterVariance`, `BetweenRaterVariance`, `PoolVariance`.
- Comparison Beta: `MomentMatchedStrength`, `MomentMatchedAlpha`, `MomentMatchedBeta`.
- Weighted scores: `MeanZT`, `MeanZO`.

**NodeSummary**

`Node`, `PriorNSamples`, and `PostNSamples`, followed by the statistics below
with `Prior` and `Post` prefixes. For example, `PriorMean` and `PostMean`.

| Statistic | Meaning |
| --- | --- |
| `Mean`, `Std`, `Median` | Mean, population standard deviation, median failure probability |
| `P025`, `P95`, `P975` | 2.5th, 95th, and 97.5th percentiles (Hazen convention) |
| `Pexc` | Probability of exceeding `q_req`; top node only |
| `Pmeet` | Probability of meeting `q_req`; top node only |

Rows follow `config.NODES`: seven basic events, then design, implementation,
operation, and top. See [the equations](mathematical_model.md#4-combine-components-through-the-fault-tree).

**PoolingComparison**

`Method`, `PriorMean`, `PriorStd`, `PriorP95`, `PostMean`, `PostP95`.
Average-score comparison is first; exact pooling is second.

## Figure reference

Seven `pool_<component>.png` plots show individual success-Beta densities, the
exact mixture, its mean, and a comparison Beta with matching mean/variance.

| System figure | Contents |
| --- | --- |
| `01_prior_q_top.png` | Prior failure probability |
| `02_posterior_q_top.png` | Posterior failure probability |
| `03_prior_vs_posterior.png` | Prior/posterior overlay |
| `04_prior_posterior_likelihood.png` | Overlay plus separately normalized likelihood |
| `05_legacy_vs_exact_pool.png` | Average-score versus exact-mixture prior |

The plotted likelihood is not the posterior density.
