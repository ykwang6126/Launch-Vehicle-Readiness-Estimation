"""Fixed independent seven-component fault tree; MATLAB faultTreeNodes."""

import numpy as np


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
        or q.shape[1] != 7
        or not len(q)
        or not np.all(np.isfinite(q) & (q >= 0) & (q <= 1))
    ):
        raise ValueError("Expected a nonempty N by 7 array of probabilities in [0, 1].")
    # An OR gate fails unless all its inputs succeed: q_gate = 1 - product(1-q).
    design_failure = 1 - (1 - q[:, 0]) * (1 - q[:, 1])
    implementation_failure = 1 - (1 - q[:, 2]) * (1 - q[:, 3]) * (1 - q[:, 4])
    operation_failure = 1 - (1 - q[:, 5]) * (1 - q[:, 6])
    top_failure = 1 - (1 - design_failure) * (1 - implementation_failure) * (
        1 - operation_failure
    )
    return np.column_stack(
        (design_failure, implementation_failure, operation_failure, top_failure)
    )
