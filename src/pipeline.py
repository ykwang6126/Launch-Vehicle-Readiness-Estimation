"""One workflow shared by the Python API and command-line entry point."""

#imports all neccessary libraries

from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
import platform
import time

import numpy as np
import pandas as pd
import scipy

from .config import (
    MEAN_CLIP,
    MU_T_LEVELS,
    M_O_LEVELS,
    S_O_LEVELS,
    SCORE_LEVELS,
    PHASES,
    N_PRIOR,
    N_POSTERIOR,
    SEED,
)
from .fault_tree import fault_tree_nodes
from .io import export_results, git_commit, read_input, sha256
from .plotting import plot_results
from .pooling import sample_components, sample_averaged_scores, summarize_pools
from .priors import build_priors
from .summary import summarize_nodes, pooling_comparison
from .updating import posterior_weights, resample_joint, weighted_moments
from .validation import validate_input, validate_run_options


@dataclass
class AnalysisResult:
    """One analysis result, with exported tables and samples retained for inspection.

    Sample rows are Monte Carlo draws; columns follow config.NODES.
    posterior_indices identifies which prior rows became posterior rows.
    weighted_mean/variance are direct likelihood-weighted diagnostics.
    """

    tables: dict[str, pd.DataFrame]
    paths: dict[str, Path]
    prior_samples: np.ndarray
    posterior_samples: np.ndarray
    posterior_weights: np.ndarray
    posterior_indices: np.ndarray
    weighted_mean: np.ndarray
    weighted_variance: np.ndarray

#creates a folder to organize the run sequence
def _create_run(output: Path) -> tuple[Path, str]:
    """Create a timestamped folder, retrying if another run uses the same name."""
    output.mkdir(parents=True, exist_ok=True)
    for _ in range(1000):
        run_stamp = datetime.now().strftime("%Y%m%d_%H%M%S_%f")[:-3]
        path = output / ("run_" + run_stamp)
        try:
            path.mkdir()
            return path, run_stamp
        except FileExistsError:
            time.sleep(0.001)
    raise FileExistsError("Unable to allocate a unique run folder.")

#actual parameter to call analysis code
def run_analysis(
    input_path: str | Path,
    output_dir: str | Path,
    n_prior: int = N_PRIOR,
    n_posterior: int = N_POSTERIOR,
    seed: int = SEED,
) -> AnalysisResult:
    """Execute specification revision 3 using one seeded NumPy PCG64 generator.

    Numerical outputs are reproducible in a pinned Python environment. MATLAB code
    uses different random samplers; identical seeds do not imply identical draws.
    """

    # 1. Validate run options. called in validate.py
    # n_prior/n_posterior are Monte Carlo sample counts, not numbers of raters.
    validate_run_options(n_prior, n_posterior, seed)
    input_path = Path(input_path).resolve()

    # 2. Read the assessment workbook and validate/clean the MATLAB_Input data; including excluding null data points/sets
    raw_input = read_input(input_path)
    assessment_rows, rater_profiles, analysis_settings, excluded_rows = validate_input(
        raw_input
    )

    computed = compute_analysis(rater_profiles, analysis_settings, n_prior, n_posterior, seed)
    return generate_report(input_path, output_dir, assessment_rows, excluded_rows,
                           analysis_settings, computed, n_prior, n_posterior, seed)


def compute_analysis(rater_profiles, analysis_settings, n_prior: int,
                     n_posterior: int, seed: int):
    """Run the existing numerical workflow without generating files."""
    # 3. Convert each (Component, RaterID) profile into a Beta prior.
    rater_profiles = build_priors(rater_profiles, analysis_settings.lambda_phase)

    # 4A. Summarize each component's equal-weight rater mixture for reporting. Isolates each rater profile then combines into one
    component_pools = summarize_pools(rater_profiles)

    # 4B. Generate the component-level prior Monte Carlo samples.
    # For each component and each draw: choose a rater profile with equal weight,
    # component_failures draw p from that profile's Beta distribution, then convert to q = 1 - p.
    rng = np.random.Generator(np.random.PCG64(seed))
    component_failures = sample_components(rater_profiles, n_prior, rng)

    # 5. Propagate the seven component failure-probability samples through the
    # fault tree to create the full system prior, including q_top.
    prior_samples = np.column_stack(
        (component_failures, fault_tree_nodes(component_failures))
    )

    # 6A. Compare every prior q_top sample with the observed binomial test evidence.
    # posterior_weights() assigns higher weight to prior samples that better explain
    # the observed n_test / k_fail result; it does not yet create a new sample set.
    likelihood_weights = posterior_weights(
        prior_samples[:, -1], analysis_settings.n_test, analysis_settings.k_fail
    )

    # 6B. Create posterior Monte Carlo samples by resampling complete prior rows
    # according to those weights. Resampling whole rows preserves joint dependence.
    posterior_samples, posterior_indices, effective_sample_size = resample_joint(
        prior_samples, likelihood_weights, n_posterior, rng
    )

    # 7. Check and summarize the posterior already created in Step 6B.
    # Weighted moments are a direct check; summarize_nodes() reports final statistics.
    weighted_mean, weighted_variance = weighted_moments(
        prior_samples, likelihood_weights
    )
    node_summary = summarize_nodes(
        prior_samples, posterior_samples, analysis_settings.q_req
    )

    # 8. Comparison output only: compare the legacy average-score method
    # with the primary exact-mixture method. These values do not affect the main
    # prior/posterior results; it remains part of the v0.1 output schema.
    average_score_prior = fault_tree_nodes(
        sample_averaged_scores(
            rater_profiles, analysis_settings.lambda_phase, n_prior, rng
        )
    )[:, -1]
    average_score_weights = posterior_weights(
        average_score_prior, analysis_settings.n_test, analysis_settings.k_fail
    )
    average_score_posterior = average_score_prior[
        rng.choice(n_prior, n_posterior, p=average_score_weights)
    ]
    method_comparison = pooling_comparison(
        prior_samples[:, -1],
        posterior_samples[:, -1],
        average_score_prior,
        average_score_posterior,
    )

    return dict(rater_profiles=rater_profiles, component_pools=component_pools,
                prior_samples=prior_samples, posterior_samples=posterior_samples,
                likelihood_weights=likelihood_weights, posterior_indices=posterior_indices,
                effective_sample_size=effective_sample_size,
                weighted_mean=weighted_mean, weighted_variance=weighted_variance,
                node_summary=node_summary, average_score_prior=average_score_prior,
                method_comparison=method_comparison)


