"""Rebuild the public example from fictional scores, never historical data."""

from pathlib import Path
from openpyxl import Workbook

from lvreadiness.config import BRANCHES, COMPONENTS

# Current overview labels and revision 3's proposed categories.
INDICATORS = (
    (
        ("Concept feasibility", "Concept robustness"),
        ("Design expertise", "Design-process discipline"),
    ),
    (
        ("Model-based evidence", "Model credibility"),
        ("Organizational heritage", "Verification rigor", "Verification Expertise"),
    ),
    (
        ("Manufacturing and Inspection Capability", "As-Built Quality"),
        ("Manufacturing Process Control", "Manufacturing Expertise"),
    ),
    (
        ("Assembly and Interface Compatibility", "Procedure Readiness"),
        ("Process Control", "Team Expertise"),
    ),
    (
        ("Verification coverage", "Verification Effectiveness"),
        ("Verification Expertise", "Verification Rigor"),
    ),
    (
        (
            "Mission Configuration Readiness",
            "Operational Support Readiness",
            "External Condition Criteria",
        ),
        ("Setup Procedure Control", "Setup Team Readiness"),
    ),
    (
        ("Operational Observability", "Operational Controllability"),
        ("Execution Procedure Readiness", "Team Execution Readiness"),
    ),
)


def build(path: Path) -> None:
    """Create a fictional score-2 assessment, using one stable synthetic rater."""
    workbook = Workbook()
    sheet = workbook.active
    sheet.title = "MATLAB_Input"
    sheet.append(
        [
            "Branch",
            "Component",
            "Indicator",
            "Cat",
            "Z",
            "Status",
            "Lifecycle Phase",
            "n_test",
            "k_fail",
            "q_req",
            "RaterID",
        ]
    )
    # Write workbook-wide settings once; remaining rows leave those cells blank.
    is_first_row = True
    for branch, component, categories in zip(BRANCHES, COMPONENTS, INDICATORS):
        for category, names in zip(("T", "O"), categories):
            for indicator in names:
                workbook_settings = ["CDR", 3, 1, 0.5] if is_first_row else [None] * 4
                sheet.append(
                    [
                        branch,
                        component,
                        indicator,
                        category,
                        2,
                        None,
                        *workbook_settings,
                        "SYN01",
                    ]
                )
                is_first_row = False
    path.parent.mkdir(parents=True, exist_ok=True)
    workbook.save(path)


if __name__ == "__main__":
    build(
        Path(__file__).resolve().parents[1]
        / "examples/synthetic_demo/Inputs_sheet.xlsx"
    )
