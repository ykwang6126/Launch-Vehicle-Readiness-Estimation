# Inputs and outputs

Only worksheet `MATLAB_Input` is read. Required columns:
`Branch, Component, Indicator, Cat, Z, RaterID, Lifecycle Phase, n_test, k_fail, q_req`.
`Status` is optional. Lifecycle settings may appear once or repeat identically.
Blank assessment rows are ignored. Scores must be finite in [0,4]. New rubric
assessments use integers; historical fractional scores are accepted as in MATLAB.
Missing/invalid settings, components, branch assignments, IDs, categories,
duplicate indicators within a profile, or missing scored T/O categories fail.

`Unable to assess` (case-insensitive and whitespace-trimmed) in Status requires
a blank score and excludes only that row. Excluded Excel row numbers appear in
the warning and metadata. Other Status text is narrative. IDs are stable people
identifiers and can recur across components. Separate rounds belong in separate
workbooks. Historical category assignments are never automatically remapped.
Input formula caches, if present, are read as values; Excel must have calculated
them. No spreadsheet-derived Beta or pool parameters are trusted.

Component aliases follow MATLAB v13, including Integration and Implementation
Verification. Canonical order and branch mapping are in config.py.

Each successful run creates `run_YYYYMMDD_HHMMSS_SSS` without overwriting earlier
runs. Output files are `results.xlsx`, `run_config.yaml`, `run_metadata.json`,
and a `figures` directory. Python does not generate native MATLAB `.fig` files.

## Workbook schemas

- RunInfo: RunStamp, InputFile, OutputFolder, N, Mpost, n_test, k_fail, q_req,
  phase_name, lambda_phase, InputMode, EffectiveSampleSize, ModelVersion, Seed,
  ScoreLevels, MuTLevels, MOLevels, SOLevels, PhaseLevels, LambdaLevels,
  MeanClipMin, MeanClipMax, PoolingWeights, NInputRows, NUsedRows, NExcludedRows,
  NRaters, NProfiles.
- RaterParameters: Branch, Component, RaterID, Z_T, Z_O, NInputRows, NUsedRows,
  NExcludedRows, mu_T, m_O, s_O, mu, strength, alpha_p, beta_p, WeightWithinComponent.
- PoolSummary: BasicEvent, Branch, Component, NProfiles, PoolMeanP,
  WithinRaterVariance, BetweenRaterVariance, PoolVariance, MomentMatchedStrength,
  MomentMatchedAlpha, MomentMatchedBeta, MeanZT, MeanZO.
- NodeSummary: Node, PriorNSamples, PostNSamples, then Prior and Post prefixes
  for Mean, Std, Median, P025, P95, P975, Pexc, Pmeet. Eleven rows in tree order.
- PoolingComparison: Method, PriorMean, PriorStd, PriorP95, PostMean, PostP95.
  The average-score comparison is first and exact linear pooling second.

Values remain numeric and unavailable entries are blank. RunInfo uses the same
mapping-array strings as MATLAB. JSON additionally records package/runtime
versions, RNG, input SHA256, excluded row numbers, weighted moments, and Git
commit when available. YAML records resolved settings, never a second required
assessment input.

## Figures

Seven `pool_<component>.png` files show profile Betas, the exact mixture, and a
reporting-only moment-matched Beta. The five top-event PNGs are:

1. 01_prior_q_top
2. 02_posterior_q_top
3. 03_prior_vs_posterior
4. 04_prior_posterior_likelihood
5. 05_legacy_vs_exact_pool

The likelihood curve is separately normalized over q for plotting only. It is
not the posterior density. Plot styles and raster pixels differ between engines.
