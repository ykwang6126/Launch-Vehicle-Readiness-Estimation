"""Verify exported Python outputs and shared-draw calculations against MATLAB.

Run with the installed project interpreter. Restricted results are written only
to the requested local report path, never copied into public test fixtures.
"""
import argparse
import json
from pathlib import Path

import numpy as np
import pandas as pd
from scipy.io import loadmat

from lvreadiness.fault_tree import fault_tree_nodes
from lvreadiness.io import sha256
from lvreadiness.summary import summarize_nodes, pooling_comparison
from lvreadiness.updating import posterior_weights, weighted_moments


def compare(matlab: Path, python: Path, source: Path) -> dict:
    report = dict(matlab_run=str(matlab.resolve()), python_run=str(python.resolve()),
                  input_sha256=sha256(source), checks=[])

    def check(name, actual, expected, tolerance):
        a,b = np.asarray(actual,dtype=float),np.asarray(expected,dtype=float)
        assert a.shape == b.shape, name
        assert np.array_equal(np.isnan(a),np.isnan(b)), name
        error = float(np.nanmax(np.abs(a-b))) if np.isfinite(a).any() else 0.
        report['checks'].append(dict(name=name,max_absolute_error=error,tolerance=float(tolerance),passed=bool(error<=tolerance)))

    m = pd.read_excel(matlab/'results.xlsx',sheet_name=None)
    p = pd.read_excel(python/'results.xlsx',sheet_name=None)
    assert list(m) == list(p), 'Worksheet names/order differ'
    for name in m:
        assert list(m[name].columns) == list(p[name].columns), f'{name}: columns differ'
        assert m[name].shape == p[name].shape, f'{name}: shape differs'
    for name in ('RaterParameters','PoolSummary'):
        numeric = m[name].select_dtypes(include='number').columns
        check(name,p[name][numeric],m[name][numeric],1e-10)
        for column in set(m[name])-set(numeric):
            assert m[name][column].equals(p[name][column]), f'{name}.{column}: labels differ'
    for column in ('N','Mpost','n_test','k_fail','q_req','lambda_phase','Seed','NInputRows','NUsedRows','NExcludedRows','NRaters','NProfiles'):
        check('RunInfo.'+column,p['RunInfo'][column],m['RunInfo'][column],0)
    for name in ('NodeSummary','PoolingComparison'):
        for column in m[name].select_dtypes(include='number'):
            if 'Samples' in column:
                tolerance=0
            elif 'Mean' in column:
                tolerance=.005
            else:
                tolerance=.01
            check(name+'.'+column,p[name][column],m[name][column],tolerance)
    assert {x.name for x in (matlab/'figures').glob('*.png')} == {x.name for x in (python/'figures').glob('*.png')}
    data = loadmat(matlab/'joint_samples.mat')
    prior,post = data['referencePrior'],data['referencePosterior']
    weights = posterior_weights(prior[:,-1],int(m['RunInfo'].n_test.iloc[0]),int(m['RunInfo'].k_fail.iloc[0]))
    check('shared_draw_tree',fault_tree_nodes(prior[:,:7]),prior[:,7:],1e-10)
    check('shared_draw_weights',weights,data['postWeights'].ravel(),1e-10)
    indices = data['postIndex'].ravel().astype(int)-1
    check('shared_draw_joint_resampling',prior[indices],post,0)
    summary=summarize_nodes(prior,post,float(m['RunInfo'].q_req.iloc[0]))
    check('shared_draw_summary',summary.iloc[:,1:],m['NodeSummary'].iloc[:,1:],1e-10)
    comparison=pooling_comparison(prior[:,-1],post[:,-1],data['qTopLegacy'].ravel(),data['qTopLegacyPost'].ravel())
    check('shared_draw_method_comparison',comparison.iloc[:,1:],m['PoolingComparison'].iloc[:,1:],1e-10)
    # Baseline is the exact distribution mean; use MC SE rather than exact equality.
    prior_mean=.3767513662; posterior_mean=.3703170278
    check('analytic_prior',p['NodeSummary'].PriorMean.iloc[-1],prior_mean,
          5*float(p['NodeSummary'].PriorStd.iloc[-1])/np.sqrt(int(p['RunInfo'].N.iloc[0])))
    metadata=json.loads((python/'run_metadata.json').read_text())
    # Conservative sum of MC and posterior-resampling standard errors.
    se=float(p['NodeSummary'].PostStd.iloc[-1])*np.sqrt(1/int(p['RunInfo'].Mpost.iloc[0])+1/metadata['EffectiveSampleSize'])
    check('analytic_posterior',p['NodeSummary'].PostMean.iloc[-1],posterior_mean,5*se)
    report['passed']=all(c['passed'] for c in report['checks'])
    return report


if __name__=='__main__':
    parser=argparse.ArgumentParser()
    parser.add_argument('matlab',type=Path); parser.add_argument('python',type=Path)
    parser.add_argument('input',type=Path); parser.add_argument('--report',type=Path,required=True)
    args=parser.parse_args()
    report=compare(args.matlab,args.python,args.input)
    args.report.parent.mkdir(parents=True,exist_ok=True)
    args.report.write_text(json.dumps(report,indent=2)+'\n',encoding='utf-8')
    print(json.dumps(report,indent=2))
    raise SystemExit(0 if report['passed'] else 1)
