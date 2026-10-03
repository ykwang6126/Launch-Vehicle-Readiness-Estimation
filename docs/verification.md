# Verification

## Current audit — October 3, 2026

The public suite passed **33 tests, with 1 skipped** in both the editable
installation and the built wheel tested outside the repository. The skip is the
restricted historical-workbook test.

- The wheel builds and preserves `import lvreadiness` and `python -m lvreadiness`.
- The full synthetic run matches the baseline exactly in all four calculation tables.
- Prior mean `q_top`: **0.8357799736**; posterior mean: **0.7984797487**.
- All 48 math expressions parse with KaTeX; all 29 local Markdown file links resolve.
- The numerical model and accepted input behavior are unchanged.

### Run the public tests

From the repository root, install first:

```powershell
.\.venv\Scripts\python.exe -m pip install -e ".[test]"
.\.venv\Scripts\python.exe -m pytest tests -q
.\.venv\Scripts\python.exe -m lvreadiness run examples/synthetic_demo/Inputs_sheet.xlsx --output outputs --seed 1
```

Use `.venv/bin/python` on macOS/Linux. The saved reference is
[`expected_results.json`](../examples/synthetic_demo/expected_results.json).
Compare numerical summaries; timestamps and file bytes need not match.

| Check | Covered by |
| --- | --- |
| Score mapping, Beta parameters, clipping | Unit model tests |
| Mixture variance, tree equations, exact moments | Unit model tests |
| Endpoint/large-count likelihoods, ESS, joint resampling | Unit model tests |
| Invalid input, unassessed rows, aliases, duplicate detection | Unit validation tests |
| Seed repeatability, API/CLI equivalence, exports, twelve figures | Integration test |
| Historical analytical baseline | Optional local regression test |

## Open review item

**V2-01 — Dhrupath:** reject Excel TRUE/FALSE in `Z`, `n_test`, `k_fail`, and
`q_req` before numeric conversion. Add tests for both Boolean values. Python can
interpret `True` as 1 and `False` as 0. This readability audit leaves that accepted
input behavior unchanged.

## Recorded MATLAB comparison — September 22, 2026

The earlier report records **34 passed** with the historical workbook available
on Windows, MATLAB R2024b, and Python 3.12. Dependency versions are listed in
[`requirements-verified.txt`](../requirements-verified.txt).
The restricted reference files are not included here, so this audit does not
independently rerun or certify that historical comparison.

| Recorded check | Maximum absolute difference | Limit |
| --- | --- | --- |
| Profile parameters | 3.56e-15 | 1e-10 |
| Pool statistics | 2.63e-13 | 1e-10 |
| Tree on shared draws | 0 | 1e-10 |
| Likelihood weights on shared draws | 3.39e-21 | 1e-10 |
| Joint rows using native indices | 0 | Exact |
| Node statistics on shared draws | 1.95e-16 | 1e-10 |
| Method comparison on shared draws | 6.11e-16 | 1e-10 |
| Independent prior means | 0.000362 | 0.005 |
| Independent posterior means | 0.001371 | 0.005 |
| Independent node quantiles | 0.004683 | 0.01 |

The recorded run used CDR, 3 tests, 1 failure, threshold 0.5, 200,000 prior draws,
50,000 posterior draws, and seed 1. It retained 12 profiles from 7 raters and
excluded one unassessed row. Five worksheet schemas and twelve PNG names matched.
Additional spread/threshold checks used tolerance 0.01; analytical means used
1e-10. Independent Monte Carlo means used five-standard-error checks.

## Optional MATLAB reproduction

Requires the native v13 script and the authorized historical workbook outside
the public repository. In MATLAB, set the script path and run the wrapper:

```matlab
referenceScript = 'C:/research/mc_faulttree_bayes_demo_v13.m';
set(groot, 'defaultFigureVisible', 'off');
run('tools/export_matlab_reference.m');
```

Run Python on the same workbook, then compare the timestamped output folders:

```powershell
.\.venv\Scripts\python.exe -m lvreadiness run "C:\research\Inputs_sheet.xlsx" --output "C:\research\python_outputs" --seed 1
.\.venv\Scripts\python.exe tools/verify_matlab.py MATLAB_RUN PYTHON_RUN "C:\research\Inputs_sheet.xlsx" --report "C:\research\matlab_parity_report.json"
```

Replace `MATLAB_RUN` and `PYTHON_RUN` with actual completed run paths.
To enable the optional historical test:

```powershell
$env:LVREADINESS_HISTORICAL_INPUT = "C:\research\Inputs_sheet.xlsx"
.\.venv\Scripts\python.exe -m pytest tests/regression -q
```

## Limits

- MATLAB and Python have different samplers; identical seeds do not imply identical draws.
- Shared-draw tests check deterministic calculations; independent runs use Monte Carlo tolerances.
- Exact repeatability across dependency versions or platforms is not established.
- The native MATLAB wrapper was reviewed but not executed in this audit environment.
- These checks verify the implementation. They do not validate the model's score calibration or new indicator assignments.
