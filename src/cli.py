"""Command-line access to the same validated Python pipeline."""

import argparse
import sys

from .config import N_PRIOR, N_POSTERIOR, SEED
from .pipeline import run_analysis


def main(argv: list[str] | None = None) -> int:
    """Run the analysis or return a nonzero status with an actionable error."""
    parser = argparse.ArgumentParser(prog="lvreadiness")
    commands = parser.add_subparsers(dest="command", required=True)
    run_command = commands.add_parser("run", help="Analyze an Excel MATLAB_Input sheet")
    run_command.add_argument("input_path")
    run_command.add_argument("--output", required=True)
    run_command.add_argument("--n-prior", type=int, default=N_PRIOR)
    run_command.add_argument("--n-posterior", type=int, default=N_POSTERIOR)
    run_command.add_argument("--seed", type=int, default=SEED)
    arguments = parser.parse_args(argv)
    # API and CLI use the same pipeline. Exit code 2 reports invalid input or I/O.
    try:
        result = run_analysis(
            arguments.input_path,
            arguments.output,
            arguments.n_prior,
            arguments.n_posterior,
            arguments.seed,
        )
    except (ValueError, OSError) as error:
        print(f"lvreadiness: {error}", file=sys.stderr)
        return 2
    top_summary = result.tables["NodeSummary"].iloc[-1]
    print(f"Prior mean q_top: {top_summary.PriorMean:.10f}")
    print(f"Posterior mean q_top: {top_summary.PostMean:.10f}")
    print(f"Results: {result.paths['results']}")
    return 0
