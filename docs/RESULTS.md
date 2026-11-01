# Experiments and measured results

Revised 2026-11-01. These results supersede the earlier interpolation-based
152.92/142.59 FPS claims, which used smaller planes and a different sampler.
Raw timing files are versioned with this document.

The latest MRI experiment is now the sixty-plane raw video and the 720p
presentation documented in DEMO.md. The earlier three-frame measurements
below are retained as historical context, not as the current demo metadata.

## Environment and method

CPU: Intel(R) Core(TM) Ultra 7 255U; 14 logical CPUs. OS: Windows-11-10.0.26200-SP0.
Python 3.12.14; NumPy 2.3.5; Numba 0.68.1; llvmlite 0.50.0;
pynrrd 1.1.3; imageio 2.38.1; imageio-ffmpeg 0.6.0.

A seeded random 500 x 500 x 500 uint8 volume contains 125,000,000 bytes
(119.21 MiB). Both C and Fortran memory order are measured. Each case includes
an initial call, three warmups, then three trials of forty timed calls.
FPS = 1000 / mean(milliseconds); the slowest trial is reported separately.
Timing includes input validation, geometry, output allocation and all voxel
sampling. It excludes imports/JIT warmup, file loading and MP4 encoding.
No result/geometry cache or multithreaded kernel is used. First-call time is
reported in the raw JSON; it can reuse an existing compiled-code cache.

Reproduce from the repository root:

```bash
python -m scripts.benchmark_suite --json results/benchmark-current.json
```

Triangle/trapezoid subsets remain available via python -m scripts.benchmark
and python -m scripts.benchmark_trapezoid, with the same CLI options.
Raw points, source SHA256, environment, individual timings and per-trial FPS
are in [benchmark-current.json](../results/benchmark-current.json).

## Warm compiled-kernel results

| Case | Layout | Output rows x columns | Mean FPS | Slowest trial FPS | p95 ms |
|---|---|---|---:|---:|---:|
| small_triangle | C | 150 x 214 | 2821.94 | 2666.92 | 0.56 |
| small_trapezoid | C | 153 x 161 | 2071.99 | 1934.73 | 0.69 |
| assignment_triangle | C | 448 x 401 | 856.49 | 841.99 | 1.88 |
| assignment_rectangle | C | 401 x 501 | 451.44 | 437.62 | 2.85 |
| review_large_trapezoid | C | 521 x 500 | 487.09 | 386.51 | 3.39 |
| diagonal_triangle | C | 706 x 707 | 99.27 | 99.09 | 12.58 |
| diagonal_rectangle | C | 500 x 707 | 317.45 | 238.21 | 5.10 |
| tilted_trapezoid | C | 418 x 401 | 148.61 | 137.75 | 9.52 |
| small_triangle | F | 150 x 214 | 1590.06 | 1273.21 | 1.62 |
| small_trapezoid | F | 153 x 161 | 1309.19 | 1165.93 | 1.40 |
| assignment_triangle | F | 448 x 401 | 837.51 | 803.48 | 1.64 |
| assignment_rectangle | F | 401 x 501 | 69.78 | 68.77 | 18.37 |
| review_large_trapezoid | F | 521 x 500 | 103.65 | 93.22 | 13.21 |
| diagonal_triangle | F | 706 x 707 | 63.07 | 60.79 | 19.64 |
| diagonal_rectangle | F | 500 x 707 | 72.04 | 71.41 | 18.32 |
| tilted_trapezoid | F | 418 x 401 | 201.97 | 192.26 | 7.15 |

All 16 case/layout combinations exceeded 30 FPS in every trial.
The lowest mean was 63.07 FPS; the slowest individual
trial was 60.79 FPS. Some large cases remain below the
expected 100 FPS target. This establishes the tested scenarios on this
computer, not a guarantee for every plane, workload or other computer.

The assignment rectangle extends to coordinate 500 on one axis; outside
samples are zero. The review trapezoid and the additional diagonal cases
have their vertices within 0..499, so the large-plane measurements are not
limited to mostly out-of-volume images. The review trapezoid points are:
(250,149.5,0), (250,349.5,0), (250,0,499), (250,499,499).

## Same-sampling baseline

The row-vectorized unit-step implementation at a9bb5ce was measured separately
with three warmups and one trial of twenty calls per case. Its sampler and
geometry are the same as the compiled version; unlike a comparison to
990b7be, this does not conflate acceleration with altered pixel values.
The shorter baseline run is indicative, not a statistical speedup guarantee.

