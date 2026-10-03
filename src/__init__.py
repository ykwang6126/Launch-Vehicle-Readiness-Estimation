"""Launch readiness model, specification v0.1 revision 3 / MATLAB v13."""

__version__ = "0.1.0"

from .pipeline import AnalysisResult, run_analysis

# These names form the public API; internal modules remain separately importable.
__all__ = ["AnalysisResult", "run_analysis", "__version__"]