def generate_report(input_path, output_dir, assessment_rows, excluded_rows,
                    analysis_settings, computed, n_prior: int,
                    n_posterior: int, seed: int) -> AnalysisResult:
    """Write plots, spreadsheets and metadata from completed calculations."""
    locals_from_result = computed
    rater_profiles = locals_from_result["rater_profiles"]
    component_pools = locals_from_result["component_pools"]
    prior_samples = locals_from_result["prior_samples"]
    posterior_samples = locals_from_result["posterior_samples"]
    likelihood_weights = locals_from_result["likelihood_weights"]
    posterior_indices = locals_from_result["posterior_indices"]
    effective_sample_size = locals_from_result["effective_sample_size"]
    weighted_mean = locals_from_result["weighted_mean"]
    weighted_variance = locals_from_result["weighted_variance"]
    node_summary = locals_from_result["node_summary"]
    average_score_prior = locals_from_result["average_score_prior"]
    method_comparison = locals_from_result["method_comparison"]
    # 9. Create a unique run folder and assemble reproducibility metadata.
    run_dir, run_stamp = _create_run(Path(output_dir).resolve())

    def format_matlab_array(values: tuple) -> str:
        """Format mapping values for RunInfo metadata only; no numerical role."""
        return "[" + " ".join(f"{v:g}" for v in values) + "]"

    run_info = dict(
        RunStamp=run_stamp,
        InputFile=str(input_path),
        OutputFolder=str(run_dir),
        N=int(n_prior),
        Mpost=int(n_posterior),
        n_test=analysis_settings.n_test,
        k_fail=analysis_settings.k_fail,
        q_req=analysis_settings.q_req,
        phase_name=analysis_settings.phase,
        lambda_phase=analysis_settings.lambda_phase,
        InputMode="linear_pool",
        EffectiveSampleSize=effective_sample_size,
        ModelVersion="13",
        Seed=int(seed),
        ScoreLevels=format_matlab_array(SCORE_LEVELS),
        MuTLevels=format_matlab_array(MU_T_LEVELS),
        MOLevels=format_matlab_array(M_O_LEVELS),
        SOLevels=format_matlab_array(S_O_LEVELS),
        PhaseLevels=",".join(PHASES),
        LambdaLevels=format_matlab_array(tuple(PHASES.values())),
        MeanClipMin=MEAN_CLIP[0],
        MeanClipMax=MEAN_CLIP[1],
        PoolingWeights="equal_within_component",
        NInputRows=len(assessment_rows),
        NUsedRows=int(rater_profiles.NUsedRows.sum()),
        NExcludedRows=len(excluded_rows),
        NRaters=int(rater_profiles.RaterID.nunique()),
        NProfiles=len(rater_profiles),
    )
    run_config = dict(
        input_sheet="MATLAB_Input",
        phase=analysis_settings.phase,
        n_test=analysis_settings.n_test,
        k_fail=analysis_settings.k_fail,
        q_req=analysis_settings.q_req,
        n_prior=int(n_prior),
        n_posterior=int(n_posterior),
        seed=int(seed),
        pooling="exact_equal_weight_linear_pool",
        score_levels=list(SCORE_LEVELS),
        mu_t_levels=list(MU_T_LEVELS),
        m_o_levels=list(M_O_LEVELS),
        s_o_levels=list(S_O_LEVELS),
        phase_levels=list(PHASES),
        lambda_levels=list(PHASES.values()),
        lambda_phase=analysis_settings.lambda_phase,
        mean_clip=list(MEAN_CLIP),
        pooling_weights="equal_within_component",
    )
    run_metadata = dict(
        run_info,
        PackageVersion="0.1.0",
        PythonVersion=platform.python_version(),
        NumPyVersion=np.__version__,
        SciPyVersion=scipy.__version__,
        RandomGenerator="PCG64",
        GitCommit=git_commit(Path(__file__).parent),
        InputSHA256=sha256(input_path),
        ExcludedExcelRows=excluded_rows,
        WeightedPosteriorMean=weighted_mean.tolist(),
        WeightedPosteriorVariance=weighted_variance.tolist(),
    )
    tables = dict(
        RunInfo=pd.DataFrame([run_info]),
        RaterParameters=rater_profiles,
        PoolSummary=component_pools,
        NodeSummary=node_summary,
        PoolingComparison=method_comparison,
    )

    # 10. Export figures, tables, run configuration, and metadata.
    plot_results(
        rater_profiles,
        component_pools,
        prior_samples[:, -1],
        posterior_samples[:, -1],
        average_score_prior,
        analysis_settings.n_test,
        analysis_settings.k_fail,
        run_dir / "figures",
    )
    paths = export_results(run_dir, tables, run_config, run_metadata)

    return AnalysisResult(
        tables,
        paths,
        prior_samples,
        posterior_samples,
        likelihood_weights,
        posterior_indices,
        weighted_mean,
        weighted_variance,
    )