| Case | Layout | Unit-step NumPy baseline FPS | Compiled mean FPS |
|---|---|---:|---:|
| assignment_triangle | C | 29.66 | 856.49 |
| review_large_trapezoid | C | 22.88 | 487.09 |
| diagonal_triangle | C | 13.74 | 99.27 |
| assignment_triangle | F | 37.15 | 837.51 |
| review_large_trapezoid | F | 19.36 | 103.65 |
| diagonal_triangle | F | 14.36 | 63.07 |

All sixteen baseline scenarios and timings are in
[benchmark-unit-baseline.json](../results/benchmark-unit-baseline.json).
The review's ~8 FPS measured a different version and environment; it is not
presented as the baseline of this controlled comparison.

## Cold start

A separate process used a fresh empty Numba cache directory:

- Imports: 1383 ms.
- First small triangle, including compilation: 1163 ms.
- Second call: 1.41 ms.

See [startup.json](../results/startup.json). Compilation is paid for each new
dtype/layout signature, can take seconds, and is not counted as warm FPS.
The NumPy fallback remains available for portability and nonnative byte order;
its large-plane speed is not claimed to meet the requirement.

## MRI demonstration

The MRI input is the existing MRHead_1.nrrd: 256 x 256 x 130, int16, values
0..279. Its voxels were independently compared with the checksum-verified
canonical Slicer download and are exactly equal; see DATASET.md for hashes.

```bash
python Ex0.py data/MRHead_1.nrrd planes.csv results/demo.mp4
```

The regenerated [MRI video](../results/demo.mp4) decodes to exactly three
H.264/yuv420p frames, 144 x 100 pixels, 2 FPS and 1.5 seconds. The CSV order
is triangle, trapezoid, triangle. Pixel values intentionally differ from the
old interpolated demo after restoring unit-distance sampling; the old video
remains recoverable from Git history.

A second [unsigned-32 synthetic video](../results/synthetic-uint32.mp4) is
reproducible with the generator described in DATASET.md. It decodes to three
14 x 8 frames at 2 FPS. Both examples were decoded after encoding, rather
than accepted solely because the encoder process exited successfully.

## Correctness evidence and limits

The final acceptance count and commands are in TESTING.md. Complete matrices
are compared to an independent scalar reference, including 48 seeded random
planes. Real NRRD/MP4 round trips cover all three unsigned dtypes and known
frame order; encoder failure preserves existing output.

The performance requirement is about projection computation, not video
playback or end-to-end disk/codec throughput. Nearest-neighbor aliasing,
first-call JIT cost, large-coordinate canvases and hardware variation remain
explicit limitations. CPU utilization, peak RSS and all possible planes were
not exhaustively measured. No performance test silently skips a failed case.

## Acceptance in the original project environment

The original project folder was fast-forwarded to the completed commits and its
existing .venv received the Numba dependency. All 35 tests passed there and
pip check reported no broken requirements. Python is 3.12.10, NumPy 2.5.4,
Numba 0.68.1 and llvmlite 0.50.0; the same CPU and OS are used.

The complete suite was rerun with the same seed, geometries, memory layouts,
warmups and three forty-call trials. Raw data:
[benchmark-project-env.json](../results/benchmark-project-env.json).

| Case | Layout | Mean FPS | Slowest trial FPS |
|---|---|---:|---:|
| small_triangle | C | 2297.77 | 1979.34 |
| small_trapezoid | C | 1953.84 | 1860.25 |
| assignment_triangle | C | 760.94 | 727.57 |
| assignment_rectangle | C | 432.13 | 405.27 |
| review_large_trapezoid | C | 437.01 | 409.89 |
| diagonal_triangle | C | 108.92 | 106.82 |
| diagonal_rectangle | C | 202.29 | 201.44 |
| tilted_trapezoid | C | 140.16 | 131.37 |
| small_triangle | F | 1608.05 | 1411.01 |
| small_trapezoid | F | 1264.41 | 980.17 |
| assignment_triangle | F | 789.03 | 715.54 |
| assignment_rectangle | F | 76.09 | 72.11 |
| review_large_trapezoid | F | 156.93 | 152.36 |
| diagonal_triangle | F | 72.54 | 67.44 |
| diagonal_rectangle | F | 110.07 | 107.47 |
| tilted_trapezoid | F | 214.59 | 191.70 |

All sixteen scenarios passed every trial above 30 FPS. The lowest mean was
72.54 FPS and the slowest trial was 67.44 FPS. Some large cases
remain below the expected 100 FPS target. These are recorded observations,
not a guarantee for all possible geometries or machines.

The first pip invocation encountered a console UnicodeEncodeError; rerunning
with Python UTF-8 mode and disabled pip progress completed installation.
README includes the corresponding command.

