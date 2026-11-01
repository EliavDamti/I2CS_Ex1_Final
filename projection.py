"""Unit-distance scanline projections in voxel-index coordinates."""

import numpy as np

GEOMETRY_EPS = 0.001


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
    counts = np.floor(lengths).astype(np.intp) + 1
    offsets = np.floor((base_length - lengths) / 2).astype(np.intp)
    # The y < Dab loop can extend the last row past a noninteger leg.
    # Add background columns if needed; never clip a requested sample.
    offsets -= min(0, int(offsets.min()))
    width = max(int(np.ceil(base_length)) + 1, int(np.max(offsets + counts)))
    result = np.zeros((len(starts), width), dtype=volume.dtype)
    for row, (start, delta, length, count, offset) in enumerate(
        zip(starts, differences, lengths, counts, offsets)
    ):
        direction = delta / length if length else np.zeros(3)
        points = start + np.arange(count)[:, None] * direction
        valid = np.all((points >= 0) & (points <= np.asarray(volume.shape) - 1), axis=1)
        indices = np.floor(points[valid] + 0.5).astype(np.intp)
        columns = np.arange(count)[valid] + offset
        result[row, columns] = volume[indices[:, 0], indices[:, 1], indices[:, 2]]
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
    steps = np.arange(1, int(np.ceil(dab)) + 1)[:, None]
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
    if tl > bl:
        raise ValueError("First trapezoid base must not exceed second base")
    if np.linalg.norm(np.cross(top / tl, bottom / bl)) > 1e-6 or np.dot(top / tl, bottom / bl) <= 0:
        raise ValueError("Trapezoid bases must be parallel and have the same direction")
    normal = np.cross(top / tl, left / ll)
    normal_length = np.linalg.norm(normal)
    if normal_length <= 1e-10:
        raise ValueError("Degenerate trapezoid area")
    if abs(np.dot(c - a1, normal / normal_length)) > 1e-6 * max(tl, bl, ll):
        raise ValueError("Trapezoid vertices must be coplanar")
    steps = np.arange(int(np.floor(ll)) + 1)[:, None]
    return _scanlines(volume, a1 + steps * (left / ll),
                      a2 + steps * (right / rl), bl)
