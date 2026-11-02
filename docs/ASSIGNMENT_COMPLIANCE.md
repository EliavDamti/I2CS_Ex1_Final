# Assignment requirements and submission checklist

The implementation was reviewed against all three pages of the supplied
I2SE_Exe1.docx.pdf. Source PDF SHA256:
`e6bb89907679be00be0cbe4f9768cb2f85e5815dd576adbd38d059745fe5dae8`.
Final submission review: 2026-11-02.

## Required deliverables

| Item | Requirement | Submitted evidence |
|---|---|---|
| 1 | Repository, problem and scope | README.md and incremental Git history |
| 2 | Software requirements specification | docs/SRS.md |
| 3 | Detailed algorithm | docs/ALGORITHM.md |
| 4 | Defined NRRD dataset | docs/DATASET.md; verified public MRI download and unsigned generators |
| 5 | Testing strategy including the demo | docs/TESTING.md; 45 passing tests and actual codec integration |
| 6 | Implementation and frequent commits | projection.py, Ex0.py, scripts/, tests/ and Git history |
| 7 | python Ex0.py file.nrrd file.csv file.mp4 | Ex0.py; results/demo_planes.csv and results/demo.mp4 |
| 8 | Experiment, short results and MP4 | docs/RESULTS.md; results/benchmark.json and submitted videos |

The required raw MRI output contains exactly 60 frames in CSV order. The
432-frame labeled presentation is supplemental. Biscuit and croissant are
additional examples, with CSV inputs in examples/ and output videos in
results/. Large local NRRD binaries are excluded; DATASET defines how to
obtain or generate the reproducible public inputs.

## Algorithm and performance checks

- Three-dimensional arrays with 1 <= each size < 1024.
- Exact uint8/uint16/uint32 values and dtype before video display conversion.
- Triangle legs differ by strictly less than EPS=0.001.
- Trapezoids enforce equal legs, upper base <= lower base (including equality),
  coplanarity, directed parallel bases and nonzero area.
- Normalized unit steps on edges and scanlines, geometric centering and zero
  exterior samples; only machine-roundoff allowance at computed volume edges.
- Nearest-neighbor sampling and all unspecified rasterization choices are
  documented explicitly, as the assignment asks for detailed design.
- Repeated 500^3 uint8 benchmarks include large/tilted projections in C and F
  layouts. RESULTS reports the mandatory >30 FPS threshold and the expected
  100 FPS target separately, using final measured data rather than old runs.

The PDF does not precisely define noninteger output dimensions, floating
voxel rounding, initial/final trapezoid scanlines or playback speed.
ALGORITHM documents those decisions. No requirement for Java or an
object-oriented class hierarchy is added to the permitted Python solution.

## Reproduce acceptance

```bash
python -m pip install -r requirements-lock.txt
python -m unittest discover -s tests -v
python -m scripts.create_demo data/MRHead_1.nrrd --verify-only
python -m scripts.benchmark_suite --json results/benchmark.json
```

See README for the canonical MRI download alternative and the required main
command. Compilation warmup, NRRD loading and video encoding are excluded
from computation FPS and reported as limitations rather than hidden costs.
