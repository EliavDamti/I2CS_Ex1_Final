# Experiments and measured results

Revised 2026-11-01. These results supersede the earlier interpolation-based
152.92/142.59 FPS claims, which used smaller planes and a different sampler.
Raw timing files are versioned with this document.

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
