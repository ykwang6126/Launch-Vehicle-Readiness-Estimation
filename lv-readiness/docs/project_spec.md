# Specification and source decisions

Implementation target: `LVReadiness_v0.1_Python_Package_Specification_v3.docx`,
version 0.1 specification revision 3, revised September 18, 2026, prepared by
Yu-Kai Wang. MATLAB implementation reference: `mc_faulttree_bayes_demo_v13.m`.
The original files remain in the enclosing research workspace.

The mathematical framework was developed by Yu-Kai Wang and Karen Marais for an
associated SciTech manuscript, *An Adaptive Probabilistic Framework to Support
Mission Success Assessment in Launch Vehicle Development*. The manuscript is not
yet publicly available. Until a public paper citation/DOI is available, users
should cite this software repository using `CITATION.cff`. The implementation
was checked against the internal manuscript version used during development.

Indicator reference: `Indicators_Definition_v2.xlsx`, seven component worksheets.
Overview labels define current assessment terminology; detailed rubrics explain
scores 0–4. The workbook does not explicitly encode T/O assignments. The
specification's proposed assignments need review before collecting new data.

## Decisions preserving source meaning

- The revised specification's directory table supersedes the older embedded
  tree: use an Excel synthetic example and `matlab_v13_expected`, not CSV and v11.
- The paper gives the base model. Revision 3 and MATLAB v13 add equal-weight
  finite-mixture pooling of individual component–rater profiles.
- Historical `Indicator` and `Cat` values are read as supplied. In particular,
  the paper's Table 3 labels Operation Setup Procedure Readiness as O, while
  the supplied historical workbook labels its Procedure readiness row T.
  Silently changing this would invalidate the specified historical baseline.
- Historical Heritage remains T. The newer Organizational heritage indicator
  is proposed as O for new assessments; it does not retrospectively alter data.
- New overview label Design expertise corresponds to Engineering Expertise in
  the detailed rubric. Setup Team Readiness similarly has a detailed rubric
  heading Setup Team Expertise. These naming differences do not change scores.
- An explicitly unassessed row is excluded, not assigned zero. Duplicate
  indicator detection occurs even for unassessed rows. Missing categories stop
  the calculation. One rater's multiple indicators never create extra weight.
- Version 0.1 accepts top-event test evidence only, despite the paper discussing
  more general future component/subsystem updating. Every test counts once.
- Source mappings are structured model assumptions, not empirically calibrated
  probabilities. Historical demo results do not establish predictive validity
  for a new Purdue student vehicle.

## Traceability

| Source requirement | Implementation |
| --- | --- |
| Spec 2–3, MATLAB cleanMatlabInput/buildProfiles | validation.py, io.py |
| Spec 4, paper equations 5–15 | priors.py, config.py |
| Spec 5, exact equal-weight mixtures | pooling.py |
| Spec 5, paper equations 1–4 | fault_tree.py |
| Spec 6, paper equations 19–22 | updating.py |
| Spec 7–9, MATLAB buildNodeSummary/export | pipeline.py, summary.py, io.py, plotting.py, cli.py |
| Spec 10 | tests and tools/verify_matlab.py |
