"""Fixed independent seven-component fault tree; MATLAB faultTreeNodes."""

import numpy as np

from .config import COMPONENTS


def fault_tree_nodes(q: np.ndarray) -> np.ndarray:
    """Propagate an N-by-7 component failure array through the fixed OR tree.

    Input columns are Concept, Design Verification, Manufacturing, Assembly and
    Integration, Impl. Verification, Operation Setup, and Operation Execution.
    Return N-by-4 failure samples: design, implementation, operation, and top.
    The product equations assume independent component priors.
    """
    q = np.asarray(q, dtype=float)
    if (
        q.ndim != 2
        or q.shape[1] != len(COMPONENTS)
        or not len(q)
        or not np.all(np.isfinite(q) & (q >= 0) & (q <= 1))
    ):
        raise ValueError("Expected a nonempty N by 7 array of probabilities in [0, 1].")
    # Unpack views in config.COMPONENTS order. Each vector has one probability
    # per Monte Carlo draw; these are risk estimates, not pass/fail outcomes.
    (
        concept,
        design_verification,
        manufacturing,
        integration,
        implementation_verification,
        operation_setup,
        operation_execution,
    ) = q.T
    # An OR gate fails unless all its inputs succeed: q_gate = 1 - product(1-q).
    design_failure = 1 - (1 - concept) * (1 - design_verification)
    implementation_failure = (
        1 - (1 - manufacturing) * (1 - integration) * (1 - implementation_verification)
    )
    operation_failure = 1 - (1 - operation_setup) * (1 - operation_execution)
    top_failure = 1 - (1 - design_failure) * (1 - implementation_failure) * (
        1 - operation_failure
    )
    return np.column_stack(
        (design_failure, implementation_failure, operation_failure, top_failure)
    )
