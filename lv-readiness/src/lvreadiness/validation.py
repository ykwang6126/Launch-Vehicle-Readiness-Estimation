"""Validate run options and convert MATLAB_Input rows into rater profiles."""

import re
import warnings
from numbers import Integral

import numpy as np
import pandas as pd

from .config import BRANCHES, COMPONENTS, PHASES, Settings


class InputError(ValueError):
    """Custom validation error raised when user input violates the package contract.

    The class does not store a list of all possible errors. Each `raise InputError(...)`
    creates one error object carrying the specific message for that failure.
    """


def normalize_text(value: object) -> str:
    """Convert an Excel cell to clean text for comparison.

    Blank/NaN cells become "". Other values become strings with leading and
    trailing whitespace removed. This does not change the underlying meaning.
    """
    return "" if value is None or pd.isna(value) else str(value).strip()


def canonical_component(value: object) -> str:
    """Map accepted component aliases to one canonical component name.

    Example: "Integration" and "Assembly & Integration" are normalized to
    the package's standard name "Assembly and Integration".
    """

    # Normalize capitalization and repeated/extra spaces before alias lookup.
    key = re.sub(r"\s+", " ", normalize_text(value).replace("\xa0", " ")).lower()

    # Start with the seven official component names, then add approved aliases.
    aliases = {c.lower(): c for c in COMPONENTS}
    aliases.update({"integration": COMPONENTS[3], "assembly & integration": COMPONENTS[3],
                    "assembly/integration": COMPONENTS[3], "design concept": COMPONENTS[0],
                    "implementation verification": COMPONENTS[4], "impl verification": COMPONENTS[4],
                    "operational setup": COMPONENTS[5], "operational execution": COMPONENTS[6]})

    if key not in aliases:
        raise InputError(f"Unknown Component: {value!r}")
    return aliases[key]


def validate_run_options(n_prior: int, n_posterior: int, seed: int) -> None:
    """Check run-time Monte Carlo options before the analysis starts.

    This validates how the program is run, not the Excel assessment data:
    n_prior and n_posterior must be positive integer sample counts, and seed
    must be a nonnegative integer.
    """

    for key, val, lower in (("n_prior", n_prior, 1), ("n_posterior", n_posterior, 1), ("seed", seed, 0)):
        if isinstance(val, bool) or not isinstance(val, Integral) or val < lower:
            raise InputError(f"{key} must be an integer >= {lower}.")


def validate_evidence(n: int, k: int) -> None:
    """Check binomial test counts used by the Bayesian update.

    n is the number of tests and k is the number of observed failures.
    Valid evidence requires integer counts with 0 <= k <= n.
    The function returns nothing; successful return simply means the values passed.
    """
    if any(isinstance(v, bool) or not isinstance(v, Integral) for v in (n, k)) or not 0 <= k <= n:
        raise InputError("Test counts must be integers satisfying 0 <= k_fail <= n_test.")