## Layout-aware follow-up after direct PDF review

The stride-selected traversal and eight-ULP integer-boundary rule are measured
with the same sixteen-case methodology. Raw measurements and the new source
hash are in [benchmark-layout-aware.json](../results/benchmark-layout-aware.json).
Earlier source-hashed runs remain historical.

| Case | Layout | Mean FPS | Slowest trial FPS |
|---|---|---:|---:|
| small_triangle | C | 1782.12 | 1639.12 |
| small_trapezoid | C | 1456.83 | 1203.72 |
| assignment_triangle | C | 550.98 | 511.86 |
| assignment_rectangle | C | 325.82 | 313.55 |
| review_large_trapezoid | C | 333.45 | 309.75 |
| diagonal_triangle | C | 101.35 | 97.72 |
| diagonal_rectangle | C | 198.69 | 190.09 |
| tilted_trapezoid | C | 132.48 | 124.74 |
| small_triangle | F | 1411.07 | 1333.93 |
| small_trapezoid | F | 1377.29 | 1319.62 |
| assignment_triangle | F | 639.23 | 554.87 |
| assignment_rectangle | F | 124.21 | 114.07 |
| review_large_trapezoid | F | 145.82 | 136.75 |
| diagonal_triangle | F | 95.14 | 94.12 |
| diagonal_rectangle | F | 109.88 | 107.65 |
| tilted_trapezoid | F | 160.64 | 158.01 |

Lowest mean: 95.14 FPS. Every trial exceeded 30 FPS;
100 FPS remains a target rather than a claim for every case.

## Expanded MRI experiment against the supplied PDF

scripts/create_demo.py generates sixty valid numbered-coordinate planes in
three groups: equal-base rectangles sweeping X, triangles sweeping Y, and
trapezoids tilted from -28 to +28 degrees. Both unsigned CSV schemas and the
real signed-short MRI extension retain their earlier coverage.

- Raw assignment video: 60 H.264 frames, 216 x 182, 2 FPS, 30 seconds.
- Separate explanatory presentation: 432 H.264 frames, 1280 x 720, 12 FPS,
  36 seconds, with section labels, voxel-plane diagram and progress.
- Every frame in both files was decoded. All sixty raw frames were compared
  to projections from their corresponding serialized CSV row. The largest
  mean absolute compression difference was 1.403 grayscale levels.
- Opening, orthogonal, triangular, oblique and ending presentation frames
  were visually inspected; source MRI pixels remain recognizable and text
  remains within its layout.
- All 41 automated tests pass, including shortened real-codec demo generation.

Exact inputs, metadata and checks: results/demo_planes.csv,
results/demo-manifest.json and results/demo-validation.json.
See DEMO.md for reproduction and ASSIGNMENT_COMPLIANCE.md for the PDF mapping.

## Final submission acceptance in the original environment

After the PDF review and complete demo changes, all 41 tests and both complete
video verifications passed in the original project folder. The final source
was measured on Python 3.12.10, NumPy 2.5.4 and Numba 0.68.1 with the same
CPU, seed, sixteen cases, warmups and three forty-call trials. Raw data:
[benchmark-submission-env.json](../results/benchmark-submission-env.json).

| Case | Layout | Mean FPS | Slowest trial FPS |
|---|---|---:|---:|
| small_triangle | C | 1737.54 | 1397.22 |
| small_trapezoid | C | 1406.38 | 1383.44 |
| assignment_triangle | C | 503.53 | 461.48 |
| assignment_rectangle | C | 397.58 | 337.84 |
| review_large_trapezoid | C | 322.20 | 282.10 |
| diagonal_triangle | C | 104.42 | 98.81 |
| diagonal_rectangle | C | 262.70 | 202.85 |
| tilted_trapezoid | C | 122.89 | 116.23 |
| small_triangle | F | 2086.67 | 1970.55 |
| small_trapezoid | F | 1347.19 | 1087.74 |
| assignment_triangle | F | 809.17 | 767.48 |
| assignment_rectangle | F | 144.01 | 136.98 |
| review_large_trapezoid | F | 156.98 | 154.37 |
| diagonal_triangle | F | 111.55 | 109.17 |
| diagonal_rectangle | F | 112.02 | 109.89 |
| tilted_trapezoid | F | 211.81 | 202.08 |

All sixteen mean rates exceed the expected 100 FPS target; the lowest is
104.42 FPS. The slowest separate trial is 98.81 FPS, and every trial exceeds
the mandatory 30 FPS minimum. This is a measured warm result for these cases,
not a guarantee for unmeasured planes or hardware. The earlier source-hashed
results are retained to show the progression and environment variation.
