# Helper tools

Install the package first. Run Python tools from the package folder using your
environment's Python executable.

| Tool | Purpose |
| --- | --- |
| `build_synthetic_example.py` | Rebuild the fictional example workbook |
| `export_matlab_reference.m` | Run the external native v13 script and save shared draws |
| `verify_matlab.py` | Compare MATLAB/Python schemas, summaries, and shared-draw calculations |

```bash
python tools/build_synthetic_example.py
python tools/verify_matlab.py MATLAB_RUN PYTHON_RUN INPUT.xlsx --report REPORT.json
```

The MATLAB tools require local reference files. See [verification](../docs/verification.md)
for the full workflow. Keep real inputs, reference draws, and comparison reports
outside the public repository.
