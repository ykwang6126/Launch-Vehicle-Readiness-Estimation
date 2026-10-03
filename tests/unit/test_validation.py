"""Reject malformed workbook input and verify supported row-cleaning behavior."""

import numpy as np
import pandas as pd
import pytest
from lvreadiness.validation import InputError, validate_input, validate_run_options
from lvreadiness.io import read_input


@pytest.mark.parametrize("value", [None, "", "bad", np.inf, -1, 4.1])
def test_invalid_score(assessment, value):
    """Reject missing, nonnumeric, nonfinite, and out-of-range scored values."""
    assessment["Z"] = assessment.Z.astype(object)
    assessment.loc[0, "Z"] = value
    with pytest.raises(InputError, match="Invalid Z"):
        validate_input(assessment)


@pytest.mark.parametrize(
    "field,value",
    [
        ("RaterID", ""),
        ("Component", "Unknown"),
        ("Branch", "Operation"),
        ("Cat", "X"),
        ("Lifecycle Phase", "UNKNOWN"),
        ("n_test", 3.5),
        ("k_fail", 4),
        ("q_req", 1.1),
    ],
)
def test_invalid_fields(assessment, field, value):
    """Reject invalid identifiers, labels, lifecycle phase, and workbook settings."""
    assessment[field] = assessment[field].astype(object)
    assessment.loc[0, field] = value
    with pytest.raises(InputError):
        validate_input(assessment)


def test_unassessed_and_profile_completeness(assessment):
    """Exclude blank unassessed rows while requiring scored T and O categories."""
    assessment["Z"] = assessment.Z.astype(object)
    assessment.loc[0, ["Z", "Status"]] = [None, "  Unable TO assess  "]
    with pytest.raises(InputError, match="scored T and O"):
        validate_input(assessment)
    extra = assessment.iloc[[0]].copy()
    extra["Indicator"] = "Second technical evidence"
    extra["Z"] = 4
    extra["Status"] = ""
    assessment = pd.concat([assessment, extra], ignore_index=True)
    with pytest.warns(UserWarning, match="Excel rows"):
        cleaned, rater_profiles, _, excluded = validate_input(assessment)
    assert excluded == [2]
    assert rater_profiles.Z_T.iloc[0] == 4
    assert rater_profiles.NExcludedRows.iloc[0] == 1
    assessment.loc[0, "Z"] = 1
    with pytest.raises(InputError, match="blank Z"):
        validate_input(assessment)


def test_duplicates_including_unassessed(assessment):
    """Reject a repeated indicator even if the repeated row is unassessed."""
    duplicate = assessment.iloc[[0]].copy()
    duplicate["Z"] = None
    duplicate["Status"] = "Unable to assess"
    with pytest.raises(InputError, match="Duplicate"):
        validate_input(pd.concat([assessment, duplicate], ignore_index=True))


def test_blank_rows_settings_once_aliases(assessment):
    """Accept settings entered once, supported component aliases, and blank rows."""
    for column in ("Lifecycle Phase", "n_test", "k_fail", "q_req"):
        assessment[column] = assessment[column].astype(object)
        assessment.loc[1:, column] = None
    assessment.loc[assessment.Component.eq("Assembly and Integration"), "Component"] = (
        "Integration"
    )
    assessment.loc[assessment.Component.eq("Impl. Verification"), "Component"] = (
        "Implementation Verification"
    )
    assessment = pd.concat([assessment, pd.DataFrame([{}])], ignore_index=True)
    assessment_rows, rater_profiles, analysis_settings, _ = validate_input(assessment)
    assert (
        len(assessment_rows) == 14
        and len(rater_profiles) == 7
        and analysis_settings.n_test == 3
    )


def test_duplicate_headers_and_wrong_sheet(tmp_path):
    """Reject duplicate column names and missing MATLAB_Input worksheets."""
    path = tmp_path / "input.xlsx"
    pd.DataFrame([[1, 2]], columns=["Z", "Z"]).to_excel(
        path, sheet_name="MATLAB_Input", index=False
    )
    with pytest.raises(InputError, match="duplicate column"):
        read_input(path)
    pd.DataFrame().to_excel(path, index=False)
    with pytest.raises(InputError, match="MATLAB_Input"):
        read_input(path)


@pytest.mark.parametrize(
    "args", [(0, 10, 1), (10, 0, 1), (2.5, 10, 1), (10, 10, -1), (10, 10, True)]
)
def test_run_options(args):
    """Reject invalid simulation counts and random seeds."""
    with pytest.raises(InputError):
        validate_run_options(*args)