def validate_input(raw_input: pd.DataFrame) -> tuple[pd.DataFrame, pd.DataFrame, Settings, list[int]]:
    """Validate MATLAB_Input and build one T/O score profile per component/rater."""

    # 1. Check required columns.
    required = {"Branch", "Component", "Indicator", "Cat", "Z", "RaterID", "n_test", "k_fail", "q_req"}
    missing = required - set(raw_input.columns)
    if missing:
        raise InputError(f"MATLAB_Input missing columns: {', '.join(sorted(missing))}")

    # Accept the current header plus the historical misspelling used in older workbooks.
    phase_columns = [column for column in raw_input.columns
                     if re.sub(r"[ _.]", "", str(column).lower()) in
                     ("lifecyclephase", "lifecylcephase")]
    if len(phase_columns) != 1:
        raise InputError("Exactly one Lifecycle Phase column is required.")

    # 2. Read the lifecycle phase.
    # A workbook represents one lifecycle phase. The value may appear once or be
    # repeated down the column; blanks are ignored and repeated values must agree.
    phase_column = phase_columns[0]
    entered_phases = [
        normalize_text(value).upper()
        for value in raw_input[phase_column]
        if normalize_text(value)
    ]
    unique_phases = set(entered_phases)

    if len(unique_phases) != 1 or not unique_phases <= PHASES.keys():
        raise InputError("Lifecycle Phase must contain one supported, consistent phase.")
    lifecycle_phase = next(iter(unique_phases))

    # Helper for n_test, k_fail, and q_req.
    # Each setting may appear once or repeat identically down the sheet. This
    # function ignores blanks, converts entered values to numbers, and rejects
    # missing, nonnumeric, nonfinite, or conflicting values.
    def read_consistent_setting(column_name: str) -> float:
        values = []
        for excel_row, raw_value in enumerate(raw_input[column_name], 2):
            if normalize_text(raw_value):
                try:
                    number = float(raw_value)
                except (ValueError, TypeError):
                    raise InputError(f"Invalid {column_name} at Excel row {excel_row}.") from None
                if not np.isfinite(number):
                    raise InputError(f"Nonfinite {column_name} at Excel row {excel_row}.")
                values.append(number)

        if not values or len(set(values)) != 1:
            raise InputError(f"{column_name} must contain one consistent value.")
        return values[0]

    # 3. Read and validate top-event test/requirement settings.
    n_test = read_consistent_setting("n_test")
    k_fail = read_consistent_setting("k_fail")
    q_req = read_consistent_setting("q_req")

    if not n_test.is_integer() or not k_fail.is_integer() or not 0 <= k_fail <= n_test:
        raise InputError("Test counts must be integers satisfying 0 <= k_fail <= n_test.")
    if not 0 <= q_req <= 1:
        raise InputError("q_req must lie in [0, 1].")

    # Keep the four workbook-level settings together so later modules can access
    # analysis_settings.phase, .n_test, .k_fail, .q_req, and .lambda_phase.
    analysis_settings = Settings(lifecycle_phase, int(n_test), int(k_fail), q_req)

    # 4. Copy the raw table before cleaning it and remember original Excel rows.
    assessment_rows = raw_input.copy()

    # Excel row 1 contains headers, so the first data row is row 2. SourceRow lets
    # validation errors/warnings point users back to the exact row in their workbook.
    assessment_rows["SourceRow"] = np.arange(2, len(assessment_rows) + 2)

    if "Status" not in assessment_rows:
        assessment_rows["Status"] = ""

    # Ignore fully blank assessment rows but retain any row containing assessment data.
    keep = assessment_rows[["Branch", "Component", "Indicator", "Cat", "Z", "RaterID", "Status"]].apply(
        lambda col: col.map(normalize_text).ne("")).any(axis=1)
    assessment_rows = assessment_rows.loc[keep].copy()

    if assessment_rows.empty:
        raise InputError("MATLAB_Input has no assessment rows.")

    # 5. Normalize text fields and reject missing identifiers.
    for col in ("Branch", "Component", "Indicator", "Cat", "RaterID", "Status"):
        assessment_rows[col] = assessment_rows[col].map(normalize_text)

    for _, row in assessment_rows.iterrows():
        if any(not row[c] for c in ("Branch", "Component", "Indicator", "RaterID")):
            raise InputError(f"Missing Branch, Component, Indicator or RaterID at Excel row {row.SourceRow}.")

    # 6. Normalize component names and T/O category labels.
    assessment_rows["Component"] = assessment_rows.Component.map(canonical_component)
    assessment_rows["Cat"] = assessment_rows.Cat.str.upper()  # "o" -> "O" (letter O), not zero.
    bad_cat = ~assessment_rows.Cat.isin(["T", "O"])

    if bad_cat.any():
        raise InputError(f"Invalid Cat at Excel rows {assessment_rows.loc[bad_cat, 'SourceRow'].tolist()}.")

    # 7. Handle "Unable to assess" and validate all remaining 0-4 scores.
    assessment_rows["Unassessed"] = assessment_rows.Status.str.casefold().eq("unable to assess")

    if (assessment_rows.Unassessed & assessment_rows.Z.map(normalize_text).ne("")).any():
        raise InputError("Rows marked Unable to assess must have blank Z.")

    assessment_rows["Z"] = pd.to_numeric(assessment_rows.Z, errors="coerce")
    bad_score = ~assessment_rows.Unassessed & (
        ~np.isfinite(assessment_rows.Z) | ~assessment_rows.Z.between(0, 4)
    )

    if bad_score.any():
        raise InputError(f"Invalid Z at Excel rows {assessment_rows.loc[bad_score, 'SourceRow'].tolist()}.")

    # 8. Build one profile per (Component, RaterID).
    # zip(COMPONENTS, BRANCHES) walks the matched component/branch pairs together.
    # groupby("RaterID") then separates that component's rows by individual rater.
    # Within each rater profile, retained T scores and O scores are averaged separately.
    rater_profiles = []
    excluded_rows = assessment_rows.loc[assessment_rows.Unassessed, "SourceRow"].astype(int).tolist()

    for component, expected_branch in zip(COMPONENTS, BRANCHES):
        component_rows = assessment_rows.loc[assessment_rows.Component.eq(component)]

        if component_rows.empty:
            raise InputError(f"Missing required component: {component}.")
        if not component_rows.Branch.str.casefold().eq(expected_branch.casefold()).all():
            raise InputError(f"Wrong Branch for {component}.")

        for rater_id, rater_rows in component_rows.groupby("RaterID", sort=False):
            if rater_rows.Indicator.str.casefold().duplicated().any():
                raise InputError(f"Duplicate indicator within {component} / {rater_id}.")

            scored_rows = rater_rows.loc[~rater_rows.Unassessed]
            if set(scored_rows.Cat) != {"T", "O"}:
                raise InputError(f"{component} / {rater_id} needs at least one scored T and O indicator.")

            rater_profiles.append(dict(
                Branch=expected_branch,
                Component=component,
                RaterID=rater_id,
                Z_T=float(scored_rows.loc[scored_rows.Cat.eq("T"), "Z"].mean()),
                Z_O=float(scored_rows.loc[scored_rows.Cat.eq("O"), "Z"].mean()),
                NInputRows=len(rater_rows),
                NUsedRows=len(scored_rows),
                NExcludedRows=len(rater_rows) - len(scored_rows),
            ))

    # 9. Report excluded "Unable to assess" rows and return validated model inputs.
    if excluded_rows:
        warnings.warn(
            f"Excluded Unable to assess indicators at Excel rows {excluded_rows}.",
            UserWarning,
            stacklevel=2,
        )

    return assessment_rows, pd.DataFrame(rater_profiles), analysis_settings, excluded_rows
