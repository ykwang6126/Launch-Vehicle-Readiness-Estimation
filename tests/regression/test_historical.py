"""Local-only restricted baseline; public tests use synthetic assessments."""

import os
from pathlib import Path

import numpy as np
import pandas as pd
import pytest

from lvreadiness.io import read_input
from lvreadiness.validation import validate_input
from lvreadiness.priors import build_priors
from lvreadiness.pooling import success_product_moments


def test_historical_analytic_reference():
    """Check the local restricted baseline when its workbook is available."""
    path = Path(
        os.environ.get(
            "LVREADINESS_HISTORICAL_INPUT",
            Path(__file__).resolve().parents[3] / "Inputs_sheet.xlsx",
        )
    )
    if not path.exists():
        pytest.skip("Restricted historical workbook is intentionally not distributed.")
    with pytest.warns(UserWarning):
        assessment_rows, rater_profiles, analysis_settings, excluded_rows = (
            validate_input(read_input(path))
        )
    assert (
        len(assessment_rows) == 47
        and len(rater_profiles) == 12
        and excluded_rows == [46]
    )
    assert (
        rater_profiles.NUsedRows.sum() == 46 and rater_profiles.RaterID.nunique() == 7
    )
    rater_profiles = build_priors(rater_profiles, analysis_settings.lambda_phase)
    moments = success_product_moments(rater_profiles, 4)
    assert 1 - moments[1] == pytest.approx(0.3767513662, abs=1e-10)
    posterior_failure_mean = (moments[2] - 2 * moments[3] + moments[4]) / (
        moments[2] - moments[3]
    )
    assert posterior_failure_mean == pytest.approx(0.3703170278, abs=1e-10)
