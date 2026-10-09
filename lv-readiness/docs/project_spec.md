# Specification and source decisions

## References

| Source | Role |
| --- | --- |
| `LVReadiness_v0.1_Python_Package_Specification_v3.docx` (September 18, 2026; Yu-Kai Wang) | Implementation requirements |
| `mc_faulttree_bayes_demo_v13.m` | Native MATLAB reference |
| `Indicators_Definition_v2.xlsx` | Indicator labels and 0–4 rubrics |
| Wang and Marais SciTech manuscript | Research framework and equations |

These development references are not distributed in this repository. The
manuscript, *An Adaptive Probabilistic Framework to Support Mission Success
Assessment in Launch Vehicle Development*, is not yet public. Cite the software
using [CITATION.cff](../CITATION.cff) until a public paper citation is available.

## Decisions retained in v0.1

- **Pooling:** one prior per component–rater pair; equal profile weights within a component.
  Multiple indicators do not increase a rater's weight.
- **Historical labels:** read `Indicator` and `Cat` as supplied. Do not silently
  reassign historical scores to newer proposed categories.
- **Unassessed rows:** exclude them, never replace them with zero. Duplicate
  detection includes these rows. Missing scored T/O categories stop the calculation.
- **Evidence:** accept top-event test outcomes only; every comparable test counts once.
- **Examples:** use a fictional Excel workbook. Historical MATLAB v13 references
  stay local in the optional regression workflow.
- **Layout:** main retains the package under `lv-readiness/`, with Python modules
  in `src/lvreadiness`. Code refactoring remains on the review branch.

## Indicator details requiring care

| Source difference | Decision |
| --- | --- |
| Paper labels Operation Setup Procedure Readiness as O; historical Procedure readiness is T | Preserve historical T |
| Historical Heritage is T; newer Organizational heritage is proposed as O | Apply no retrospective remapping |
| Overview “Design expertise” / rubric “Engineering Expertise” | Naming difference does not change scores |
| Overview “Setup Team Readiness” / rubric “Setup Team Expertise” | Naming difference does not change scores |
| Indicator workbook does not encode T/O assignments | Review proposed assignments before collecting new data |

Score mappings are structured assumptions. Reproducing historical demo results
verifies the implementation, not calibration for a new vehicle.

## Requirement traceability

| Requirement | Implementation |
| --- | --- |
| Spec 2–3: workbook and profile validation | `io.py`, `validation.py` |
| Spec 4; paper equations 5–15: prior mapping | `config.py`, `priors.py` |
| Spec 5: equal-weight mixture | `pooling.py` |
| Spec 5; paper equations 1–4: fault tree | `fault_tree.py` |
| Spec 6; paper equations 19–22: update | `updating.py` |
| Spec 7–9: workflow, summaries, exports | `pipeline.py`, `summary.py`, `io.py`, `plotting.py`, `cli.py` |
| Spec 10: verification | `tests/`, `tools/verify_matlab.py` |
