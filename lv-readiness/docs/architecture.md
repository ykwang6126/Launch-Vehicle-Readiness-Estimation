# Architecture

The public run_analysis function and CLI both call pipeline.py. config.py owns
constants and defaults. io.py reads one worksheet, validates duplicate headers,
and exports tables and provenance. validation.py enforces settings, row, and
profile constraints. priors.py computes success-space parameters. pooling.py
provides exact mixture moments and sampling. fault_tree.py owns tree equations.
updating.py owns log-space weights, ESS, weighted moments, and joint resampling.
summary.py owns statistics. plotting.py writes the twelve diagnostic PNG files
without opening interactive windows.

One NumPy Generator(PCG64(seed)) is passed through numerical functions. Profile
order is stable within the fixed component order. Only sampling consumes RNG
state; plotting, reporting, and validation do not. Basic prior samples, all node
samples, weights, and posterior indices are available on AnalysisResult.

Paths are supplied at runtime. Historical inputs are outside the package.
Package installation does not require MATLAB. MATLAB is needed only to regenerate
native regression references using tools/export_matlab_reference.m. The replay
verifier reads those native arrays; normal Python runs never import MATLAB results.

Unit tests exercise mathematics and invalid inputs; integration tests exercise
the API, CLI, exports, and repeatability. Historical regression runs locally when
the restricted workbook is available and otherwise skips. Synthetic inputs are
distributed so public unit/integration tests do not require restricted data.
