# Code walkthrough - October 9, 2026

[Printable checklist](LVReadiness_Walkthrough_20261009.pdf)

**Length:** 120 minutes. **Branch:** `review/readability-audit`.
**Goal:** review the mathematics first, then make a first pass through all 13 source modules.
This is a full coverage walkthrough; unresolved details become follow-up items.

## Roles

- Yu-Kai: state the intended calculation; check assumptions and expected results; decide acceptance.
- Dhrupath: explain the implementation; show evidence; own fixes and readability changes.
- AI: explain syntax and help cross-check examples. Expected results must have a stated derivation.

## Agenda

| Minutes | Read together | Confirm |
| --- | --- | --- |
| 0-20 | `docs/mathematical_model.md`, pooling section; `docs/exact_moments.md` | Density pooling; within/between variance; purpose and derivation of exact moments |
| 20-30 | `src/config.py` | Mapping values, lifecycle factors, seven components, eleven-node order |
| 30-45 | `src/io.py`, `src/validation.py` | One-sheet input; settings; profiles; excluded rows; open Boolean issue |
| 45-55 | `src/priors.py` | Work through T=3, O=2.5, CDR by hand |
| 55-70 | `src/pooling.py` | Equal weights; mixture sampling; exact moments; comparison-only methods |
| 70-80 | `src/fault_tree.py` | OR equations; zero/one cases; independence assumptions |
| 80-95 | `src/updating.py` | Likelihood; log weights; full-row resampling; ESS |
| 95-105 | `src/summary.py`, `src/plotting.py` | Failure versus success; percentiles; Pmeet; twelve figures |
| 105-115 | `src/pipeline.py` | Calculation order; RNG; settings; metadata; exports |
| 115-120 | `src/cli.py`, `src/__init__.py`, `src/__main__.py` | API/CLI entry points; defaults; error status; assign remaining work |

## Review method

For each calculation: state inputs and outputs, point to its equation, trace one
example, then mark Accepted / Revise / Open. Read core calculation lines closely.
For supporting code, confirm behavior and inspect important branches.
Timebox syntax discussions; record unresolved questions without skipping the next module.

## Expected numbers

| Example | Expected result |
| --- | --- |
| T=3, O=2.5, CDR | mu=0.924; strength=18.2; alpha=16.8168; beta=1.3832 |
| Two equally weighted priors: Beta(2,8), Beta(8,2) | Mean=0.5; within=0.01454545; between=0.09; total=0.10454545 |
| Seven component failure probabilities of 0.1 | q_top=1-0.9^7=0.5217031 |
| n=3, k=1, q=[0.1,0.3,0.5] | Unnormalized likelihood=[0.081,0.147,0.125] |

## Record decisions

| Item / file | Finding | Accepted / Revise / Open | Owner | Due |
| --- | --- | --- | --- | --- |
| V2-01 / validation | Reject TRUE/FALSE in numeric Excel fields; add tests | Revise | Dhrupath | Agree in meeting |
| | | | | |
| | | | | |
| | | | | |

## Before using TASA results

- Record the exact code commit and workbook; keep restricted inputs outside the repository.
- Confirm lifecycle, test counts, retained rater profiles, excluded rows, and q_req.
- Inspect RaterParameters and PoolSummary before interpreting NodeSummary.
- Review ESS and compare weighted posterior mean with the resampled mean.
- Check the model assumptions and evidence overlap for this assessment round.
- Mark results preliminary while relevant mathematical or input issues remain open.

## After the meeting

Dhrupath completes agreed fixes and remaining tests during fall break. Yu-Kai
finishes the TASA presentation draft by Friday. Before the October 16 group review,
rerun public tests and the fictional example; bring the accepted items, evidence,
and unresolved research questions. Recheck numerical results after any model change.
