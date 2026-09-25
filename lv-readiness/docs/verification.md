# Verification report

Executed September 22, 2026 on Windows, MATLAB R2024b and Python 3.12.
Python dependency versions are pinned in requirements-verified.txt. The package
installed successfully into a new workspace .venv using pip editable installation.
The complete unit, integration, and available historical regression suite passed:
**34 passed**. Tests include API/CLI equivalence, repeated-run exact numerical
reproducibility, exports, invalid inputs, mixture moments, analytical baselines,
endpoint likelihoods, large test counts, ESS warnings, and joint resampling.

## Native reference and independent Python run

The original MATLAB v13 source was not modified. The wrapper
tools/export_matlab_reference.m reran it and saved joint draws and native runtime
metadata. Recorded local reference: `../../outputs/run_20260922_161750_933`.
Recorded Python run: `../../outputs/python/run_20260922_162034_006`.
Both used the supplied Inputs_sheet.xlsx, CDR, n=3, k=1, q_req=0.5,
N=200000, Mpost=50000, seed=1. All 47 historical assessment rows were read,
46 scores were used, and Excel row 46 was excluded. Seven raters and twelve
profiles were retained. Historical row labels and scores were not edited.

The machine-readable local comparison is
`../../outputs/python/matlab_parity_report.json`; source hashes are in
`../../outputs/python/source_manifest.json`. These assessment-derived results
remain outside the publishable package. The following error magnitudes describe
implementation parity without distributing individual assessments.

| Check | Maximum absolute difference | Acceptance |
| --- | --- | --- |
| Profile parameters | 3.56e-15 | 1e-10 |
| Pool statistics | 2.63e-13 | 1e-10 |
| Tree calculations on identical MATLAB samples | 0 | 1e-10 |
| Likelihood weights on identical MATLAB samples | 3.39e-21 | 1e-10 |
| Joint resampling using native indices | 0 | Exact |
| Node statistics on identical MATLAB samples | 1.95e-16 | 1e-10 |
| Method comparison on identical MATLAB samples | 6.11e-16 | 1e-10 |
| Independent prior node means | 0.000362 | 0.005 |
| Independent posterior node means | 0.001371 | 0.005 |
| Independent node quantiles, including medians | 0.004683 | 0.01 |

All checks passed. All five worksheet names, column order, table shapes, numeric
counts, and twelve PNG filenames matched the MATLAB reference. Additional checks
used tolerance 0.01 for standard deviations and threshold probabilities; these
are supplementary implementation checks rather than new specification limits.
Analytical historical prior/posterior means matched the specification to 1e-10;
the independent MC means passed five-standard-error checks. The prior check used
sample SD/sqrt(N). The posterior check used a conservative approximation combining
resampling uncertainty and ESS-based importance-sampling uncertainty.

## Reproduce

From the enclosing research workspace, rerun MATLAB with:

```matlab
set(groot,'defaultFigureVisible','off');
run('lv-readiness/tools/export_matlab_reference.m');
```

Then run Python and compare the newly generated folders:

```powershell
.\.venv\Scripts\python run_lvreadiness.py run Inputs_sheet.xlsx --output outputs/python --seed 1
.\.venv\Scripts\python lv-readiness/tools/verify_matlab.py MATLAB_RUN PYTHON_RUN Inputs_sheet.xlsx --report outputs/python/matlab_parity_report.json
.\.venv\Scripts\python -m pytest lv-readiness/tests
```

Substitute actual timestamped run paths for MATLAB_RUN and PYTHON_RUN.
The MATLAB sample file contains restricted assessment-derived values and must
remain local. Never commit the historical workbook or its outputs.

## Scope and remaining research decisions

Default independent Python simulations are not bit-for-bit identical to MATLAB:
the RNG and Beta samplers differ. Shared-sample checks demonstrate matching
deterministic transformations; independent MC checks demonstrate agreement within
the specified tolerances. Timestamps, binary files, and rendering differ by design.
Python creates PNGs; native editable FIG files are generated only by MATLAB.

The synthetic example uses only fictional scores and has a saved expected-results
JSON. Python repeatability was checked in the installed environment; exact
cross-version or cross-platform bitwise reproducibility has not been established.
The public test suite skips the historical test when the restricted workbook is
absent. A full second-source audit of the original assessment responses requires
those original response records, which were not supplied here. This verifies the
port and current workbook, not the scientific calibration of the readiness model.
New indicator assignments and an open-source license still require author review.
