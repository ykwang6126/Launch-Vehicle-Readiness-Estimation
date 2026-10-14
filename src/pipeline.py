"""One workflow shared by the Python API and command-line entry point."""

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
    Settings,
    TOP_NODE_INDEX,
    TREE_TOP_INDEX,
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


@dataclass
class ComputedAnalysis:
    """Numerical results passed to reporting, before any files are written.

    Prior/posterior sample columns follow config.NODES; rows are possible sets
    of failure probabilities. Weights and indices refer to prior sample rows.
    Tables retain the workbook column names for MATLAB compatibility.
    """

    rater_profiles: pd.DataFrame
    component_pools: pd.DataFrame
    prior_samples: np.ndarray
    posterior_samples: np.ndarray
    likelihood_weights: np.ndarray
    posterior_indices: np.ndarray
    effective_sample_size: float
    weighted_mean: np.ndarray
    weighted_variance: np.ndarray
    node_summary: pd.DataFrame
    average_score_prior: np.ndarray
    method_comparison: pd.DataFrame


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

    # 1. Validate run options in validation.py.
    # n_prior/n_posterior are Monte Carlo sample counts, not numbers of raters.
    validate_run_options(n_prior, n_posterior, seed)
    input_path = Path(input_path).resolve()

    # 2. Validate workbook data; only explicitly unassessed indicators are excluded.
    raw_input = read_input(input_path)
    assessment_rows, rater_profiles, analysis_settings, excluded_rows = validate_input(
        raw_input
    )

    computed = compute_analysis(
        rater_profiles, analysis_settings, n_prior, n_posterior, seed
    )
    return generate_report(
        input_path, output_dir, assessment_rows, excluded_rows,
        analysis_settings, computed, n_prior, n_posterior, seed,
    )


def compute_analysis(
    rater_profiles: pd.DataFrame,
    analysis_settings: Settings,
    n_prior: int,
    n_posterior: int,
    seed: int,
) -> ComputedAnalysis:
    """Calculate priors, posterior, summaries, and comparison without writing files.

    Profiles are validated rows with Component, RaterID, Branch, Z_T, Z_O and
    input/used/excluded row counts. Samples have shape (draw count, len(NODES)).
    One random stream is consumed in the original order to preserve seeded runs.
    """
    # 3. Convert each (Component, RaterID) profile into a Beta prior.
    rater_profiles = build_priors(rater_profiles, analysis_settings.lambda_phase)

    # 4A. Report mixture statistics, retaining uncertainty and rater disagreement.
    component_pools = summarize_pools(rater_profiles)

    # 4B. Generate the component-level prior Monte Carlo samples.
    # For each component and each draw: choose a rater profile with equal weight,
    # draw success p from that profile's Beta, then convert to failure q = 1 - p.
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
        prior_samples[:, TOP_NODE_INDEX],
        analysis_settings.n_test,
        analysis_settings.k_fail,
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
    )[:, TREE_TOP_INDEX]
    average_score_weights = posterior_weights(
        average_score_prior, analysis_settings.n_test, analysis_settings.k_fail
    )
    average_score_posterior = average_score_prior[
        rng.choice(n_prior, n_posterior, p=average_score_weights)
    ]
    method_comparison = pooling_comparison(
        prior_samples[:, TOP_NODE_INDEX],
        posterior_samples[:, TOP_NODE_INDEX],
        average_score_prior,
        average_score_posterior,
    )

    return ComputedAnalysis(
        rater_profiles=rater_profiles,
        component_pools=component_pools,
        prior_samples=prior_samples,
        posterior_samples=posterior_samples,
        likelihood_weights=likelihood_weights,
        posterior_indices=posterior_indices,
        effective_sample_size=effective_sample_size,
        weighted_mean=weighted_mean,
        weighted_variance=weighted_variance,
        node_summary=node_summary,
        average_score_prior=average_score_prior,
        method_comparison=method_comparison,
    )


def _format_matlab_array(values: tuple) -> str:
    """Format mapping values for RunInfo metadata only; no numerical role."""
    return "[" + " ".join(f"{v:g}" for v in values) + "]"


