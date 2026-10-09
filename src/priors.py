"""Success-space parameters: paper equations 5–11, specification section 4."""

import numpy as np
import pandas as pd

from .config import MEAN_CLIP, MU_T_LEVELS, M_O_LEVELS, S_O_LEVELS, SCORE_LEVELS


def parameters(
    z_t: np.ndarray | float, z_o: np.ndarray | float, lambda_phase: float
) -> dict:
    """Convert T/O mean scores into success-Beta parameters for one or many profiles.

    z_t and z_o are category averages on 0–4, including fractional averages.
    lambda_phase is the lifecycle strength factor. Returned keys match the
    RaterParameters columns; alpha_p and beta_p describe success p, not failure q.
    """
    z_t, z_o = np.asarray(z_t, dtype=float), np.asarray(z_o, dtype=float)
    if not all(np.all(np.isfinite(z) & (z >= 0) & (z <= 4)) for z in (z_t, z_o)):
        raise ValueError("Category scores must be finite and within [0, 4].")
    if not np.isfinite(lambda_phase) or lambda_phase <= 0:
        raise ValueError("lambda_phase must be positive and finite.")
    # Linear interpolation preserves fractional averages instead of rounding them.
    mu_t = np.interp(z_t, SCORE_LEVELS, MU_T_LEVELS)
    m_o = np.interp(z_o, SCORE_LEVELS, M_O_LEVELS)
    s_o = np.interp(z_o, SCORE_LEVELS, S_O_LEVELS)
    # Organization changes both the mean and the strength. Clipping keeps the
    # success mean strictly between 0 and 1 so both Beta parameters stay positive.
    mu = np.clip(mu_t * m_o, *MEAN_CLIP)
    strength = s_o * lambda_phase
    return dict(
        mu_T=mu_t,
        m_O=m_o,
        s_O=s_o,
        mu=mu,
        strength=strength,
        alpha_p=mu * strength,
        beta_p=(1 - mu) * strength,
    )


def build_priors(profiles: pd.DataFrame, lambda_phase: float) -> pd.DataFrame:
    """Attach Beta parameters and equal-within-component weights."""

    # Work on a copy so adding columns does not modify the input table.
    rater_priors = profiles.copy()

    # Pass each profile's Z_T and Z_O values, together with lambda_phase,
    # to the helper that calculates the distribution parameters.
    # to_numpy() converts the pandas columns into NumPy arrays.
    # items() lets us iterate over each name and its corresponding values.
    for parameter_name, parameter_values in parameters(
        rater_priors.Z_T.to_numpy(), rater_priors.Z_O.to_numpy(), lambda_phase
    ).items():
        # Add a column (or replace an existing one) with these values.
        # Each value corresponds to a row in the rater profile table.
        rater_priors[parameter_name] = parameter_values

    # transform("size") repeats the number of profiles for each component.
    # A rater with more indicators still receives the same weight as other raters.
    #
    # groupby("Component") groups rows belonging to the same component.
    # transform("size") returns a count aligned with every original row.
    # Taking 1 / count gives every profile in that component equal weight.
    #
    # Example: three profiles for a component each receive weight 1/3.
    # These weights are used later to randomly select a rater profile.
    rater_priors["WeightWithinComponent"] = 1 / rater_priors.groupby(
        "Component"
    ).Component.transform("size")

    # Return the profiles with their calculated parameters and weights.
    return rater_priors
