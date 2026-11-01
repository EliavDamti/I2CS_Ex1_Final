import unittest
import numpy as np
from projection import project_trapezoid
from tests.reference import reference


class TrapezoidTests(unittest.TestCase):
    def test_coordinate_values_in_every_row(self):
        x, y, z = np.indices((10, 10, 10))
        volume = (x + 10*y + 100*z).astype(np.uint16)
        points = ((2, 3, 2), (2, 5, 2), (2, 2, 4), (2, 6, 4))
        actual = project_trapezoid(volume, *points)
        self.assertEqual(actual.shape, (3, 5))
        np.testing.assert_array_equal(actual[0], [0, 232, 242, 252, 0])
        np.testing.assert_array_equal(actual, reference(volume, points))

    def test_rectangle_includes_both_integer_end_bases(self):
        volume = np.arange(1000, dtype=np.uint16).reshape(10, 10, 10)
        points = ((2, 3, 2), (2, 5, 2), (2, 3, 4), (2, 5, 4))
        actual = project_trapezoid(volume, *points)
        self.assertEqual(actual.shape, (3, 3))
        np.testing.assert_array_equal(actual, reference(volume, points))

    def test_equal_base_sheared_parallelogram(self):
        volume = np.full((10, 10, 10), 123, dtype=np.uint8)
        points = ((2, 2, 2), (2, 4, 2), (2, 3, 5), (2, 5, 5))
        np.testing.assert_array_equal(project_trapezoid(volume, *points), reference(volume, points))


if __name__ == "__main__":
    unittest.main()
