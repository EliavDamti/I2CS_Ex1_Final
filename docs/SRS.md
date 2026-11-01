# Software Requirements Specification

Status: implemented contract, revised 2026-11-01.

## Scope

Extract triangular and trapezoidal voxel-index slices from a 3D NRRD volume
and encode one MP4 frame per CSV record, in the supplied order.
This is a scanline slice extraction, with no integration along viewing rays.
The entry point is python Ex0.py file.nrrd file.csv file.mp4.

## Functional requirements

| ID | Requirement | Acceptance |
|---|---|---|
| FR-01 | Load a three-dimensional NRRD with index_order="F". Each axis size is 1..1023. | NRRD integration and invalid-volume tests |
| FR-02 | Preserve uint8/uint16/uint32 intensities and dtype in projections. Also support int16 for MRHead. | Dtype extrema and negative-intensity tests |
| FR-03 | Validate finite 3D vertices, positive edges and nonzero area. | Invalid geometry tests |
| FR-04 | Accept triangle leg difference strictly below 0.001 voxel units. | Multi-scale EPS and strict-boundary tests |
| FR-05 | Accept equal trapezoid bases; require first base <= second, equal legs within EPS, parallel directed bases and coplanarity. | Rectangle, sheared parallelogram, invalid trapezoids |
| FR-06 | Follow normalized unit-distance steps on legs and scanlines. | Independent scalar reference and hand-computed rows |
| FR-07 | Use nearest neighbor floor(p+0.5); test continuous bounds before rounding; fill outside with zero. | Boundary and partial/full exterior tests |
| FR-08 | Return E[row,column], centered by the geometric offset; preserve all requested samples with background padding. | Full-matrix reference comparisons |
| FR-09 | Read ordered triangle/four-point CSV records with informative errors. | CSV parser tests |
| FR-10 | Encode one uniformly sized RGB H.264/yuv420p frame per record at 2 playback FPS. | Decode actual MP4, count frames, check dimensions and order |
| FR-11 | Normalize display globally, including zero, and center each projection on an even-sized canvas. | Normalization and video tests |
| FR-12 | Reject invalid files/records/geometry without silently losing a populated CSV record. | Negative CLI/parser tests |
| FR-13 | Provide reproducible unsigned NRRD generation and verified public MRI provenance. | Generator reload/hash tests and recorded MRI voxel comparison |

## Decisions resolving assignment ambiguities

ALGORITHM.md defines precise output dimensions, geometric centering, rounding,
triangle overshoot for noninteger legs and the trapezoid endpoint convention.
CSV schema and error behavior are documented in README.md and DATASET.md.
CSV coordinates refer to voxel indices, without applying the NRRD physical
origin, directions or anisotropic spacing.

## Nonfunctional requirements

- NFR-01: For a 500^3 byte volume, the assignment requires over 30 computation
  FPS and expects around 100 FPS. Benchmarks must include large and tilted
  projections, with hardware, dependency versions, repeated timings and output
  sizes recorded. This is distinct from the MP4 playback rate. Report each
  case individually; a small-plane result does not establish all-plane speed.
  The measured path uses the Numba dependency after warmup; first-use
  compilation is recorded separately and NumPy fallback speed is not assumed.
- NFR-02: Maintain independent expected-value tests, including the full
  NRRD->CSV->MP4 demonstration.
- NFR-03: Keep projection computation separate from parsing and video display.
- NFR-04: Use focused commits and update design, test and experiment records
  when behavior changes.
- NFR-05: Keep large MRI inputs out of Git; supply provenance, checksums and
  reproducible synthetic datasets.

## Errors and limits

Missing files, malformed CSV, unsupported volumes and invalid geometry must
fail explicitly. Projection functions raise ValueError. Encoding and filesystem
errors must propagate as failures. No records may be silently omitted apart
from completely empty CSV lines.

Finite coordinates outside the volume are allowed and yield zero samples.
Projection canvas size can exceed the volume bounds, so callers should avoid
unbounded coordinate magnitudes. There is no clinical diagnostic claim.
