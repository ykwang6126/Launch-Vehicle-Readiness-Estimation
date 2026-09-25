from pathlib import Path
import pandas as pd
import pytest

from lvreadiness.config import BRANCHES, COMPONENTS


@pytest.fixture
def assessment():
    rows = []
    for branch, component in zip(BRANCHES, COMPONENTS):
        for cat in ('T', 'O'):
            rows.append(dict(Branch=branch, Component=component, Indicator=f'Synthetic {cat}', Cat=cat,
                             Z=2, RaterID='SYN01', Status='', **{'Lifecycle Phase': 'CDR'},
                             n_test=3, k_fail=1, q_req=.5))
    return pd.DataFrame(rows)


@pytest.fixture
def synthetic_workbook(tmp_path, assessment):
    path = tmp_path / 'Inputs_sheet.xlsx'
    assessment.to_excel(path, sheet_name='MATLAB_Input', index=False)
    return path
