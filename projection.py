"""Unit-distance scanline projections in voxel-index coordinates."""

import math
import numpy as np

try:
    from numba import njit
except ImportError:
    njit = None

GEOMETRY_EPS = 0.001
BACKEND = "numba" if njit is not None else "numpy"


def _fill_scanlines(volume, result, starts, directions, counts, offsets, column_major=False):
    """Streaming scalar kernel, compiled without fast-math reassociation."""
    sx, sy, sz = volume.shape
    # Arithmetic on normalized vectors can put an exact boundary endpoint
    # a few ULPs outside the volume (for example 25 * (7 / 25) > 7).
    epsilon = 8 * np.finfo(np.float64).eps
    tx, ty, tz = epsilon * max(1, sx-1), epsilon * max(1, sy-1), epsilon * max(1, sz-1)
    outer_count = int(counts.max()) if column_major else len(starts)
    for outer in range(outer_count):
        inner_count = len(starts) if column_major else counts[outer]
        for inner in range(inner_count):
            row = inner if column_major else outer
            j = outer if column_major else inner
            if j < 0 or j >= counts[row]:
                continue
            x = starts[row, 0] + j * directions[row, 0]
            y = starts[row, 1] + j * directions[row, 1]
            z = starts[row, 2] + j * directions[row, 2]
            if -tx <= x <= sx - 1 + tx and -ty <= y <= sy - 1 + ty and -tz <= z <= sz - 1 + tz:
                result[row, offsets[row] + j] = volume[
                    math.floor(x + 0.5), math.floor(y + 0.5), math.floor(z + 0.5)]


_fill_scanlines_compiled = njit(cache=True)(_fill_scanlines) if njit is not None else None


def _snap_integer(values):
    """Remove norm/centering roundoff within eight float64 ULPs of an integer."""
    values = np.asarray(values)
    nearest = np.rint(values)
    tolerance = 8 * np.spacing(np.maximum(1.0, np.abs(values)))
    return np.where(np.abs(values - nearest) <= tolerance, nearest, values)


def validate_volume(volume):
    """Accept assignment unsigned integers and the signed-short MRI sample."""
    if not isinstance(volume, np.ndarray) or volume.ndim != 3:
        raise ValueError("Volume must be a 3-dimensional NumPy array")
    if any(size < 1 or size >= 1024 for size in volume.shape):
        raise ValueError("Each volume dimension must be between 1 and 1023")
    if (volume.dtype.kind, volume.dtype.itemsize) not in {
        ("u", 1), ("u", 2), ("u", 4), ("i", 2)
    }:
        raise ValueError("Volume dtype must be uint8, uint16, uint32 or int16")


def _vertices(*points):
    try:
        points = [np.asarray(point, dtype=np.float64) for point in points]
    except (ValueError, TypeError, OverflowError) as error:
        raise ValueError("Vertices must be finite 3D points") from error
    if any(point.shape != (3,) or not np.all(np.isfinite(point))
           for point in points):
        raise ValueError("Vertices must be finite 3D points")
    return points


def sample_volume(volume, point):
    """Nearest voxel; continuous positions outside [0, size-1] return zero."""
    validate_volume(volume)
    point, = _vertices(point)
    if np.any(point < 0) or np.any(point > np.asarray(volume.shape) - 1):
        return 0
    return volume[tuple(np.floor(point + 0.5).astype(np.intp))]


def _scanlines(volume, starts, ends, base_length):
    """Sample integer unit distances, preserving geometric row centering."""
    differences = ends - starts
    lengths = np.linalg.norm(differences, axis=1)
    counts = np.floor(_snap_integer(lengths)).astype(np.intp) + 1
    offsets = np.floor(_snap_integer((base_length - lengths) / 2)).astype(np.intp)
    # The y < Dab loop can extend the last row past a noninteger leg.
    # Add background columns if needed; never clip a requested sample.
    offsets -= min(0, int(offsets.min()))
    width = max(int(np.ceil(_snap_integer(base_length))) + 1, int(np.max(offsets + counts)))
    result = np.zeros((len(starts), width), dtype=volume.dtype)
    directions = np.divide(differences, lengths[:, None],
                           out=np.zeros_like(differences), where=lengths[:, None] != 0)
    if _fill_scanlines_compiled is not None and volume.dtype.isnative:
        # Compare address displacements in the two traversal directions.
        # Local sample j stays constant across rows, independent of padding.
        strides = np.asarray(volume.strides)
        column_major = len(starts) > 1 and (
            abs(np.dot(starts[1] - starts[0], strides))
            < abs(np.dot(directions[-1], strides))
        )
        _fill_scanlines_compiled(volume, result, starts, directions, counts, offsets,
                                 column_major)
        return result
    return _fill_scanlines_numpy(volume, result, starts, directions, counts, offsets)


