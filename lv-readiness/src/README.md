# Source code

Python modules are under `src/lvreadiness`. The installed package name is
**`lvreadiness`**. Run `pip install -e ".[test]"` from the package folder
(`lv-readiness/`) before using the API or CLI.

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

Mathematical symbols such as `mu`, `alpha`, and `beta` follow the
[model documentation](../docs/mathematical_model.md).
