"""Mapping constants from paper Tables 4–5 and MATLAB v13."""

from dataclasses import dataclass

# The three lookup tables below share the same score positions (0 through 4).
# MU_T_LEVELS: technical success mean; M_O_LEVELS: organizational mean factor;
# S_O_LEVELS: organizational strength before the lifecycle factor is applied.
SCORE_LEVELS = (0, 1, 2, 3, 4)
MU_T_LEVELS = (0.40, 0.60, 0.75, 0.88, 0.96)
M_O_LEVELS = (0.90, 0.99, 1.03, 1.07, 1.10)
S_O_LEVELS = (4, 8, 12, 16, 20)
# Later lifecycle phases increase Beta strength, reducing prior spread at a fixed mean.
PHASES = {"SFR": 0.7, "PDR": 1.0, "CDR": 1.3, "TRR": 1.6, "SVR": 2.0}
MEAN_CLIP = (0.01, 0.99)
N_PRIOR, N_POSTERIOR, SEED = 200000, 50000, 1
# These tuples use matching positions: component, branch, and basic-event name.
# Keep this order when creating sample columns and exported tables.
COMPONENTS = (
    "Concept",
    "Design Verification",
    "Manufacturing",
    "Assembly and Integration",
    "Impl. Verification",
    "Operation Setup",
    "Operation Execution",
)
BRANCHES = (
    "Design",
    "Design",
    "Implementation",
    "Implementation",
    "Implementation",
    "Operation",
    "Operation",
)
BASIC_EVENTS = ("q_C", "q_Vd", "q_M", "q_I", "q_Vi", "q_S", "q_E")
NODES = BASIC_EVENTS + ("q_dsgn", "q_impl", "q_op", "q_top")


@dataclass(frozen=True)
class Settings:
    """The four workbook settings shared by every component and rater.

    phase selects the lifecycle factor; n_test and k_fail are test/failure counts;
    q_req is the maximum acceptable top-event failure probability.
    frozen=True prevents later code from accidentally changing these settings.
    """

    phase: str
    n_test: int
    k_fail: int
    q_req: float

    @property
    def lambda_phase(self) -> float:
        """Look up the strength factor associated with the workbook lifecycle phase."""
        return PHASES[self.phase]
