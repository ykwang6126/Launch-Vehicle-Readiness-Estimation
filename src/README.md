# Source code

All modules are directly under `src`. `pyproject.toml` installs this directory as
**`lvreadiness`**, so imports and the CLI keep their existing names.
Run `pip install -e ".[test]"` from the repository root before using them.

| Module | Responsibility |
| --- | --- |
| `pipeline.py` | Run the complete analysis and return tables, paths, and samples |
| `io.py` | Read `MATLAB_Input`; export Excel, YAML, and JSON |
| `input_validation.py` | Check input and build separate component–rater profiles |
| `config.py` | Mapping tables, lifecycle factors, component order, and defaults |
| `priors.py` | Convert T/O scores into success-Beta parameters |
| `pooling.py` | Pool raters, sample mixtures, and calculate exact moments |
| `fault_tree.py` | Combine seven component failure probabilities |
| `updating.py` | Calculate test likelihood weights and resample complete rows |
| `summary.py` | Calculate statistics and compare pooling methods |
| `plotting.py` | Save the twelve diagnostic figures |
| `__main__.py` | Parse command-line options and call the pipeline |
| `__init__.py` | Expose `run_analysis`, `AnalysisResult`, and version |

Suggested review order: `config` → `io` → `input_validation` → `priors` → `pooling` →
`fault_tree` → `updating` → `summary` → `plotting` → `pipeline` → `__main__`.

Comments explain inputs, array shapes, equations, and the reason for important
steps. Mathematical symbols such as `mu`, `alpha`, and `beta` follow the
[model documentation](../docs/mathematical_model.md).

For a short explanation of the pandas operations and probability notation, see
the [reading guide](../docs/reading_the_code.md).

The installed `lvreadiness` command and `python -m lvreadiness` both call
`__main__.main`; importing that module does not run an analysis. The former
`cli.py` forwarding layer has been consolidated here. `__init__.py` remains
the small package boundary needed to preserve `from lvreadiness import
run_analysis`, `AnalysisResult`, and `__version__`.
