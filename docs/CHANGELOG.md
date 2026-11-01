# Change record

## 2026-11-01 — unit-distance sampling and geometry regression coverage

Baseline: a6ebdf6, which already fixed the EPS/equal-base issues from the
990b7be review. Those fixes are retained; no earlier history is rewritten.

- Replaced ceil-interval endpoint interpolation with normalized unit steps on
  both legs and scanlines. Restored geometric floor centering.
- Defined noninteger triangle overshoot and a trapezoid convention that starts
  at the upper base and takes whole unit steps up to the leg length.
- Added padding when the supplied triangle loop extends beyond its final base.
- Added shared volume validation: three axes, sizes 1..1023, the three unsigned
  assignment dtypes and the signed int16 MRHead extension.
- Retained strict absolute leg EPS=0.001, ordered/equal bases and geometric
  degeneracy checks; normalized geometry vectors before angle checks.
- Replaced assertion-at-import scripts with discoverable unittest cases.
  Added a scalar full-image reference, manually calculated regression values,
  tilted/fractional planes, dtype extrema, invalid trapezoids and boundaries.
- Rewrote SRS/ALGORITHM/TESTING to document the current numerical contract.
  README commands and the CSV/video documents are updated with the pipeline
  change that follows.

## 2026-11-01 — assignment CSV and complete video pipeline

- Added automatic support for numbered coordinates and the assignment's
  Number of Points (3 or 4) header, preserving named-point CSV compatibility.
- Added a captured assignment fixture with source attribution in README.
  Its invalid geometric records remain invalid rather than being rewritten.
- Reject populated blank-type records, unknown counts, duplicate/ambiguous
  headers, extra fields and missing/nonfinite/nonnumeric coordinates.
  Report the physical CSV line; skip only completely empty records.
- Factored create_video into a callable pipeline. Validate all projections
  before encoding; write to a temporary MP4 and replace the output only after
  successful encoding. Remove temporary files after an encoder failure.
- Use float64 for display normalization so uint32 values just below maximum
  are not rounded prematurely. Retain source dtypes in projection matrices.
- Added clear CLI errors, output-extension/input-path protection and a frame
  size guard. Preserve global normalization, RGB centering and 2 FPS playback.
- Replaced incorrect README module commands and stale geometric restrictions.
  Updated the test strategy. Validation: all 29 tests pass, including real
  NRRD and FFmpeg round trips for all unsigned assignment dtypes.

## 2026-11-01 — large-plane acceleration and broad benchmarks

- Added Numba as a dependency and a streaming sampling kernel with no fastmath
  and no parallel-thread scheduling. Cache compiled code only, never results.
  Preserve NumPy geometry metadata and all unit-step numerical decisions.
- Retain an explicit NumPy fallback for unavailable Numba/nonnative byte order:
  generate coordinate grids in 32-row blocks and specialize constant axes.
- Test that the compiled backend actually runs; independently test the fallback
  and nonnative-endian uint16. Add 48 seeded random full-image comparisons.
- Replace narrow benchmark entry points with wrappers over a common suite.
  Cover small/large/assignment/diagonal/tilted geometries in C and F layouts,
  with seeded random intensities, three warmups and three trials of forty
  calls. Record first-call cost, output shapes, raw timings, p95, trial FPS,
  CPU/platform/dependency versions and projection source hash.
- Record a separately timed unit-step baseline from a9bb5ce to distinguish
  acceleration from the earlier change in sampling semantics.
- Update README, algorithm complexity, test coverage and experiment results.

## 2026-11-01 — reproducible data and refreshed demonstrations

- Add a deterministic unsigned NRRD generator covering the full uint8,
  uint16 and uint32 ranges, with valid three-plane CSV and voxel-hash manifest.
  Use uint64 intermediate arithmetic, F-order NRRD indexing and ignored output.
- Add a downloader for Slicer's checksum-addressed canonical MRHead dataset.
  Verify SHA256 before writing and refuse existing destinations.
- Download the canonical sample once and compare it to the original local MRI:
  voxel arrays match exactly; record both file hashes and their shared voxel
  hash, shape, dtype, intensity range and spatial metadata.
- Replace the outdated dataset document with direct provenance, exact
  generation/download commands, formulas, test datasets and benchmark inputs.
- Add generator round-trip/hash tests and offline downloader failure tests.
- Regenerate the MRI demo using the corrected sampler and decode its three
  ordered H.264 frames. Add and decode a generated uint32 demonstration.
- Update all requirements, dataset, testing and README links/commands.
  Final acceptance: 35 tests pass. No legacy result video is claimed to be
  pixel-identical after intentionally changing the sampling algorithm.

## 2026-11-01 — acceptance in the original project environment

- Fast-forward the original main branch without changing earlier commits or
  unrelated local datasets; install Numba/llvmlite in the existing .venv.
- Verify all 35 tests and pip dependency consistency in that environment:
  Python 3.12.10, NumPy 2.5.4, Numba 0.68.1.
- Repeat all sixteen benchmark scenarios there and preserve raw results in
  benchmark-project-env.json. Keep those measurements separate from the
  initial Python 3.12.14/NumPy 2.3.5 experiment.
- Document the UTF-8 pip invocation that resolves console encoding errors
  with the Hebrew Windows project path. No projection code changes here.