def _fill_scanlines_numpy(volume, result, starts, directions, counts, offsets):
    """Portable fallback, also supporting nonnative byte order."""
    width = result.shape[1]
    constant_axes = {}
    for axis, size in enumerate(volume.shape):
        tolerance = 8 * np.finfo(np.float64).eps * max(1, size-1)
        if np.all(directions[:, axis] == 0) and np.all(starts[:, axis] == starts[0, axis]):
            coordinate = starts[0, axis]
            if coordinate < -tolerance or coordinate > size - 1 + tolerance:
                return result
            constant_axes[axis] = int(np.floor(coordinate + 0.5))
    columns = np.arange(width)[None, :]
    # Small row blocks keep temporary coordinate/index grids in cache.
    # Axis-by-axis generation avoids a full H*W*3 point tensor.
    for first in range(0, len(starts), 32):
        last = min(first + 32, len(starts))
        local = columns - offsets[first:last, None]
        valid = (local >= 0) & (local < counts[first:last, None])
        indices = []
        for axis, size in enumerate(volume.shape):
            if axis in constant_axes:
                indices.append(constant_axes[axis])
                continue
            coordinate = (starts[first:last, axis, None]
                          + local * directions[first:last, axis, None])
            tolerance = 8 * np.finfo(np.float64).eps * max(1, size-1)
            valid &= (coordinate >= -tolerance) & (coordinate <= size - 1 + tolerance)
            # Clamp arithmetic roundoff at a boundary and make masked indices
            # safe to convert; genuinely exterior samples remain invalid.
            np.clip(coordinate, 0, size - 1, out=coordinate)
            coordinate += 0.5
            np.floor(coordinate, out=coordinate)
            indices.append(coordinate.astype(np.intp))
        if np.any(valid):
            selection = tuple(index if np.isscalar(index) else index[valid] for index in indices)
            result[first:last][valid] = volume[selection]
    return result


def project_triangle(volume, a, b, c):
    """Follow the assignment's y < Dab loop and normalized unit vectors."""
    validate_volume(volume)
    a, b, c = _vertices(a, b, c)
    ab, ac = b - a, c - a
    dab, dac, dbc = (np.linalg.norm(vector) for vector in (ab, ac, c - b))
    if not np.all(np.isfinite([dab, dac, dbc])) or min(dab, dac, dbc) <= 0:
        raise ValueError("Degenerate triangle")
    if abs(dab - dac) >= GEOMETRY_EPS:
        raise ValueError("Triangle must be isosceles: leg difference < 0.001")
    if np.linalg.norm(np.cross(ab / dab, ac / dac)) <= 1e-10:
        raise ValueError("Triangle vertices are collinear")
    steps = np.arange(1, int(np.ceil(_snap_integer(dab))) + 1)[:, None]
    return _scanlines(volume, a + steps * (ab / dab),
                      a + steps * (ac / dac), dbc)


def project_trapezoid(volume, a1, a2, b, c):
    """Include the upper base, then take unit steps while distance <= leg."""
    validate_volume(volume)
    a1, a2, b, c = _vertices(a1, a2, b, c)
    left, right, top, bottom = b - a1, c - a2, a2 - a1, c - b
    ll, rl, tl, bl = (np.linalg.norm(v) for v in (left, right, top, bottom))
    if not np.all(np.isfinite([ll, rl, tl, bl])) or min(ll, rl, tl, bl) <= 0:
        raise ValueError("Degenerate trapezoid")
    if abs(ll - rl) >= GEOMETRY_EPS:
        raise ValueError("Trapezoid leg difference must be < 0.001")
    # Equal rotated bases can differ by a few ULPs after coordinate
    # subtraction and norm evaluation. This is roundoff, not leg EPS.
    base_roundoff = 8 * np.spacing(max(tl, bl))
    if tl - bl > base_roundoff:
        raise ValueError("First trapezoid base must not exceed second base")
    if np.linalg.norm(np.cross(top / tl, bottom / bl)) > 1e-6 or np.dot(top / tl, bottom / bl) <= 0:
        raise ValueError("Trapezoid bases must be parallel and have the same direction")
    normal = np.cross(top / tl, left / ll)
    normal_length = np.linalg.norm(normal)
    if normal_length <= 1e-10:
        raise ValueError("Degenerate trapezoid area")
    if abs(np.dot(c - a1, normal / normal_length)) > 1e-6 * max(tl, bl, ll):
        raise ValueError("Trapezoid vertices must be coplanar")
    steps = np.arange(int(np.floor(_snap_integer(ll))) + 1)[:, None]
    return _scanlines(volume, a1 + steps * (left / ll),
                      a2 + steps * (right / rl), bl)
