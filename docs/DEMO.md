# MRI demonstration

## Watch

- [Explanatory presentation: 720p, 36 seconds](../results/showcase.mp4)
- [Raw assignment output: 60 planes, 30 seconds](../results/demo.mp4)
- [Poster](../results/demo-poster.png)

The presentation shows the actual projection data enlarged with nearest
neighbor. A normalized isometric box marks each current triangle or
trapezoid in the MRI volume. Labels identify the voxel axis/tilt, geometry,
projection dimensions and CSV position. There is no fabricated anatomy or
AI-generated source imagery, and no audio track.

## Contents

| Presentation time | Content | Raw CSV rows |
|---|---|---|
| 0-3 s | Intro and three demonstration sections | None |
| 3-13 s | Equal-base rectangular planes sweeping voxel X | 1-20 |
| 13-23 s | Isosceles triangles sweeping voxel Y | 21-40 |
| 23-33 s | Oblique trapezoids rotating -28 to +28 degrees | 41-60 |
| 33-36 s | Closing explanation | None |

Voxel coordinates are used without applying physical MRI spacing/origin.
The source is the same MRHead_1.nrrd described in DATASET.md:
256 x 256 x 130, int16 with observed intensities 0..279.
Both videos use the same global intensity display range and serialized
coordinates. Raw projection matrices retain the source dtype before display
conversion.

## Reproduce

```bash
python -m scripts.create_demo data/MRHead_1.nrrd
```

If using the canonical verified download, substitute data/MRHead-canonical.nrrd.

The command writes results/demo_planes.csv, demo-manifest.json, demo.mp4,
showcase.mp4, demo-poster.png and demo-validation.json. The CSV and manifest
are committed alongside the videos, so the exact inputs can be reviewed.

The original main interface remains:

```bash
python Ex0.py data/MRHead_1.nrrd results/demo_planes.csv results/demo.mp4
```

That produces exactly one frame for every CSV row, with no labels or inserted
title frames. The separate presentation repeats each source image six times
at 12 FPS and adds opening/closing cards. MP4 playback rates do not indicate
projection computation throughput.

## Verify

```bash
python -m scripts.create_demo data/MRHead_1.nrrd --verify-only
python -m unittest tests.test_demo -v
```

The verifier decodes every frame, checks H.264, FPS, dimensions and exact
frame counts, and compares every raw frame to its corresponding projection.
A mean absolute error allowance of 8 grayscale levels handles lossy H.264.
The recorded largest mean error is about 1.40. Numerical projection precision
is tested separately before video normalization/compression.

Automated tests generate and decode a short version from a synthetic NRRD,
check all sixty serialized MRI planes for valid geometry and section order,
and reject an inconsistent manifest. Layout was visually checked at opening,
orthogonal, triangular, oblique and ending frames.

The portable font fallback can change text appearance between systems.
Nearest-neighbor enlargement deliberately preserves visible source pixels.
