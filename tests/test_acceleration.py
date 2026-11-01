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

    def test_fortran_traversal_on_tilted_and_exterior_planes(self):
        rng = np.random.default_rng(42)
        volume = np.asfortranarray(rng.integers(0, 2**32, (24, 24, 24), dtype=np.uint32))
        for case in range(12):
            basis, _ = np.linalg.qr(rng.normal(size=(3, 3)))
            u, v = basis[:, 0], basis[:, 1]
            center = rng.uniform(0, 24, size=3)
            length = rng.uniform(.3, 16)
            triangle = (center, center+length*u, center+length*v)
            trapezoid = (center-2*u, center+2*u,
                         center-5*u+length*v, center+5*u+length*v)
            for function, points in ((projection.project_triangle, triangle),
                                     (projection.project_trapezoid, trapezoid)):
                with self.subTest(case=case, shape=function.__name__):
                    np.testing.assert_array_equal(function(volume, *points), reference(volume, points))


if __name__ == "__main__":
    unittest.main()
