# Testing strategy

Final acceptance: **45 tests passed** on 2026-11-02 with Python 3.12.10 and
the versions in `requirements-lock.txt`.

```bash
python -m unittest discover -s tests -v
```

Tests use standard-library unittest. Individual modules can run with
`python -m tests.test_coordinates`. No FFmpeg integration test is skipped.

## Numerical correctness

- Hand-computed voxel-coded rows distinguish normalized unit steps from
  endpoint interpolation and verify centering.
- Complete matrices are compared with a separate scalar reference for
  fractional/oblique planes, axis permutations, negative strides and seeded
  random data, including C/Fortran layouts and all required unsigned types.
- Unsigned extrema remain exact; signed int16 MRI values are also covered.
- Strict absolute EPS boundaries, rotated equal bases, genuine base reversals,
  collinearity, nonparallel/noncoplanar inputs and malformed vertices.
- Volume shape/type restrictions, nearest-neighbor half ties and exterior data.
- A hand-specified 7-24-25 rectangle on an 8x25x2 volume must return a complete
  2x26 matrix of 123s. This regression is checked across axis permutations and
  both backends without deriving its expectation from the scalar reference.
- Genuinely exterior scanlines remain zero; explicit sample_volume inputs
  outside the continuous bounds are not clamped.

## CSV and actual video integration

Both supported schemas, BOM/whitespace, optional metadata/fourth coordinates,
blank rows, duplicate/missing headers, invalid types/counts and nonfinite
coordinates are covered. Populated invalid rows must fail with a line number.

Actual NRRDs and H.264 videos are written/read for uint8, uint16 and uint32.
Decoded white/black/gray slices verify order and independently known center
intensities, common even dimensions and 2 FPS playback. CLI failures and a
simulated encoder failure verify preservation of existing output and temporary
file cleanup.

## Backends and data

Tests require the installed Numba accelerator to compile a native signature.
The NumPy fallback and nonnative-endian input are separately exercised.
Deterministic NRRD generators are reloaded and checked for expected voxels,
extrema and hashes. Downloader checksum rejection and overwrite protection
are tested offline.

## Full demonstrations

```bash
python -m scripts.create_demo data/MRHead_1.nrrd --verify-only
```

The complete MRI verification decodes 60 raw frames and 432 presentation
frames. Every raw frame is compared with its ordered CSV projection, allowing
mean absolute encoding error up to 8 grayscale levels. Projection precision
is tested before lossy compression. Short synthetic demo creation/decoding
and inconsistent-manifest rejection are also part of the automated suite.

The final biscuit (120 frames) and croissant (100 frames) outputs were also
fully decoded and compared with their CSV rows. Their source hashes and
summary results are in `results/examples-validation.json`. Croissant changes
viewpoints sharply because the input CSV does so; smoothness is not a pass
condition for arbitrary ordered planes.

Performance is measured separately, using the final source hash recorded in
`results/benchmark.json`; hardware-dependent FPS is not a unit-test assertion.
