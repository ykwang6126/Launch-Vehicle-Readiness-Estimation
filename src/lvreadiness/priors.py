"""Success-space parameters: paper equations 5–11, specification section 4."""

import numpy as np
import pandas as pd

from .config import MEAN_CLIP, MU_T_LEVELS, M_O_LEVELS, S_O_LEVELS, SCORE_LEVELS


def parameters(z_t: np.ndarray | float, z_o: np.ndarray | float, lambda_phase: float) -> dict:
    """Interpolate unrounded scores and apply the paper's strength equation."""
    z_t, z_o = np.asarray(z_t, dtype=float), np.asarray(z_o, dtype=float)
    if not all(np.all(np.isfinite(z) & (z >= 0) & (z <= 4)) for z in (z_t, z_o)):
        raise ValueError("Category scores must be finite and within [0, 4].")
    if not np.isfinite(lambda_phase) or lambda_phase <= 0:
        raise ValueError("lambda_phase must be positive and finite.")
    mu_t = np.interp(z_t, SCORE_LEVELS, MU_T_LEVELS)
    m_o = np.interp(z_o, SCORE_LEVELS, M_O_LEVELS)
    s_o = np.interp(z_o, SCORE_LEVELS, S_O_LEVELS)
    mu = np.clip(mu_t * m_o, *MEAN_CLIP)
    strength = s_o * lambda_phase
    return dict(mu_T=mu_t, m_O=m_o, s_O=s_o, mu=mu, strength=strength,
                alpha_p=mu*strength, beta_p=(1-mu)*strength)


def build_priors(profiles: pd.DataFrame, lambda_phase: float) -> pd.DataFrame:
    """Attach Beta parameters and equal-within-component weights."""
    result = profiles.copy()
    for key, value in parameters(result.Z_T.to_numpy(), result.Z_O.to_numpy(), lambda_phase).items():
        result[key] = value
    result["WeightWithinComponent"] = 1 / result.groupby("Component").Component.transform("size")
    return result
