# LVReadiness: single Python script

This folder contains the readiness analysis in one script, `lvreadiness.py`. It runs from top to bottom, with numbered sections and comments referencing the MATLAB v13 baseline.

The script prepares component/rater assessments, calculates Beta parameters, samples equal-weight mixtures, propagates failure probabilities through the fault tree, updates the samples using test evidence, and saves plots and tables.

## Files

| File | Purpose |
| --- | --- |
| `lvreadiness.py` | Complete analysis and output generation. |
| `Inputs_sheet.xlsx` | Input workbook. The script reads only its `MATLAB_Input` worksheet. |
| `Indicators_Definition_v2.xlsx` | Reference workbook describing indicators. The script does not read it. |
| `flowchart_and_inputs_outputs.md` | Execution flowchart and input/output guide. |
| `requirements.txt` | Python libraries needed to run the script. |

## Run on Windows

Use Python 3.11 or newer. Open PowerShell in the repository folder and run:

```powershell
cd "Singular Python Script"
python -m venv .venv
& ".\.venv\Scripts\python.exe" -m pip install -r requirements.txt
& ".\.venv\Scripts\python.exe" lvreadiness.py
```

Create the environment and install libraries once. For later runs, use the final command from this folder.

In VS Code, select this folder's `.venv\Scripts\python.exe` with **Python: Select Interpreter** so the editor uses the same installed libraries.

## Run on macOS or Linux

From the repository folder:

```bash
cd "Singular Python Script"
python3 -m venv .venv
./.venv/bin/python -m pip install -r requirements.txt
./.venv/bin/python lvreadiness.py
```

## Inputs and settings

Keep `Inputs_sheet.xlsx` beside the script. File paths are resolved from the script's location, so the workbook can be found even when the script is launched from another directory.

The worksheet supplies the lifecycle phase, total tests (`n_test`), failed tests (`k_fail`), top-event requirement (`q_req`), and assessment rows. The lifecycle column must be named exactly `Lifecycle Phase`. The optional `Status` column can mark an assessment as `Unable to assess`; its `Z` cell must be blank, and that row is excluded from averaging. All other assessment rows require a numeric `Z` score from 0 to 4.

Section 3 sets the random seed and sample counts. Defaults are seed 1, 200,000 prior draws, and 50,000 posterior resamples. Sections 4–6 contain the score mappings, phase multipliers, and component order. The fixed seed makes Python runs repeatable in the same environment; it does not reproduce MATLAB's exact random draws.

See the [flowcharts and input/output guide](flowchart_and_inputs_outputs.md) for all required input columns, a section-by-section explanation, and detailed flowcharts for profiles, sampling, updating, and the comparison.

## Reading the latest code

| Sections | What happens |
| --- | --- |
| 1–6 | Import libraries and define file paths, sample counts, mappings, and component order. |
| 8–10 | Read the worksheet, lifecycle phase, and three test/requirement settings. |
| 11–12 | Clean and validate assessment rows; average T and O scores separately for each component/rater pair. |
| 13–15 | Map scores to model parameters, calculate each profile's success-Beta parameters, and display them. |
| 16–17 | Sample the equal-weight mixtures and calculate branch and top-event failure probabilities. |
| 18 | Calculate direct likelihoods, normalize posterior weights, and resample whole rows. |
| 19 | Build one dictionary per node and combine the dictionaries into the summary table. |
| 20 | Run the average-score comparison with the same fault tree and direct Bayesian update. |
| 21–22 | Plot component distributions and top-event results. |
| 23 | Save the Excel tables and JSON run record. |

Section 7 was removed with the custom plot settings; the other section numbers were retained. Plots now use Matplotlib defaults, with titles, labels, and legends.

Sections 18 and 20 use this direct calculation:

```python
likelihood = q_top**k_fail * (1 - q_top)**number_of_successes
posterior_weights = likelihood / np.sum(likelihood)
```

The code checks the likelihood sum before dividing. With many tests, direct likelihoods can round down to zero; the script stops if the sum is zero or nonfinite. A zero sum can also mean no sampled probability supports the evidence. The supplied example has three tests. Section 22 still uses logarithms to calculate the normalized likelihood curve on its plotting grid; that curve does not update the samples.

## Outputs

Each run creates `outputs/run_<timestamp>/` containing:

- `results.xlsx`, with `RunInfo`, `RaterParameters`, `PoolSummary`, `NodeSummary`, and `PoolingComparison` worksheets.
- `run_metadata.json`, recording the resolved settings, input path, assessment counts, and run information.
- `figures/`, with seven component plots and five analysis plots, each in PNG and SVG format.

The terminal prints summaries and the output folder's location. Generated outputs and virtual environments are ignored by Git.

There is no PDF-document or YAML export. `pdf` in a plot label or `beta_distribution.pdf(...)` means probability density. Plot filenames are made with `lower()` and `replace()`; the script does not import `re`. The `json` library formats lists for Excel cells and writes `run_metadata.json`; it is not part of the probability calculations.

Component plots show success probability `p`. Fault-tree and top-event results use failure probability `q = 1 - p`. The probability of meeting `q_req` is an uncertainty measure, not the mission-success probability. Monte Carlo rows represent possible sets of probabilities, not individual simulated launches.

## Model scope

The model uses a fixed seven-component fault tree, independent component priors, equal profile weights within each component, and binary top-event test evidence. Score mappings are inherited modeling assumptions. The moment-matched Beta distributions are reporting approximations; sampling uses the original mixture of rater distributions.

This folder changes the organization and readability of the implementation. It does not independently validate the model's predictive accuracy. Repository citation and licensing information remain in the root README and `CITATION.cff`.
