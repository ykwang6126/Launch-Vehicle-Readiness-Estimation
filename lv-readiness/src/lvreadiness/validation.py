"""Validate run options and convert MATLAB_Input rows into rater profiles."""

import re
import warnings
from numbers import Integral

import numpy as np
import pandas as pd

from .config import BRANCHES, COMPONENTS, PHASES, Settings


class InputError(ValueError):
    """Raised when run options or assessment data violate the input contract."""


def text(value: object) -> str:
    """Normalize blank cells and surrounding whitespace without inventing values."""
    return "" if value is None or pd.isna(value) else str(value).strip()


def canonical_component(value: object) -> str:
    """Map accepted component aliases to the canonical component names."""

    # Normalize capitalization/spacing, then translate approved aliases only.
    key = re.sub(r"\s+", " ", text(value).replace("\xa0", " ")).lower()
    aliases = {c.lower(): c for c in COMPONENTS}
    aliases.update({"integration": COMPONENTS[3], "assembly & integration": COMPONENTS[3],
                    "assembly/integration": COMPONENTS[3], "design concept": COMPONENTS[0],
                    "implementation verification": COMPONENTS[4], "impl verification": COMPONENTS[4],
                    "operational setup": COMPONENTS[5], "operational execution": COMPONENTS[6]})
    if key not in aliases:
        raise InputError(f"Unknown Component: {value!r}")
    return aliases[key]


def validate_runtime(n_prior: int, n_posterior: int, seed: int) -> None:
    """Validate Monte Carlo sample counts and random seed (not assessment data)."""

    # Sample counts must be positive integers; the seed may be zero or greater.
    for key, val, lower in (("n_prior", n_prior, 1), ("n_posterior", n_posterior, 1), ("seed", seed, 0)):
        if isinstance(val, bool) or not isinstance(val, Integral) or val < lower:
            raise InputError(f"{key} must be an integer >= {lower}.")


def validate_evidence(n: int, k: int) -> None:
    """Validate binomial test evidence before the Bayesian update."""
    if any(isinstance(v, bool) or not isinstance(v, Integral) for v in (n, k)) or not 0 <= k <= n:
        raise InputError("Test counts must be integers satisfying 0 <= k_fail <= n_test.")


