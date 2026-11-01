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

CSV/video integration and reproducible dataset tests are added alongside the
corresponding pipeline changes. Performance measurements belong in RESULTS.md
and are separate from correctness tests; FPS is not a hardware-independent
unit-test assertion.
