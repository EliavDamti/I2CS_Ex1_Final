"""Slow scalar reference, independent of the NumPy projection kernel."""
import math
import numpy as np


def stable(value):
    integer = round(value)
    return integer if abs(value-integer) <= 8*math.ulp(max(1., abs(value))) else value


def reference(volume, points):
    if len(points) == 3:
        a, b, c = points
        left = [b[k] - a[k] for k in range(3)]
        right = [c[k] - a[k] for k in range(3)]
        origin_left = origin_right = a
        base = math.dist(b, c)
        steps = range(1, math.ceil(stable(math.dist(a, b))) + 1)
    else:
        a1, a2, b, c = points
        left = [b[k] - a1[k] for k in range(3)]
        right = [c[k] - a2[k] for k in range(3)]
        origin_left, origin_right = a1, a2
        base = math.dist(b, c)
        steps = range(math.floor(stable(math.dist(a1, b))) + 1)
    ll = math.sqrt(sum(x*x for x in left))
    rl = math.sqrt(sum(x*x for x in right))
    rows = []
    for step in steps:
        start = [origin_left[k] + step * (left[k] / ll) for k in range(3)]
        end = [origin_right[k] + step * (right[k] / rl) for k in range(3)]
        length = math.dist(start, end)
        offset = math.floor(stable((base - length) / 2))
        values = []
        for j in range(math.floor(stable(length)) + 1):
            point = [start[k] + j * ((end[k] - start[k]) / length)
                     if length else start[k] for k in range(3)]
            if all(0 <= point[k] <= volume.shape[k] - 1 for k in range(3)):
                values.append(volume[tuple(math.floor(x + .5) for x in point)])
            else:
                values.append(0)
        rows.append((offset, values))
    pad = max(0, -min(offset for offset, _ in rows))
    width = max(math.ceil(stable(base)) + 1, max(offset + pad + len(v) for offset, v in rows))
    result = np.zeros((len(rows), width), dtype=volume.dtype)
    for y, (offset, values) in enumerate(rows):
        result[y, offset + pad:offset + pad + len(values)] = values
    return result
