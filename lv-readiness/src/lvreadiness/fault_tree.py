"""Fixed independent seven-component fault tree; MATLAB faultTreeNodes."""

import numpy as np


def fault_tree_nodes(q: np.ndarray) -> np.ndarray:
    """Return design, implementation, operation, top failure samples in order."""
    q = np.asarray(q, dtype=float)
    if q.ndim != 2 or q.shape[1] != 7 or not len(q) or not np.all(np.isfinite(q) & (q >= 0) & (q <= 1)):
        raise ValueError("Expected a nonempty N by 7 array of probabilities in [0, 1].")
    design = 1-(1-q[:, 0])*(1-q[:, 1])
    implementation = 1-(1-q[:, 2])*(1-q[:, 3])*(1-q[:, 4])
    operation = 1-(1-q[:, 5])*(1-q[:, 6])
    top = 1-(1-design)*(1-implementation)*(1-operation)
    return np.column_stack((design, implementation, operation, top))