def _build_run_info(
    input_path: Path,
    run_dir: Path,
    run_stamp: str,
    assessment_rows: pd.DataFrame,
    excluded_rows: list[int],
    analysis_settings: Settings,
    computed: ComputedAnalysis,
    n_prior: int,
    n_posterior: int,
    seed: int,
) -> dict[str, object]:
    """Build the existing RunInfo schema from settings and assessment counts."""
    rater_profiles = computed.rater_profiles
    return dict(
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
        EffectiveSampleSize=computed.effective_sample_size,
        ModelVersion="13",
        Seed=int(seed),
        ScoreLevels=_format_matlab_array(SCORE_LEVELS),
        MuTLevels=_format_matlab_array(MU_T_LEVELS),
        MOLevels=_format_matlab_array(M_O_LEVELS),
        SOLevels=_format_matlab_array(S_O_LEVELS),
        PhaseLevels=",".join(PHASES),
        LambdaLevels=_format_matlab_array(tuple(PHASES.values())),
        MeanClipMin=MEAN_CLIP[0],
        MeanClipMax=MEAN_CLIP[1],
        PoolingWeights="equal_within_component",
        NInputRows=len(assessment_rows),
        NUsedRows=int(rater_profiles.NUsedRows.sum()),
        NExcludedRows=len(excluded_rows),
        NRaters=int(rater_profiles.RaterID.nunique()),
        NProfiles=len(rater_profiles),
    )


def _build_run_config(
    analysis_settings: Settings,
    n_prior: int,
    n_posterior: int,
    seed: int,
) -> dict[str, object]:
    """Record the resolved settings and mapping constants used by this run."""
    return dict(
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


def _build_run_metadata(
    run_info: dict[str, object],
    input_path: Path,
    excluded_rows: list[int],
    computed: ComputedAnalysis,
) -> dict[str, object]:
    """Add provenance and direct weighted diagnostics to the run information."""
    return dict(
        run_info,
        PackageVersion="0.1.0",
        PythonVersion=platform.python_version(),
        NumPyVersion=np.__version__,
        SciPyVersion=scipy.__version__,
        RandomGenerator="PCG64",
        GitCommit=git_commit(Path(__file__).parent),
        InputSHA256=sha256(input_path),
        ExcludedExcelRows=excluded_rows,
        WeightedPosteriorMean=computed.weighted_mean.tolist(),
        WeightedPosteriorVariance=computed.weighted_variance.tolist(),
    )


def generate_report(
    input_path: Path,
    output_dir: str | Path,
    assessment_rows: pd.DataFrame,
    excluded_rows: list[int],
    analysis_settings: Settings,
    computed: ComputedAnalysis,
    n_prior: int,
    n_posterior: int,
    seed: int,
) -> AnalysisResult:
    """Export completed calculations without drawing any new random samples.

    assessment_rows retains SourceRow and Unassessed for tracing input counts.
    Report field names and table ordering intentionally follow MATLAB v13.
    """
    # Allocate output only after validation and numerical computation succeed.
    run_dir, run_stamp = _create_run(Path(output_dir).resolve())
    run_info = _build_run_info(
        input_path, run_dir, run_stamp, assessment_rows, excluded_rows,
        analysis_settings, computed, n_prior, n_posterior, seed,
    )
    run_config = _build_run_config(analysis_settings, n_prior, n_posterior, seed)
    run_metadata = _build_run_metadata(run_info, input_path, excluded_rows, computed)
    tables = dict(
        RunInfo=pd.DataFrame([run_info]),
        RaterParameters=computed.rater_profiles,
        PoolSummary=computed.component_pools,
        NodeSummary=computed.node_summary,
        PoolingComparison=computed.method_comparison,
    )

    # 10. Export figures, tables, run configuration, and metadata.
    plot_results(
        computed.rater_profiles,
        computed.component_pools,
        computed.prior_samples[:, TOP_NODE_INDEX],
        computed.posterior_samples[:, TOP_NODE_INDEX],
        computed.average_score_prior,
        analysis_settings.n_test,
        analysis_settings.k_fail,
        run_dir / "figures",
    )
    paths = export_results(run_dir, tables, run_config, run_metadata)

    return AnalysisResult(
        tables,
        paths,
        computed.prior_samples,
        computed.posterior_samples,
        computed.likelihood_weights,
        computed.posterior_indices,
        computed.weighted_mean,
        computed.weighted_variance,
    )
