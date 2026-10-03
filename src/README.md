# Source code

All modules are directly under `src`. `pyproject.toml` installs this directory as
**`lvreadiness`**, so imports and the CLI keep their existing names.
Run `pip install -e ".[test]"` from the repository root before using them.

| Module | Responsibility |
| --- | --- |
| `pipeline.py` | Run the complete analysis and return tables, paths, and samples |
| `io.py` | Read `MATLAB_Input`; export Excel, YAML, and JSON |
| `validation.py` | Check input and build separate component–rater profiles |
| `config.py` | Mapping tables, lifecycle factors, component order, and defaults |
| `priors.py` | Convert T/O scores into success-Beta parameters |
| `pooling.py` | Pool raters, sample mixtures, and calculate exact moments |
| `fault_tree.py` | Combine seven component failure probabilities |
| `updating.py` | Calculate test likelihood weights and resample complete rows |
| `summary.py` | Calculate statistics and compare pooling methods |
| `plotting.py` | Save the twelve diagnostic figures |
| `cli.py` | Parse command-line options and call the pipeline |
| `__init__.py` | Expose `run_analysis`, `AnalysisResult`, and version |
| `__main__.py` | Support `python -m lvreadiness` |

Suggested review order: `config` → `io` → `validation` → `priors` → `pooling` →
`fault_tree` → `updating` → `summary` → `plotting` → `pipeline` → `cli`.

Comments explain inputs, array shapes, equations, and the reason for important
steps. Mathematical symbols such as `mu`, `alpha`, and `beta` follow the
[model documentation](../docs/mathematical_model.md).
