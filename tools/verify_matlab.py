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
    """Compare output schemas, Monte Carlo summaries, and shared MATLAB draws.

    matlab and python are completed run folders; source is the input workbook.
    Shared draws isolate deterministic calculations from sampler differences.
    """
    report = dict(
        matlab_run=str(matlab.resolve()),
        python_run=str(python.resolve()),
        input_sha256=sha256(source),
        checks=[],
    )

    def check(name, actual, expected, tolerance):
        """Record numeric error after checking shape and unavailable-value positions."""
        actual_values, expected_values = np.asarray(actual, dtype=float), np.asarray(
            expected, dtype=float
        )
        assert actual_values.shape == expected_values.shape, name
        assert np.array_equal(np.isnan(actual_values), np.isnan(expected_values)), name
        error = (
            float(np.nanmax(np.abs(actual_values - expected_values)))
            if np.isfinite(actual_values).any()
            else 0.0
        )
        report["checks"].append(
            dict(
                name=name,
                max_absolute_error=error,
                tolerance=float(tolerance),
                passed=bool(error <= tolerance),
            )
        )

    # Check schemas and deterministic profile/pool values first.
    matlab_tables = pd.read_excel(matlab / "results.xlsx", sheet_name=None)
    python_tables = pd.read_excel(python / "results.xlsx", sheet_name=None)
    assert list(matlab_tables) == list(python_tables), "Worksheet names/order differ"
    for name in matlab_tables:
        assert list(matlab_tables[name].columns) == list(
            python_tables[name].columns
        ), f"{name}: columns differ"
        assert (
            matlab_tables[name].shape == python_tables[name].shape
        ), f"{name}: shape differs"
    for name in ("RaterParameters", "PoolSummary"):
        numeric = matlab_tables[name].select_dtypes(include="number").columns
        check(name, python_tables[name][numeric], matlab_tables[name][numeric], 1e-10)
        for column in set(matlab_tables[name]) - set(numeric):
            assert matlab_tables[name][column].equals(
                python_tables[name][column]
            ), f"{name}.{column}: labels differ"
    for column in (
        "N",
        "Mpost",
        "n_test",
        "k_fail",
        "q_req",
        "lambda_phase",
        "Seed",
        "NInputRows",
        "NUsedRows",
        "NExcludedRows",
        "NRaters",
        "NProfiles",
    ):
        check(
            "RunInfo." + column,
            python_tables["RunInfo"][column],
            matlab_tables["RunInfo"][column],
            0,
        )
    # Independent MATLAB/Python runs use different draws, so summaries use
    # Monte Carlo tolerances rather than exact numerical equality.
    for name in ("NodeSummary", "PoolingComparison"):
        for column in matlab_tables[name].select_dtypes(include="number"):
            if "Samples" in column:
                tolerance = 0
            elif "Mean" in column:
                tolerance = 0.005
            else:
                tolerance = 0.01
            check(
                name + "." + column,
                python_tables[name][column],
                matlab_tables[name][column],
                tolerance,
            )
    assert {x.name for x in (matlab / "figures").glob("*.png")} == {
        x.name for x in (python / "figures").glob("*.png")
    }
    # Replay calculations using MATLAB's saved draws for a tighter parity check.
    data = loadmat(matlab / "joint_samples.mat")
    prior, posterior = data["referencePrior"], data["referencePosterior"]
    weights = posterior_weights(
        prior[:, -1],
        int(matlab_tables["RunInfo"].n_test.iloc[0]),
        int(matlab_tables["RunInfo"].k_fail.iloc[0]),
    )
    check("shared_draw_tree", fault_tree_nodes(prior[:, :7]), prior[:, 7:], 1e-10)
    check("shared_draw_weights", weights, data["postWeights"].ravel(), 1e-10)
    # MATLAB indices start at 1; NumPy indices start at 0.
    indices = data["postIndex"].ravel().astype(int) - 1
    check("shared_draw_joint_resampling", prior[indices], posterior, 0)
    summary = summarize_nodes(
        prior, posterior, float(matlab_tables["RunInfo"].q_req.iloc[0])
    )
    check(
        "shared_draw_summary",
        summary.iloc[:, 1:],
        matlab_tables["NodeSummary"].iloc[:, 1:],
        1e-10,
    )
    comparison = pooling_comparison(
        prior[:, -1],
        posterior[:, -1],
        data["qTopLegacy"].ravel(),
        data["qTopLegacyPost"].ravel(),
    )
    check(
        "shared_draw_method_comparison",
        comparison.iloc[:, 1:],
        matlab_tables["PoolingComparison"].iloc[:, 1:],
        1e-10,
    )
    # Baseline is the exact distribution mean; use MC SE rather than exact equality.
    prior_mean = 0.3767513662
    posterior_mean = 0.3703170278
    check(
        "analytic_prior",
        python_tables["NodeSummary"].PriorMean.iloc[-1],
        prior_mean,
        5
        * float(python_tables["NodeSummary"].PriorStd.iloc[-1])
        / np.sqrt(int(python_tables["RunInfo"].N.iloc[0])),
    )
    metadata = json.loads((python / "run_metadata.json").read_text())
    # Conservative sum of MC and posterior-resampling standard errors.
    standard_error = float(python_tables["NodeSummary"].PostStd.iloc[-1]) * np.sqrt(
        1 / int(python_tables["RunInfo"].Mpost.iloc[0])
        + 1 / metadata["EffectiveSampleSize"]
    )
    check(
        "analytic_posterior",
        python_tables["NodeSummary"].PostMean.iloc[-1],
        posterior_mean,
        5 * standard_error,
    )
    report["passed"] = all(c["passed"] for c in report["checks"])
    return report


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("matlab", type=Path)
    parser.add_argument("python", type=Path)
    parser.add_argument("input", type=Path)
    parser.add_argument("--report", type=Path, required=True)
    arguments = parser.parse_args()
    report = compare(arguments.matlab, arguments.python, arguments.input)
    arguments.report.parent.mkdir(parents=True, exist_ok=True)
    arguments.report.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(report, indent=2))
    raise SystemExit(0 if report["passed"] else 1)
