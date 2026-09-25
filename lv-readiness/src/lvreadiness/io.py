"""Read MATLAB_Input and export the MATLAB v13 workbook and provenance schema."""

import hashlib
import json
from pathlib import Path
import shutil
import subprocess

import pandas as pd
import yaml
from openpyxl import load_workbook

from .validation import InputError


def read_input(path: str | Path) -> pd.DataFrame:
    """Read just the required sheet; do not use spreadsheet-derived parameters."""
    path = Path(path)
    if not path.is_file():
        raise InputError(f"Input workbook not found: {path}")
    book = load_workbook(path, read_only=True, data_only=True)
    try:
        if "MATLAB_Input" not in book.sheetnames:
            raise InputError("Required worksheet MATLAB_Input is missing.")
        rows = list(book["MATLAB_Input"].values)
        if not rows:
            raise InputError("MATLAB_Input is empty.")
        headers = list(rows[0])
        if len([h for h in headers if h is not None]) != len(set(h for h in headers if h is not None)):
            raise InputError("MATLAB_Input has duplicate column names.")
        frame = pd.DataFrame(rows[1:], columns=headers)
        return frame.loc[:, [c is not None for c in frame.columns]]
    finally:
        book.close()


def sha256(path: str | Path) -> str:
    """Fingerprint the exact input or reference file for reproducibility."""
    with Path(path).open("rb") as source:
        return hashlib.file_digest(source, "sha256").hexdigest() if hasattr(hashlib, 'file_digest') else hashlib.sha256(source.read()).hexdigest()


def git_commit(path: Path) -> str | None:
    """Record a commit only when git and a containing repository are available."""
    git = shutil.which("git")
    if git is None:
        return None
    try:
        proc = subprocess.run([git, "-C", str(path), "rev-parse", "HEAD"],
                              capture_output=True, text=True, timeout=5, check=False)
        return proc.stdout.strip() if proc.returncode == 0 else None
    except (OSError, subprocess.TimeoutExpired):
        return None


def export_results(run_dir: Path, tables: dict[str, pd.DataFrame], config: dict, metadata: dict) -> dict[str, Path]:
    """Save typed numbers and true blanks; preserve the five worksheet schemas."""
    workbook = run_dir / "results.xlsx"
    with pd.ExcelWriter(workbook, engine="openpyxl") as writer:
        for name, table in tables.items():
            table.to_excel(writer, sheet_name=name, index=False, na_rep="")
            # Force labels to remain strings, even if assessment IDs begin '='.
            sheet = writer.sheets[name]
            for row_index, values in enumerate(table.itertuples(index=False, name=None), 2):
                for col_index, value in enumerate(values, 1):
                    if isinstance(value, str):
                        sheet.cell(row_index, col_index).data_type = "s"
    config_path, metadata_path = run_dir / "run_config.yaml", run_dir / "run_metadata.json"
    config_path.write_text(yaml.safe_dump(config, sort_keys=False), encoding="utf-8")
    metadata_path.write_text(json.dumps(metadata, indent=2, allow_nan=False)+"\n", encoding="utf-8")
    return dict(results=workbook, config=config_path, metadata=metadata_path, figures=run_dir/"figures")
