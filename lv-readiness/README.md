# LVReadiness

Estimate launch-vehicle mission success and uncertainty from readiness assessments
and test evidence.

The calculation uses technical and organizational scores to build a Beta prior
for each component–rater pair, pools raters equally, combines seven components
through a fault tree, and updates the result with system-level test outcomes.

**Status:** v0.1 is under review. Main retains the original implementation and package layout.
The implementation follows specification revision 3 and MATLAB v13.

## Quick start

Python 3.10 or later is required. From the repository root, enter the package folder with `cd lv-readiness`,
then run these commands from that folder.

### Windows (PowerShell)

```powershell
python -m venv .venv
.\.venv\Scripts\python.exe -m pip install -e ".[test]"
.\.venv\Scripts\python.exe -m lvreadiness run examples/synthetic_demo/Inputs_sheet.xlsx --output outputs --seed 1
```

### macOS / Linux

```bash
python3 -m venv .venv
.venv/bin/python -m pip install -e ".[test]"
.venv/bin/python -m lvreadiness run examples/synthetic_demo/Inputs_sheet.xlsx --output outputs --seed 1
```

Install once per environment. MATLAB is not needed for Python analyses.

## Inputs and results

The example is fictional. For your own analysis, replace its path with your
workbook path. Only the `MATLAB_Input` worksheet is read.

| Input | Meaning |
| --- | --- |
| T / O scores | Technical / organizational assessment, each on 0–4 |
| `RaterID` | Stable person identifier; raters remain separate until pooling |
| Lifecycle phase | One phase per workbook: SFR, PDR, CDR, TRR, or SVR |
| `n_test`, `k_fail` | Number of comparable tests and observed failures |
| `q_req` | Maximum acceptable system failure probability |

Each run creates a new `outputs/run_<timestamp>/` folder containing:

- `results.xlsx`: parameters, pooled priors, node statistics, and method comparison.
- `figures/`: seven component plots and five system plots.
- `run_config.yaml`: settings used for the run.
- `run_metadata.json`: versions, input fingerprint, excluded rows, and diagnostics.

The command prints the prior and posterior mean **failure** probability `q_top`.
Estimated mission success is `1 - mean(q_top)`.
See [input/output details](docs/input_output.md) for rules and column definitions.

## Python API

```python
from lvreadiness import run_analysis

result = run_analysis("Inputs_sheet.xlsx", "outputs", seed=1)
print(result.tables["NodeSummary"])
print(result.paths["results"])
```

Defaults: 200,000 prior draws, 50,000 posterior draws, seed 1.
Use `--n-prior`, `--n-posterior`, and `--seed` to change these in the CLI.
Phase, test counts, and threshold are read from Excel.

## Repository guide

| Folder | Contents |
| --- | --- |
| [src](src/README.md) | Python modules under `src/lvreadiness` |
| [docs](docs/README.md) | Equations, input/output rules, workflow, and verification |
| [examples](examples/README.md) | Fictional workbook and saved reference results |
| [tests](tests/README.md) | Model, input, and complete-workflow checks |
| [tools](tools/README.md) | Example builder and optional MATLAB comparison |

## Tests

```powershell
.\.venv\Scripts\python.exe -m pytest tests -q
```

On macOS/Linux, use `.venv/bin/python -m pytest tests -q`.
The historical test skips when its restricted workbook is absent.
Python and MATLAB use different random samplers; matching seeds do not produce
matching draws. See [verification](docs/verification.md) for the comparison rules
and the current test result.

## Citation and licensing

Please cite the software using [CITATION.cff](../CITATION.cff):

> Wang, Yu-Kai. (2026). *LVReadiness: Probabilistic Launch Vehicle Readiness and Mission-Success Assessment* (Version 0.1.0). GitHub.

The associated SciTech paper citation will be added when publicly available.
Licensing and IP ownership remain under review; no open-source license is granted.
Real assessments and their outputs are kept outside the distributed example.
