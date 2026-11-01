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
