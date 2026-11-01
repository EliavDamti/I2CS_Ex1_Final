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
