# Final experiment results

Submission measurements recorded on 2026-11-02. This document summarizes the
current implementation; earlier experiments and raw reports remain available
in Git history.

## Environment and method

Intel Core Ultra 7 255U, 14 logical CPUs, Windows 11; Python 3.12.10,
NumPy 2.5.4, Numba 0.68.1 and llvmlite 0.50.0. Exact installed versions are
in requirements-lock.txt.

The benchmark uses a seeded random 500x500x500 uint8 volume (125 MB).
Eight geometries run in both C and Fortran memory order. Each case has three
warmups and three trials of 40 projections. Timings include geometry
validation, scanline construction, allocation and sampling. They exclude
imports/JIT warmup, volume generation, NRRD loading, CSV parsing and video
encoding. No projection-result cache or parallel kernel is used.

```bash
python -m scripts.benchmark_suite --json results/benchmark.json
```

[The single current report](../results/benchmark.json) records the final
projection source hash, exact points, output sizes, environment and every
individual timing. First-call times can reuse Numba's compiled-code cache;
they are not measurements of a fresh installation's cold compilation.

## Computation performance

| Geometry | Layout | Mean FPS | Slowest trial FPS |
|---|---|---:|---:|
| Small triangle | C | 2009.56 | 1837.54 |
| Small trapezoid | C | 1824.53 | 1635.28 |
| Assignment triangle | C | 635.87 | 588.17 |
| Assignment rectangle | C | 284.26 | 241.65 |
| Large trapezoid | C | 329.32 | 326.58 |
| Diagonal triangle | C | 98.68 | 89.74 |
| Diagonal rectangle | C | 191.28 | 182.00 |
| Tilted trapezoid | C | 109.57 | 100.70 |
| Small triangle | F | 1776.92 | 1733.34 |
| Small trapezoid | F | 1185.75 | 1078.17 |
| Assignment triangle | F | 597.87 | 540.34 |
| Assignment rectangle | F | 124.77 | 121.93 |
| Large trapezoid | F | 151.98 | 149.09 |
| Diagonal triangle | F | 103.93 | 102.94 |
| Diagonal rectangle | F | 90.79 | 88.04 |
| Tilted trapezoid | F | 194.28 | 181.95 |

All 48 trials exceeded the mandatory 30 FPS threshold. The lowest case mean
was 90.79 FPS; the slowest trial was 88.04 FPS. Fourteen of sixteen case means
exceeded the expected 100 FPS target. This establishes the measured cases on
this computer, not a universal performance guarantee. Large diagonal slices
are the remaining cases below the target. Numba compilation can take seconds
on first use of a new dtype/layout; fallback speed is not claimed to meet
the requirement.

## MRI experiment and submitted MP4

The public Slicer MRHead source is 256x256x130 int16 with intensities 0..279.
It was verified voxel-for-voxel against Slicer's canonical download; DATASET
records provenance and hashes.

```bash
python Ex0.py data/MRHead_1.nrrd results/demo_planes.csv results/demo.mp4
python -m scripts.create_demo data/MRHead_1.nrrd --verify-only
```

The [raw MRI video](../results/demo.mp4) contains 60 ordered H.264 frames,
182x216 pixels, 2 FPS and 30 seconds. Every frame was decoded and compared
with its CSV projection; the largest mean absolute compression error was
1.403 grayscale levels. The [separate presentation](../results/showcase.mp4)
contains 432 frames, 1280x720 pixels, 12 FPS and 36 seconds. It shows the
three sweeps, current plane and progress; it repeats source images for
readability. See DEMO for the presentation structure.

## Additional examples

| Dataset | Planes | Decoded frames | Video size (width x height) | Largest mean encoding error |
|---|---|---|---|---:|
| Biscuit | 120 trapezoids | 120 | 258x256 | 1.490 |
| Croissant | 100 triangles | 100 | 502x560 | 0.914 |
| Generated uint32 | 3 mixed planes | 3 | 14x8 | Checked by unsigned codec tests |

Biscuit and croissant videos were regenerated from the final source. All
220 frames matched their ordered CSV projections within the 8-level mean
compression allowance. results/examples-validation.json records the input,
CSV, code and output hashes and comparison summaries. Their CSVs are in
examples/; NRRD binaries are local user-supplied inputs.

Croissant's adjacent plane angles change by a median of about 58 degrees,
and centers move by about 115 voxels. Every triangle extends partly beyond
the source volume. Abrupt changes and zero-filled exterior areas therefore
follow the provided CSV; they do not indicate dropped or reordered frames.

## Correctness and practical limits

All 45 automated tests pass, including independent expected pixels for the
boundary regression, scalar-reference comparisons, both sampling backends
and actual NRRD/MP4 round trips. pip check reports no broken requirements.

Projection matrices retain integer precision; the MP4 is normalized and
lossy. Computation FPS differs from playback speed. Memory grows with the
number of stored projection matrices and with canvas dimensions. Physical
coordinate resampling, GPU execution and streaming arbitrary CSV lengths
are outside the implemented scope.
