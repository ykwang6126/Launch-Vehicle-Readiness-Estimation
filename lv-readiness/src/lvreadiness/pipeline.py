"""One workflow shared by the Python API and command-line entry point."""

from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
import platform
import time

import numpy as np
import pandas as pd
import scipy

from .config import (MEAN_CLIP, MU_T_LEVELS, M_O_LEVELS, S_O_LEVELS, SCORE_LEVELS,
                     PHASES, N_PRIOR, N_POSTERIOR, SEED)
from .fault_tree import fault_tree_nodes
from .io import export_results, git_commit, read_input, sha256
from .plotting import plot_results
from .pooling import sample_components, sample_averaged_scores, summarize_pools
from .priors import build_priors
from .summary import summarize_nodes, pooling_comparison
from .updating import posterior_weights, resample_joint, weighted_moments
from .validation import validate_input, validate_runtime


@dataclass
class AnalysisResult:
    """Tables, paths and joint samples for subsequent diagnostics and testing."""

    tables: dict[str, pd.DataFrame]
    paths: dict[str, Path]
    prior_samples: np.ndarray
    posterior_samples: np.ndarray
    posterior_weights: np.ndarray
    posterior_indices: np.ndarray
    weighted_mean: np.ndarray
    weighted_variance: np.ndarray


def _create_run(output: Path) -> tuple[Path, str]:
    output.mkdir(parents=True, exist_ok=True)
    for _ in range(1000):
        stamp = datetime.now().strftime("%Y%m%d_%H%M%S_%f")[:-3]
        path = output / ("run_"+stamp)
        try:
            path.mkdir()
            return path, stamp
        except FileExistsError:
            time.sleep(.001)
    raise FileExistsError("Unable to allocate a unique run folder.")


