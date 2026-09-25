import numpy as np
import pandas as pd
import pytest
from lvreadiness.validation import InputError, validate_input, validate_runtime
from lvreadiness.io import read_input


@pytest.mark.parametrize('value', [None, '', 'bad', np.inf, -1, 4.1])
def test_invalid_score(assessment,value):
    assessment['Z'] = assessment.Z.astype(object)
    assessment.loc[0,'Z'] = value
    with pytest.raises(InputError, match='Invalid Z'):
        validate_input(assessment)


@pytest.mark.parametrize('field,value', [('RaterID',''),('Component','Unknown'),('Branch','Operation'),
                                        ('Cat','X'),('Lifecycle Phase','UNKNOWN'),('n_test',3.5),
                                        ('k_fail',4),('q_req',1.1)])
def test_invalid_fields(assessment,field,value):
    assessment[field] = assessment[field].astype(object)
    assessment.loc[0,field] = value
    with pytest.raises(InputError):
        validate_input(assessment)


def test_unassessed_and_profile_completeness(assessment):
    assessment['Z'] = assessment.Z.astype(object)
    assessment.loc[0,['Z','Status']] = [None,'  Unable TO assess  ']
    with pytest.raises(InputError, match='scored T and O'):
        validate_input(assessment)
    extra = assessment.iloc[[0]].copy()
    extra['Indicator'] = 'Second technical evidence'; extra['Z'] = 4; extra['Status'] = ''
    assessment = pd.concat([assessment,extra],ignore_index=True)
    with pytest.warns(UserWarning,match='Excel rows'):
        cleaned,profiles,_,excluded = validate_input(assessment)
    assert excluded == [2]
    assert profiles.Z_T.iloc[0] == 4
    assert profiles.NExcludedRows.iloc[0] == 1
    assessment.loc[0,'Z'] = 1
    with pytest.raises(InputError,match='blank Z'):
        validate_input(assessment)


def test_duplicates_including_unassessed(assessment):
    duplicate = assessment.iloc[[0]].copy()
    duplicate['Z'] = None; duplicate['Status'] = 'Unable to assess'
    with pytest.raises(InputError, match='Duplicate'):
        validate_input(pd.concat([assessment,duplicate],ignore_index=True))


def test_blank_rows_settings_once_aliases(assessment):
    for column in ('Lifecycle Phase','n_test','k_fail','q_req'):
        assessment[column] = assessment[column].astype(object)
        assessment.loc[1:,column] = None
    assessment.loc[assessment.Component.eq('Assembly and Integration'),'Component'] = 'Integration'
    assessment.loc[assessment.Component.eq('Impl. Verification'),'Component'] = 'Implementation Verification'
    assessment = pd.concat([assessment,pd.DataFrame([{}])],ignore_index=True)
    rows,profiles,settings,_ = validate_input(assessment)
    assert len(rows) == 14 and len(profiles) == 7 and settings.n_test == 3


def test_duplicate_headers_and_wrong_sheet(tmp_path):
    path = tmp_path/'input.xlsx'
    pd.DataFrame([[1,2]],columns=['Z','Z']).to_excel(path,sheet_name='MATLAB_Input',index=False)
    with pytest.raises(InputError,match='duplicate column'):
        read_input(path)
    pd.DataFrame().to_excel(path,index=False)
    with pytest.raises(InputError,match='MATLAB_Input'):
        read_input(path)


@pytest.mark.parametrize('args', [(0,10,1),(10,0,1),(2.5,10,1),(10,10,-1),(10,10,True)])
def test_runtime(args):
    with pytest.raises(InputError):
        validate_runtime(*args)
