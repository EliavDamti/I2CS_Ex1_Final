# Testing strategy and current coverage

Run from the repository root:

```bash
python -m unittest discover -s tests -v
```

Tests use unittest from Python's standard library. Dependencies come from
requirements.txt. Test modules are also executable with python -m
tests.test_coordinates (without a .py suffix).

## Core acceptance coverage

- Hand-computed coordinate rows distinguish unit stepping from the old
  interpolated sampling: the first row contains [232,322], not [232,332,322].
- An independent scalar reference compares complete images for both shapes,
  including fractional lengths, tilted planes, axis permutations and array
  views with noncontiguous and negative strides.
- Continuous bounds, nearest-neighbor half ties and exterior regions.
- Exact unsigned extrema for all three assignment dtypes; signed int16 MRI
  compatibility and negative values.
- EPS acceptance/rejection at multiple scales, the strict tolerance boundary,
  equal bases, the assignment rectangle and sheared equal-base shapes.
- Unequal legs, reversed/opposite/nonparallel bases, noncoplanar points,
  duplicate points and a collinear triangle with equal legs.
- Empty/oversized/non-3D volumes, unsupported dtypes and invalid vertices.

The reference intentionally uses slow scalar arithmetic rather than calling
the production sampling kernel. Full-output assertions prevent a constant
volume or a single last-row assertion from hiding coordinate errors.

## CSV and video integration

- Both CSV schemas map to identical ordered points. The original assignment
  fixture is read in full, including its rectangle.
- BOM/whitespace, optional fourth coordinates for triangles, blank lines,
  duplicate/missing/ambiguous headers, wrong counts, short/extra rows,
  nonnumeric/nonfinite coordinates and populated rows with a blank type.
- Actual NRRD write/read and actual FFmpeg H.264 encoding/decoding for uint8,
  uint16 and uint32, with exactly three frames in known white/black/gray order.
- Even common frame dimensions, playback rate and independently expected
  center intensities, allowing eight grayscale levels for lossy compression.
- CLI success and nonzero invalid-record exit; existing output preservation.
- Simulated encoder failure verifies temporary cleanup and output preservation.
- Missing/unsupported NRRD inputs, uint32 normalization precision, constant
  zero input, signed display ranges and centering validation.

## Acceleration verification

The full suite requires the installed Numba accelerator to be active and have
compiled a native signature. It also explicitly forces the NumPy fallback and
tests nonnative-endian data without loss. Twenty-four seeded random planes of
each shape compare complete images against the scalar reference, including
samples outside the volume.

No FFmpeg integration test is silently skipped.

## Reproducible datasets

Generate/reload all three unsigned NRRDs, validate extrema and voxel hashes,
and verify every generated plane. Check downloader hash mismatch and existing
file protection without network access. The actual canonical Slicer download
was separately verified against the original MRI's full voxel array.

Recorded acceptance result: 35 tests passed, including real codec integration,
both sampling backends and 48 seeded random full-matrix comparisons.
The same 35 tests also passed from the original project folder with its own
.venv (Python 3.12.10, NumPy 2.5.4, Numba 0.68.1); pip check reported no broken
requirements. That environment's performance is recorded separately in RESULTS.

After reviewing the attached PDF directly, the layout/stability extension adds
24 random Fortran-order uint32 plane comparisons, a hand-specified complete
rotated 4x5 rectangle, and a genuine 4+1e-10 leg that must keep its fifth row.
This guards numerical integer boundaries separately from the assignment EPS.

The full demonstration extension adds three integration/definition tests:
all sixty serialized MRI planes and section order; real synthetic NRRD to raw
and presentation videos with decoding and mismatch rejection; invalid sweep
inputs. The final suite contains 41 passing tests. The full MRI experiment
separately decodes 60 raw and 432 presentation frames and compares every raw
frame with its ordered CSV projection. See demo-validation.json and DEMO.md.
The final 41-case suite and full video verification were also rerun successfully
inside the original project's .venv after the commits were applied.
Performance measurements belong in RESULTS.md and are separate from
correctness tests; FPS is not a hardware-independent unit-test assertion.

The biscuit CSV exposed a separate base-order roundoff regression: equal
rotated bases differed by one or two float64 ULPs. Two added cases accept the
reported coordinates and reject a genuine 1e-10 base reversal. The suite now
contains 43 tests. The user's complete 120-record input is also validated and
encoded separately; the user-owned CSV is not added to the repository.
