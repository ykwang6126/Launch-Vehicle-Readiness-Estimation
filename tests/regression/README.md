# Historical regression

`test_historical.py` checks the analytical reference for an authorized local
historical workbook. It skips when that workbook is absent.

Set `LVREADINESS_HISTORICAL_INPUT` to the workbook path, then run
`python -m pytest tests/regression -q` from the repository root.
See [verification](../../docs/verification.md#optional-matlab-reproduction)
for PowerShell commands. Do not add the workbook or derived draws here.
