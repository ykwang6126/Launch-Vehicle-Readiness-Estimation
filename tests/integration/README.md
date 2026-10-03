# Integration test

`test_pipeline.py` runs the complete fictional analysis twice and compares
samples and tables. It also checks separate output folders, five worksheet
schemas, twelve figures, API/CLI agreement, and invalid-run exit codes.

Run from the repository root: `python -m pytest tests/integration -q`.