def validate_input(frame: pd.DataFrame) -> tuple[pd.DataFrame, pd.DataFrame, Settings, list[int]]:
    """Validate MATLAB_Input and build one T/O score profile per component/rater."""

    # 1. Check that the required columns and one lifecycle-phase column exist.
    required = {"Branch", "Component", "Indicator", "Cat", "Z", "RaterID", "n_test", "k_fail", "q_req"}
    missing = required - set(frame.columns)
    if missing:
        raise InputError(f"MATLAB_Input missing columns: {', '.join(sorted(missing))}")
    phase_cols = [c for c in frame.columns if re.sub(r"[ _.]", "", str(c).lower()) in
                  ("lifecyclephase", "lifecylcephase")]
    if len(phase_cols) != 1:
        raise InputError("Exactly one Lifecycle Phase column is required.")

    # 2. Require one supported lifecycle phase across the workbook.
    phases = {text(v).upper() for v in frame[phase_cols[0]] if text(v)}
    if len(phases) != 1 or not phases <= PHASES.keys():
        raise InputError("Lifecycle Phase must contain one supported, consistent phase.")

    # Helper: settings may appear once or repeat identically down the sheet.
    # Collect nonblank values and require exactly one consistent numeric value.
    def scalar(name: str) -> float:
        vals = []
        for i, v in enumerate(frame[name], 2):
            if text(v):
                try:
                    number = float(v)
                except (ValueError, TypeError):
                    raise InputError(f"Invalid {name} at Excel row {i}.") from None
                if not np.isfinite(number):
                    raise InputError(f"Nonfinite {name} at Excel row {i}.")
                vals.append(number)
        if not vals or len(set(vals)) != 1:
            raise InputError(f"{name} must contain one consistent value.")
        return vals[0]

    # 3. Validate top-event test settings and package them into Settings.
    n, k, threshold = (scalar(c) for c in ("n_test", "k_fail", "q_req"))
    if not n.is_integer() or not k.is_integer() or not 0 <= k <= n:
        raise InputError("Test counts must be integers satisfying 0 <= k_fail <= n_test.")
    if not 0 <= threshold <= 1:
        raise InputError("q_req must lie in [0, 1].")
    settings = Settings(next(iter(phases)), int(n), int(k), threshold)

    # 4. Prepare assessment rows and preserve original Excel row numbers.
    df = frame.copy()
    df["SourceRow"] = np.arange(2, len(df) + 2)
    if "Status" not in df:
        df["Status"] = ""

    # Ignore fully blank assessment rows but keep any row containing assessment data.
    keep = df[["Branch", "Component", "Indicator", "Cat", "Z", "RaterID", "Status"]].apply(
        lambda col: col.map(text).ne("")).any(axis=1)
    df = df.loc[keep].copy()
    if df.empty:
        raise InputError("MATLAB_Input has no assessment rows.")

    # 5. Normalize text fields and reject missing IDs/labels needed to identify a score.
    for col in ("Branch", "Component", "Indicator", "Cat", "RaterID", "Status"):
        df[col] = df[col].map(text)
    for _, row in df.iterrows():
        if any(not row[c] for c in ("Branch", "Component", "Indicator", "RaterID")):
            raise InputError(f"Missing Branch, Component, Indicator or RaterID at Excel row {row.SourceRow}.")

    # 6. Normalize component/category labels and validate T/O categories.
    df["Component"] = df.Component.map(canonical_component)
    df["Cat"] = df.Cat.str.upper()
    bad_cat = ~df.Cat.isin(["T", "O"])
    if bad_cat.any():
        raise InputError(f"Invalid Cat at Excel rows {df.loc[bad_cat, 'SourceRow'].tolist()}.")

    # 7. Handle "Unable to assess" and validate all remaining 0-4 scores.
    df["Unassessed"] = df.Status.str.casefold().eq("unable to assess")
    if (df.Unassessed & df.Z.map(text).ne("")).any():
        raise InputError("Rows marked Unable to assess must have blank Z.")
    df["Z"] = pd.to_numeric(df.Z, errors="coerce")
    bad = ~df.Unassessed & (~np.isfinite(df.Z) | ~df.Z.between(0, 4))
    if bad.any():
        raise InputError(f"Invalid Z at Excel rows {df.loc[bad, 'SourceRow'].tolist()}.")

    # 8. Build one profile per (Component, RaterID).
    # Within each profile, average retained T scores and O scores separately.
    # Each profile must retain at least one scored T indicator and one scored O indicator.
    profiles = []
    excluded = df.loc[df.Unassessed, "SourceRow"].astype(int).tolist()
    for component, branch in zip(COMPONENTS, BRANCHES):
        group = df.loc[df.Component.eq(component)]
        if group.empty:
            raise InputError(f"Missing required component: {component}.")
        if not group.Branch.str.casefold().eq(branch.casefold()).all():
            raise InputError(f"Wrong Branch for {component}.")
        for rater, rows in group.groupby("RaterID", sort=False):
            if rows.Indicator.str.casefold().duplicated().any():
                raise InputError(f"Duplicate indicator within {component} / {rater}.")
            used = rows.loc[~rows.Unassessed]
            if set(used.Cat) != {"T", "O"}:
                raise InputError(f"{component} / {rater} needs at least one scored T and O indicator.")
            profiles.append(dict(Branch=branch, Component=component, RaterID=rater,
                                 Z_T=float(used.loc[used.Cat.eq('T'), 'Z'].mean()),
                                 Z_O=float(used.loc[used.Cat.eq('O'), 'Z'].mean()),
                                 NInputRows=len(rows), NUsedRows=len(used), NExcludedRows=len(rows)-len(used)))

    # 9. Report exclusions and return both cleaned rows and profile-level model inputs.
    if excluded:
        warnings.warn(f"Excluded Unable to assess indicators at Excel rows {excluded}.", UserWarning, stacklevel=2)
    return df, pd.DataFrame(profiles), settings, excluded
