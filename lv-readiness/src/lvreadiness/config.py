"""Mapping constants from paper Tables 4–5 and MATLAB v13."""

from dataclasses import dataclass

SCORE_LEVELS = (0, 1, 2, 3, 4)
MU_T_LEVELS = (0.40, 0.60, 0.75, 0.88, 0.96)
M_O_LEVELS = (0.90, 0.99, 1.03, 1.07, 1.10)
S_O_LEVELS = (4, 8, 12, 16, 20)
PHASES = {"SFR": 0.7, "PDR": 1.0, "CDR": 1.3, "TRR": 1.6, "SVR": 2.0}
MEAN_CLIP = (0.01, 0.99)
N_PRIOR, N_POSTERIOR, SEED = 200000, 50000, 1
COMPONENTS = ("Concept", "Design Verification", "Manufacturing",
              "Assembly and Integration", "Impl. Verification",
              "Operation Setup", "Operation Execution")
BRANCHES = ("Design", "Design", "Implementation", "Implementation",
            "Implementation", "Operation", "Operation")
BASIC_EVENTS = ("q_C", "q_Vd", "q_M", "q_I", "q_Vi", "q_S", "q_E")
NODES = BASIC_EVENTS + ("q_dsgn", "q_impl", "q_op", "q_top")


@dataclass(frozen=True)
class Settings:
    """Assessment settings, read only from MATLAB_Input."""

    phase: str
    n_test: int
    k_fail: int
    q_req: float

    @property
    def lambda_phase(self) -> float:
        return PHASES[self.phase]
