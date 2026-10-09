# LVReadiness — Launch Vehicle Readiness Estimation

**How can engineers assess whether a system is ready when only a few tests are available?**

LVReadiness is research software developed by Yu-Kai Wang, a Ph.D. candidate in Aeronautics and Astronautics at Purdue University. It combines structured engineering assessments with limited test evidence to estimate launch-vehicle mission-success probability and the uncertainty in that estimate.

The goal is to support safety and reliability decisions before large operational datasets exist: make assessment assumptions explicit, retain disagreement between assessors, and show how test results change the estimated risk.

## How it works

1. **Assess readiness:** enter technical and organizational scores for seven areas spanning design, verification, manufacturing, integration, and operations.
2. **Represent uncertainty:** map each component–rater assessment to a Beta distribution for success probability.
3. **Pool judgments:** combine rater distributions with equal weights, retaining both individual uncertainty and disagreement.
4. **Estimate system risk:** propagate component probabilities through a fault tree using Monte Carlo simulation.
5. **Update with tests:** use system-level test outcomes to weight and resample complete joint samples.
6. **Review results:** compare prior and posterior risk, uncertainty intervals, and the probability of meeting a specified failure-probability threshold.

![Assessment-to-results workflow](lv-readiness/docs/figures/review_workflow.svg)

## What the tool produces

- Prior and posterior estimates of system and component failure probability.
- Uncertainty summaries and probability of meeting a user-defined requirement.
- Rater parameters and pooled uncertainty, including within-rater uncertainty and between-rater disagreement.
- An Excel results workbook, twelve diagnostic plots, and configuration and runtime metadata.

Estimated mission-success probability is **1 − mean system failure probability**. The probability of meeting a requirement is a separate measure of uncertainty; it is not the mission-success probability.

## Start here

| Your interest | Recommended page |
| --- | --- |
| Understand the method visually | [Workflow, pooling, and Bayesian updating diagrams](lv-readiness/docs/review_diagrams.md) |
| Run the Python example | [Installation and quick start](lv-readiness/README.md) |
| Read the equations and assumptions | [Mathematical model](lv-readiness/docs/mathematical_model.md) |
| Prepare inputs or interpret outputs | [Input and output guide](lv-readiness/docs/input_output.md) |
| Explore the implementation | [Source code guide](lv-readiness/src/README.md) |
| Review numerical checks and limits | [Verification](lv-readiness/docs/verification.md) |

## Research context and scope

This project addresses readiness assessment for launch vehicles with limited evidence. Its broader research motivation is relevant to other safety-critical systems, including aircraft, satellites, or automated vehicles, where engineers must combine assessments and testing to support safety decisions.

Version 0.1 uses a fixed seven-component fault tree, independent component priors, and comparable binary system-level test outcomes. Score mappings are model assumptions that require calibration and research review. Numerical verification checks implementation consistency; it does not establish predictive accuracy for a new system.

## Development status

Version 0.1 is under active review. The main-branch Python package remains in [`lv-readiness/`](lv-readiness/README.md). Documentation from the readability audit has been adapted to this layout. Code refactoring remains on [`review/readability-audit`](https://github.com/ykwang6126/Launch-Vehicle-Readiness-Estimation/tree/review/readability-audit).

## Citation

If you use LVReadiness, please cite the software repository:

**Wang, Yu-Kai. (2026). _LVReadiness: Probabilistic Launch Vehicle Readiness and Mission-Success Assessment_ (Version 0.1.0). GitHub.**

GitHub's **Cite this repository** feature uses [CITATION.cff](CITATION.cff). A preferred citation to the associated SciTech paper will be added when that publication becomes publicly available.

## License and IP status

No open-source license has been granted yet. Licensing and IP ownership are under review. Public visibility of this repository does not itself grant an open-source license.
