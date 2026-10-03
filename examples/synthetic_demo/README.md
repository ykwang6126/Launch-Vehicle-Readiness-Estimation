# Synthetic demo

| File | Purpose |
| --- | --- |
| `Inputs_sheet.xlsx` | Fictional assessment: seven components, one rater, all scores 2 |
| `expected_results.json` | Analytical means, saved Python statistics, and workbook fingerprint |

Settings: CDR, 3 tests, 1 failure, `q_req = 0.5`.
Run from the repository root after installation:

```bash
python -m lvreadiness run examples/synthetic_demo/Inputs_sheet.xlsx --output outputs --seed 1
```

At 200,000 prior draws and 50,000 posterior draws, the saved Python means are:

| Failure probability | Mean |
| --- | --- |
| Prior `q_top` | 0.8357799736 |
| Posterior `q_top` | 0.7984797487 |

The analytical means are approximately 0.8358316563 and 0.7986232148.
Monte Carlo results vary with sampler versions; the analytical means do not.
This high-failure fictional example demonstrates the calculation, not a real
vehicle assessment.

Rebuild the workbook with `python tools/build_synthetic_example.py`. Rebuilding
can change the workbook's byte fingerprint even when the cell values are unchanged.
