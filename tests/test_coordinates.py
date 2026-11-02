import unittest
from unittest.mock import patch
import numpy as np
import projection
from projection import project_triangle, project_trapezoid, sample_volume
from tests.reference import reference


class CoordinateTests(unittest.TestCase):
    def setUp(self):
        x, y, z = np.indices((10, 10, 10))
        self.volume = (x + 10*y + 100*z).astype(np.uint16)

    def test_assignment_unit_step_regression(self):
        actual = project_triangle(self.volume, (2, 2, 2), (2, 6, 2), (2, 2, 6))
        np.testing.assert_array_equal(actual[0], [0, 0, 232, 322, 0, 0, 0])
        np.testing.assert_array_equal(actual[-1], [262, 352, 352, 442, 532, 622, 0])
        np.testing.assert_array_equal(actual, reference(self.volume, ((2, 2, 2), (2, 6, 2), (2, 2, 6))))

    def test_fractional_and_oblique_planes(self):
        # Equal, orthogonal legs in a plane tilted across all three axes.
        origin = np.array([2.13, 2.17, 2.19])
        u = np.array([1., 1., 0.]) / np.sqrt(2)
        v = np.array([-1., 1., 2.]) / np.sqrt(6)
        for length in (.4, 1.7, 3., 4.3):
            triangle = (origin, origin + length*u, origin + length*v)
            trapezoid = (origin - .4*u, origin + .4*u,
                         origin - 1.2*u + length*v, origin + 1.2*u + length*v)
            for function, points in ((project_triangle, triangle), (project_trapezoid, trapezoid)):
                with self.subTest(length=length, shape=function.__name__):
                    np.testing.assert_array_equal(function(self.volume, *points), reference(self.volume, points))

    def test_axis_permutations_and_noncontiguous_volume(self):
        points = np.array([[2.13, 2.17, 2.19], [2.13, 6.17, 2.19], [2.13, 2.17, 6.19]])
        for axes in ((0, 1, 2), (1, 2, 0), (2, 0, 1)):
            volume = self.volume.transpose(axes)
            transformed = points[:, axes]
            np.testing.assert_array_equal(project_triangle(volume, *transformed), reference(volume, transformed))
        view = self.volume[::-1, :, ::-1]
        np.testing.assert_array_equal(project_triangle(view, *points), reference(view, points))

    def test_rounding_and_continuous_bounds(self):
        self.assertEqual(sample_volume(self.volume, (2.5, 3.5, 4.5)), 543)
        self.assertEqual(sample_volume(self.volume, (-.01, 3, 4)), 0)
        self.assertEqual(sample_volume(self.volume, (9.01, 3, 4)), 0)
        self.assertEqual(sample_volume(self.volume, (9, 9, 9)), 999)

    def test_partially_and_fully_outside(self):
        for shift in (-4.13, -30.13, 30.13):
            points = np.array([[2., 2., 2.], [2., 6., 2.], [2., 2., 6.]]) + shift
            np.testing.assert_array_equal(project_triangle(self.volume, *points), reference(self.volume, points))

    def test_seeded_random_full_image_comparisons(self):
        rng = np.random.default_rng(20261101)
        volume = rng.integers(0, 65536, (24, 24, 24), dtype=np.uint16)
        for case in range(24):
            basis, _ = np.linalg.qr(rng.normal(size=(3, 3)))
            u, v = basis[:, 0], basis[:, 1]
            origin = rng.uniform(4, 19, size=3)
            length = rng.uniform(.2, 16)
            top, bottom = sorted(rng.uniform(.3, 8, size=2))
            triangle = (origin, origin + length*u, origin + length*v)
            trapezoid = (origin-top*u/2, origin+top*u/2,
                         origin-bottom*u/2+length*v, origin+bottom*u/2+length*v)
            for function, points in ((project_triangle, triangle), (project_trapezoid, trapezoid)):
                with self.subTest(case=case, shape=function.__name__):
                    np.testing.assert_array_equal(function(volume, *points), reference(volume, points))

    def test_rotated_integer_rectangle_has_no_missing_edge_samples(self):
        volume = np.full((24, 24, 24), 123, dtype=np.uint8)
        origin = np.array([6.13, 6.17, 6.19])
        u = np.array([1., 1., 0.]) / np.sqrt(2)
        v = np.array([-1., 1., 2.]) / np.sqrt(6)
        points = (origin, origin+4*u, origin+3*v, origin+4*u+3*v)
        actual = project_trapezoid(volume, *points)
        np.testing.assert_array_equal(actual, np.full((4, 5), 123, dtype=np.uint8))

    def test_real_noninteger_leg_is_not_snapped_away(self):
        length = 4 + 1e-10
        actual = project_triangle(self.volume, (2, 2, 2), (2, 2+length, 2), (2, 2, 2+length))
        self.assertEqual(actual.shape[0], 5)

    def test_rotated_rectangle_preserves_exact_volume_boundary(self):
        # A 7-24-25 edge ends at x=7, but float64 produces 7+1 ULP.
        # Expected pixels are analytic, independent of the scalar reference.
        points = np.array(((0, 0, 0), (7, 24, 0), (0, 0, 1), (7, 24, 1)), dtype=float)
        volume = np.full((8, 25, 2), 123, dtype=np.uint8)
        for fallback in (False, True):
            backend = None if fallback else projection._fill_scanlines_compiled
            with patch('projection._fill_scanlines_compiled', backend):
                for axes in ((0, 1, 2), (1, 2, 0), (2, 0, 1)):
                    with self.subTest(fallback=fallback, axes=axes):
                        data, vertices = volume.transpose(axes), points[:, axes]
                        np.testing.assert_array_equal(project_trapezoid(data, *vertices),
                                                      np.full((2, 26), 123, dtype=np.uint8))
                        # Shift the entire plane genuinely beyond a boundary.
                        outside = vertices.copy()
                        flat_axis = axes.index(2)
                        outside[:, flat_axis] += 1 + 1e-8
                        self.assertFalse(project_trapezoid(data, *outside).any())

    def test_explicit_outside_sample_is_not_clamped(self):
        # The roundoff allowance applies to computed scanlines, not user points.
        self.assertEqual(sample_volume(self.volume, (9+1e-12, 3, 4)), 0)
        self.assertEqual(sample_volume(self.volume, (-1e-12, 3, 4)), 0)


if __name__ == "__main__":
    unittest.main()
