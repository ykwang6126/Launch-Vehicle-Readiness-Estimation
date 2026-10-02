"""Command-line access to the same validated Python pipeline."""

import argparse
import sys

from .config import N_PRIOR, N_POSTERIOR, SEED
from .pipeline import run_analysis


def main(argv: list[str] | None = None) -> int:
    """Run the analysis or return a nonzero status with an actionable error."""
    parser = argparse.ArgumentParser(prog="lvreadiness")
    sub = parser.add_subparsers(dest="command", required=True)
    run = sub.add_parser("run", help="Analyze an Excel MATLAB_Input sheet")
    run.add_argument("input_path")
    run.add_argument("--output", required=True)
    run.add_argument("--n-prior", type=int, default=N_PRIOR)
    run.add_argument("--n-posterior", type=int, default=N_POSTERIOR)
    run.add_argument("--seed", type=int, default=SEED)
    args = parser.parse_args(argv)
    try:
        result = run_analysis(args.input_path, args.output, args.n_prior, args.n_posterior, args.seed)
    except (ValueError, OSError) as exc:
        print(f"lvreadiness: {exc}", file=sys.stderr)
        return 2
    row = result.tables['NodeSummary'].iloc[-1]
    print(f"Prior mean q_top: {row.PriorMean:.10f}")
    print(f"Posterior mean q_top: {row.PostMean:.10f}")
    print(f"Results: {result.paths['results']}")
    return 0
