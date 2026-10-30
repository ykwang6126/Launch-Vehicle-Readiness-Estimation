# LVReadiness — Launch Vehicle Readiness Estimation

LVReadiness is research software developed by Yu-Kai Wang, a Ph.D. candidate in Aeronautics and Astronautics at Purdue University. It combines structured engineering assessments with limited test evidence to estimate launch-vehicle mission-success probability and uncertainty.

This `review/singularaudit` branch contains the analysis as one Python script, with numbered sections and comments referencing the MATLAB v13 baseline.

## Start here

| Task | Guide |
| --- | --- |
| Install libraries and run the script | [Single-script README](Singular%20Python%20Script/README.md) |
| Follow the execution and understand inputs/outputs | [Five flowcharts and input/output guide](Singular%20Python%20Script/flowchart_and_inputs_outputs.md) |
| Read the implementation | [lvreadiness.py](Singular%20Python%20Script/lvreadiness.py) |
| Review the required libraries | [requirements.txt](Singular%20Python%20Script/requirements.txt) |

Keep the input workbook beside the script. The script reads only its `MATLAB_Input` worksheet. Setup commands for Windows, macOS, and Linux are in the single-script README.

## How the current script works

1. Read the lifecycle phase, test counts, requirement, and indicator assessments.
2. Validate and clean the rows. Exclude entries explicitly marked `Unable to assess`, whose scores must be blank.
3. Average technical and organizational scores separately for each component/rater profile.
4. Map profile scores to Beta distributions for component success probability.
5. Sample equal-weight mixtures and propagate component failures through the seven-component fault tree.
6. Use direct likelihood calculations to weight and resample complete rows using top-event test evidence.
7. Build node-summary dictionaries and separately compare the results with averaging scores before constructing distributions.
8. Save plots, an Excel workbook, and JSON run metadata.

The direct likelihood updates in sections 18 and 20 are easier to read but can round down to zero with many tests. The script checks for zero or invalid likelihood sums. Section 22 uses the same direct formula for its separate plotting curve, normalizes it by area, and checks that the area is finite and positive. These likelihood calculations do not use logarithms or `np.errstate`.

## Outputs

Each run creates a timestamped folder under `Singular Python Script/outputs/` containing:

- `results.xlsx` with five worksheets: run information, rater parameters, component pools, node summaries, and the pooling-method comparison.
- Seven component plots and five top-event plots, each saved as PNG and SVG.
- `run_metadata.json` with the resolved settings and run details.

Generated outputs and virtual environments are excluded from Git. There is no YAML or PDF-document export. In the code, `pdf` means probability density.

Component plots show success probability `p`. Fault-tree results use failure probability `q = 1 - p`. Estimated mission-success probability is **1 − mean top-event failure probability**. The probability of meeting `q_req` is a separate uncertainty measure.

## Research scope

The model uses a fixed seven-component fault tree, independent component priors, and comparable binary top-event test outcomes. Score mappings are modeling assumptions that require calibration and research review. Numerical checks establish implementation consistency; they do not establish predictive accuracy for a new system.

Rater profiles receive equal weights within each component. Moment-matched Beta distributions are reporting approximations; Monte Carlo sampling uses the original rater mixtures. The fixed seed makes Python runs repeatable in the same environment, but does not reproduce MATLAB's exact random draws.

## Citation

If you use LVReadiness, please cite the software repository:

**Wang, Yu-Kai. (2026). _LVReadiness: Probabilistic Launch Vehicle Readiness and Mission-Success Assessment_ (Version 0.1.0). GitHub.**

GitHub's **Cite this repository** feature uses [CITATION.cff](CITATION.cff). A preferred citation to the associated SciTech paper will be added when that publication becomes publicly available.

## License and IP status

No open-source license has been granted yet. Licensing and IP ownership are under review. Public visibility of this repository does not itself grant an open-source license.
