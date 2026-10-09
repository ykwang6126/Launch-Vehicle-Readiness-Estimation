# Unit tests

- `test_model.py`: lookup mappings, mixture moments, fault-tree equations,
  likelihoods, row resampling, ESS, percentiles, and threshold statistics.
- `test_validation.py`: invalid scores/settings, missing fields, duplicate
  indicators, unassessed rows, aliases, workbook headers, and run options.

Run from the package folder: `python -m pytest tests/unit -q`.
