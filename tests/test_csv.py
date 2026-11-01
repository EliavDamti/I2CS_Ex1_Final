import tempfile
from pathlib import Path
import unittest
from Ex0 import read_planes


NAMED = "type,ax,ay,az,bx,by,bz,cx,cy,cz,dx,dy,dz"
NUMBERED = ",Number of Points (3 or 4),x1,y1,z1,x2,y2,z2,x3,y3,z3,x4,y4,z4"


class CSVTests(unittest.TestCase):
    def parse(self, text):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "planes.csv"
            path.write_text(text, encoding="utf-8")
            return read_planes(path)

    def test_assignment_fixture_order_and_points(self):
        planes = read_planes(Path(__file__).parent / "fixtures" / "assignment-example.csv")
        self.assertEqual([kind for kind, _ in planes], ["triangle", "trapezoid", "triangle", "trapezoid"])
        self.assertEqual(planes[1][1], ((200, 0, 0), (200, 0, 500), (200, 400, 0), (200, 400, 500)))

    def test_bom_whitespace_and_blank_lines(self):
        planes = self.parse("\ufeff " + NAMED.replace(",", ", ") +
                            "\n\ntriangle,2,2,2,2,6,2,2,2,6,,,\n,,,,,,,,,,,,\n")
        self.assertEqual(len(planes), 1)

    def test_triangle_only_header(self):
        planes = self.parse("type,ax,ay,az,bx,by,bz,cx,cy,cz\ntriangle,2,2,2,2,6,2,2,2,6\n")
        self.assertEqual(planes[0][0], "triangle")

    def test_schemas_map_to_identical_points(self):
        named = self.parse(NAMED + "\ntrapezoid,2,2,2,2,6,2,2,2,6,2,6,6\n")
        numbered = self.parse(NUMBERED + "\n0,4,2,2,2,2,6,2,2,2,6,2,6,6\n")
        self.assertEqual(named, numbered)

    def test_populated_invalid_rows_are_never_skipped(self):
        records = (
            ",2,2,2,2,6,2,2,2,6,,,",
            "circle,2,2,2,2,6,2,2,2,6,,,",
            "triangle,nan,2,2,2,6,2,2,2,6,,,",
            "triangle,inf,2,2,2,6,2,2,2,6,,,",
            "triangle,bad,2,2,2,6,2,2,2,6,,,",
            "triangle,2,2,2",
            "trapezoid,2,2,2,2,6,2,2,2,6,,,",
            "triangle,2,2,2,2,6,2,2,2,6,,,,EXTRA",
        )
        for record in records:
            with self.subTest(record=record):
                with self.assertRaisesRegex(ValueError, "CSV row 3"):
                    self.parse(NAMED + "\ntriangle,2,2,2,2,6,2,2,2,6,,,\n" + record)

    def test_numbered_point_counts(self):
        for count in ("", "2", "5", "3.0"):
            with self.subTest(count=count):
                with self.assertRaisesRegex(ValueError, "CSV row 2"):
                    self.parse(NUMBERED + "\n0," + count + ",2,2,2,2,6,2,2,2,6,,,")

    def test_bad_headers_and_empty_files(self):
        for text in ("", NAMED, "type,ax,ay\ntriangle,1,2",
                     NAMED + ",ax\n", NAMED + ",Number of Points (3 or 4)\n"):
            with self.subTest(text=text):
                with self.assertRaises(ValueError):
                    self.parse(text)


if __name__ == "__main__":
    unittest.main()
