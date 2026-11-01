import unittest
import numpy as np
from projection import project_triangle, project_trapezoid


class AssignmentGeometryTests(unittest.TestCase):
    def test_rotated_equal_bases_from_biscuit_csv(self):
        # These bases differ by one ULP after parsing rounded CSV coordinates.
        points = ((84.59417127, -44.49601041, 97.49942825),
                  (-42.90582873, 176.34046756, 97.49942825),
                  (297.90582873, 78.65953244, 31.50057175),
                  (170.40582873, 299.49601041, 31.50057175))
        volume = np.ones((1, 1, 1), dtype=np.uint8)
        result = project_trapezoid(volume, *points)
        self.assertTrue(result.size)

    def test_genuinely_longer_first_base_still_rejected(self):
        # Much smaller than leg EPS, but well above floating-point roundoff.
        points = ((2, 3-5e-11, 2), (2, 5+5e-11, 2),
                  (2, 3, 4), (2, 5, 4))
        volume = np.ones((10, 10, 10), dtype=np.uint8)
        with self.assertRaisesRegex(ValueError, "First trapezoid base"):
            project_trapezoid(volume, *points)

    def test_triangle_absolute_epsilon_at_different_scales(self):
        volume = np.ones((10, 10, 10), dtype=np.uint8)
        for length in (1., 4., 100.):
            for difference, accepted in ((.0005, True), (.000999, True), (.001001, False), (.002, False)):
                with self.subTest(length=length, difference=difference):
                    points = ((0, 0, 0), (0, length, 0), (0, 0, length + difference))
                    if accepted:
                        project_triangle(volume, *points)
                    else:
                        with self.assertRaises(ValueError):
                            project_triangle(volume, *points)
        # At the strict boundary, no nonzero tolerance is added.
        with self.assertRaises(ValueError):
            project_triangle(volume, (0, 0, 0), (0, .001, 0), (0, 0, .002))

    def test_trapezoid_epsilon_with_parallel_bases(self):
        volume = np.ones((10, 10, 10), dtype=np.uint8)
        for shift, accepted in ((.0002, True), (.0005, True), (.002, False)):
            points = ((2, 3, 2), (2, 5, 2), (2, 2+shift, 4), (2, 6+shift, 4))
            with self.subTest(shift=shift):
                if accepted:
                    project_trapezoid(volume, *points)
                else:
                    with self.assertRaises(ValueError):
                        project_trapezoid(volume, *points)

    def test_assignment_rectangle(self):
        volume = np.ones((1, 1, 1), dtype=np.uint8)
        result = project_trapezoid(volume, (200, 0, 0), (200, 0, 500),
                                   (200, 400, 0), (200, 400, 500))
        self.assertEqual(result.shape, (401, 501))
        self.assertFalse(result.any())


if __name__ == "__main__":
    unittest.main()
