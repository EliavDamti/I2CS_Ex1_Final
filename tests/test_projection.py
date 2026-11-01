import unittest
import numpy as np
from projection import project_triangle, project_trapezoid
from tests.reference import reference


class ProjectionTests(unittest.TestCase):
    def test_unsigned_extremes_are_preserved(self):
        triangle = ((2, 2, 2), (2, 6, 2), (2, 2, 6))
        rectangle = ((2, 2, 2), (2, 6, 2), (2, 2, 6), (2, 6, 6))
        for dtype in (np.uint8, np.uint16, np.uint32, np.int16):
            volume = np.full((10, 10, 10), np.iinfo(dtype).max, dtype=dtype)
            for function, points in ((project_triangle, triangle), (project_trapezoid, rectangle)):
                with self.subTest(dtype=dtype, shape=function.__name__):
                    actual = function(volume, *points)
                    self.assertEqual(actual.dtype, volume.dtype)
                    np.testing.assert_array_equal(actual, reference(volume, points))
                    self.assertEqual(actual.max(), np.iinfo(dtype).max)

    def test_negative_mri_intensities(self):
        volume = np.full((10, 10, 10), -1234, dtype=np.int16)
        actual = project_triangle(volume, (2, 2, 2), (2, 6, 2), (2, 2, 6))
        self.assertIn(-1234, actual)


if __name__ == "__main__":
    unittest.main()
