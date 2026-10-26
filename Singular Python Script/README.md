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

The worksheet supplies the lifecycle phase, total tests (`n_test`), failed tests (`k_fail`), top-event requirement (`q_req`), and assessment rows. The lifecycle column must be named exactly `Lifecycle Phase`.

Section 3 sets the random seed and sample counts. Defaults are seed 1, 200,000 prior draws, and 50,000 posterior resamples. Sections 4–6 contain the score mappings, phase multipliers, and component order. The fixed seed makes Python runs repeatable in the same environment; it does not reproduce MATLAB's exact random draws.

See `flowchart_and_inputs_outputs.md` for all required input columns and a section-by-section explanation.

## Outputs

Each run creates `outputs/run_<timestamp>/` containing:

- `results.xlsx`, with `RunInfo`, `RaterParameters`, `PoolSummary`, `NodeSummary`, and `PoolingComparison` worksheets.
- `run_metadata.json`, recording the resolved settings, input path, assessment counts, and run information.
- `figures/`, with seven component plots and five analysis plots, each in PNG and SVG format.

The terminal prints summaries and the output folder's location. Generated outputs and virtual environments are ignored by Git.

Component plots show success probability `p`. Fault-tree and top-event results use failure probability `q = 1 - p`. The probability of meeting `q_req` is an uncertainty measure, not the mission-success probability. Monte Carlo rows represent possible sets of probabilities, not individual simulated launches.

## Model scope

The model uses a fixed seven-component fault tree, independent component priors, equal profile weights within each component, and binary top-event test evidence. Score mappings are inherited modeling assumptions. The moment-matched Beta distributions are reporting approximations; sampling uses the original mixture of rater distributions.

This folder changes the organization and readability of the implementation. It does not independently validate the model's predictive accuracy. Repository citation and licensing information remain in the root README and `CITATION.cff`.
