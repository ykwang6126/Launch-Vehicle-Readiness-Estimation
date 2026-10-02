# LVReadiness Python package

LVReadiness converts technical and organizational readiness scores into component
Beta priors, pools raters equally, propagates a seven-component fault tree, and
updates joint samples with top-event binomial test evidence. This is the Python
implementation of specification v0.1 revision 3 and MATLAB v13.

## Citation

If you use LVReadiness, please cite the software repository:

**Wang, Yu-Kai. (2026). _LVReadiness: Probabilistic Launch Vehicle Readiness and Mission-Success Assessment_ (Version 0.1.0). GitHub.**

GitHub's **Cite this repository** feature uses `CITATION.cff`. A preferred
citation to the associated SciTech paper will be added when that publication
becomes publicly available.

## Install and run on Windows

Target repository: [ykwang6126/Launch-Vehicle-Readiness-Estimation](https://github.com/ykwang6126/Launch-Vehicle-Readiness-Estimation).

Requires Python 3.10 or later. Open **Terminal > New Terminal** in VS Code,
select PowerShell, and run the following commands from the repository root.

Create your own local environment and install the package and test dependencies:

```powershell
python -m venv .venv
.\.venv\Scripts\python.exe -m pip install -e ".[test]"
```

Run the included fictional assessment:

```powershell
.\.venv\Scripts\python.exe -m lvreadiness run examples/synthetic_demo/Inputs_sheet.xlsx --output outputs --seed 1
```

The command prints the prior and posterior mean failure probabilities and the
results path. Each run creates a new `outputs/run_YYYYMMDD_HHMMSS_SSS/` folder
containing `results.xlsx`, twelve PNG plots in `figures/`, `run_config.yaml`,
and `run_metadata.json`. Existing runs are not overwritten.

Run the tests:

```powershell
.\.venv\Scripts\python.exe -m pytest tests -q
```

No environment activation is necessary. Installation is needed only once per
environment, or again when dependencies change. Reuse the analysis command for
later runs. Do not copy or upload `.venv`; recreate it after moving the checkout
or when setting up another computer. Normal Python analyses do not require MATLAB.

### Analyze your own workbook

Keep real assessments outside the repository. Replace the example path below
with your workbook path, retaining quotes around paths containing spaces:

```powershell
.\.venv\Scripts\python.exe -m lvreadiness run "C:\path\to\Inputs_sheet.xlsx" --output outputs --seed 1
```

Save scores and settings in the workbook's `MATLAB_Input` worksheet before
running. See [input and output requirements](docs/input_output.md). The historical
regression test skips when its restricted workbook is unavailable; the public
unit and integration tests use synthetic data.

## Python interface

```python
from lvreadiness import run_analysis

result = run_analysis("Inputs_sheet.xlsx", "outputs", seed=1)
print(result.tables["NodeSummary"])
print(result.paths["results"])
```

Both interfaces default to 200,000 prior samples and 50,000 posterior samples.
CLI overrides: `--n-prior`, `--n-posterior`, `--seed`, `--output`.
Phase, test counts, and requirement threshold always come from `MATLAB_Input`.

## Matching MATLAB

The mathematical model, deterministic parameters, worksheet schemas, and figure
filenames follow v13. The default NumPy PCG64/Beta sampler is not MATLAB's random
sampler: a seed of 1 does not yield identical random draws across languages.
Independent simulations must meet the specification's mean tolerance of 0.005
and quantile tolerance of 0.01. Tests on shared MATLAB draws check deterministic
operations at absolute tolerance 1e-10. Repeated Python runs with the same inputs,
seed, and dependency versions produce identical numerical arrays and summaries.
Timestamps, paths, metadata, binary workbook files, and plot rendering are not
expected to be byte-identical. Editable MATLAB `.fig` files remain MATLAB-only.

See [verification](docs/verification.md) for the executed checks and limitations,
[model](docs/mathematical_model.md) for equations, [I/O](docs/input_output.md) for
schemas, and [source decisions](docs/project_spec.md) for document discrepancies.

## Data and publication

The example workbook is synthetic. Historical assessments and derived local
results are not distributed. Project-specific ignore rules help keep local
assessment and output artifacts out of version control.

This repository currently has no open-source license. Licensing and IP ownership
are under review; public visibility does not itself grant an open-source license.
