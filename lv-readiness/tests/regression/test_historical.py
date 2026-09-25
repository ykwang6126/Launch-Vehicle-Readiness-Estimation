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
    path = Path(os.environ.get('LVREADINESS_HISTORICAL_INPUT', Path(__file__).resolve().parents[3]/'Inputs_sheet.xlsx'))
    if not path.exists():
        pytest.skip('Restricted historical workbook is intentionally not distributed.')
    with pytest.warns(UserWarning):
        rows, profiles, settings, excluded = validate_input(read_input(path))
    assert len(rows) == 47 and len(profiles) == 12 and excluded == [46]
    assert profiles.NUsedRows.sum() == 46 and profiles.RaterID.nunique() == 7
    profiles = build_priors(profiles, settings.lambda_phase)
    moments = success_product_moments(profiles,4)
    assert 1-moments[1] == pytest.approx(.3767513662,abs=1e-10)
    posterior = (moments[2]-2*moments[3]+moments[4])/(moments[2]-moments[3])
    assert posterior == pytest.approx(.3703170278,abs=1e-10)
