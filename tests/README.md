# Tests

Install from the repository root, then run:

```bash
python -m pip install -e ".[test]"
python -m pytest tests -q
```

| Location | Checks |
| --- | --- |
| `conftest.py` | Shared fictional assessment and temporary workbook fixtures |
| [unit](unit/README.md) | Mathematics, input rules, and simulation options |
| [integration](integration/README.md) | Complete pipeline, API/CLI, outputs, repeatability |
| [regression](regression/README.md) | Optional restricted historical baseline |

The public suite uses fictional data. Expected historical skip: the workbook
is not distributed. See [verification](../docs/verification.md) for the current
result and open Boolean-input review item.
