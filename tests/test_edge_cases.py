import unittest
import numpy as np
from projection import project_triangle, project_trapezoid, sample_volume


class InvalidInputTests(unittest.TestCase):
    def setUp(self):
        self.volume = np.ones((10, 10, 10), dtype=np.uint8)

    def test_bad_volume_shape_and_dtype(self):
        for volume in (None, np.zeros((3, 3)), np.zeros((0, 3, 3), dtype=np.uint8),
                       np.zeros((1024, 1, 1), dtype=np.uint8),
                       np.zeros((3, 3, 3), dtype=np.float64)):
            for function, points in ((project_triangle, ((2, 2, 2), (2, 6, 2), (2, 2, 6))),
                                     (sample_volume, ((1, 1, 1),))):
                with self.subTest(shape=getattr(volume, "shape", None), function=function.__name__):
                    with self.assertRaises(ValueError):
                        function(volume, *points)

    def test_malformed_vertices(self):
        for point in ((1, 2), (np.nan, 2, 3), (1, np.inf, 3), ("bad", 2, 3)):
            with self.subTest(point=point):
                with self.assertRaises(ValueError):
                    project_triangle(self.volume, point, (2, 6, 2), (2, 2, 6))
                with self.assertRaises(ValueError):
                    sample_volume(self.volume, point)

    def test_collinear_equal_legs_and_duplicate_vertices(self):
        for points in (((2, 4, 2), (2, 2, 2), (2, 6, 2)),
                       ((2, 2, 2), (2, 2, 2), (2, 2, 2))):
            with self.assertRaises(ValueError):
                project_triangle(self.volume, *points)

    def test_invalid_trapezoids(self):
        cases = {
            "unequal legs": ((2, 3, 2), (2, 5, 2), (2, 2, 4), (2, 7, 4)),
            "reversed bases": ((2, 2, 2), (2, 6, 2), (2, 3, 4), (2, 5, 4)),
            "opposite bases": ((2, 3, 2), (2, 5, 2), (2, 6, 4), (2, 2, 4)),
            "zero area": ((2, 2, 2), (2, 4, 2), (2, 3, 2), (2, 5, 2)),
            "zero edge": ((2, 2, 2), (2, 2, 2), (2, 3, 4), (2, 5, 4)),
            "nonparallel equal legs": ((2, 2, 2), (2, 4, 2), (2, 2, 4), (2, 6, 2)),
            "noncoplanar equal legs": ((2, 3, 2), (2, 5, 2), (1, 2, 4), (3, 6, 4)),
        }
        for name, points in cases.items():
            with self.subTest(name=name):
                with self.assertRaises(ValueError):
                    project_trapezoid(self.volume, *points)


if __name__ == "__main__":
    unittest.main()
