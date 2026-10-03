"""Reusable fictional assessments and temporary workbooks for public tests."""

from pathlib import Path
import pandas as pd
import pytest

from lvreadiness.config import BRANCHES, COMPONENTS


@pytest.fixture
def assessment():
    """Build one fictional T/O profile for each of the seven components."""
    rows = []
    for branch, component in zip(BRANCHES, COMPONENTS):
        for category in ("T", "O"):
            rows.append(
                dict(
                    Branch=branch,
                    Component=component,
                    Indicator=f"Synthetic {category}",
                    Cat=category,
                    Z=2,
                    RaterID="SYN01",
                    Status="",
                    **{"Lifecycle Phase": "CDR"},
                    n_test=3,
                    k_fail=1,
                    q_req=0.5,
                )
            )
    return pd.DataFrame(rows)


@pytest.fixture
def synthetic_workbook(tmp_path, assessment):
    """Save the assessment fixture in a temporary MATLAB_Input workbook."""
    path = tmp_path / "Inputs_sheet.xlsx"
    assessment.to_excel(path, sheet_name="MATLAB_Input", index=False)
    return path
