# Assignment traceability and acceptance

Reviewed directly against all three pages of I2SE_Exe1.docx.pdf on 2026-11-01.
Source PDF SHA256:
e6bb89907679be00be0cbe4f9768cb2f85e5815dd576adbd38d059745fe5dae8.

This document maps the user's requested implementation work to the assignment.
External links and examples are treated as reference material. They do not
override the mathematical input checks or the one-frame-per-CSV-row contract.

## Page 3 deliverables

| Item | Requirement | Implementation / evidence |
|---|---|---|
| 1 | Repository, problem and scope in README | README.md; meaningful retained Git history |
| 2 | SRS | docs/SRS.md, explicit functional/nonfunctional requirements and acceptance mapping |
| 3 | Detailed algorithm | docs/ALGORITHM.md: validation, normalized unit steps, centering, rounding, trapezoid extension, complexity and compilation |
| 4 | Defined NRRD dataset | docs/DATASET.md; real MRHead provenance and verified voxel hash; generator for all unsigned dtypes |
| 5 | Testing strategy including the demo | docs/TESTING.md; complete scalar-reference images and real NRRD/CSV/MP4 integration |
| 6 | Implementation and frequent commits | projection.py, Ex0.py, scripts/ and tests/; focused commits with validation and document updates |
| 7 | python Ex0.py file.nrrd file.csv file.mp4 | Ex0.py; both CSV schemas; raw results/demo.mp4 contains exactly 60 ordered CSV projections |
| 8 | Experiment, short results and MP4 | docs/RESULTS.md; source-hashed timing JSON, 500^3 input, results/demo.mp4 and the explanatory results/showcase.mp4 |

## Algorithm and Q&A acceptance

| Requirement | Defined behavior and check |
|---|---|
| Three axes with 1 <= size < 2^10 | validate_volume; invalid-volume tests |
| Unsigned 8/16/32-bit entries | Exact dtype extrema and generated NRRD round trips; signed int16 extension supports the supplied MRI |
| Isosceles triangle | Strict abs(leg1-leg2) < 0.001, positive edges and noncollinearity |
| Four points | Equal legs within the same EPS; upper base <= lower, including equality; parallel directed bases, coplanarity, nonzero area |
| Normalized vectors and unit steps | No ceil-interval interpolation; hand-computed [232,322] first-row regression and independent full-image reference |
| Exterior samples are zero | Continuous bounds checked before nearest-neighbor rounding; partial/full exterior tests |
| Correct placement in E | E[row,column]; geometric floor centering, padding for the noninteger triangle loop's overshoot |
| Floating integer boundaries | Eight-ULP stabilization for floor/ceil and centering; independent rotated-rectangle and true-fraction tests |
| At least 30 computation FPS; 100 expected | Repeated 500^3 tests across 16 size/orientation/layout combinations, with cold compilation separate; see RESULTS for per-case values and limits |

The PDF does not fully define noninteger matrix dimensions, floating voxel
rounding, trapezoid starting/ending scanlines or video playback rate. The
explicit choices in ALGORITHM/SRS resolve those points without redistributing
the provided unit steps. Eight-ULP stabilization is numerical roundoff handling,
not a relaxation of the strict leg EPS.

## Demo acceptance and reproduction

Full reconstruction:

```bash
python -m scripts.create_demo data/MRHead_1.nrrd
```

This creates sixty valid numbered-coordinate CSV rows:
twenty equal-base rectangular slices, twenty isosceles triangles, and twenty
tilted trapezoids. The raw MP4 is 30 seconds at 2 FPS, 216 x 182 pixels,
with exactly one projection per row. The explanatory 1280 x 720 presentation
is 36 seconds at 12 FPS, with titles, a current-plane diagram and a progress
indicator. It repeats each projection for readability; it is supplemental
to the raw submission clip.

Reproduce the required raw main entry point directly:

```bash
python Ex0.py data/MRHead_1.nrrd results/demo_planes.csv results/demo.mp4
```

Decode and verify existing results:

```bash
python -m scripts.create_demo data/MRHead_1.nrrd --verify-only
python -m unittest discover -s tests -v
```

demo-manifest.json records every ordered plane and playback decision.
demo-validation.json records 60 decoded raw frames, their ordered projection
comparisons, 432 decoded presentation frames, codecs and uniform dimensions.
Six presentation frames, covering title, each section and the ending, were
also visually inspected for layout and image visibility.

## Linked references

The PDF links to [3D Slicer](https://www.slicer.org/), an
[original MRI download](https://drive.google.com/file/d/1cqqOgSf8k4e14K5CBs-V_EvMmATX1K-J/view?usp=sharing),
an [SRS reference](https://en.wikipedia.org/wiki/Software_requirements_specification)
and the [CSV example sheet](https://docs.google.com/spreadsheets/d/1Tfy1yMYhAJjRBA8ZpRp_07pZXqGtxWhWoP02yZW1FQE/edit?usp=sharing).
The local MRI was already verified voxel-for-voxel against Slicer's
checksum-addressed canonical download; see DATASET. The captured CSV fixture
preserves the linked example. Its third and fourth shapes have unequal legs
and remain explicit geometry failures, although their format parses.

## Practical limits

Final acceptance in the original .venv: all 41 tests passed, both complete
videos decoded and all raw CSV comparisons passed. The final sixteen-case
benchmark is results/benchmark-submission-env.json: every mean exceeds
100 FPS (lowest 104.42), with a slowest individual trial of 98.81 FPS.

Measured warm throughput is not a universal guarantee for all possible planes
or machines. The first Numba signature compilation can take seconds.
Earlier environments include cases near or below the expected 100 FPS target;
all measured trials exceed the mandatory 30 FPS minimum. Physical-coordinate
resampling, clinical interpretation and an unlimited-size streaming pipeline
are outside this assignment's implemented scope.
