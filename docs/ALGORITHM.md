# Projection design

## Contract and coordinates

The volume is indexed as M[x,y,z]; the returned image is E[row,column].
Coordinates are voxel indices, not physical LPS/RAS millimeters. NRRD loading
uses index_order="F". Projection output retains the input integer dtype and
intensities; only the video display is normalized.

Accepted volume shapes have 1 <= size < 1024 on each of three axes. The
assignment dtypes are uint8, uint16 and uint32. Signed int16 is an explicit
extension for the MRHead sample. Unsupported dtypes, empty volumes, malformed
vertices and NaN/infinite coordinates raise ValueError.

## Geometry

Triangle input is (a,b,c). All edges have positive length, the vertices are
noncollinear, and abs(norm(b-a)-norm(c-a)) < 0.001. This is an absolute
tolerance in voxel units; it is independent of edge length. Equality at 0.001
is rejected using the computed float64 lengths.

Trapezoid input is (a1,a2,b,c). The bases are a1->a2 and b->c, and the legs
are a1->b and a2->c. The legs satisfy the same strict absolute tolerance.
The first base must be no longer than the second, including equality.
For that ordering comparison only, a difference up to eight ULPs at the
larger base length is treated as numerical equality. Rotated equal bases
serialized to CSV can otherwise differ by one or two ULPs after norm
evaluation. A real reversal, even 1e-10, is still rejected; the 0.001 leg
tolerance is not applied to base ordering.
Rectangles and sheared equal-base parallelograms are accepted.

All four edges must be nonzero. Bases must point in the same direction and
their unit-vector cross-product norm must be <= 1e-6. The plane normal is
cross(top_unit,left_unit); a norm <= 1e-10 rejects zero area. Coplanarity uses
distance to that plane <= 1e-6 * max(base lengths, left leg length).
The last two tolerances address floating-point geometry, not leg equality.

## Triangle: preserve the supplied unit steps

Let L=norm(b-a), R=norm(c-a), B=norm(c-b). Define
u=(b-a)/L and v=(c-a)/R, each a unit vector.

The supplied loop is integer y=0 while y<L, stepping both endpoints BEFORE
sampling. Accordingly there are ceil(L) rows:
s=y+1, start=a+s*u, end=a+s*v.
There is no division by ceil(L) and no redistribution between endpoints.

For each row d=norm(end-start), direction=(end-start)/d. For integer j>=0
while j<=d, sample start+j*direction. Thus there are floor(d)+1 samples.
The endpoint is included only if it lies at an integer unit distance.
This reproduces [232,322] in the review's first-row counterexample.

For noninteger L the supplied y<L loop takes one step past the left endpoint.
We preserve that behavior explicitly; we do not clamp the last row to b/c.
For unequal legs within EPS, each leg uses its own normalized direction.

## Trapezoid extension

The assignment says to extend the method to trapezoids but does not specify
the initial row or endpoint loop. We include the upper base at s=0, then take
unit steps with integer s<=left_leg_length. Height=floor(left_leg_length)+1.
The lower base appears exactly when the leg length is an integer. We do not
append a shorter final step or interpolate the final row to the lower base.
Both leg directions are independently normalized. The horizontal unit-step
loop is identical to the triangle loop.

This explicit extension differs from the earlier endpoint-interpolation
implementation, which always included both bases using ceil(L)+1 rows.

## Rasterization, centering and zero background

Before floor/ceil of distances or centering offsets, values within eight
float64 ULPs of an integer are snapped to that integer. This prevents a
rotated length-4 edge from losing its last sample because a norm evaluates
to 3.9999999999999996. This numerical roundoff rule is independent of the
strict 0.001 leg tolerance; an actual fraction such as 4+1e-10 is preserved.

The assignment's geometric row offset is floor((B-d)/2). Samples occupy
offset+j, without replacing geometric centering with pixel-count centering.
The nominal canvas width is ceil(B)+1. A final overshooting triangle row can
have a negative offset: shift every row right by -min(0,min(offset)) and
enlarge the canvas if necessary so no requested sample is discarded.
All unspecified output pixels are zero.

A sample is valid only when each continuous coordinate lies in [0,size-1].
Nearest-neighbor indexing is floor(coordinate+0.5), including half ties
toward the higher index. Bounds are checked BEFORE rounding. Background and
out-of-volume samples remain zero, including with signed int16 input.

## Pseudocode

1. Validate volume, finite vertices, equal-leg tolerance and shape geometry.
2. Generate scanline endpoints at the unit distances defined above.
3. For each row calculate d, floor(d)+1 and geometric offset.
4. Allocate a zero canvas with the source dtype, padding overshooting rows.
5. For each j<=d compute start+j*unit_direction.
6. Check continuous bounds; round valid points and copy M[x,y,z].
7. Return the complete image. File I/O and video encoding are separate.

## Acceleration, complexity and verification

Geometry and row metadata are calculated with NumPy. The sampling loop is
compiled with Numba njit(cache=True), without fastmath or parallel threads.
It compares volume-stride address displacements along a row and between
scanlines, then traverses rows or local sample columns for locality. In column
order, local sample j stays fixed across rows; centering does not alter the
sampling coordinates. Ragged-column traversal may also check inactive slots.
It copies each valid requested voxel directly to
the output. No H*W*3 coordinate tensor or full-canvas index grids are needed.
Numba caches compiled machine code; no geometry, volume or projection result
is cached. Every call validates the input and allocates/recomputes its output.

For H rows, W canvas columns and S requested samples, time is O(H+S+H*W)
including zero allocation; storage is O(H*W) for the output and O(H) for
scanline metadata. Compilation is lazy per dtype/layout signature: first use
can take seconds. Benchmarks explicitly warm signatures before timing and
report first-call timings separately. All dependency installation is through
requirements.txt; GPU hardware or a separately installed C compiler is not
needed when supported Numba wheels are available.

A NumPy fallback is used when Numba is absent or the source has nonnative byte
order. It generates axis-wise coordinate/index grids in 32-row blocks, uses
constant-axis specialization when possible and retains exactly the same
continuous-bound and rounding policies. Its temporary storage is O(32*W+H)
beyond the output. It is verified for correctness, but its throughput is not
claimed to meet the large-plane performance requirement. The complete test
suite checks that an installed accelerator actually compiles and runs.

The Numba usage follows its
[official JIT documentation](https://numba.readthedocs.io/en/stable/user/jit.html).

The independent scalar reference in tests/reference.py uses math distances,
scalar coordinate arithmetic and individual voxel reads. Tests compare every
pixel across fractional and tilted planes, axis permutations, noncontiguous
arrays and out-of-volume regions. Twenty-four seeded random orientations are
also checked for each shape. Hand-computed regression rows verify the
unit-step change separately. Backend tests exercise the NumPy fallback and
nonnative byte order as well as the default compiled path.

Nearest-neighbor aliasing, physical-coordinate conversion, interpolation,
GPU execution and streaming an unbounded number of video frames are outside
the current scope. Runtime depends on projection size and hardware.