def run_analysis(input_path: str | Path, output_dir: str | Path,
                 n_prior: int = N_PRIOR, n_posterior: int = N_POSTERIOR,
                 seed: int = SEED) -> AnalysisResult:
    """Execute specification revision 3 using one seeded NumPy PCG64 generator.

    Numerical outputs are reproducible in a pinned Python environment. MATLAB
    uses different random samplers; identical seeds do not imply identical draws.
    """

    # 1. Validate run options.
    # n_prior/n_posterior are Monte Carlo sample counts, not numbers of raters.
    validate_runtime(n_prior, n_posterior, seed)
    input_path = Path(input_path).resolve()

    # 2. Read the assessment workbook and validate/clean the MATLAB_Input data.
    raw_input = read_input(input_path)
    cleaned, profiles, settings, excluded = validate_input(raw_input)

    # 3. Convert each (Component, RaterID) profile into a Beta prior.
    profiles = build_priors(profiles, settings.lambda_phase)

    # 4A. Summarize each component's equal-weight rater mixture for reporting.
    pools = summarize_pools(profiles)

    # 4B. Generate the component-level prior Monte Carlo samples.
    # For each component and each draw: choose a rater profile with equal weight,
    # draw p from that profile's Beta distribution, then convert to q = 1 - p.
    rng = np.random.Generator(np.random.PCG64(seed))
    basic = sample_components(profiles, n_prior, rng)

    # 5. Propagate the seven component failure-probability samples through the
    # fault tree to create the full system prior, including q_top.
    prior = np.column_stack((basic, fault_tree_nodes(basic)))

    # 6A. Compare every prior q_top sample with the observed binomial test evidence.
    # posterior_weights() assigns higher weight to prior samples that better explain
    # the observed n_test / k_fail result; it does not yet create a new sample set.
    weights = posterior_weights(prior[:, -1], settings.n_test, settings.k_fail)

    # 6B. Create posterior Monte Carlo samples by resampling complete prior rows
    # according to those weights. Resampling whole rows preserves joint dependence.
    posterior, indices, ess = resample_joint(prior, weights, n_posterior, rng)

    # 7. Check and summarize the posterior already created in Step 6B.
    # Weighted moments are a direct check; summarize_nodes() reports final statistics.
    weighted_mean, weighted_variance = weighted_moments(prior, weights)
    summary = summarize_nodes(prior, posterior, settings.q_req)

    # 8. TEMPORARY VERIFICATION ONLY: compare the legacy average-score method
    # with the primary exact-mixture method. These values do not affect the main
    # prior/posterior results. Remove this comparison before official deployment.
    legacy = fault_tree_nodes(sample_averaged_scores(profiles, settings.lambda_phase, n_prior, rng))[:, -1]
    legacy_weights = posterior_weights(legacy, settings.n_test, settings.k_fail)
    legacy_post = legacy[rng.choice(n_prior, n_posterior, p=legacy_weights)]
    comparison = pooling_comparison(prior[:, -1], posterior[:, -1], legacy, legacy_post)

    # 9. Create a unique run folder and assemble reproducibility metadata.
    run_dir, stamp = _create_run(Path(output_dir).resolve())

    def format_matlab_array(values: tuple) -> str:
        """Format mapping values for RunInfo metadata only; no numerical role."""
        return '['+' '.join(f'{v:g}' for v in values)+']'

    info = dict(RunStamp=stamp, InputFile=str(input_path), OutputFolder=str(run_dir),
                N=int(n_prior), Mpost=int(n_posterior), n_test=settings.n_test, k_fail=settings.k_fail,
                q_req=settings.q_req, phase_name=settings.phase, lambda_phase=settings.lambda_phase,
                InputMode="linear_pool", EffectiveSampleSize=ess, ModelVersion="13", Seed=int(seed),
                ScoreLevels=format_matlab_array(SCORE_LEVELS), MuTLevels=format_matlab_array(MU_T_LEVELS),
                MOLevels=format_matlab_array(M_O_LEVELS), SOLevels=format_matlab_array(S_O_LEVELS),
                PhaseLevels=','.join(PHASES), LambdaLevels=format_matlab_array(tuple(PHASES.values())),
                MeanClipMin=MEAN_CLIP[0], MeanClipMax=MEAN_CLIP[1], PoolingWeights="equal_within_component",
                NInputRows=len(cleaned), NUsedRows=int(profiles.NUsedRows.sum()),
                NExcludedRows=len(excluded), NRaters=int(profiles.RaterID.nunique()), NProfiles=len(profiles))
    config = dict(input_sheet="MATLAB_Input", phase=settings.phase, n_test=settings.n_test,
                  k_fail=settings.k_fail, q_req=settings.q_req, n_prior=int(n_prior), n_posterior=int(n_posterior),
                  seed=int(seed), pooling="exact_equal_weight_linear_pool", score_levels=list(SCORE_LEVELS),
                  mu_t_levels=list(MU_T_LEVELS), m_o_levels=list(M_O_LEVELS), s_o_levels=list(S_O_LEVELS),
                  phase_levels=list(PHASES), lambda_levels=list(PHASES.values()), lambda_phase=settings.lambda_phase,
                  mean_clip=list(MEAN_CLIP), pooling_weights="equal_within_component")
    metadata = dict(info, PackageVersion="0.1.0", PythonVersion=platform.python_version(),
                    NumPyVersion=np.__version__, SciPyVersion=scipy.__version__, RandomGenerator="PCG64",
                    GitCommit=git_commit(Path(__file__).parent), InputSHA256=sha256(input_path),
                    ExcludedExcelRows=excluded, WeightedPosteriorMean=weighted_mean.tolist(),
                    WeightedPosteriorVariance=weighted_variance.tolist())
    tables = dict(RunInfo=pd.DataFrame([info]), RaterParameters=profiles, PoolSummary=pools,
                  NodeSummary=summary, PoolingComparison=comparison)

    # 10. Export figures, tables, run configuration, and metadata.
    plot_results(profiles, pools, prior[:, -1], posterior[:, -1], legacy,
                 settings.n_test, settings.k_fail, run_dir/"figures")
    paths = export_results(run_dir, tables, config, metadata)

    return AnalysisResult(tables, paths, prior, posterior, weights, indices, weighted_mean, weighted_variance)
