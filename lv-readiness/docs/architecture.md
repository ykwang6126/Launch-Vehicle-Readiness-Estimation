# Processing workflow

1. Read the workbook's `MATLAB_Input` sheet and check headers.
2. Validate settings and assessment rows. Keep original Excel row numbers for errors.
3. Group by component and rater. Average scored T and O indicators separately.
4. Map each profile to a success-Beta prior. Give raters equal weight within each component.
5. Sample each component mixture, convert success `p` to failure `q`, and evaluate the fault tree.
6. Weight complete prior rows using the system test likelihood; resample rows to form the posterior.
7. Summarize nodes, create comparison plots, and export results to a new run folder.

## What calls what

Both `python -m lvreadiness` and the Python API call `run_analysis` in
[`pipeline.py`](../src/lvreadiness/pipeline.py). See the [source guide](../src/README.md)
for each module's responsibility.

`AnalysisResult` contains:

| Field | Contents |
| --- | --- |
| `tables`, `paths` | Exported tables and output file paths |
| `prior_samples`, `posterior_samples` | Draws for seven basic events and four combined nodes |
| `posterior_weights` | One likelihood weight per prior row |
| `posterior_indices` | Prior row indices selected for posterior draws |
| `weighted_mean`, `weighted_variance` | Direct posterior diagnostics before resampling |

## Reproducibility

- One seeded NumPy `PCG64` generator supplies all random draws.
- Component order is fixed; rater order follows input appearance within each component.
- Validation, statistics, and plotting do not consume random draws.
- The average-score comparison runs after the main posterior and does not change it.
- Repeated runs match numerically in the same dependency environment. Run paths and timestamps differ.

## Installation and layout

`src/lvreadiness` contains the installed package. Install from the package
folder (`lv-readiness/`) before running tests or helper scripts.

MATLAB is used only for optional reference generation. Python never needs
restricted historical data for its public tests.
