# I2SE Ex1 — 3D volume plane projection

Extract isosceles triangle and trapezoid slices from a 3D NRRD volume and
encode one MP4 frame per CSV record, in order.

The implementation follows the assignment's normalized **unit-distance**
scanline steps. Projection matrices preserve source integer intensities.
Nearest-neighbor voxel sampling uses floor(p+0.5); positions outside the
continuous volume bounds return zero.

## Setup

Use Python 3.10 or later:

```bash
python -m pip install -r requirements.txt
```

Numba compiles the sampling loop on its first use for each dtype/layout.
Allow for that startup cost; subsequent projections reuse the compiled code.
Install all requirements to use the measured performance path. A portable
NumPy fallback preserves correctness when Numba is unavailable.

Windows virtual environment:

```powershell
py -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
```

Run the following commands from the repository root. On Windows, substitute
.\.venv\Scripts\python.exe for python when using that environment.

If pip reports UnicodeEncodeError in a Windows terminal, use UTF-8 mode:

```powershell
.\.venv\Scripts\python.exe -X utf8 -m pip install --progress-bar off -r requirements.txt
```

## Run the demonstration

Place MRHead_1.nrrd in data/; provenance, download links and checksums are in
[DATASET.md](docs/DATASET.md).

```bash
python Ex0.py data/MRHead_1.nrrd planes.csv results/demo.mp4
```

[View the MRI demonstration](results/demo.mp4).
The playback rate is 2 FPS; projection throughput is measured separately.

For a verified public MRI download or a reproducible synthetic demo:

```bash
python -m scripts.download_mri
python -m scripts.generate_datasets
python Ex0.py data/generated/synthetic-uint32.nrrd data/generated/planes.csv results/synthetic-uint32.mp4
```

The downloader saves data/MRHead-canonical.nrrd, verifies Slicer's SHA256
and refuses to replace an existing file. The generator requires no network.

## Input contract

- Volume: three axes, each size 1..1023; uint8, uint16 or uint32.
  Signed int16 is also supported for the MRHead sample.
- Coordinates: finite voxel indices M[x,y,z], independent of NRRD physical
  origin/directions. The reader uses index_order="F".
- Triangle: vertices (a,b,c), nonzero area, abs(dist(a,b)-dist(a,c)) < 0.001.
- Trapezoid: (a1,a2,b,c), equal legs within the same strict absolute tolerance,
  nonzero area, coplanar points and parallel bases with matching direction.
  dist(a1,a2) <= dist(b,c); equal bases and rectangles are valid.
- Returned arrays use E[row,column]. They retain the input dtype.
- Invalid files, populated CSV records and geometry fail explicitly.
  CLI errors exit with status 2 and do not replace an existing output video.

The triangle's integer y<Dab loop may step beyond a noninteger leg, as in the
assignment. For trapezoids, the documented extension starts at the upper base
and takes whole unit steps while distance <= left-leg length. Sampling,
centering, padding and numerical tolerances are defined in
[ALGORITHM.md](docs/ALGORITHM.md).

## CSV formats

Both schemas are accepted automatically. An optional index/metadata column
is ignored. Headers tolerate surrounding spaces and a UTF-8 BOM.

Assignment example schema:

```csv
Number of Points (3 or 4),x1,y1,z1,x2,y2,z2,x3,y3,z3,x4,y4,z4
3,128,70,25,128,170,25,128,70,125,,,
4,128,80,40,128,120,40,128,60,100,128,140,100
```

Original repository schema, retained for compatibility:

```csv
type,ax,ay,az,bx,by,bz,cx,cy,cz,dx,dy,dz
triangle,128,70,25,128,170,25,128,70,125,,,
trapezoid,128,80,40,128,120,40,128,60,100,128,140,100
```

For three points the columns represent (a,b,c); for four they represent
(a1,a2,b,c). A triangle-only file may omit the fourth point's columns.
Every populated row requires a valid type/count and all used coordinates.
Completely empty rows are ignored; malformed rows report their CSV line.

The [linked assignment sheet](https://docs.google.com/spreadsheets/d/1Tfy1yMYhAJjRBA8ZpRp_07pZXqGtxWhWoP02yZW1FQE/edit)
is captured in tests/fixtures/assignment-example.csv. Its header and all four
records parse, including its rectangle. Its third and fourth records have
unequal legs and are rejected during geometry validation; format compatibility
does not bypass the assignment's mathematical input requirements.

## Tests

```bash
python -m unittest discover -s tests -v
```

An individual module can also run as:

```bash
python -m tests.test_coordinates
```

Tests include complete image comparisons against an independent scalar
reference, hand-computed unit-step regressions, EPS boundaries, invalid
trapezoids, tilted planes, all unsigned dtypes, both CSV schemas and real
NRRD->CSV->MP4 encoding/decoding. See [TESTING.md](docs/TESTING.md).

## Performance

```bash
python -m scripts.benchmark_suite --json results/benchmark-current.json
python -m scripts.benchmark
python -m scripts.benchmark_trapezoid
```

These measure computation including geometry validation and allocation,
excluding NRRD loading and video encoding. Output size and orientation affect
throughput. See [RESULTS.md](docs/RESULTS.md) for reproducible measurements;
a fast small plane alone does not establish the over-30-FPS requirement for
larger planes.

The suite covers eight geometries in both C and Fortran memory order on a
seeded random 500^3 uint8 volume. It records three warmups and three trials
of forty timed projections, plus environment details and individual timings.

## Layout and documents

| Path | Purpose |
|---|---|
| projection.py | Geometry validation and unit-distance projection |
| Ex0.py | CSV parsing, normalization and atomic MP4 creation |
| planes.csv | Three MRI demonstration planes |
| tests/ | Discoverable unit tests, scalar reference and CSV fixture |
| scripts/ | Benchmark, MRI PNG and metadata tools |
| docs/SRS.md | Requirements and acceptance criteria |
| docs/ALGORITHM.md | Numerical contract, pseudocode and complexity |
| docs/DATASET.md | Dataset definition and provenance |
| docs/TESTING.md | Verification strategy and coverage |
| docs/RESULTS.md | Measured experiments and limitations |
| docs/CHANGELOG.md | Detailed changes since the reviewed baseline |

The application keeps all computed projections in memory before encoding.
Nearest-neighbor sampling can alias. Physical-coordinate conversion and GPU
execution are outside scope. Large coordinate magnitudes can produce large
canvases even for small input volumes.
