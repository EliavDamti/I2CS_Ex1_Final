# I2SE Ex1 - 3D volume plane projection

Extract isosceles triangle and trapezoid slices from a 3D NRRD volume and
encode one MP4 frame per CSV record, in order. The implementation uses the
assignment's normalized unit-distance scanlines and preserves integer
intensities in the projection matrices.

## Install

Use Python 3.10 or later. The submission was validated on Python 3.12.10.

```bash
python -m pip install -r requirements.txt
```

To reproduce the tested Python 3.12 environment, install the recorded versions:

```bash
python -m pip install -r requirements-lock.txt
```

On Windows, create a virtual environment with `py -m venv .venv`, then use
`.venv\Scripts\python.exe` instead of `python`. If pip has a terminal encoding
error, use `.venv\Scripts\python.exe -X utf8 -m pip install --progress-bar off -r requirements.txt`.

Numba compiles each dtype/layout on first use; subsequent calls reuse compiled
code. The NumPy fallback preserves correctness, but its performance is not
claimed to meet the large-plane requirement.

## Run

Run commands from the repository root. The required main interface is:

```bash
python Ex0.py file.nrrd file.csv file.mp4
```

Reproduce the submitted 60-frame MRI video:

```bash
python Ex0.py data/MRHead_1.nrrd results/demo_planes.csv results/demo.mp4
```

The NRRD input is excluded from Git. See [DATASET.md](docs/DATASET.md) for
provenance, hashes, a verified public download and deterministic generators.
A download-only setup can use:

```bash
python -m scripts.download_mri
python Ex0.py data/MRHead-canonical.nrrd results/demo_planes.csv results/demo-canonical.mp4
```

The minimal three-plane example uses a separate output:

```bash
python Ex0.py data/MRHead_1.nrrd planes.csv results/quickstart.mp4
```

## Submitted demonstrations

| Video | Input CSV | Content |
|---|---|---|
| [MRI raw output](results/demo.mp4) | [demo_planes.csv](results/demo_planes.csv) | 60 ordered planes, 30 seconds at 2 FPS |
| [MRI presentation](results/showcase.mp4) | Same 60 planes | 720p explanatory presentation, 36 seconds |
| [Biscuit output](results/biscuit.mp4) | [biscuit_cake.csv](examples/biscuit_cake.csv) | 120 ordered trapezoids, 60 seconds |
| [Croissant output](results/croissant.mp4) | [croissant.csv](examples/croissant.csv) | 100 ordered triangles, 50 seconds |

The raw videos have exactly one frame per CSV row. The separate MRI
presentation repeats images and adds labels. The croissant CSV changes
positions and angles sharply; its video deliberately follows that order,
so it is a collection of different cuts rather than a smooth scan.

```bash
python Ex0.py data/biscuit_cake.nrrd examples/biscuit_cake.csv results/biscuit.mp4
python Ex0.py data/croissant.nrrd examples/croissant.csv results/croissant.mp4
python -m scripts.create_demo data/MRHead_1.nrrd
python -m scripts.create_demo data/MRHead_1.nrrd --verify-only
```

Biscuit and croissant NRRDs are user-supplied local datasets; they are not
required to run the public MRI or synthetic examples.

## Input and numerical contract

- Volume: three axes of size 1..1023; uint8, uint16 or uint32. Signed int16
  is additionally supported for the MRI sample.
- Coordinates: finite voxel indices `M[x,y,z]`, loaded with `index_order="F"`.
  NRRD physical origin, directions and spacing are not applied.
- Triangle points `(a,b,c)`: nonzero area and `abs(dist(a,b)-dist(a,c)) < 0.001`.
- Trapezoid points `(a1,a2,b,c)`: equal legs within the same strict tolerance,
  coplanar points, parallel directed bases, nonzero area and first base no
  longer than the second. Equal bases are accepted with roundoff handling.
- Sampling: nearest neighbor `floor(p+0.5)`. Exterior positions return zero;
  computed scanlines allow only machine-roundoff deviations at volume edges.
- Outputs use `E[row,column]` and retain the source dtype. Video display is
  globally normalized, centered and padded to common even dimensions.
- Invalid files, populated CSV rows and geometry fail explicitly. CLI errors
  exit with status 2 and preserve an existing output video.

The assignment leaves several rasterization details unspecified.
[ALGORITHM.md](docs/ALGORITHM.md) defines dimensions, rounding, centering,
fractional triangle overshoot and the trapezoid endpoint convention.

## CSV formats

The assignment's numbered-coordinate schema:

```csv
Number of Points (3 or 4),x1,y1,z1,x2,y2,z2,x3,y3,z3,x4,y4,z4
3,128,70,25,128,170,25,128,70,125,,,
4,128,80,40,128,120,40,128,60,100,128,140,100
```

The original named-coordinate schema is also accepted:

```csv
type,ax,ay,az,bx,by,bz,cx,cy,cz,dx,dy,dz
triangle,128,70,25,128,170,25,128,70,125,,,
trapezoid,128,80,40,128,120,40,128,60,100,128,140,100
```

An optional metadata/index column is ignored. Headers tolerate surrounding
spaces and a UTF-8 BOM. Triangles may omit fourth-point columns. Completely
empty rows are ignored; malformed populated rows report their CSV line.
The assignment sheet's captured fixture is in `tests/fixtures/`; its last
two records parse but fail the stated equal-leg geometry requirement.

## Verify and measure

```bash
python -m unittest discover -s tests -v
python -m scripts.create_demo data/MRHead_1.nrrd --verify-only
python -m scripts.benchmark_suite --json results/benchmark.json
```

The benchmark measures eight geometries in C and Fortran memory layouts on
a seeded 500^3 uint8 volume. Each case has three warmups and three trials of
40 projections. Computation includes validation, allocation and sampling;
NRRD loading, video encoding and compilation warmup are excluded.
[RESULTS.md](docs/RESULTS.md) summarizes the final measured rates and limits.
Playback FPS is separate from computation FPS.

## Submission map

| Assignment deliverable | Location |
|---|---|
| Problem, scope and repository | This README and Git history |
| Software requirements | [SRS.md](docs/SRS.md) |
| Detailed algorithm | [ALGORITHM.md](docs/ALGORITHM.md) |
| NRRD dataset definition | [DATASET.md](docs/DATASET.md) |
| Testing strategy | [TESTING.md](docs/TESTING.md) and `tests/` |
| Implementation | `projection.py`, `Ex0.py`, `scripts/` |
| Required main and MP4 demonstration | Commands above and `results/demo.mp4` |
| Experiment and short results | [RESULTS.md](docs/RESULTS.md), `results/benchmark.json` |

[ASSIGNMENT_COMPLIANCE.md](docs/ASSIGNMENT_COMPLIANCE.md) provides the complete
requirement checklist. [DEMO.md](docs/DEMO.md) explains the MRI presentation.
[CHANGELOG.md](docs/CHANGELOG.md) preserves development history.

`results/` contains submitted videos and current evidence. Earlier benchmark
reports remain available in Git history. `examples/` holds additional CSV
inputs; large volumes and local generated files are ignored.

Limitations: all projection matrices are retained until encoding, so memory
grows with the CSV length. Nearest-neighbor sampling can alias. Very large
coordinates can allocate large canvases. Physical-coordinate conversion and
GPU processing are outside scope.
