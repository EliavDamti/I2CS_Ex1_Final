import unittest
from unittest.mock import patch
import numpy as np

import projection
from tests.reference import reference


class AccelerationTests(unittest.TestCase):
    def test_installed_accelerator_is_active(self):
        self.assertEqual(projection.BACKEND, "numba", "Install all requirements for the compiled performance path")
        volume = np.ones((10, 10, 10), dtype=np.uint8)
        projection.project_triangle(volume, (2, 2, 2), (2, 6, 2), (2, 2, 6))
        self.assertTrue(projection._fill_scanlines_compiled.signatures)

    def test_numpy_fallback_matches_scalar_reference(self):
        x, y, z = np.indices((12, 12, 12))
        volume = (x+12*y+144*z).astype(np.uint16)
        shapes = (
            (projection.project_triangle, ((2.13, 2.17, 2.19), (2.13, 6.47, 2.19), (2.13, 2.17, 6.49))),
            (projection.project_trapezoid, ((2, 3, 2), (2, 5, 2), (2, 2, 4), (2, 6, 4))),
        )
        with patch("projection._fill_scanlines_compiled", None):
            for function, points in shapes:
                np.testing.assert_array_equal(function(volume, *points), reference(volume, points))

    def test_nonnative_byte_order_falls_back_without_value_loss(self):
        volume = np.arange(1000, dtype=np.uint16).reshape(10, 10, 10).astype(">u2")
        points = ((2, 2, 2), (2, 6, 2), (2, 2, 6))
        actual = projection.project_triangle(volume, *points)
        self.assertEqual(actual.dtype, volume.dtype)
        np.testing.assert_array_equal(actual, reference(volume, points))


if __name__ == "__main__":
    unittest.main()
